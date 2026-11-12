"""A5.4: is the verifier a *good decision rule* about when to repair?

The second-round referee's point 4 is correct as written: that declared-group averaging
helps non-LLM pipelines shows the averaging operation is useful, not that a verifier is
necessary, and it does not identify any decision rule. This module turns the question into
a measurable one.

**Decision problem (fixed in advance).** A pipeline holds a candidate predictor and a
supplied group (the task's declared group, which every arm could be given). Before
deployment it must decide: *apply the Reynolds average, or ship the raw predictor?* Five
rules, all evaluated on the same development rows and the same fitted predictors:

``R0_supplied_group``   always average.
``R1_label_gate``       average iff the supplied group passes the label-preservation test.
``R2_label_channel``    R1 **and** the channel residual is below the harness tolerance
                        (the gate the ``llm-verify-repair`` arm actually implements).
``R3_predictor_defect`` average iff the fitted predictor's own measured non-invariance
                        exceeds a development threshold (no verifier involved).
``R4_mismatch_control`` R2's decision, but averaging over a *mismatched* group (negative
                        control; defined only where a mismatched group exists).

Outcomes are paired per candidate: ``delta = risk_after - risk_before`` (negative helps).
Reported per rule: firing rate, mean delta over **all** candidates (intention-to-treat at
the decision level), precision, recall, mean harm among fired, mean missed gain among
not-fired. Thresholds come from development records only.

Monte-Carlo twirling is recorded per run (``exact``, ``n_elements``) because the graphs
declared group has order 720: exact-projection guarantees do not transfer to a 24-element
average, and the aggregate MC share is reported.

Usage::

    python3 -m research.search.decision_rules --runs logs/runs_confirm \\
        --out research/search/decision_rules.json [--workers 24]
"""
import argparse
import glob
import json
import multiprocessing as mp
import os
import time

import numpy as np

from research.core import paired as _P
from research.core import tasks as _tasks
from research.search import refit as _refit
from research.search import verifier_bridge as _vb

DEV_ROWS_MC = 256
MC_TWIRL_ELEMENTS = 24
CHANNEL_TOL = 1e-10            # harness verify_candidate tolerance
REPAIR_RESIDUAL_FLOOR = 1e-6   # harness REPAIR_RESIDUAL_FLOOR: repair fires ABOVE it
MC_SEED = 90210
_W = {}


def _average(fit, task, rows, elems):
    acc = None
    for perm in elems:
        v = np.asarray(_refit.predictions(fit, task,
                                          _vb.transform_rows(task, rows, perm)),
                       dtype=float).reshape(-1)
        acc = v if acc is None else acc + v
    return acc / len(elems)


def _mismatched_group(task, rng):
    """A group that is *not* a symmetry of the scored target, when one exists."""
    from verify import closure
    n = int(task.n_qubits)
    if not str(getattr(task, "name", "")).startswith("ring"):
        return None, ("no mismatched group exists: the scored target's label-symmetry "
                      "group is the full symmetric group")
    declared = set(closure([list(g) for g in task.generators], n))
    for _ in range(200):
        p = tuple(rng.permutation(n))
        if p in declared:
            continue
        H = closure([list(p)], n)
        if not set(H) <= declared:
            return H, None
    return None, "search for a mismatched group failed"


def analyse_run(path):
    log = _refit.load_run(path)
    task = _W["tasks"][log["family"]]
    dev = np.asarray(task.splits["validation"], bool)
    x_dev, y = np.asarray(task.x)[dev], np.asarray(task.targets[
        log.get("target") or task.primary_target])[dev]
    fit, _, _, _, check = _refit.refit_best(log, task=task)
    rng = np.random.default_rng(MC_SEED + int(log["seed"]))
    idx = rng.choice(len(x_dev), size=min(DEV_ROWS_MC, len(x_dev)), replace=False)
    rows, yy = x_dev[idx], y[idx]

    declared = _W["closures"][log["family"]]
    exact = len(declared) <= MC_TWIRL_ELEMENTS
    elems = declared if exact else [declared[i] for i in rng.choice(
        len(declared), size=MC_TWIRL_ELEMENTS, replace=False)]

    raw = np.asarray(_refit.predictions(fit, task, rows), dtype=float).reshape(-1)
    t0 = time.perf_counter()
    avg = _average(fit, task, rows, elems)
    t_average = time.perf_counter() - t0
    risk_before = float(np.mean((raw - yy) ** 2))
    risk_after = float(np.mean((avg - yy) ** 2))
    defect = float(np.mean((raw - avg) ** 2))          # R3 statistic

    cand = log["best"]["candidate"]
    params = _vb.sample_param_dicts(cand, rng, 3)
    # same call shape as the deployed gate in harness.py (no x override), but with the
    # task's declared group so every arm gets the same decision input
    t1 = time.perf_counter()
    chan = _vb.verify_candidate(cand, task, params, group="true")
    lab = _vb.label_preservation(task, {"generators": [list(g) for g in task.generators]},
                                 64)
    t_verify = time.perf_counter() - t1
    mm_group, mm_reason = _mismatched_group(task, rng)
    risk_mismatch = None
    if mm_group is not None:
        risk_mismatch = float(np.mean((_average(fit, task, rows, list(mm_group))
                                       - yy) ** 2))
    return {"path": path, "family": log["family"], "arm": log["arm"],
            "seed": int(log["seed"]), "reproduction": check,
            "n_rows": int(len(rows)), "twirl_exact": bool(exact),
            "n_elements": len(elems), "group_order": len(declared),
            "risk_before": risk_before, "risk_after_declared": risk_after,
            "delta_declared": risk_after - risk_before,
            "predictor_defect": defect,
            "channel_mean": chan["mean_channel_residual"],
            "channel_pass": bool(chan["sampled_pass"]),
            "channel_above_floor": bool(chan["mean_channel_residual"]
                                        > REPAIR_RESIDUAL_FLOOR),
            "label_pass": bool(lab["violated_fraction"] == 0.0),
            "seconds_to_verify": t_verify, "seconds_to_average": t_average,
            "risk_mismatch": risk_mismatch, "mismatch_reason": mm_reason,
            "delta_mismatch": (risk_mismatch - risk_before
                               if risk_mismatch is not None else None),
            "repair_fired_in_run": bool((log["best"].get("repair") or {}).get("repaired"))}


def _init(tasks, closures):
    _W["tasks"], _W["closures"] = tasks, closures


def _rule_metrics(rows, fired, delta_key="delta_declared"):
    d = np.array([r[delta_key] for r in rows], float)
    f = np.array(list(fired), bool)
    helped = d < 0
    harm = d[f & ~helped]
    missed = d[~f & helped]
    return {
        "n_candidates": int(len(rows)), "n_fired": int(f.sum()),
        "firing_rate": float(f.mean()) if len(rows) else None,
        # realised decision-level change: non-firing candidates contribute 0, so this
        # differs across rules (the unconditional mean delta is reported separately)
        "mean_realised_delta": float(d[f].sum() / len(rows)) if len(rows) else None,
        "mean_delta_if_always_applied": float(d.mean()) if len(rows) else None,
        "mean_delta_fired": float(d[f].mean()) if f.any() else None,
        "precision_helped_given_fired": _P.wilson_ci(int((f & helped).sum()), int(f.sum())),
        "recall_fired_given_helped": _P.wilson_ci(int((f & helped).sum()),
                                                  int(helped.sum())),
        "mean_harm_among_fired": float(harm.mean()) if harm.size else None,
        "n_harmed": int(harm.size),
        "mean_missed_gain": float(-missed.mean()) if missed.size else None,
        "n_missed_beneficial": int(missed.size),
        "total_missed_gain": float(-missed.sum()) if missed.size else 0.0}


def summarise(runs):
    out = {"protocol": "REVISED_PROTOCOL Addendum A5.4", "runs": runs, "families": {}}
    for fam in sorted({r["family"] for r in runs}):
        rs = [r for r in runs if r["family"] == fam]
        defects = np.array([r["predictor_defect"] for r in rs], float)
        taus = {"median": float(np.median(defects)),
                "q1": float(np.quantile(defects, 0.25)),
                "q3": float(np.quantile(defects, 0.75))}
        fired = {
            "R0_supplied_group": [True] * len(rs),
            "R1_label_gate": [r["label_pass"] for r in rs],
            # the rule the llm-verify-repair arm actually deploys: label test passes AND
            # channel residual ABOVE the floor (harness.REPAIR_RESIDUAL_FLOOR = 1e-6)
            "R2_deployed_gate": [r["label_pass"] and r["channel_above_floor"]
                                 for r in rs],
            # the opposite reading of "channel gate" (residual below tolerance), kept so
            # the two conventions cannot be confused
            "R2b_channel_below_tol": [r["label_pass"] and r["channel_pass"] for r in rs],
            "R3_predictor_defect_median": [r["predictor_defect"] > taus["median"]
                                           for r in rs],
            "R3_predictor_defect_q1": [r["predictor_defect"] > taus["q1"] for r in rs],
            "R3_predictor_defect_q3": [r["predictor_defect"] > taus["q3"] for r in rs],
        }
        fam_out = {"n_runs": len(rs), "thresholds": taus,
                   "cost": {"mean_seconds_to_verify":
                            float(np.mean([r["seconds_to_verify"] for r in rs])),
                            "mean_seconds_to_average":
                            float(np.mean([r["seconds_to_average"] for r in rs]))},
                   "mc_twirl_share": float(np.mean([not r["twirl_exact"] for r in rs])),
                   "rules": {k: _rule_metrics(rs, v) for k, v in fired.items()},
                   "by_arm": {}}
        for arm in sorted({r["arm"] for r in rs}):
            sub = [r for r in rs if r["arm"] == arm]
            fam_out["by_arm"][arm] = {
                "n": len(sub),
                "mean_delta_declared": float(np.mean([r["delta_declared"]
                                                      for r in sub])),
                "mean_predictor_defect": float(np.mean([r["predictor_defect"]
                                                        for r in sub])),
                "n_channel_pass": int(sum(r["channel_pass"] for r in sub)),
                "n_channel_above_floor": int(sum(r["channel_above_floor"] for r in sub)),
                "n_repair_fired_in_run": int(sum(r["repair_fired_in_run"]
                                                 for r in sub))}
        mm = [r for r in rs if r["delta_mismatch"] is not None]
        fam_out["R4_mismatch_control"] = {
            "n_candidates": len(mm),
            "mean_delta_mismatch": float(np.mean([r["delta_mismatch"] for r in mm]))
            if mm else None,
            "note": "negative control: R2's decision with a mismatched group"
            if mm else fired and "" or ""}
        if not mm:
            fam_out["R4_mismatch_control"]["note"] = (
                "undefined on this family: " + str(rs[0]["mismatch_reason"]))
        out["families"][fam] = fam_out
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="research/search/decision_rules.py")
    ap.add_argument("--runs", default="logs/runs_confirm")
    ap.add_argument("--out", default="research/search/decision_rules.json")
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args(argv)
    if "locked" in a.runs.lower() or "locked" in a.out.lower():
        raise SystemExit("decision_rules is development-only")
    paths = sorted(glob.glob(os.path.join(a.runs, "run_*.json")))
    families = sorted({_refit.load_run(p)["family"] for p in paths})
    tasks, closures = {}, {}
    from verify import closure as _closure
    for fam in families:
        tasks[fam] = _tasks.load_family(fam, development=True, locked=False)
        closures[fam] = _closure([list(g) for g in tasks[fam].generators],
                                 int(tasks[fam].n_qubits))
    ctx = mp.get_context("fork")
    with ctx.Pool(a.workers, initializer=_init, initargs=(tasks, closures)) as pool:
        runs = pool.map(analyse_run, paths, chunksize=1)
    bad = [r for r in runs if not r["reproduction"]["exact"]]
    print("refit reproduction: %d/%d exact, max abs diff %.2e"
          % (len(paths) - len(bad), len(paths),
             max(r["reproduction"]["abs_diff"] for r in runs)), flush=True)
    if bad:
        raise SystemExit("refit did not reproduce %d runs exactly; refusing to analyse"
                         % len(bad))
    out = summarise(runs)
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    for fam, d in out["families"].items():
        print("\n=== %s (%d runs, MC twirl share %.2f) ==="
              % (fam, d["n_runs"], d["mc_twirl_share"]))
        for rule, m in d["rules"].items():
            print("  %-28s fire %3d/%3d  realised delta %+.5f  (always-applied %+.5f)  "
                  "precision %s  recall %s  harmed %d  missed beneficial %d "
                  "(total gain %.4f)"
                  % (rule, m["n_fired"], m["n_candidates"], m["mean_realised_delta"],
                     m["mean_delta_if_always_applied"],
                     "%.2f" % (m["precision_helped_given_fired"]["rate"] or 0.0),
                     "%.2f" % (m["recall_fired_given_helped"]["rate"] or 0.0),
                     m["n_harmed"], m["n_missed_beneficial"],
                     m["total_missed_gain"] or 0.0))
        print("  R4 mismatch control:", json.dumps(d["R4_mismatch_control"]))
    print("\nwrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
