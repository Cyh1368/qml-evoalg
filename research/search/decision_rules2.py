"""A6.2-A6.3: corrected, defective and alternative repair rules on identical frozen
predictors, each rule scored under **its own** decision, with measured costs.

Differences from ``decision_rules.py``, which the third-round review invalidated in part:

* the **corrected** label gate (A6.1) is a first-class rule, not a footnote;
* every rule is evaluated in five supplied-group regimes, and in each regime the rule's
  **own firing mask** selects what gets averaged. The previous ``R4`` averaged the
  mismatched-group delta over *all* candidates while being described as "R2's decision",
  so it cannot support a safety claim; that quantity is kept here under its honest name,
  ``unconditional_mismatch_stress_test``;
* costs are **measured** per rule, including the cost of R3's own statistic, which needs
  the averaged predictions on its sample (the earlier accounting did not establish a
  computation saving, as the review points out);
* a decision objective ``J = risk + w * (gate + one-off averaging + H * per-prediction
  overhead)`` is reported over a horizon grid, with dominated rules identified;
* intervals use the 12 paired seeds as resampling units (seed-vector bootstrap over a
  seed x arm matrix), and arm-specific results are reported, because five arms share the
  same twelve seeds;
* two approximate-symmetry regimes (perturbation below and above the frozen tolerance)
  separate "our gate was buggy" from "label gates are a recall bottleneck".

One structural fact this module makes explicit, because it changes how gate metrics must be
read: **the label test's decision does not depend on the candidate at all** - it tests the
supplied group against the target on gate rows. Only the channel and defect tests vary per
candidate. Precision/recall of a pure label gate over candidates is therefore degenerate by
construction, not by luck.
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
from research.search import refit as _refit
from research.search import verifier_bridge as _vb

MC_TWIRL_ELEMENTS = 24
REPAIR_RESIDUAL_FLOOR = 1e-6      # harness constant: repair fires ABOVE it
EVAL_ROWS = 1024
EVAL_SEED = 5150
DEFECT_SAMPLE_ROWS = 64
HORIZONS = [1, 10, 100, 1000]
W_GRID = [0.0, 1e-4, 1e-3, 1e-2, 1e-1, 1.0]
RULES = ["R0_always", "R1_defective", "R2_defective", "R1_corrected", "R2_corrected",
         "R3_defect", "R_rand75"]
REGIMES = ["declared", "subgroup", "mismatched", "approx_1e-12", "approx_1e-9",
           "approx_1e-6", "approx_1e-3"]
# Four perturbation levels spanning the frozen tolerance: below it, at it, above it,
# far above it. The perturbation is eps * (x . v) for a fixed random vector v, which is
# NOT invariant under the site-permutation action (an integer row hash is, because these
# inputs are continuous 6-vectors, and a Hamming weight is permutation-invariant).
EPS_APPROX = {"approx_1e-12": 1e-12, "approx_1e-9": 1e-9,
              "approx_1e-6": 1e-6, "approx_1e-3": 1e-3}
NOISE_SEED = 20261207
_W: dict = {}


# ------------------------------------------------------------------ regime groups
def _subgroup_of(task):
    """A valid proper subgroup of the supplied group."""
    from verify import closure
    n = int(task.n_qubits)
    rot = [(i + 1) % n for i in range(n)]
    if str(task.name).startswith("ring"):
        gens = [[rot[rot[i]] for i in range(n)]]              # C3 inside D6
    else:
        gens = [[1, 2, 0, 3, 4, 5], [0, 1, 2, 4, 3, 5]]       # S3 on three sites
    return closure(gens, n)


def _mismatched(task, rng):
    from verify import closure
    n = int(task.n_qubits)
    declared = set(closure([list(g) for g in task.generators], n))
    for _ in range(400):
        p = tuple(rng.permutation(n))
        H = closure([list(p)], n)
        if not set(H) <= declared:
            return H, None
    return None, ("no mismatched group exists: the scored target's label-symmetry group is "
                  "the whole permutation hypothesis space")


def _twirl_elems(group, rng):
    if len(group) <= MC_TWIRL_ELEMENTS:
        return list(group), True
    idx = rng.choice(len(group), size=MC_TWIRL_ELEMENTS, replace=False)
    return [group[i] for i in idx], False


class _NoisyTask:
    """Same inputs, labels perturbed by eps * (x . v) for a fixed random vector v."""

    def __init__(self, task, eps, v):
        self._t, self.eps, self.v = task, float(eps), v
        self.n_qubits = task.n_qubits
        self.x = task.x
        self.name = task.name
        self.targets = task.targets
        self.splits = task.splits
        self.generators = task.generators
        self.primary_target = task.primary_target

    def label_oracle(self, rows, target=None):
        y = np.asarray(self._t.label_oracle(rows, target=target), dtype=float)
        noise = self.eps * (np.asarray(rows, dtype=float) @ self.v)
        # with target=None the oracle returns one column per target: same noise per row
        return y + noise.reshape((-1,) + (1,) * (y.ndim - 1))

    def __getattr__(self, k):
        return getattr(self._t, k)


# ----------------------------------------------------------------- one candidate
def evaluate_candidate(args):
    path, regimes, _unused = args
    log = _refit.load_run(path)
    task = _W["tasks"][log["family"]]
    fam, seed = log["family"], int(log["seed"])
    fit, _, _, _, check = _refit.refit_best(log, task=task)
    rng = np.random.default_rng(90210 + seed)
    x = np.asarray(task.x)
    y = np.asarray(task.targets[task.primary_target], dtype=float)
    dev = np.asarray(task.splits["validation"], bool)
    idx = np.flatnonzero(dev)
    if len(idx) > EVAL_ROWS:
        idx = np.sort(rng.choice(idx, size=EVAL_ROWS, replace=False))
    rows, yy = x[idx], y[idx]
    gate_rows = x[:64]
    probe = _W["probe"][fam]
    cand = log["best"]["candidate"]
    params = _vb.sample_param_dicts(cand, rng, 3)

    raw = np.asarray(_refit.predictions(fit, task, rows), dtype=float).reshape(-1)
    t0 = time.perf_counter()
    _ = _refit.predictions(fit, task, rows[:64])
    sec_pred_raw = (time.perf_counter() - t0) / 64.0

    t0 = time.perf_counter()
    chan = _vb.verify_candidate(cand, task, params, group="true")
    sec_channel = time.perf_counter() - t0

    v = np.random.default_rng(NOISE_SEED).standard_normal(int(task.n_qubits))
    out = {"path": path, "family": fam, "arm": log["arm"], "seed": seed,
           "reproduction": check, "n_rows": int(len(rows)),
           "target": task.primary_target,
           "channel_mean": float(chan["mean_channel_residual"]),
           "channel_above_floor": bool(chan["mean_channel_residual"]
                                       > REPAIR_RESIDUAL_FLOOR),
           "regimes": {}}

    for rname, group in regimes.items():
        if group is None:
            continue
        noisy = rname in EPS_APPROX
        eps = EPS_APPROX.get(rname, 0.0)
        ttask = _NoisyTask(task, eps, v) if noisy else task
        y_eval = yy + eps * (rows @ v) if noisy else yy
        elems, exact = _twirl_elems(group, rng)
        t0 = time.perf_counter()
        avg = _dr._average(fit, task, rows, elems)
        sec_avg = time.perf_counter() - t0
        risk_before = float(np.mean((raw - y_eval) ** 2))
        risk_after = float(np.mean((avg - y_eval) ** 2))
        srows, sraw = rows[:DEFECT_SAMPLE_ROWS], raw[:DEFECT_SAMPLE_ROWS]
        t0 = time.perf_counter()
        savg = _dr._average(fit, task, srows, elems)
        sec_defect = time.perf_counter() - t0
        defect = float(np.mean((sraw - savg) ** 2))
        gens_declared = [list(g) for g in task.generators]
        t0 = time.perf_counter()
        lab_d = _cg.label_test(ttask, gens_declared, task.primary_target, gate_rows,
                               0.0, 0.0, all_columns=True)
        sec_lab_d = time.perf_counter() - t0
        t0 = time.perf_counter()
        lab_c = _cg.label_test(ttask, [list(g) for g in group], task.primary_target,
                               gate_rows)
        sec_lab_c = time.perf_counter() - t0
        truth, worst = _cg.sound_on_probe(ttask, [list(g) for g in group],
                                          task.primary_target, probe)
        out["regimes"][rname] = {
            "group_order": len(group), "n_elements": len(elems), "twirl_exact": exact,
            "eps": eps, "risk_before": risk_before, "risk_after": risk_after,
            "delta": risk_after - risk_before,
            "group_is_label_symmetry": bool(truth), "probe_worst": worst,
            "defect_statistic": defect,
            "label_defective_accepts": bool(lab_d["violated_fraction"] == 0.0),
            "label_corrected_accepts": bool(lab_c["violated_fraction"] == 0.0),
            "label_defective_violated": lab_d["violated_fraction"],
            "label_corrected_violated": lab_c["violated_fraction"],
            "costs_seconds": {"label_defective": sec_lab_d, "label_corrected": sec_lab_c,
                              "channel": sec_channel, "defect_statistic": sec_defect,
                              "average_full": sec_avg},
            "seconds_per_prediction_raw": sec_pred_raw,
            "seconds_per_prediction_averaged": sec_pred_raw * len(elems),
            "averaging_overhead_factor": len(elems)}
    return out


# ------------------------------------------------------------------- rule masks
def _masks(recs, regime, rng_seed=4242):
    have = [r for r in recs if regime in r["regimes"]]
    if not have:
        return None, {}
    defects = np.array([r["regimes"][regime]["defect_statistic"] for r in have])
    taus = {"q1": float(np.quantile(defects, 0.25)),
            "median": float(np.quantile(defects, 0.5))}
    m = {
        "R0_always": [True] * len(have),
        "R1_defective": [r["regimes"][regime]["label_defective_accepts"] for r in have],
        "R2_defective": [bool(r["regimes"][regime]["label_defective_accepts"]
                              and r["channel_above_floor"]) for r in have],
        "R1_corrected": [r["regimes"][regime]["label_corrected_accepts"] for r in have],
        "R2_corrected": [bool(r["regimes"][regime]["label_corrected_accepts"]
                              and r["channel_above_floor"]) for r in have],
        "R3_defect": [bool(r["regimes"][regime]["defect_statistic"] > taus["q1"])
                      for r in have],
    }
    n3 = int(sum(m["R3_defect"]))
    rand = [False] * len(have)
    for i in np.random.default_rng(rng_seed).permutation(len(have))[:n3]:
        rand[int(i)] = True
    m["R_rand75"] = rand
    return have, {"thresholds": taus, "masks": m,
                  "n_fired": {k: int(sum(v)) for k, v in m.items()}}


def _rule_metrics(have, mask, regime):
    f = np.asarray(list(mask), bool)
    d = np.array([r["regimes"][regime]["delta"] for r in have])
    helped = d < 0
    seeds = np.array([r["seed"] for r in have])
    arms = np.array([r["arm"] for r in have])
    contrib = np.where(f, d, 0.0)
    matrix = []
    for s in np.unique(seeds):
        row = [float(contrib[(seeds == s) & (arms == a)].mean())
               for a in np.unique(arms)
               if ((seeds == s) & (arms == a)).any()]
        matrix.append(row)
    width = min(len(r) for r in matrix)
    matrix = [r[:width] for r in matrix]
    out = {"n_candidates": int(len(d)), "n_fired": int(f.sum()),
           "realised_mean_delta": float(contrib.mean()),
           "mean_delta_if_always_applied": float(d.mean()),
           "mean_delta_among_fired": float(d[f].mean()) if f.any() else None,
           "n_harmful": int((d > 0).sum()),
           "harmful_rejected": int(((d > 0) & ~f).sum()),
           "n_beneficial": int((d < 0).sum()),
           "beneficial_missed": int(((d < 0) & ~f).sum()),
           "mean_harm_among_rejected": (float(d[(d > 0) & ~f].mean())
                                        if ((d > 0) & ~f).any() else None),
           "mean_gain_among_missed": (float(d[(d < 0) & ~f].mean())
                                      if ((d < 0) & ~f).any() else None),
           "fired_on_beneficial": int((f & helped).sum()),
           "realised_seed_vector_bootstrap": _P.seed_vector_bootstrap_ci(matrix)}
    return out


def _cost_metrics(have, mask, regime, rule):
    f = np.asarray(list(mask), bool)
    lab_key = ("label_defective" if "defective" in rule else
               "label_corrected" if "corrected" in rule else None)
    gate = []
    for r in have:
        c = r["regimes"][regime]["costs_seconds"]
        g = 0.0
        if lab_key:
            g += c[lab_key]
        if rule in ("R2_defective", "R2_corrected"):
            g += c["channel"]
        if rule == "R3_defect":
            g += c["defect_statistic"]
        gate.append(g)
    oneoff = [r["regimes"][regime]["costs_seconds"]["average_full"] if fire else 0.0
              for r, fire in zip(have, f)]
    overhead = [(r["regimes"][regime]["seconds_per_prediction_averaged"]
                 - r["regimes"][regime]["seconds_per_prediction_raw"]) if fire else 0.0
                for r, fire in zip(have, f)]
    return {"gate_seconds_per_candidate": float(np.mean(gate)),
            "oneoff_averaging_seconds_per_candidate": float(np.mean(oneoff)),
            "per_prediction_overhead_seconds": float(np.mean(overhead))}


def _objective(risk_term, cost):
    base = (cost["gate_seconds_per_candidate"]
            + cost["oneoff_averaging_seconds_per_candidate"])
    return {"H%d_w%g" % (H, w): float(risk_term + w * (base
                                                       + H * cost["per_prediction_overhead_seconds"]))
            for H in HORIZONS for w in W_GRID}


def _init(tasks, probe):
    _W["tasks"], _W["probe"] = tasks, probe


def main(argv=None):
    ap = argparse.ArgumentParser(prog="research/search/decision_rules2.py")
    ap.add_argument("--runs", default="logs/runs_confirm")
    ap.add_argument("--out", default="research/search/decision_rules2.json")
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args(argv)
    paths = sorted(glob.glob(os.path.join(a.runs, "run_*.json")))
    families = sorted({_refit.load_run(p)["family"] for p in paths})
    tasks, probe = {}, {}
    for fam in families:
        tasks[fam] = _tasks.load_family(fam, development=True, locked=False)
        from research.search.verify_semantics import probe_indices
        probe[fam] = probe_indices(tasks[fam], n_rows=_cg.PROBE_ROWS,
                                   seed=_cg.PROBE_SEED)

    regimes_by_family = {}
    for fam, task in tasks.items():
        from verify import closure
        rng = np.random.default_rng(31337)
        mm, mm_reason = _mismatched(task, rng)
        dec = closure([list(g) for g in task.generators], int(task.n_qubits))
        reg = {"declared": dec, "subgroup": _subgroup_of(task), "mismatched": mm}
        for k in EPS_APPROX:
            reg[k] = dec if str(task.name).startswith("ring") else None
        reg["_mismatch_reason"] = mm_reason
        regimes_by_family[fam] = reg
        print("%s regimes: %s" % (fam, {k: (len(v) if v else None)
                                        for k, v in regimes_by_family[fam].items()
                                        if not k.startswith("_")}), flush=True)

    jobs = [(p, {k: v for k, v in regimes_by_family[_refit.load_run(p)["family"]].items()
                 if not k.startswith("_")}, 0) for p in paths]
    results = []
    with mp.get_context("fork").Pool(processes=int(a.workers), initializer=_init,
                                     initargs=(tasks, probe)) as pool:
        for r in pool.imap_unordered(evaluate_candidate, jobs, chunksize=1):
            results.append(r)
            if len(results) % 20 == 0:
                print("  %d/%d candidates" % (len(results), len(paths)), flush=True)

    out = {"protocol": "A6.2/A6.3", "eval_rows": EVAL_ROWS, "eval_seed": EVAL_SEED,
           "defect_sample_rows": DEFECT_SAMPLE_ROWS, "horizons": HORIZONS,
           "w_grid": W_GRID, "rules": RULES, "regimes": REGIMES, "eps_approx": EPS_APPROX,
           "noise_seed": NOISE_SEED, "atol_abs": _cg.ATOL_ABS, "atol_rel": _cg.ATOL_REL,
           "regime_orders": {f: {k: (len(v) if v else None)
                                 for k, v in r.items() if not k.startswith("_")}
                             for f, r in regimes_by_family.items()},
           "mismatch_reason": {f: r["_mismatch_reason"]
                               for f, r in regimes_by_family.items()},
           "candidates": results, "summary": {}}

    for fam in families:
        recs = [r for r in results if r["family"] == fam]
        fam_out = {}
        for regime in REGIMES:
            have, info = _masks(recs, regime)
            if have is None:
                fam_out[regime] = {"undefined": True,
                                   "reason": (regimes_by_family[fam]["_mismatch_reason"]
                                              or "no candidates in this regime")}
                continue
            rules = {}
            for rule in RULES:
                mask = info["masks"][rule]
                m = _rule_metrics(have, mask, regime)
                m["cost"] = _cost_metrics(have, mask, regime, rule)
                m["objective"] = _objective(m["realised_mean_delta"], m["cost"])
                rules[rule] = m
            # unconditional mismatch stress test (the honest version of the old R4)
            rules["unconditional_mismatch_stress_test"] = {
                "n_candidates": len(have),
                "mean_delta": float(np.mean([r["regimes"][regime]["delta"] for r in have])),
                "note": ("no firing mask applied; this is not any rule's realised risk")}
            per_arm = {}
            for arm in sorted({r["arm"] for r in have}):
                sel = [i for i, r in enumerate(have) if r["arm"] == arm]
                per_arm[arm] = {
                    rule: {"n": len(sel),
                           "fired": int(sum(info["masks"][rule][i] for i in sel)),
                           "realised": float(np.mean(
                               [have[i]["regimes"][regime]["delta"] for i in sel
                                if info["masks"][rule][i]]))}
                    for rule in RULES}
            fam_out[regime] = {
                "n_candidates": len(have),
                "group_is_label_symmetry": bool(have[0]["regimes"][regime]
                                                ["group_is_label_symmetry"]),
                "label_decision_constant_across_candidates": bool(
                    len({r["regimes"][regime]["label_corrected_accepts"]
                         for r in have}) == 1),
                "thresholds": info["thresholds"], "n_fired": info["n_fired"],
                "rules": rules, "per_arm": per_arm}
        out["summary"][fam] = fam_out
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
