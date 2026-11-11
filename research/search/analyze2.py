"""WP-SEARCH reanalysis under ``research/REVISED_PROTOCOL.md`` section 3-4.

Fixes the four statistical defects the referee identified in ``analyze.py``
(kept unchanged as the exploratory record):

1. **The repair endpoint.** ``analyze.py`` compared ``best['dev_risk']`` for every
   arm, so the inference-time Reynolds average that ``llm-verify-repair`` deploys
   was never scored. Here it is: **E-S1** is the paired before/after effect of
   averaging on the *same frozen candidate*, **E-S2** compares the *deployed*
   pipelines (averaged predictor where the repair fired), and both are reported
   next to the coverage of the intervention (eligible / attempted / fired), which
   bounds what they can mean.
2. **The p-values.** Side-counting bootstrap "p-values" are replaced by the
   null-centred (shifted) bootstrap plus a sign-flip test with its symmetry
   assumption stated; simulated p-values carry a floor and are never 0.
3. **Multiplicity.** Families are declared (A = the two primary task-specific
   tests, D = the secondary contrasts of one family), Holm is applied within a
   family only, and raw CIs are labelled unadjusted.
4. **Null language.** A CI containing 0 yields "difference not detected", never
   "clean null" / "unchanged" / "does not improve". Practical equivalence is
   claimed only against the prespecified margin ``0.05 * Var_target``.

Usage::

    python3 -m research.search.analyze2 --dir logs/runs_confirm \\
        --out research/search/confirm_analysis2.json [--label confirmatory]
"""
import argparse
import glob
import json
import os

import numpy as np

from research.core import paired as _P
from research.core import tasks as _tasks

LLM_ARMS = ("llm-fitness", "llm-verify", "llm-verify-repair")
PRIMARY = ("llm-verify", "llm-fitness")
SECONDARY = [("llm-verify-repair", "llm-verify"),
             ("llm-fitness", "mutation-ea"),
             ("mutation-ea", "random"),
             ("llm-verify", "random"),
             ("llm-verify-repair", "llm-fitness")]
REF_TREATMENT = ("ycrc-local", "none")
MARGIN_FRACTION = 0.05                      # prespecified equivalence margin


# ------------------------------------------------------------------ load / index
def load_runs(directory):
    runs = []
    for path in sorted(glob.glob(os.path.join(directory, "run_*.json"))):
        with open(path) as fh:
            d = json.load(fh)
        rep = d["best"].get("repair") or {}
        props = d.get("proposals") or []
        valid = [p for p in props if p.get("valid")]
        runs.append({
            "path": path, "arm": d["arm"], "family": d["family"],
            "model": d.get("model"), "effort": d.get("reasoning_effort"),
            "seed": int(d["seed"]), "budget": d["budget"], "steps": d.get("steps"),
            "dev_risk": float(d["best"]["dev_risk"]),
            "invalid": int(d["invalid_total"]),
            "proposals_total": int(d["proposals_total"]),
            "evaluated_valid": int(d["evaluated_valid"]),
            "tokens": int(d["tokens"]["total_tokens"]),
            "wall_time": float(d.get("wall_time", 0.0)),
            "n_hypothesis": int(sum(1 for p in valid
                                    if (p.get("candidate") or {}).get("hypothesis")
                                    and (p["candidate"]["hypothesis"]
                                         .get("generators")))),
            "n_valid": len(valid),
            "repair_eligible_hypothesis": bool(rep.get("attempted", False)),
            "repair_fired": bool(rep.get("repaired", False)),
            "dev_risk_averaged": rep.get("dev_risk_repaired_diagnostic"),
            "repair_group_order": rep.get("group_order"),
            "repair_residual": rep.get("mean_channel_residual"),
            "git_commit": (d.get("metadata") or {}).get("git_commit"),
        })
    return runs


def _index(runs, arm, family, model=None, effort=None, endpoint="candidate"):
    out = {}
    for r in runs:
        if r["arm"] != arm or r["family"] != family:
            continue
        if arm in LLM_ARMS:
            if model is not None and (r["model"], r["effort"]) != (model, effort):
                continue
        elif r["model"] is not None:
            continue
        if endpoint == "deployed":
            value = r["dev_risk_averaged"] if r["repair_fired"] else r["dev_risk"]
        else:
            value = r["dev_risk"]
        out.setdefault(r["seed"], []).append(float(value))
    return {s: float(np.mean(v)) for s, v in out.items()}


def paired_diff(runs, a, b, family, ma=None, ea=None, mb=None, eb=None,
                endpoint="candidate"):
    ia = _index(runs, a, family, ma, ea, endpoint)
    ib = _index(runs, b, family, mb, eb, endpoint)
    seeds = sorted(set(ia) & set(ib))
    diffs = [ia[s] - ib[s] for s in seeds]          # a - b; negative => a better
    return {"a": a, "b": b, "family": family, "endpoint": endpoint,
            "model": ma if a in LLM_ARMS else mb,
            "effort": ea if a in LLM_ARMS else eb,
            "unit": "paired search run (seed)", "n_pairs": len(diffs),
            "seeds": seeds, "diffs": diffs,
            "mean_diff_a_minus_b": float(np.mean(diffs)) if diffs else None,
            "frac_a_better": float(np.mean([d < 0 for d in diffs])) if diffs else None}


def add_inference(c, margin=None, n_boot=20000, seed=13):
    d = c["diffs"]
    c["bootstrap"] = _P.bootstrap_ci(d, n_boot=n_boot, seed=seed)
    c["p_shifted_bootstrap"] = _P.shifted_bootstrap_p(d, n_boot=n_boot, seed=seed)
    c["p_signflip"] = _P.signflip_p(d, n_boot=200000, seed=seed)
    c["loo"] = _P.loo_range(d)
    c["equivalence"] = _P.equivalence(c["bootstrap"]["ci95_low"],
                                      c["bootstrap"]["ci95_high"], margin)
    c["verdict"] = _P.verdict(c["bootstrap"]["ci95_low"],
                              c["bootstrap"]["ci95_high"], margin)
    return c


# ------------------------------------------------------------- E-S1 / E-S2 repair
def repair_estimands(runs, family, margin):
    sub = [r for r in runs if r["family"] == family and r["arm"] == "llm-verify-repair"]
    coverage = {"n_runs": len(sub),
                "attempted (best candidate carried a hypothesis)":
                    int(sum(1 for r in sub if r["repair_eligible_hypothesis"])),
                "fired (label preservation passed and residual > tolerance)":
                    int(sum(1 for r in sub if r["repair_fired"]))}
    fired = [r for r in sub if r["repair_fired"] and r["dev_risk_averaged"] is not None]
    diffs = [r["dev_risk_averaged"] - r["dev_risk"] for r in fired]
    e1 = {"a": "averaged predictor", "b": "frozen candidate", "family": family,
          "estimand": "E-S1 paired effect of inference-time Reynolds averaging on "
                      "the same frozen dev-selected candidate",
          "unit": "run (coverage-conditional: only runs where the repair fired)",
          "n_pairs": len(diffs), "diffs": diffs,
          "coverage": coverage,
          "mean_diff_averaged_minus_candidate": float(np.mean(diffs)) if diffs else None,
          "frac_averaged_better": float(np.mean([d < 0 for d in diffs])) if diffs else None,
          "group_orders": sorted({r["repair_group_order"] for r in fired}),
          "limitation": "coverage-conditional; runs where the repair did not fire "
                        "contribute nothing, so this is not an intention-to-treat "
                        "effect for the arm"}
    e1.update({"bootstrap": _P.bootstrap_ci(diffs, seed=13),
               "p_shifted_bootstrap": _P.shifted_bootstrap_p(diffs, seed=13),
               "p_signflip": _P.signflip_p(diffs, seed=13),
               "loo": _P.loo_range(diffs)})
    e1["equivalence"] = _P.equivalence(e1["bootstrap"]["ci95_low"],
                                       e1["bootstrap"]["ci95_high"], margin)
    e1["verdict"] = _P.verdict(e1["bootstrap"]["ci95_low"],
                               e1["bootstrap"]["ci95_high"], margin)
    return e1


# ------------------------------------------------------------------- E-S4 reliability
def reliability(runs, family):
    sub = [r for r in runs if r["family"] == family]
    per_arm = {}
    for arm in sorted({r["arm"] for r in sub}):
        a = [r for r in sub if r["arm"] == arm]
        per_arm[arm] = {
            "n_runs": len(a),
            "mean_invalid_rate": float(np.mean([r["invalid"] / max(1, r["proposals_total"])
                                                for r in a])),
            "mean_hypothesis_rate": float(np.mean([r["n_hypothesis"] / max(1, r["n_valid"])
                                                   for r in a])),
            "mean_tokens": float(np.mean([r["tokens"] for r in a])),
            "mean_wall_time_s": float(np.mean([r["wall_time"] for r in a])),
            "mean_evaluated_valid": float(np.mean([r["evaluated_valid"] for r in a])),
            "mean_dev_risk": float(np.mean([r["dev_risk"] for r in a])),
        }
    # paired reliability contrast verify vs fitness (invalid rate, hypothesis rate)
    out = {"per_arm": per_arm, "paired": []}
    for metric in ("invalid", "n_hypothesis"):
        ia, ib = {}, {}
        for r in sub:
            if r["arm"] == "llm-verify":
                ia[r["seed"]] = r[metric] / max(1, r["proposals_total"]
                                                if metric == "invalid" else r["n_valid"])
            elif r["arm"] == "llm-fitness":
                ib[r["seed"]] = r[metric] / max(1, r["proposals_total"]
                                                if metric == "invalid" else r["n_valid"])
        seeds = sorted(set(ia) & set(ib))
        diffs = [ia[s] - ib[s] for s in seeds]
        c = {"metric": metric, "a": "llm-verify", "b": "llm-fitness",
             "family": family, "n_pairs": len(diffs), "diffs": diffs,
             "mean_diff_a_minus_b": float(np.mean(diffs)) if diffs else None}
        c.update({"bootstrap": _P.bootstrap_ci(diffs, seed=13),
                  "p_shifted_bootstrap": _P.shifted_bootstrap_p(diffs, seed=13)})
        c["verdict"] = _P.verdict(c["bootstrap"]["ci95_low"],
                                  c["bootstrap"]["ci95_high"])
        out["paired"].append(c)
    return out


# ------------------------------------------------------------------------- driver
def analyze(directory, label=""):
    runs = load_runs(directory)
    families = sorted({r["family"] for r in runs})
    treatments = sorted({(r["model"], r["effort"]) for r in runs
                         if r["arm"] in LLM_ARMS and r["model"]})
    margins = {}
    for fam in families:
        task = _tasks.load_family(fam, development=True, locked=False)
        y = np.asarray(task.targets[task.primary_target], float)
        dev = np.asarray(task.splits["validation"], bool)
        margins[fam] = {"var_target_dev": float(np.var(y[dev])),
                        "margin": MARGIN_FRACTION * float(np.var(y[dev]))}
    result = {"directory": directory, "label": label, "n_runs": len(runs),
              "families": families,
              "treatments": [list(t) for t in treatments],
              "endpoint_vocabulary": "development risk (validation split used by "
                                     "selection and feedback); NOT held out",
              "margins": margins, "primary": [], "secondary": [],
              "repair": [], "reliability": [],
              "inference": {"interval": "percentile bootstrap of mean paired "
                                        "difference, 20000 resamples of units",
                            "p": "null-centred bootstrap + sign-flip (symmetry "
                                 "assumption stated); floors reported, never 0",
                            "multiplicity": "Holm within declared family A "
                                            "(primaries) and per-family D (secondaries)"}}
    # family A: the two primary task-specific tests
    prim = []
    for fam in families:
        for (model, effort) in treatments:
            c = paired_diff(runs, PRIMARY[0], PRIMARY[1], fam, model, effort,
                            model, effort)
            c["estimand"] = "E-S3 development-selected risk, verifier vs fitness"
            prim.append(add_inference(c, margin=margins[fam]["margin"]))
    adj = _P.holm([c["p_shifted_bootstrap"]["p"] for c in prim])
    for c, a in zip(prim, adj):
        c["p_holm_family_A"] = float(a)
    result["primary"] = prim

    for fam in families:
        # family D: secondary contrasts within this family
        sec = []
        for (a, b) in SECONDARY:
            ma, ea = REF_TREATMENT if a in LLM_ARMS else (None, None)
            mb, eb = REF_TREATMENT if b in LLM_ARMS else (None, None)
            for endpoint in ("candidate", "deployed"):
                c = paired_diff(runs, a, b, fam, ma, ea, mb, eb, endpoint=endpoint)
                c["estimand"] = ("E-S2 deployed pipeline endpoint" if endpoint ==
                                 "deployed" else "candidate (unaveraged) endpoint")
                sec.append(add_inference(c, margin=margins[fam]["margin"]))
        adj = _P.holm([c["p_shifted_bootstrap"]["p"] for c in sec])
        for c, a_ in zip(sec, adj):
            c["p_holm_family_D"] = float(a_)
            c["p_holm_reported"] = ("< %.3g" % c["p_holm_family_D"])
            if c["p_holm_family_D"] <= c["p_shifted_bootstrap"].get("p_floor", 0):
                c["p_holm_family_D_note"] = "at the bootstrap resolution floor"
        result["secondary"].extend(sec)
        result["repair"].append(repair_estimands(runs, fam, margins[fam]["margin"]))
        result["reliability"].append(reliability(runs, fam))
    return result


def main(argv=None):
    p = argparse.ArgumentParser(prog="research/search/analyze2.py")
    p.add_argument("--dir", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--label", default="")
    a = p.parse_args(argv)
    res = analyze(a.dir, a.label)
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        with open(a.out, "w") as fh:
            json.dump(res, fh, indent=1, default=str)
    print("runs=%d families=%s" % (res["n_runs"], res["families"]))
    for c in res["primary"]:
        b = c["bootstrap"]
        print("\n[E-S3 primary] %-11s %-18s n=%d mean=%+.5f CI=[%+.5f,%+.5f] "
              "p_boot=%.4f p_flip=%.4f p_holm=%.4f -> %s"
              % (c["family"], "%s/%s" % (c["model"], c["effort"]), c["n_pairs"],
                 b["mean"], b["ci95_low"], b["ci95_high"],
                 c["p_shifted_bootstrap"]["p"], c["p_signflip"]["p"],
                 c["p_holm_family_A"], c["verdict"]))
        print("    leave-one-out mean range [%+.5f, %+.5f]; margin=%.5f"
              % (c["loo"]["loo_min"], c["loo"]["loo_max"],
                 res["margins"][c["family"]]["margin"]))
    for e in res["repair"]:
        b = e["bootstrap"]
        print("\n[E-S1 averaging] %-11s coverage=%s n_fired=%d mean=%s CI=[%s,%s] "
              "p_flip=%s -> %s"
              % (e["family"], e["coverage"], e["n_pairs"],
                 "n/a" if b["mean"] is None else "%+.5f" % b["mean"],
                 "n/a" if b["ci95_low"] is None else "%+.5f" % b["ci95_low"],
                 "n/a" if b["ci95_high"] is None else "%+.5f" % b["ci95_high"],
                 "n/a" if e["p_signflip"]["p"] is None else "%.4f" % e["p_signflip"]["p"],
                 e["verdict"]))
    for e in res["secondary"]:
        if e["endpoint"] != "deployed":
            continue
        b = e["bootstrap"]
        print("[E-S2 deployed] %-11s %-18s vs %-18s n=%d mean=%s CI=[%s,%s] "
              "p_holm=%.3g%s"
              % (e["family"], e["a"], e["b"], e["n_pairs"],
                 "n/a" if b["mean"] is None else "%+.5f" % b["mean"],
                 "n/a" if b["ci95_low"] is None else "%+.5f" % b["ci95_low"],
                 "n/a" if b["ci95_high"] is None else "%+.5f" % b["ci95_high"],
                 e["p_holm_family_D"],
                 " (at resolution floor)" if e.get("p_holm_family_D_note") else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
