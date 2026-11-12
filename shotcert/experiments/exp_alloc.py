"""A5: does the closed-form optimum, ESTIMATED FROM SHOTS, beat the alternatives at matched cost?

The theorem says the optimal symmetrisation weight at budget S is w*(S) = (dD+A)/(2A) - V/(2AS). This
experiment does not get A, dD, V from the simulator: it estimates them from calibration shots and then
deploys. Every arm spends exactly S shots per prediction and the same number of calibration shots, so
the comparison is matched by construction on both calibration and deployment.

Estimating quadratic functionals from noisy shots. A, B and the discrepancy terms are quadratic in the
orbit means, and plugging shot means straight in adds a positive noise bias. The fix is cross-fitting:
split each circuit's s shots into two independent halves A and B, and form each quadratic functional as
a product of one statistic from A and the same statistic from B. Because the halves are independent and
conditionally unbiased, E[(mbar^A - m0^A)(mbar^B - m0^B)] = (mu_bar - mu_0)^2 exactly, and similarly for
the cross terms. No noise-bias correction, no unknown constants.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from shotcert.certify import calibration_losses_fast, true_delta, wilson
from shotcert.core import Policy, born_prob, label_vector, orbit_expectations
from shotcert.tasks import control_task
from shotcert.theory import coefficients, thresholds, w_star


def shot_means(task, xs, s, rng):
    """s destructive shots at each orbit point: (n, G) array of +-1 shot means."""
    P = born_prob(np.stack([np.asarray(task.model(a(xs)), dtype=float).reshape(-1)
                            for a in task.group.actions], axis=1))
    return 2.0 * (rng.binomial(s, P) / float(s)) - 1.0


def estimate_coeffs(task, xs, s, rng):
    """Cross-fitted estimates of A, dD, V from two independent half-records per circuit."""
    recA = shot_means(task, xs, s, rng)
    recB = shot_means(task, xs, s, rng)
    y = label_vector(task, xs)
    G = recA.shape[1]

    def parts(rec):
        m0 = rec[:, 0]
        mb = rec.mean(axis=1)
        return m0, mb

    m0A, mbA = parts(recA)
    m0B, mbB = parts(recB)
    dA, dB = mbA - m0A, mbB - m0B
    A = float(np.mean(dA * dB))                                    # unbiased for E[(mubar-mu0)^2]
    B = float(np.mean((m0A - y) * dB))                             # unbiased for E[(mu0-y)(mubar-mu0)]
    # dD = D0 - DG = -2B - A exactly (algebra, so the same cross-fitted B and A give a consistent dD)
    dD = -2.0 * B - A
    # V = sigmabar^2 - sigma0^2 with sigma_g^2 = 1 - mu_g^2, so V = mean_g(1-mu_g^2) - (1-mu_0^2)
    #    = mu_0^2 - mean_g mu_g^2; cross-fit each square.
    sq0 = float(np.mean(m0A * m0B))
    sqb = float(np.mean((recA * recB).mean(axis=1)))
    V = sq0 - sqb
    return {"A": A, "B": B, "dD": dD, "V": V, "D0": float(np.mean(m0A * m0B)) - 2 * float(np.mean(m0A * y))
            + float(np.mean(y * y)), "sigma0": 1.0 - sq0}


def deploy(task, xs, w, S, rng):
    """One deployed prediction per instance at mixture weight w, total S shots; returns squared losses."""
    P = born_prob(np.stack([np.asarray(task.model(a(xs)), dtype=float).reshape(-1)
                            for a in task.group.actions], axis=1))
    G = P.shape[1]
    S_a = int(round(w * S))
    S_0 = S - S_a
    y = label_vector(task, xs)
    n = len(y)
    z = np.zeros(n)
    if S_a > 0:
        per = max(S_a // G, 1)
        acc = np.zeros(n)
        for g in range(G):
            acc += 2.0 * (rng.binomial(per, P[:, g]) / per) - 1.0
        z += w * acc / G
    if S_0 > 0:
        z += (1.0 - w) * (2.0 * (rng.binomial(S_0, P[:, 0]) / S_0) - 1.0)
    return (z - y) ** 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shotcert/results/alloc.json")
    ap.add_argument("--reps", type=int, default=60)
    ap.add_argument("--n", type=int, default=400)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    t0 = time.time()
    res = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "reps": args.reps, "n_calib": args.n,
           "matched": "every arm spends exactly S shots per prediction and the same calibration shots",
           "rows": []}
    from shotcert.physics import cluster_task, heisenberg_task
    tasks = [("control_help", control_task(regime="help")),
             ("control_hurt", control_task(regime="hurt")),
             ("control_interior", control_task(regime="interior")),
             ("heisenberg_even_n6", heisenberg_task(n=6, a_odd=0.0, c_rect=0.18)),
             ("heisenberg_raw_n6", heisenberg_task(n=6, a_odd=1.0, c_rect=0.18)),
             ("cluster_n7", cluster_task(n=7, a_odd=0.0))]
    for (tname, task) in tasks:
        G = len(task.group.actions)
        xs_th = task.x_dist(300, np.random.default_rng(4040))
        c_true = coefficients(task, xs_th)
        for S in (16, 64, 256):
            s_half = max(S // (2 * G), 1)
            rng = np.random.default_rng(770000 + 13 * S + 101 * len(tname))
            arms = {k: [] for k in ("w_hat", "w_true", "raw", "full", "half")}
            what_hat = []
            for _ in range(args.reps):
                xs_cal = task.x_dist(args.n, rng)
                c_hat = estimate_coeffs(task, xs_cal, s_half, rng)
                what = w_star(c_hat, S)
                what_hat.append(what)
                xs_dep = task.x_dist(args.n, rng)
                for name, w in (("w_hat", what), ("w_true", w_star(c_true, S)),
                                ("raw", 0.0), ("full", 1.0), ("half", 0.5)):
                    arms[name].append(float(np.mean(deploy(task, xs_dep, w, S, rng))))
            row = {"task": tname, "S": S, "calib_shots": args.n * 2 * G * s_half,
                   "deploy_shots_per_prediction": S,
                   "w_true": w_star(c_true, S),
                   "w_hat_mean": float(np.mean(what_hat)),
                   "w_hat_sd": float(np.std(what_hat)),
                   "A_true": c_true["A"], "dD_true": c_true["dD"], "V_true": c_true["V"],
                   "thresholds": list(thresholds(c_true)),
                   "risk": {k: float(np.mean(v)) for k, v in arms.items()},
                   "risk_sd": {k: float(np.std(v)) for k, v in arms.items()}}
            row["regret_vs_oracle"] = row["risk"]["w_hat"] - min(row["risk"].values())
            res["rows"].append(row)
            print("%-18s S=%3d w_true=%.2f w_hat=%.2f(sd %.2f) | risk w_hat=%.5f oracle=%.5f "
                  "raw=%.5f full=%.5f half=%.5f regret=%.5f"
                  % (tname, S, row["w_true"], row["w_hat_mean"], row["w_hat_sd"],
                     row["risk"]["w_hat"], min(row["risk"].values()), row["risk"]["raw"],
                     row["risk"]["full"], row["risk"]["half"], row["regret_vs_oracle"]), flush=True)
            with open(args.out, "w") as f:
                json.dump(res, f, indent=1)
    res["wall_seconds"] = round(time.time() - t0, 1)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote %s in %.1fs" % (args.out, res["wall_seconds"]))


if __name__ == "__main__":
    main()
