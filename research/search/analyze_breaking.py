"""Analysis of the breaking-target selectivity test (protocol Addendum A1).

``ring_n6`` with target ``alpha_1`` = invariant oracle + 1.0 x breaking component: the
declared group is NOT a label symmetry of this target, so a verifier that pushes the
search toward invariance must hurt here.  Comparing the same three LLM arms against the
same seeds on the invariant target (the frozen 120-run record) and on this breaking
target is the selectivity test: does the verifier's effect track the target's symmetry,
or is it just "extra feedback"?

Endpoints (all development risk on the run's own validation split; this is a NEW
prospective comparison, not a reanalysis of the frozen record):

* per-arm risk / accuracy / nonconstant / repair-fired / invalid-proposal counts;
* paired per-seed contrasts with the protocol's inference and Holm inside family E;
* verifier selectivity on this target: how many proposals carry a hypothesis, how many
  of them pass the label-preservation gate (which, on a breaking target, should reject
  any group that genuinely moves labels), and how many carry the task's declared group.

Usage::

    python3 -m research.search.analyze_breaking --dir logs/runs_breaking \
        --out research/search/breaking_target.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from research.core import paired  # noqa: E402
from research.core import tasks as _tasks  # noqa: E402
from research.search import refit as _refit  # noqa: E402
from research.search import verifier_bridge as vb  # noqa: E402
from research.search.dev_analysis import (_hyp_closure,  # noqa: E402 (internal reuse)
                                          _task_group_closure)

CONTRASTS = (("llm-verify", "llm-fitness"),
             ("llm-verify-repair", "llm-verify"),
             ("llm-verify-repair", "llm-fitness"),
             ("mutation-ea", "random"),
             ("llm-verify", "random"))


def _load(directory):
    runs = []
    for path in sorted(glob.glob(os.path.join(directory, "run_*.json"))):
        with open(path) as fh:
            log = json.load(fh)
        log["_path"] = path
        runs.append(log)
    return runs


def main(argv=None):
    a = argparse.ArgumentParser()
    a.add_argument("--dir", default="logs/runs_breaking")
    a.add_argument("--out", default="research/search/breaking_target.json")
    a.add_argument("--family", default="ring_n6")
    a.add_argument("--target", default="alpha_1")
    args = a.parse_args(argv)

    runs = _load(args.dir)
    tasks = {}
    rows, bad_target = [], []
    for log in runs:
        fam = log["family"]
        if fam not in tasks:
            tasks[fam] = _tasks.load_family(fam, development=True, locked=False)
        task = tasks[fam]
        if log.get("target") != args.target:
            bad_target.append(log["_path"])
            continue
        dev = np.asarray(task.splits["validation"], bool)
        key = log.get("target") or task.primary_target
        y = np.asarray(task.targets[key])[dev]
        x_dev = np.asarray(task.x)[dev]
        rep = log["best"].get("repair") or {}
        # deterministic refit of the selected candidate: gives accuracy, a nonconstant
        # check, and a reproduction check against the logged dev risk
        fit, _lp, _sc, _hist, check = _refit.refit_best(log, task=task)
        pred = _refit.predictions(fit, task, x_dev)
        rows.append({"arm": log["arm"], "seed": int(log["seed"]),
                     "dev_risk": float(log["best"]["dev_risk"]),
                     "refit_dev_risk": float(np.mean((pred - y) ** 2)),
                     "reproduction_abs_diff": float(check["abs_diff"]),
                     "accuracy": float(np.mean(np.sign(pred) == np.sign(y))),
                     "nonconstant": bool(np.std(pred) > 1e-8),
                     "repair_attempted": bool(rep.get("attempted", False)),
                     "repair_fired": bool(rep.get("repaired", False)),
                     "proposals_total": int(log["proposals_total"]),
                     "invalid_total": int(log["invalid_total"]),
                     "n_hyp": 0, "n_hyp_pass_gate": 0, "n_hyp_is_task_group": 0})
        closure = _task_group_closure(task)
        for p in log.get("proposals") or []:
            cand = p.get("candidate") or {}
            hyp = cand.get("hypothesis") or {}
            gens = hyp.get("generators")
            if not gens or not p.get("valid"):
                continue
            r = rows[-1]
            r["n_hyp"] += 1
            try:
                cl = _hyp_closure(task, gens)
                r["n_hyp_is_task_group"] += int(
                    len(cl) == len(closure) and set(map(tuple, cl)) == set(map(tuple, closure)))
            except Exception:
                pass
            try:
                lp = vb.label_preservation(task, hyp, 64)
                r["n_hyp_pass_gate"] += int(lp["violated_fraction"] == 0.0)
            except Exception:
                pass

    arms = {}
    for arm in sorted({r["arm"] for r in rows}):
        sub = [r for r in rows if r["arm"] == arm]
        arms[arm] = {
            "n": len(sub),
            "dev_risk_mean": float(np.mean([r["dev_risk"] for r in sub])),
            "dev_risk_sd": float(np.std([r["dev_risk"] for r in sub], ddof=1)) if len(sub) > 1 else None,
            "accuracy_mean": float(np.mean([r["accuracy"] for r in sub])),
            "n_nonconstant": int(sum(r["nonconstant"] for r in sub)),
            "max_refit_reproduction_abs_diff": float(
                max(r["reproduction_abs_diff"] for r in sub)),
            "n_repair_attempted": int(sum(r["repair_attempted"] for r in sub)),
            "n_repair_fired": int(sum(r["repair_fired"] for r in sub)),
            "proposals_total": int(sum(r["proposals_total"] for r in sub)),
            "invalid_total": int(sum(r["invalid_total"] for r in sub)),
            "proposals_with_hypothesis": int(sum(r["n_hyp"] for r in sub)),
            "hypotheses_passing_label_gate": int(sum(r["n_hyp_pass_gate"] for r in sub)),
            "hypotheses_equal_to_task_group": int(sum(r["n_hyp_is_task_group"] for r in sub)),
        }

    by = {(r["arm"], r["seed"]): r["dev_risk"] for r in rows}
    contrasts = []
    for a_arm, b_arm in CONTRASTS:
        seeds = sorted({s for (arm, s) in by if arm == a_arm} &
                       {s for (arm, s) in by if arm == b_arm})
        if not seeds:
            continue
        d = [by[(a_arm, s)] - by[(b_arm, s)] for s in seeds]
        boot = paired.bootstrap_ci(d)
        p_shift = paired.shifted_bootstrap_p(d)
        p_flip = paired.signflip_p(d)
        contrasts.append({"a": a_arm, "b": b_arm, "unit": "paired seed",
                          "n_pairs": len(d), "seeds": seeds, "diffs": d,
                          "mean_diff_a_minus_b": float(np.mean(d)),
                          "loo_range": paired.loo_range(d),
                          "bootstrap": boot, "p_shifted_bootstrap": p_shift,
                          "p_signflip": p_flip,
                          "verdict": paired.verdict(boot["ci95_low"], boot["ci95_high"])})
    for c, p in zip(contrasts, paired.holm([c["p_shifted_bootstrap"]["p"]
                                            for c in contrasts])):
        c["holm_p_within_family_E"] = p

    out = {"directory": args.dir, "family": args.family, "target": args.target,
           "scope": "development risk on the run's validation split; new prospective "
                    "comparison declared in REVISED_PROTOCOL.md Addendum A1",
           "prediction_declared_in_advance": "if the verifier's benefit came from pushing "
           "toward the declared group, it must turn negative on this target",
           "n_runs": len(rows), "skipped_wrong_target": bad_target,
           "arms": arms, "contrasts": contrasts}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote %s (%d runs)" % (args.out, len(rows)))
    for arm, v in arms.items():
        print("%-20s risk %.4f acc %.3f repair %d/%d fired hyp %d (pass %d, correct %d)"
              % (arm, v["dev_risk_mean"], v["accuracy_mean"], v["n_repair_fired"],
                 v["n_repair_attempted"], v["proposals_with_hypothesis"],
                 v["hypotheses_passing_label_gate"], v["hypotheses_equal_to_task_group"]))
    for c in contrasts:
        b, ps, pf = c["bootstrap"], c["p_shifted_bootstrap"], c["p_signflip"]
        def _s(v, spec="%.4g"):
            return "n/a" if v is None else spec % v
        print("  %-18s - %-18s n=%2d %+.5f CI[%s,%s] pB=%s%s pS=%s %s"
              % (c["a"], c["b"], c["n_pairs"], c["mean_diff_a_minus_b"],
                 _s(b["ci95_low"], "%+.5f"), _s(b["ci95_high"], "%+.5f"),
                 _s(ps["p"]), "" if ps.get("p_floor") is None
                 else " (floor %s)" % _s(ps["p_floor"]), _s(pf["p"]), c["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
