"""Why certification costs what it costs, and whether the frontier is statistics or inequality.

The control experiment shows a sharp transition in certificate power along the (preparations,
shots) axis at fixed total budget. Two explanations look identical in that plot and are not:

  (i) the *statistics* need more instances, because the contrast D varies between instances by far
      more than the risk gap being certified, and shots cannot reduce between-instance variance; or
  (ii) the *inequality* needs more instances, because the empirical-Bernstein range term
      7(b-a)ln/(3(n-1)) is huge at small n regardless of the data.

If (ii) dominates, the frontier is a property of the bound we happened to use and not of the
problem, and saying otherwise is the kind of overclaim that ended the previous submission. Both are
measured here: Var(D) is fitted as A + B/S (A between-instance, B/S deployed-noise), and the EB
bound is split into its variance and range parts at every (n, S).
"""

from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from shotcert.certify import LOSS_RANGE, calibration_losses, eb_bound
from shotcert.core import Policy, label_vector, predict_batch
from shotcert.experiments.exp_control import menu
from shotcert.tasks import control_task


def var_D(task, pol, xs, S, reps=8000, rng=None):
    """Var(D) for the paired contrast against a0, and its between-instance / noise split.

    D = (Z_a - Y)^2 - (Z_a0 - Y)^2 with both predictors stochastic. Writing Z = m + eps given x,
        Var(D) = Var_x(E[D|x]) + E[Var(D|x)],
    and the second term is the one shots can buy down. Measuring the two separately is what turns
    "certification is expensive" into a statement about which resource is missing.
    """
    rng = rng or np.random.default_rng(0)
    a0 = Policy("a0", "raw", 1, S)
    Za = predict_batch(task, xs, pol, rng, reps=reps)
    Z0 = predict_batch(task, xs, a0, rng, reps=reps)
    y = label_vector(task, xs)
    D = (Za - y) ** 2 - (Z0 - y) ** 2                # (reps, n)
    per_inst_mean = D.mean(axis=0)
    per_inst_var = D.var(axis=0, ddof=1)
    return {"var_total": float(np.var(D, ddof=1)),
            "var_between": float(np.var(per_inst_mean, ddof=1)),
            "var_noise": float(np.mean(per_inst_var)),
            "mean_D": float(np.mean(D))}


def eb_split(D, delta):
    """The two additive parts of the empirical-Bernstein bound, reported separately."""
    import math
    n = len(D)
    v = float(np.var(D, ddof=1))
    ln = math.log(LOSS_RANGE / (delta * n))
    var_term = (LOSS_RANGE / 2.0) * math.sqrt(max(2.0 * v * ln / n, 0.0))
    range_term = 7.0 * LOSS_RANGE * ln / (3.0 * (n - 1))
    return {"mean": float(np.mean(D)), "sd": math.sqrt(v),
            "var_term": var_term, "range_term": range_term,
            "ub": eb_bound(D, delta)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shotcert/results/variance.json")
    ap.add_argument("--n-pool", type=int, default=300)
    ap.add_argument("--reps", type=int, default=2500)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    t0 = time.time()
    res = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "regimes": {}, "wall_seconds": None}
    rng = np.random.default_rng(2024)
    for reg in ("help", "hurt", "interior"):
        task = control_task(regime=reg)
        xs = task.x_dist(args.n_pool, np.random.default_rng(909))
        entry = {"var_vs_S": {}, "eb_split": {}}
        for S in (4, 16, 64, 256):
            rows = {}
            for pol in menu(S):
                if pol.name not in ("strat", "k4", "mix50"):
                    continue
                rows[pol.name] = var_D(task, pol, xs, S, reps=args.reps, rng=rng)
            entry["var_vs_S"][S] = rows
        # EB split at the allocations used by the frontier, for the best candidate
        for (n, S) in ((50, 128), (100, 64), (200, 32), (400, 16), (800, 8), (1600, 4)):
            cl = calibration_losses(task, menu(S), task.x_dist(n, rng), rng)
            base = cl["a0"]
            names = [k for k in cl if k != "a0"]
            entry["eb_split"]["%d_%d" % (n, S)] = {
                nm: eb_split(cl[nm] - base, 0.05 / len(names)) for nm in names}
        res["regimes"][reg] = entry
    res["wall_seconds"] = round(time.time() - t0, 1)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote %s in %.1fs" % (args.out, res["wall_seconds"]))
    for reg, e in res["regimes"].items():
        v4 = e["var_vs_S"][4]["strat"]
        v256 = e["var_vs_S"][256]["strat"]
        print("%-9s strat Var(D): S=4 %.5f (between %.5f noise %.5f) | S=256 %.5f (between %.5f noise %.5f)"
              % (reg, v4["var_total"], v4["var_between"], v4["var_noise"],
                 v256["var_total"], v256["var_between"], v256["var_noise"]))


if __name__ == "__main__":
    main()
