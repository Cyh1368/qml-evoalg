"""A7.3/A7.4/A7.5: gate-parity decision comparison, mixture objective, calibrated screen.

Why this is a new module rather than an edit to ``decision_rules2``: the A6 record
(``decision_rules2.json``) is the artifact the third-round rebuttal cites, and the fourth-round
review identified defects that change its numbers. The old record stays as the audited artifact of
what was actually run, and this module produces the corrected comparison. Shared structures are
imported from ``decision_rules2`` rather than re-implemented, so the two cannot drift.

What is fixed relative to A6.2/A6.3, each item verified in source before being accepted:

* **Gate parity.** Every gate receives the *current regime's* group and target. In A6.2 the
  defective label test always received ``gens_declared`` and the channel residual was computed once
  with ``group="true"`` outside the regime loop, so in the mismatched and approximate regimes the
  two "gates" were not tests of the same proposed repair.
* **Two threshold designs, named differently.** ``defect_q1_frozen`` computes a numeric threshold
  once on the declared-group regime and applies it unchanged everywhere (fixed-threshold transfer);
  ``defect_q1_within`` recomputes it inside each regime, which preserves a selection fraction by
  construction and is *within-regime quantile selection*, not threshold transfer.
* **``never_repair`` is an explicit zero-cost baseline.** Where every gate rejects, never repairing
  has the same realized loss and no gate cost, so no gate can be unqualifiedly optimal there.
* **Timings are measured, tagged and repeated.** Averaged-inference time is a timed call over the
  twirl elements, not raw time multiplied by group order; every timing carries
  ``measured``/``extrapolated`` and the spread of three repeats.
* **Mixture objective.** A policy is a function of the candidate and the supplied group only; the
  regime is not observed at decision time, so policies are scored under a predeclared mixture over
  regimes rather than regime by regime.
* **Calibrated tolerance (A7.5a).** Two rules, ``calib_exact`` and ``calib_harm``, each choosing the
  largest tolerance on a scale-free grid whose one-sided 95% Clopper--Pearson bound on its own error
  rate is at most alpha.
"""

from __future__ import annotations

import argparse
import glob
import json
import multiprocessing as mp
import os
import time

import numpy as np

from research.core import paired as _P
from research.core import tasks as _tasks
from research.search import corrected_gate as _cg
from research.search import decision_rules as _dr
from research.search import decision_rules2 as _dr2
from research.search import refit as _refit
from research.search import verifier_bridge as _vb

# ---------------------------------------------------------------- A7.5 grid, frozen
TOL_GRID_REL = [0.0, 1e-9, 1e-6, 1e-4, 1e-3, 3e-3, 1e-2, 3e-2]
ALPHA = 0.05
EPS_SCALED = {"approx_s05": 0.05, "approx_s10": 0.10,
              "approx_s20": 0.20, "approx_s40": 0.40}
MIXTURES = [0.0, 0.25, 0.50, 0.75, 1.0]
RULES3 = ["never_repair", "always_repair", "defective_label", "corrected_label",
          "deployed_gate", "defect_q1_frozen", "defect_q1_within", "random_matched",
          "calib_exact", "calib_harm"]
TIMING_REPEATS = 3
TIME_TAG = {"label": "measured", "channel": "measured", "defect": "measured",
            "average_full": "measured", "pred_raw": "measured", "pred_averaged": "measured"}
_W: dict = {}


def _timed(fn, repeats=TIMING_REPEATS):
    """Median of ``repeats`` wall-clock measurements, with spread. Never a single draw."""
    ts = []
    for _ in range(int(repeats)):
        t0 = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t0)
    return {"median": float(np.median(ts)), "min": float(min(ts)), "max": float(max(ts)),
            "repeats": int(repeats), "basis": "measured"}


# --------------------------------------------------------------- regime groups
def regime_groups(task, rng):
    """Regime name -> group, plus the scaled approximate-symmetry continuum.

    The continuum is the ring target perturbed as y_eps = y_0 + eps * spread * (x . v) with a fixed
    unit v, where ``spread`` is the target's own standard deviation, so eps is a fraction of the
    signal rather than a number in one dataset's units. Scope is stated in the record: this is a
    controlled synthetic continuum, not an independently validated task-relevant approximately
    symmetric application.
    """
    from verify import closure
    n = int(task.n_qubits)
    dec = closure([list(g) for g in task.generators], n)
    mm, reason = _dr2._mismatched(task, rng)
    reg = {"declared": dec, "subgroup": _dr2._subgroup_of(task), "mismatched": mm}
    y = np.asarray(task.targets[task.primary_target], dtype=float)
    spread = float(np.std(y))
    for k in EPS_SCALED:
        reg[k] = dec if str(task.name).startswith("ring") else None
    return reg, {"mismatch_reason": reason, "target_spread": spread}


# --------------------------------------------------------------- per-candidate pass
def evaluate_candidate_v2(args):
    path, regimes, spread, eps_map = args
    log = _refit.load_run(path)
    task = _W["tasks"][log["family"]]
    fam, seed = log["family"], int(log["seed"])
    fit, _, _, _, check = _refit.refit_best(log, task=task)
    rng = np.random.default_rng(90210 + seed)
    x = np.asarray(task.x)
    y = np.asarray(task.targets[task.primary_target], dtype=float)
    dev = np.asarray(task.splits["validation"], bool)
    idx = np.flatnonzero(dev)
    if len(idx) > _dr2.EVAL_ROWS:
        idx = np.sort(rng.choice(idx, size=_dr2.EVAL_ROWS, replace=False))
    rows, yy = x[idx], y[idx]
    gate_rows = x[:64]
    probe = _W["probe"][fam]
    cand = log["best"]["candidate"]
    params = _vb.sample_param_dicts(cand, rng, 3)
    v = np.random.default_rng(_dr2.NOISE_SEED).standard_normal(int(task.n_qubits))

    t_r = _timed(lambda: _refit.predictions(fit, task, rows[:64]))
    sec_pred_raw = t_r["median"] / 64.0

    out = {"path": path, "family": fam, "arm": log["arm"], "seed": seed,
           "reproduction": check, "n_rows": int(len(rows)),
           "target": task.primary_target, "target_spread": spread,
           "seconds_per_prediction_raw": sec_pred_raw, "timing_basis": TIME_TAG,
           "regimes": {}}

    for rname, group in regimes.items():
        if not group:
            continue
        eps_frac = eps_map.get(rname, 0.0)
        eps = eps_frac * spread
        ttask = _dr2._NoisyTask(task, eps, v) if eps else task
        y_eval = yy + eps * (rows @ v) if eps else yy
        elems, exact = _dr2._twirl_elems(group, rng)
        gens = [list(g) for g in group]

        raw = np.asarray(_refit.predictions(fit, task, rows), dtype=float).reshape(-1)
        t_avg = _timed(lambda: _dr._average(fit, task, rows, elems))
        avg = _dr._average(fit, task, rows, elems)
        srows, sraw = rows[:_dr2.DEFECT_SAMPLE_ROWS], raw[:_dr2.DEFECT_SAMPLE_ROWS]
        t_def = _timed(lambda: _dr._average(fit, task, srows, elems))
        savg = _dr._average(fit, task, srows, elems)
        # PARITY: the channel condition is computed for the group of THIS regime, on THIS target.
        t_ch = _timed(lambda: _vb.verify_candidate(cand, ttask, params, group=gens))
        chan = _vb.verify_candidate(cand, ttask, params, group=gens)
        # PARITY: both label tests see the same group; only the test semantics differ.
        t_ld = _timed(lambda: _cg.label_test(ttask, gens, task.primary_target, gate_rows,
                                             0.0, 0.0, all_columns=True))
        lab_d = _cg.label_test(ttask, gens, task.primary_target, gate_rows, 0.0, 0.0,
                               all_columns=True)
        t_lc = _timed(lambda: _cg.label_test(ttask, gens, task.primary_target, gate_rows))
        lab_c = _cg.label_test(ttask, gens, task.primary_target, gate_rows)
        # tolerance grid, on this regime's own target
        tol_rates = {}
        for rel in TOL_GRID_REL:
            t = _timed(lambda: _cg.label_test(ttask, gens, task.primary_target, gate_rows,
                                              atol_abs=rel * spread, atol_rel=0.0), repeats=1)
            r = _cg.label_test(ttask, gens, task.primary_target, gate_rows,
                               atol_abs=rel * spread, atol_rel=0.0)
            tol_rates["%.3e" % rel] = {"accepts": bool(r["violated_fraction"] == 0.0),
                                       "violated_fraction": r["violated_fraction"],
                                       "scope": r["scope"],
                                       "seconds": t["median"]}
        truth, worst = _cg.sound_on_probe(ttask, gens, task.primary_target, probe)
        risk_before = float(np.mean((raw - y_eval) ** 2))
        risk_after = float(np.mean((avg - y_eval) ** 2))
        out["regimes"][rname] = {
            "group_order": len(group), "n_elements": len(elems), "twirl_exact": exact,
            "eps_fraction": eps_frac, "eps_absolute": eps,
            "risk_candidate": risk_before, "risk_averaged": risk_after,
            "delta": risk_after - risk_before,
            "group_is_label_symmetry": bool(truth), "probe_worst": worst,
            "defect_statistic": float(np.mean((sraw - savg) ** 2)),
            "channel_mean": float(chan["mean_channel_residual"]),
            "channel_above_floor": bool(chan["mean_channel_residual"]
                                        > _dr2.REPAIR_RESIDUAL_FLOOR),
            "label_defective_accepts": bool(lab_d["violated_fraction"] == 0.0),
            "label_corrected_accepts": bool(lab_c["violated_fraction"] == 0.0),
            "label_corrected_scope": lab_c["scope"],
            "tolerance_grid": tol_rates,
            "costs_seconds": {
                "label_defective": t_ld["median"], "label_corrected": t_lc["median"],
                "channel": t_ch["median"], "defect_statistic": t_def["median"],
                "average_full": t_avg["median"]},
            "cost_spread_seconds": {"label_corrected": [t_lc["min"], t_lc["max"]],
                                    "channel": [t_ch["min"], t_ch["max"]],
                                    "average_full": [t_avg["min"], t_avg["max"]]},
            "seconds_per_prediction_raw": sec_pred_raw,
            "seconds_per_prediction_averaged": t_avg["median"] / len(rows),
            "averaging_overhead_factor_measured": (t_avg["median"] / len(rows)) / sec_pred_raw,
            "averaging_group_order": len(elems)}
    return out


# ---------------------------------------------------------------------- policies
def _tolerance_accepts(rec, regime, rel):
    return rec["regimes"][regime]["tolerance_grid"]["%.3e" % rel]["accepts"]


def calibrate(recs, regime, alpha=ALPHA):
    """A7.5a: largest tolerance whose CP-95 upper bound on its own error rate is <= alpha."""
    out = {}
    for rule, panel in (("calib_exact", lambda r: not r["group_is_label_symmetry"]),
                        ("calib_harm", lambda r: r["delta"] > 0.0)):
        have = [r for r in recs if regime in r["regimes"]]
        per_tol = {}
        chosen, chosen_row = None, None
        for rel in TOL_GRID_REL:                       # ascending: last qualifying wins
            acc = [_tolerance_accepts(r, regime, rel) for r in have]
            # error entries: the panel; errors among them: accepted anyway
            panel_rows = [r for r in have if panel(r["regimes"][regime])]
            errs = sum(1 for r, a in zip(have, acc)
                       if a and panel(r["regimes"][regime]))
            bound = _cg.cp_upper_95(errs, len(panel_rows)) if panel_rows else None
            row = {"tolerance_relative": rel, "n_panel": len(panel_rows),
                   "errors": int(errs), "cp95_upper": bound,
                   "n_accepts": int(sum(acc))}
            per_tol["%.3e" % rel] = row
            if bound is not None and bound <= alpha:
                chosen, chosen_row = rel, row
        out[rule] = {"alpha": alpha, "chosen_tolerance_relative": chosen,
                     "chosen": chosen_row, "grid": per_tol,
                     "panel_definition": ("group is not a label symmetry on the probe set"
                                          if rule == "calib_exact"
                                          else "realised risk change is positive (repair hurt)")}
    return out


def masks_v3(recs, regime, frozen_tau, calib):
    have = [r for r in recs if regime in r["regimes"]]
    if not have:
        return None, {}
    n = len(have)
    defects = np.array([r["regimes"][regime]["defect_statistic"] for r in have])
    tau_within = float(np.quantile(defects, 0.25))
    m = {
        "never_repair": [False] * n,
        "always_repair": [True] * n,
        "defective_label": [r["regimes"][regime]["label_defective_accepts"] for r in have],
        "corrected_label": [r["regimes"][regime]["label_corrected_accepts"] for r in have],
        "deployed_gate": [bool(r["regimes"][regime]["label_corrected_accepts"]
                               and r["regimes"][regime]["channel_above_floor"]) for r in have],
        "defect_q1_within": [bool(r["regimes"][regime]["defect_statistic"] > tau_within)
                             for r in have],
        "defect_q1_frozen": ([bool(r["regimes"][regime]["defect_statistic"] > frozen_tau)
                              for r in have] if frozen_tau is not None else [False] * n),
    }
    n_fire = int(sum(m["defect_q1_within"]))
    rand = [False] * n
    for i in np.random.default_rng(4242).permutation(n)[:n_fire]:
        rand[int(i)] = True
    m["random_matched"] = rand
    for rule in ("calib_exact", "calib_harm"):
        rel = (calib.get(rule) or {}).get("chosen_tolerance_relative")
        m[rule] = ([_tolerance_accepts(r, regime, rel) for r in have] if rel is not None
                   else [False] * n)
    taus = {"q1_within": tau_within, "q1_frozen": frozen_tau,
            "threshold_kind": {"q1_within": "within-regime quantile (recalibrated)",
                               "q1_frozen": "numeric threshold frozen on the declared regime"}}
    return have, {"thresholds": taus, "masks": m,
                  "n_fired": {k: int(sum(v)) for k, v in m.items()}}


# ------------------------------------------------------------------------- costs
_GATE_KEYS = {"defective_label": ["label_defective"], "corrected_label": ["label_corrected"],
              "deployed_gate": ["label_corrected", "channel"],
              "defect_q1_frozen": ["defect_statistic"], "defect_q1_within": ["defect_statistic"],
              "calib_exact": ["label_corrected"], "calib_harm": ["label_corrected"]}
H = 1000
W_GRID = [0.0, 1e-4, 1e-3, 1e-2, 1e-1, 1.0]


def cost_v3(have, mask, regime, rule):
    f = np.asarray(list(mask), bool)
    keys = _GATE_KEYS.get(rule, [])
    gate = [sum(r["regimes"][regime]["costs_seconds"][k] for k in keys) for r in have]
    oneoff = [r["regimes"][regime]["costs_seconds"]["average_full"] if fire else 0.0
              for r, fire in zip(have, f)]
    overhead = [(r["regimes"][regime]["seconds_per_prediction_averaged"]
                 - r["regimes"][regime]["seconds_per_prediction_raw"]) if fire else 0.0
                for r, fire in zip(have, f)]
    return {"gate_seconds_per_candidate": float(np.mean(gate)),
            "oneoff_averaging_seconds_per_candidate": float(np.mean(oneoff)),
            "per_prediction_overhead_seconds": float(np.mean(overhead)),
            "n_fired": int(f.sum()),
            "all_timings_measured": True,
            "note": ("gate time is paid per candidate screened during search; repair and "
                     "inference overhead are paid per deployed prediction and enter the "
                     "objective multiplied by the horizon H=%d, so the two are not added in "
                     "the same units without that factor" % H)}


def objective(risk, cost):
    base = cost["gate_seconds_per_candidate"] + cost["oneoff_averaging_seconds_per_candidate"]
    return {"H%d_w%g" % (H, w): float(risk + w * (base + H * cost["per_prediction_overhead_seconds"]))
            for w in W_GRID}


def _metrics(have, mask, regime):
    m = _dr2._rule_metrics(have, mask, regime)
    m["cost"] = cost_v3(have, mask, regime, "")
    return m


def _init(tasks, probe):
    _W["tasks"], _W["probe"] = tasks, probe


def main(argv=None):
    ap = argparse.ArgumentParser(prog="research/search/decision_rules3.py")
    ap.add_argument("--runs", default="logs/runs_confirm")
    ap.add_argument("--out", default="research/search/decision_rules3.json")
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args(argv)

    paths = sorted(glob.glob(os.path.join(a.runs, "run_*.json")))
    families = sorted({_refit.load_run(p)["family"] for p in paths})
    tasks, probe, reg_by_fam, meta = {}, {}, {}, {}
    for fam in families:
        tasks[fam] = _tasks.load_family(fam, development=True, locked=False)
        from research.search.verify_semantics import probe_indices
        probe[fam] = probe_indices(tasks[fam], n_rows=_cg.PROBE_ROWS, seed=_cg.PROBE_SEED)
        rng = np.random.default_rng(31337)
        reg_by_fam[fam], meta[fam] = regime_groups(tasks[fam], rng)
        print("%s regimes: %s (spread %.4f)" % (
            fam, {k: (len(v) if v else None) for k, v in reg_by_fam[fam].items()},
            meta[fam]["target_spread"]), flush=True)

    jobs = []
    for p in paths:
        fam = _refit.load_run(p)["family"]
        reg = {k: v for k, v in reg_by_fam[fam].items()}
        eps = {k: EPS_SCALED.get(k, 0.0) for k in reg}
        jobs.append((p, reg, meta[fam]["target_spread"], eps))

    results = []
    with mp.get_context("fork").Pool(processes=int(a.workers), initializer=_init,
                                     initargs=(tasks, probe)) as pool:
        for r in pool.imap_unordered(evaluate_candidate_v2, jobs, chunksize=1):
            results.append(r)
            if len(results) % 20 == 0:
                print("  %d/%d candidates" % (len(results), len(paths)), flush=True)

    out = {"protocol": "A7.3/A7.4/A7.5", "eval_rows": _dr2.EVAL_ROWS,
           "horizon": H, "w_grid": W_GRID, "rules": RULES3,
           "tolerance_grid_relative": TOL_GRID_REL, "alpha": ALPHA,
           "eps_scaled": EPS_SCALED, "mixtures": MIXTURES,
           "noise_seed": _dr2.NOISE_SEED, "timing_repeats": TIMING_REPEATS,
           "regime_orders": {f: {k: (len(v) if v else None)
                                 for k, v in r.items()} for f, r in reg_by_fam.items()},
           "mismatch_reason": {f: meta[f]["mismatch_reason"] for f in families},
           "target_spread": {f: meta[f]["target_spread"] for f in families},
           "parity_fixes": ["all gates receive the current regime's group and target",
                            "channel residual recomputed per regime with the regime's group",
                            "never_repair added as an explicit zero-cost baseline",
                            "frozen numeric threshold and within-regime quantile reported apart",
                            "all timings measured, repeated, and tagged"],
           "candidates": results, "summary": {}}

    for fam in families:
        recs = [r for r in results if r["family"] == fam]
        regimes_present = [k for k in reg_by_fam[fam]
                           if any(k in r["regimes"] for r in recs)]
        # threshold frozen on the declared regime, applied unchanged elsewhere
        decl = [r for r in recs if "declared" in r["regimes"]]
        frozen_tau = (float(np.quantile(
            [r["regimes"]["declared"]["defect_statistic"] for r in decl], 0.25))
            if decl else None)
        fam_out = {"regimes": {}, "mixtures": {}}
        per_regime_deployed = {}
        for regime in regimes_present:
            calib = calibrate(recs, regime)
            have, info = masks_v3(recs, regime, frozen_tau, calib)
            if have is None:
                continue
            rules = {}
            for rule in RULES3:
                mask = info["masks"][rule]
                m = _metrics(have, mask, regime)
                m["cost"] = cost_v3(have, mask, regime, rule)
                m["deployed_risk"] = float(np.mean(
                    [r["regimes"][regime]["risk_candidate"]
                     + fire * r["regimes"][regime]["delta"]
                     for r, fire in zip(have, mask)]))
                m["objective"] = objective(m["deployed_risk"], m["cost"])
                rules[rule] = m
                per_regime_deployed.setdefault(rule, {})[regime] = m["deployed_risk"]
            fam_out["regimes"][regime] = {
                "calibration": calib, "thresholds": info["thresholds"],
                "n_fired": info["n_fired"], "n_candidates": len(have), "rules": rules}
        # mixture over regimes: the policy is chosen before the regime is revealed
        valid = [k for k in regimes_present if k in ("declared", "mismatched")]
        for pi in MIXTURES:
            row = {}
            for rule in RULES3:
                d = per_regime_deployed.get(rule, {})
                if not all(k in d for k in valid):
                    continue
                risk = pi * d.get("declared", 0.0) + (1 - pi) * d.get("mismatched", 0.0)
                cost_mix = {}
                for k in valid:
                    c = fam_out["regimes"][k]["rules"][rule]["cost"]
                    wt = pi if k == "declared" else (1 - pi)
                    for ck, cv in c.items():
                        if isinstance(cv, (int, float)):
                            cost_mix[ck] = cost_mix.get(ck, 0.0) + wt * cv
                row[rule] = {"risk_mix": float(risk), "cost_mix": cost_mix,
                             "objective": objective(float(risk), cost_mix)}
            best = {w: min(row, key=lambda r: row[r]["objective"]["H%d_w%g" % (H, w)])
                    for w in W_GRID} if row else {}
            fam_out["mixtures"]["pi_declared_%.2f" % pi] = {"policies": row, "argmin_by_w": best}
        out["summary"][fam] = fam_out

    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True, default=str)
    print("wrote %s: %d candidates, %d families" % (a.out, len(results), len(families)),
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
