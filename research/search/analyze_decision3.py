"""A7 analysis of the gate-parity decision comparison (decision_rules3.json).

The run stores the raw per-candidate, per-regime quantities; this module derives the decision
objects, so the objective can be decomposed without re-running the expensive pass. The
decomposition matters because the fourth-round review correctly pointed out that a single scalar
objective can charge evaluation work as deployment work: gate time and one-off averaging are paid
**per candidate screened during search**, while the extra inference time of an averaged predictor
is paid **per deployed prediction**. They are reported as separate components, and the combined
objective states that risk is a per-prediction rate (MSE) while the horizon term is cumulative.

Also computes, per the pre-declared categories in Addendum A7.5: whether either calibrated rule is
strictly best at any mixture weight and cost weight, and the point on the approximate-symmetry
continuum where the optimal decision flips.
"""

from __future__ import annotations

import argparse
import json

import numpy as np

W_GRID = [0.0, 1e-4, 1e-3, 1e-2, 1e-1, 1.0]
H = 1000


def components(cost):
    """Split cost into search-time and deployed parts (never merged silently)."""
    search = (cost["gate_seconds_per_candidate"]
              + cost["oneoff_averaging_seconds_per_candidate"])
    deployed = cost["per_prediction_overhead_seconds"]
    return {"search_seconds_per_candidate": search,
            "deployed_seconds_per_prediction": deployed}


def objective(risk, comp, w):
    """Total objective: per-prediction risk plus w * (search cost + H * per-prediction cost)."""
    return float(risk + w * (comp["search_seconds_per_candidate"]
                             + H * comp["deployed_seconds_per_prediction"]))


def regime_table(fam_body, regime):
    r = fam_body["regimes"][regime]
    rows = []
    for rule, m in sorted(r["rules"].items()):
        comp = components(m["cost"])
        rows.append({"rule": rule, "n_fired": m["cost"]["n_fired"],
                     "n_candidates": m["n_candidates"],
                     "deployed_risk": m["deployed_risk"],
                     "realised_mean_delta": m["realised_mean_delta"],
                     "mean_delta_if_always": m["mean_delta_if_always_applied"],
                     "harmful_rejected": m["harmful_rejected"], "n_harmful": m["n_harmful"],
                     "beneficial_missed": m["beneficial_missed"],
                     "n_beneficial": m["n_beneficial"],
                     "ci_low": m["realised_seed_vector_bootstrap"]["ci95_low"],
                     "ci_high": m["realised_seed_vector_bootstrap"]["ci95_high"],
                     **comp,
                     "objective": {("%.0e" % w): objective(m["deployed_risk"], comp, w)
                                   for w in W_GRID}})
    return rows


def mixture_table(fam_body):
    """Policies chosen before the regime is revealed, scored under the pre-declared mixtures."""
    out = {}
    for key, body in sorted(fam_body.get("mixtures", {}).items()):
        pi = float(key.rsplit("_", 1)[1])
        pol = {}
        for rule, d in body.get("policies", {}).items():
            comp = components(d["cost_mix"])
            pol[rule] = {"risk_mix": d["risk_mix"], **comp,
                         "objective": {("%.0e" % w): objective(d["risk_mix"], comp, w)
                                       for w in W_GRID}}
        argmin = {("%.0e" % w): min(pol, key=lambda r: pol[r]["objective"]["%.0e" % w])
                  for w in W_GRID} if pol else {}
        out[key] = {"pi_declared": pi, "policies": pol, "argmin_by_w": argmin}
    return out


def calibration_table(fam_body):
    out = {}
    for regime, r in sorted(fam_body["regimes"].items()):
        cal = r.get("calibration") or {}
        out[regime] = {}
        for rule in ("calib_exact", "calib_harm"):
            c = cal.get(rule) or {}
            out[regime][rule] = {"chosen_tolerance_relative":
                                 c.get("chosen_tolerance_relative"),
                                 "panel": c.get("panel_definition"),
                                 "chosen_row": c.get("chosen")}
    return out


def flip_point(fam_body):
    """Where on the continuum the always-vs-never decision flips, from measured mean deltas."""
    pts = []
    for regime, r in sorted(fam_body["regimes"].items()):
        d = [r["rules"].get(k, {}).get("mean_delta_if_always_applied")
             for k in ("always_repair",)]
        if d and d[0] is not None:
            pts.append({"regime": regime, "mean_delta_if_always": d[0],
                        "always_better": bool(d[0] < 0)})
    flips = [(a["regime"], b["regime"]) for a, b in zip(pts, pts[1:])
             if a["always_better"] != b["always_better"]]
    return {"ordered": pts, "flips_between": flips}


def verdict(fam_body, mix):
    """A7.5's pre-declared verdict categories, applied mechanically."""
    best = set()
    for m in mix.values():
        best.update(m["argmin_by_w"].values())
    cal_best = sorted(best & {"calib_exact", "calib_harm"})
    if cal_best:
        kind = ("best in at least one (mixture, cost-weight) cell"
                if len(cal_best) < 2 else "best for both calibrated rules")
        return {"category": "calibrated rule wins somewhere", "detail": kind,
                "winning_rules": cal_best,
                "cells": {k: v["argmin_by_w"] for k, v in mix.items()}}
    return {"category": "scoped negative: a calibrated exactness screen does not beat "
                        "always/never on this continuum",
            "detail": "no (mixture, cost-weight) cell selects a calibrated rule",
            "winning_rules": [], "cells": {k: v["argmin_by_w"] for k, v in mix.items()}}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="research/search/analyze_decision3.py")
    ap.add_argument("--record", default="research/search/decision_rules3.json")
    ap.add_argument("--out", default="research/search/decision_rules3_analysis.json")
    a = ap.parse_args(argv)
    with open(a.record) as fh:
        rec = json.load(fh)

    out = {"protocol": "A7.3/A7.4/A7.5",
           "objective_definition": ("risk + w * (search_seconds + H * deployed_seconds), H=%d; "
                                    "risk is a per-prediction MSE (a rate), the horizon term is "
                                    "cumulative, and search-time cost is never counted as "
                                    "deployment cost" % H),
           "cost_components": ["gate_seconds_per_candidate (search)",
                               "oneoff_averaging_seconds_per_candidate (search)",
                               "per_prediction_overhead_seconds (deployment, xH)"],
           "families": {}}
    for fam, body in rec.get("summary", {}).items():
        regimes = {r: regime_table(body, r) for r in sorted(body["regimes"])}
        mix = mixture_table(body)
        out["families"][fam] = {
            "regimes": regimes,
            "calibration": calibration_table(body),
            "mixtures": mix,
            "flip_point": flip_point(body),
            "verdict": verdict(body, mix),
            "thresholds": {r: body["regimes"][r]["thresholds"] for r in sorted(body["regimes"])},
        }
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True, default=str)

    for fam, f in out["families"].items():
        print("== %s" % fam)
        for r, rows in f["regimes"].items():
            ce = f["calibration"][r]["calib_exact"]["chosen_tolerance_relative"]
            ch = f["calibration"][r]["calib_harm"]["chosen_tolerance_relative"]
            print("   %-12s calib_exact t=%-10s calib_harm t=%-10s" % (r, ce, ch))
        print("   verdict: %s" % f["verdict"]["category"])
        for k, v in f["mixtures"].items():
            print("      %-20s argmin@w=0: %-18s @w=1e-2: %s"
                  % (k, v["argmin_by_w"].get("0e+00"), v["argmin_by_w"].get("1e-02")))
    print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
