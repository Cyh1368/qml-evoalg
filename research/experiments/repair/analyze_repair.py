"""Corrected analysis of the causal-repair experiments (WP-REPAIR v1 record and
WP-REPAIR-2), implementing ``research/REVISED_PROTOCOL.md`` sections 1-4.

Works on either result file and always reports **units, not rows**:

* at ``eta = 0`` the target is direction-free, so the replication unit is the
  optimiser seed; the v1 record's 24 rows collapse to 8 units and the interval is
  recomputed from those 8 pairs (this is the fix for the pseudoreplication the
  referee identified, and it is reported side by side with the old number);
* at ``eta > 0`` the unit is (direction, optimiser seed); every direction is
  reported separately and a cluster bootstrap over directions is given for the
  population-of-directions reading, with its caveat;
* floor accounting: risk, floor (analytic / representative-MC / exact finite-orbit)
  and **excess above the floor** are reported together, so "pinned near the floor"
  is checkable rather than rhetorical;
* the E-R1 function-space contrast ``R_orb(f) - R_orb(P_G f)`` is reported with its
  cross term, which is exactly zero for an invariant target and nonzero when the
  target breaks the symmetry (the projection identity is not a theorem about
  retrained asymmetric architectures).

Usage::

    python3 -m research.experiments.repair.analyze_repair \\
        --in research/experiments/repair/repair2_results.json \\
        --out research/experiments/repair/repair2_analysis.json
"""
import argparse
import json
import os

import numpy as np

from research.core import paired as _P

CONTRASTS = (("repaired", "control_dup"), ("repaired", "control_rand"),
             ("repaired", "original"), ("control_dup", "original"),
             ("control_matched", "original"))
CONTRASTS_V1 = (("repaired", "control"), ("repaired", "original"),
                ("control", "original"))


def arm_names(rows):
    return sorted({r["arm"] for r in rows})


def unit_key(row, eta):
    """The replication unit: optimiser seed at eta=0, (direction, seed) at eta>0."""
    if float(eta) == 0.0:
        return (int(row["opt_seed"]),)
    return (row.get("direction_seed") or row.get("teacher_seed"),
            int(row["opt_seed"]))


def risk_field(row):
    return row.get("dev_risk")


def contrast(rows, a, b, eta, steps=None, field="dev_risk"):
    sel = [r for r in rows if r["eta"] == float(eta)
           and (steps is None or int(r.get("steps", 0)) == int(steps))]
    A, B = {}, {}
    for r in sel:
        if r["arm"] == a:
            A.setdefault(unit_key(r, eta), []).append(r)
        elif r["arm"] == b:
            B.setdefault(unit_key(r, eta), []).append(r)
    keys = sorted(set(A) & set(B), key=str)
    pairs = [(k, float(A[k][i][field]) - float(B[k][i][field]))
             for k in keys for i in range(min(len(A[k]), len(B[k])))]
    collapsed = _P.collapse_units(pairs)
    diffs = list(collapsed.values())
    out = {"a": a, "b": b, "eta": float(eta), "steps": steps, "endpoint": field,
           "unit": "optimiser seed (eta=0: target is direction-free)"
                   if float(eta) == 0.0
                   else "(direction, optimiser seed), direction as blocking factor",
           "n_rows": len(pairs), "n_units": len(diffs),
           "duplicates_collapsed": len(pairs) - len(diffs),
           "diffs": diffs,
           "mean_diff_a_minus_b": float(np.mean(diffs)) if diffs else None,
           "frac_a_better": float(np.mean([d < 0 for d in diffs])) if diffs else None}
    out["bootstrap"] = _P.bootstrap_ci(diffs)
    out["p_shifted_bootstrap"] = _P.shifted_bootstrap_p(diffs)
    out["p_signflip"] = _P.signflip_p(diffs)
    out["loo"] = _P.loo_range(diffs)
    out["verdict"] = _P.verdict(out["bootstrap"]["ci95_low"],
                                out["bootstrap"]["ci95_high"])
    # per-cluster (direction) breakdown at eta > 0
    if float(eta) != 0.0:
        per = {}
        for k, d in pairs:
            per.setdefault(str(k[0]), []).append(d)
        out["by_direction"] = {k: {"n": len(v), "mean": float(np.mean(v)),
                                   "frac_a_better": float(np.mean([x < 0 for x in v]))}
                               for k, v in sorted(per.items())}
        out["cluster_bootstrap"] = _P.cluster_bootstrap_ci(per)
        out.update(_estimand_layers(pairs))
    else:
        out["primary_estimand"] = "E-0: optimiser seeds, direction-free target"
        out["primary"] = {"n_units": out["n_units"],
                          "mean_diff_a_minus_b": out["mean_diff_a_minus_b"],
                          "bootstrap": out["bootstrap"],
                          "p_shifted_bootstrap": out["p_shifted_bootstrap"],
                          "p_signflip": out["p_signflip"],
                          "estimand": out["primary_estimand"]}
    return c_add_holm_placeholder(out)


def _estimand_layers(pairs, n_boot=20000, seed=0):
    """Addendum A5.1: four estimands for the crossed eta>0 design.

    The cell-level interval (E-D) resamples 192 quantities that reuse both directions and
    optimiser seeds, so it is kept only for traceability.  E-A is the headline: the 8
    breaking directions are a *fixed* design set, so a claim about optimiser randomness
    averages directions within a seed and resamples the seed vectors.
    """
    seeds = sorted({k[1] for k, _ in pairs}, key=str)
    dirs = sorted({k[0] for k, _ in pairs}, key=str)
    cell = {(k[1], k[0]): d for k, d in pairs}
    full = [s for s in seeds if all((s, g) in cell for g in dirs)]
    if len(dirs) < 2 or len(full) < 2:
        return {}
    M = np.array([[cell[(s, g)] for g in dirs] for s in full])
    sv = M.mean(axis=1)
    dv = M.mean(axis=0)
    ea = _P.seed_vector_bootstrap_ci(M, n_boot=n_boot, seed=seed)
    ea["p_shifted_bootstrap"] = _P.shifted_bootstrap_p(sv, n_boot=n_boot, seed=seed)
    ea["p_signflip"] = _P.signflip_p(sv, n_boot=n_boot, seed=seed)
    eb = _P.cluster_bootstrap_ci({g: M[:, i].tolist() for i, g in enumerate(dirs)},
                                 n_boot=n_boot, seed=seed)
    eb["p_shifted_bootstrap"] = _P.shifted_bootstrap_p(dv, n_boot=n_boot, seed=seed)
    eb["p_signflip"] = _P.signflip_p(dv, n_boot=n_boot, seed=seed)
    ec = _P.crossed_bootstrap_ci(M, n_boot=n_boot, seed=seed)
    return {
        "primary_estimand": "E-A",
        "estimand_EA_seed_vector": ea,
        "estimand_EB_direction_cluster": eb,
        "estimand_EC_crossed": ec,
        "estimand_ED_legacy_cell": {
            "mean_diff_a_minus_b": out_mean(pairs), "bootstrap": None,
            "note": "cell-level resampling of (direction, seed) cells; retained for "
                    "traceability only, not a protocol headline"},
        "estimand_matrix": {"n_seeds": int(M.shape[0]), "n_directions": int(M.shape[1]),
                            "incomplete_seeds_dropped": len(seeds) - len(full)},
        "conditioning_caveat": "all four intervals condition on one dataset and one task "
                               "family; none quantifies newly sampled datasets or families",
        "primary": {"n_units": int(M.shape[0]),
                    "mean_diff_a_minus_b": float(np.mean(sv)),
                    "bootstrap": {k: ea[k] for k in ("mean", "ci95_low", "ci95_high")},
                    "p_shifted_bootstrap": ea["p_shifted_bootstrap"],
                    "p_signflip": ea["p_signflip"],
                    "estimand": "E-A"},
    }


def out_mean(pairs):
    return float(np.mean([d for _, d in pairs]))


def c_add_holm_placeholder(c):
    return c


def floor_accounting(rows, eta, steps=None):
    """Risk, floor and excess above floor per arm, with the exact-orbit floor."""
    sel = [r for r in rows if r["eta"] == float(eta)
           and (steps is None or int(r.get("steps", 0)) == int(steps))]
    out = []
    for arm in sorted({r["arm"] for r in sel}):
        rs = [r for r in sel if r["arm"] == arm]
        entry = {"arm": arm, "n_units": len({_P_unit(r, eta) for r in rs}),
                 "mean_dev_risk": float(np.mean([r["dev_risk"] for r in rs])),
                 "mean_channel_residual": float(np.mean([r["channel_mean"] for r in rs])),
                 "max_channel_residual": float(np.max([r["channel_max"] for r in rs]))}
        for key, name in (("floor_analytic", "floor_representative_mc"),
                          ("orb_floor", "floor_exact_finite_orbit"),
                          ("orb_risk", "orb_risk"),
                          ("orb_risk_proj", "orb_risk_reynolds_projection"),
                          ("orb_excess_floor", "orb_excess_above_floor"),
                          ("orb_asymmetry", "orb_asymmetry"),
                          ("orb_cross_term", "orb_cross_term")):
            if key in rs[0]:
                entry[name] = float(np.mean([r[key] for r in rs]))
        if "floor_exact_finite_orbit" in entry:
            entry["excess_over_floor"] = entry["orb_risk"] - entry["floor_exact_finite_orbit"]
        out.append(entry)
    return out


def _P_unit(row, eta):
    return unit_key(row, eta)


def er1_function_space(rows, eta, steps=None):
    """E-R1: paired R_orb(f) - R_orb(Pf) with its cross term, per arm.

    The identity checked here is ``R(f) - R(Pf) = E[(f-Pf)^2] - 2 E[(f-Pf)(y-ybar)]``
    (sign as in REVISED_PROTOCOL Amendment A3).  ``identity_gap_max`` is the deviation from
    the *invariant-target* specialisation (it equals ``2|cross|`` and is therefore nonzero
    for eta > 0 by construction); ``full_identity_gap_max`` is the deviation from the full
    identity and must be at roundoff for every row, at every eta.
    """
    sel = [r for r in rows if r["eta"] == float(eta)
           and (steps is None or int(r.get("steps", 0)) == int(steps))
           and "orb_risk" in r]
    out = []
    for arm in sorted({r["arm"] for r in sel}):
        rs = [r for r in sel if r["arm"] == arm]
        d = [r["orb_risk"] - r["orb_risk_proj"] for r in rs]
        e = {"arm": arm, "n_units": len({_P_unit(r, eta) for r in rs}),
             "mean_risk_minus_proj": float(np.mean(d)),
             "mean_asymmetry": float(np.mean([r["orb_asymmetry"] for r in rs])),
             "mean_cross_term": float(np.mean([r.get("orb_cross_term", 0.0)
                                               for r in rs])),
             "identity_gap_max": float(np.max([abs(x - r["orb_asymmetry"])
                                               for x, r in zip(d, rs)])),
             "full_identity_gap_max": float(np.max([
                 abs((x - r["orb_asymmetry"]) + 2.0 * r.get("orb_cross_term", 0.0))
                 for x, r in zip(d, rs)]))}
        e["bootstrap"] = _P.bootstrap_ci(d)
        out.append(e)
    return out


def analyze(path, margin_fraction=0.05):
    with open(path) as fh:
        data = json.load(fh)
    rows = data["rows"]
    etas = sorted({r["eta"] for r in rows})
    steps_list = sorted({int(r.get("steps", 0)) for r in rows})
    pairs = CONTRASTS if any(r["arm"] == "control_dup" for r in rows) else CONTRASTS_V1
    # equivalence margin: fraction of the target variance on the dev split
    from research.core import tasks as _tasks
    task = _tasks.load_family(data.get("family", "ring_n6"), development=True,
                              locked=False)
    y = np.asarray(task.targets[task.primary_target], float)
    dev = np.asarray(task.splits["validation"], bool)
    base_var = float(np.var(y[dev]))
    result = {"input": path, "family": data.get("family"),
              "protocol": "REVISED_PROTOCOL sections 1-4",
              "steps_present": steps_list,
              "unit_counts": {}, "contrasts": [], "floor_accounting": {},
              "er1_function_space": {}, "budget_sensitivity": [],
              "margin": {"rule": "0.05 * Var_target(dev) of the eta=0 target",
                         "var_target_dev": base_var, "margin": margin_fraction * base_var}}
    main_steps = data.get("steps_main") or (min(steps_list) if steps_list else None)
    for eta in etas:
        cs = []
        for (a, b) in pairs:
            c = contrast(rows, a, b, eta, steps=main_steps)
            if c["n_units"]:
                prim = c["primary"]["bootstrap"]
                c["equivalence"] = _P.equivalence(prim["ci95_low"], prim["ci95_high"],
                                                  margin_fraction * base_var * (1 + eta ** 2))
                cs.append(c)
        adj = _P.holm([c["primary"]["p_shifted_bootstrap"]["p"] for c in cs])
        for c, a_ in zip(cs, adj):
            c["p_holm_within_eta"] = float(a_)
            # Addendum A5.6: the printed verdict follows the primary estimand and the
            # multiplicity-adjusted test, never the legacy cell-level interval.
            c["verdict"] = _P.verdict(c["primary"]["bootstrap"]["ci95_low"],
                                      c["primary"]["bootstrap"]["ci95_high"],
                                      p_adjusted=float(a_))
            c["verdict_legacy_cell_ci"] = _P.verdict(c["bootstrap"]["ci95_low"],
                                                     c["bootstrap"]["ci95_high"])
        result["contrasts"].extend(cs)
        result["floor_accounting"][str(eta)] = floor_accounting(rows, eta, main_steps)
        result["er1_function_space"][str(eta)] = er1_function_space(rows, eta, main_steps)
        result["unit_counts"][str(eta)] = {
            "rows": len([r for r in rows if r["eta"] == eta
                         and int(r.get("steps", 0)) == int(main_steps)]),
            "units": len({_P_unit(r, eta) for r in rows
                          if r["eta"] == eta and int(r.get("steps", 0)) == int(main_steps)})}
    for st in steps_list:
        if st == main_steps:
            continue
        for eta in etas:
            for (a, b) in pairs[:1] + pairs[3:4]:
                c = contrast(rows, a, b, eta, steps=st)
                if c["n_units"]:
                    c["role"] = "budget sensitivity"
                    result["budget_sensitivity"].append(c)
    if data.get("metadata"):
        result["metadata"] = data["metadata"]
    return result


def main(argv=None):
    p = argparse.ArgumentParser(prog="research/experiments/repair/analyze_repair.py")
    p.add_argument("--in", dest="inp",
                   default="research/experiments/repair/repair2_results.json")
    p.add_argument("--out", default=None)
    a = p.parse_args(argv)
    res = analyze(a.inp)
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        with open(a.out, "w") as fh:
            json.dump(res, fh, indent=1, default=str)
    print("units per eta:", res["unit_counts"])
    for c in res["contrasts"]:
        b = c["primary"]["bootstrap"]
        print("eta=%.1f steps=%s %-14s vs %-14s rows=%d units=%d[%s] mean=%+.5f "
              "CI=[%+.5f,%+.5f] p_boot=%.4g p_flip=%.4g p_holm=%.4g %s"
              % (c["eta"], c["steps"], c["a"], c["b"], c["n_rows"],
                 c["primary"]["n_units"], c.get("primary_estimand", "?"),
                 b["mean"], b["ci95_low"], b["ci95_high"],
                 c["primary"]["p_shifted_bootstrap"]["p"],
                 c["primary"]["p_signflip"]["p"],
                 c["p_holm_within_eta"], c["verdict"]))
    print("\n--- floor accounting (exact finite-orbit floor and excess) ---")
    for eta, rows in res["floor_accounting"].items():
        for e in rows:
            if "orb_risk" not in e:
                print("eta=%s %-15s n=%2d dev=%.5f floor_mc=%.5f chan=%.2e "
                      "(no orbit-completed record in this file)"
                      % (eta, e["arm"], e["n_units"], e["mean_dev_risk"],
                         e.get("floor_representative_mc", float("nan")),
                         e["mean_channel_residual"]))
                continue
            print("eta=%s %-15s n=%2d dev=%.5f chan=%.2e orb=%.5f floor_orb=%.5f "
                  "excess=%+.5f proj=%.5f asym=%.2e cross=%+.2e"
                  % (eta, e["arm"], e["n_units"], e["mean_dev_risk"],
                     e["mean_channel_residual"], e["orb_risk"],
                     e["floor_exact_finite_orbit"], e["excess_over_floor"],
                     e["orb_risk_reynolds_projection"], e["orb_asymmetry"],
                     e["orb_cross_term"]))
    print("\n--- E-R1 function space ---")
    for eta, rows in res["er1_function_space"].items():
        for e in rows:
            print("eta=%s %-15s R(f)-R(Pf)=%+.6f  E[(f-Pf)^2]=%.6f cross=%+.6f "
                  "no-cross-term gap=%.1e  full A3 gap=%.1e"
                  % (eta, e["arm"], e["mean_risk_minus_proj"],
                     e["mean_asymmetry"], e["mean_cross_term"],
                     e["identity_gap_max"], e.get("full_identity_gap_max", float("nan"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
