"""Control experiment: verify the decomposition, the certificate's coverage, and the budget frontier.

Three questions, in the order a reader should be able to check them:

  Q1  Is R_S(a) = bias^2 + V_G/k + Sigma/S true, and does the k-vs-S split behave as claimed (F1)?
  Q2  Does the paired certificate achieve its nominal coverage when the deployed predictor is
      stochastic, across independent calibration repetitions?
  Q3  Under a total budget B = n preparations x S shots, which allocation maximises certificate
      power, and does the answer depend on whether the policy menu contains symmetry spending?

Q3 is the operational question the paper is about: shots and preparations buy different things, and
for a stochastic deployed predictor the tradeoff is not the classical one.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time

import numpy as np

from shotcert.certify import calib_ledger, calibration_losses, certify, mp_bound, true_delta
from shotcert.core import Policy, components, exact_risk, label_vector, predict_batch
from shotcert.tasks import control_task

REGIMES = ("help", "hurt", "interior")
MENU_S = 64


def menu(S):
    """Frozen policy menu at total shots S. Every entry must satisfy shots_used <= S.

    k is capped at S: with per = S//k, a policy with k > S would spend k shots, which is a
    matched-budget violation dressed up as a policy. The cap is why the menu shrinks at small S, and
    why the frontier is a real tradeoff rather than an artefact of extra shots.
    """
    ks = [k for k in (1, 2, 4, 8, 16, 32, 64) if k <= S]
    out = [Policy("a0", "raw", 1, S),
           Policy("strat", "stratified", 2, S),
           Policy("mix25", "mix", 2, S, w=0.25),
           Policy("mix50", "mix", 2, S, w=0.5),
           Policy("mix75", "mix", 2, S, w=0.75)]
    for k in ks:
        out.append(Policy("k%d" % k, "orbit_k", k, S))
    dropped = [p.name for p in out if not p.feasible()]
    kept = [p for p in out if p.feasible()]
    menu.dropped = getattr(menu, "dropped", {})
    menu.dropped[S] = dropped       # reported, so a shrinking menu is visible, not hidden
    assert any(p.name == "a0" for p in kept) and any(p.name == "strat" for p in kept), kept
    return kept


def q1_decomposition(n_eval=1500):
    out = {}
    for reg in REGIMES:
        t = control_task(regime=reg)
        xs = t.x_dist(n_eval, np.random.default_rng(101))
        rows = {}
        for pol in menu(64):
            R = exact_risk(t, pol, xs)
            b2, vg, sg = components(t, xs, pol)
            k = max(pol.k, 1)
            rows[pol.name] = {"R": R, "bias2": b2, "V_G": vg, "Sigma": sg,
                              "identity_gap": R - (b2 + vg / k + sg / pol.S)}
        # F1: at fixed S, sweep k and watch which term moves
        ks = [1, 2, 4, 8, 16, 32, 64]
        f1 = []
        for k in ks:
            _, vg, sg = components(t, xs, Policy("k", "orbit_k", k, 64))
            f1.append({"k": k, "V_G": vg, "Sigma": sg,
                       "R": exact_risk(t, Policy("k", "orbit_k", k, 64), xs)})
        # F2: with a per-circuit switching cost c, total cost of a prediction
        f2 = []
        for c in (0.0, 0.02, 0.1, 0.5):
            best = None
            for k in ks:
                pol = Policy("k", "orbit_k", k, 64)
                R = exact_risk(t, pol, xs)
                cost = 64 + c * min(k, 4 * len(t.group.actions))
                obj = R + c * min(k, 4 * len(t.group.actions)) / 64.0
                if best is None or obj < best[1] - 1e-15:
                    best = (k, obj, R)
            f2.append({"c": c, "k_star": best[0], "R_at_kstar": best[2]})
        out[reg] = {"rows": rows, "F1": f1, "F2": f2,
                    "max_identity_gap": max(abs(r["identity_gap"]) for r in rows.values())}
    return out


def q2_coverage(n_eval=800, reps=300, delta=0.05):
    """Empirical violation rate of the certificate, per regime and per calibration size."""
    out = []
    for reg in REGIMES:
        t = control_task(regime=reg)
        xs_eval = t.x_dist(n_eval, np.random.default_rng(202))
        truth = true_delta(t, menu(64), xs_eval, "a0")
        best_true = min(truth, key=lambda k: truth[k])
        worst_true = max(truth, key=lambda k: truth[k])
        for n in (25, 50, 100, 200, 400):
            rng = np.random.default_rng(7000 + n)
            viol = sel_worse = fallback = sel_better = 0
            for _ in range(reps):
                xs = t.x_dist(n, rng)
                losses = calibration_losses(t, menu(64), xs, rng)
                dec = certify(losses, menu(64), "a0", eps=0.0, delta=delta)
                if dec.status == "fallback":
                    fallback += 1
                    continue
                d = truth.get(dec.chosen, 0.0)
                if d > 1e-12:
                    viol += 1
                    sel_worse += 1
                else:
                    sel_better += 1
            out.append({"regime": reg, "n": n, "reps": reps,
                        "violation_rate": viol / reps, "fallback_rate": fallback / reps,
                        "power": sel_better / reps,
                        "true_best": best_true, "true_best_delta": truth[best_true],
                        "true_worst": worst_true, "true_worst_delta": truth[worst_true]})
    return out


def q3_budget_frontier(B=6400, delta=0.05, reps=200, n_eval=800):
    """Total budget B = n * S. Sweep the allocation; measure certificate power and violation rate."""
    out = []
    allocs = [(n, B // n) for n in (25, 50, 80, 100, 160, 200, 320, 400, 800, 1600)
              if B % n == 0 and B // n >= 4]
    for reg in REGIMES:
        t = control_task(regime=reg)
        xs_eval = t.x_dist(n_eval, np.random.default_rng(303))
        for (n, S) in allocs:
            pol_menu = menu(S)
            truth = true_delta(t, pol_menu, xs_eval, "a0")
            rng = np.random.default_rng(900000 + n * 31 + S)
            viol = better = fb = 0
            for _ in range(reps):
                xs = t.x_dist(n, rng)
                losses = calibration_losses(t, pol_menu, xs, rng)
                dec = certify(losses, pol_menu, "a0", eps=0.0, delta=delta)
                if dec.status == "fallback":
                    fb += 1
                    continue
                if truth.get(dec.chosen, 0.0) > 1e-12:
                    viol += 1
                else:
                    better += 1
            out.append({"regime": reg, "B": B, "n": n, "S": S,
                        "violation_rate": viol / reps, "power": better / reps,
                        "fallback_rate": fb / reps,
                        "best_true_delta": min(truth.values()),
                        "best_true": min(truth, key=lambda k: truth[k])})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shotcert/results/control.json")
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--frontier-reps", type=int, default=200)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    t0 = time.time()
    res = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "q1_decomposition": q1_decomposition(),
           "q2_coverage": q2_coverage(reps=args.reps),
           "q3_budget_frontier": q3_budget_frontier(reps=args.frontier_reps),
           "wall_seconds": None}
    res["wall_seconds"] = round(time.time() - t0, 1)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote %s in %.1fs" % (args.out, res["wall_seconds"]))
    for reg in REGIMES:
        print("%-9s max identity gap %.2e" % (reg, res["q1_decomposition"][reg]["max_identity_gap"]))


if __name__ == "__main__":
    main()
