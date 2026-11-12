"""Physical-task experiment: does the control's resource structure survive a real mechanism?

Same three questions as the control, on the bond-alternating Heisenberg response (primary) and the
transverse-field cluster model (independent evaluation). The regimes differ by how much of the odd
response the target contains, a_odd, and the symmetry failure is a second-order rectification of the
analog control line, not a perturbed label.

Two things are reported separately on purpose:
  * the risk decomposition and its Monte-Carlo verification (is the theory right?), and
  * the certification frontier (is the valid certificate strong enough to be worth anything?).
A correct but vacuous certificate is a failure mode, not a result, so the fallback rate is a
first-class outcome here and not a footnote.
"""

from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from shotcert.certify import calibration_losses, certify, true_delta
from shotcert.core import Policy, components, exact_risk
from shotcert.experiments.exp_control import menu
from shotcert.physics import cluster_task, heisenberg_task


def _risk_table(task, xs, S=64):
    rows = {}
    for pol in menu(S):
        R = exact_risk(task, pol, xs)
        b2, vg, sg = components(task, xs, pol)
        k = max(pol.k, 1)
        rows[pol.name] = {"R": R, "bias2": b2, "V_G": vg, "Sigma": sg,
                          "shots_used": pol.shots_used,
                          "identity_gap": R - (b2 + vg / k + sg / pol.S)}
    return rows


def _mc_check(task, xs, reps=4000, S=32):
    """Exact risk versus deployed Monte Carlo, per policy, with a paired standard error."""
    from shotcert.core import label_vector, predict_batch
    rng = np.random.default_rng(4242)
    out = {}
    for pol in menu(S):
        Z = predict_batch(task, xs, pol, rng, reps=reps)
        y = label_vector(task, xs)
        L = (Z - y) ** 2
        se = float(np.mean(np.std(L, axis=0) / np.sqrt(reps)))
        ex = exact_risk(task, pol, xs)
        out[pol.name] = {"exact": ex, "mc": float(np.mean(L)), "se": se,
                         "z": abs(float(np.mean(L)) - ex) / max(se, 1e-12)}
    return out


def _frontier(task, allocs, eps, delta=0.05, reps=150, n_eval=400):
    rows = []
    xs_eval = task.x_dist(n_eval, np.random.default_rng(555))
    for (n, S) in allocs:
        pol_menu = menu(S)
        truth = true_delta(task, pol_menu, xs_eval, "a0")
        rng = np.random.default_rng(31337 + n * 17 + S)
        viol = better = fb = 0
        chosen = {}
        for _ in range(reps):
            xs = task.x_dist(n, rng)
            losses = calibration_losses(task, pol_menu, xs, rng)
            dec = certify(losses, pol_menu, "a0", eps=eps, delta=delta)
            chosen[dec.status] = chosen.get(dec.status, 0) + 1
            if dec.status == "fallback":
                fb += 1
                continue
            d = truth.get(dec.chosen, 0.0)
            if d > 1e-12:
                viol += 1
            else:
                better += 1
        rows.append({"n": n, "S": S, "eps": eps,
                     "violation_rate": viol / reps, "power": better / reps,
                     "fallback_rate": fb / reps,
                     "best_true": min(truth, key=lambda k: truth[k]),
                     "best_true_delta": min(truth.values()),
                     "statuses": chosen})
    return rows


def run_task(task, label, allocs, eps, mc_xs_n=150, table_xs_n=400):
    xs_tab = task.x_dist(table_xs_n, np.random.default_rng(777))
    xs_mc = task.x_dist(mc_xs_n, np.random.default_rng(778))
    tab = _risk_table(task, xs_tab, S=64)
    return {"label": label, "note": task.note, "y_var": task.y_var,
            "risk_S64": tab,
            "max_identity_gap": max(abs(v["identity_gap"]) for v in tab.values()),
            "max_mc_z": max(v["z"] for v in _mc_check(task, xs_mc).values()) if mc_xs_n else None,
            "mc_check_S32": _mc_check(task, xs_mc),
            "frontier": _frontier(task, allocs, eps)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shotcert/results/physics.json")
    ap.add_argument("--reps", type=int, default=150)
    ap.add_argument("--n-primary", type=int, default=6)
    ap.add_argument("--n-eval", type=int, default=7)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    # epsilon declared from the control pilot: the interior-policy gain scale there was ~0.01,
    # so eps = 0.01 asks for a certified reduction of at least that size. eps = 0 is the stricter
    # variant and is reported alongside, not instead.
    eps = 0.01
    allocs = [(50, 128), (100, 64), (200, 32), (400, 16), (800, 8), (1600, 4)]
    t0 = time.time()
    res = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "eps_declared": eps, "allocs": allocs, "tasks": []}

    for a_odd, tag in ((0.0, "even_target"), (0.35, "mostly_even"), (1.0, "raw_target")):
        t = heisenberg_task(n=args.n_primary, a_odd=a_odd, c_rect=0.18)
        res["tasks"].append(run_task(t, "heisenberg_%s_n%d" % (tag, args.n_primary),
                                     allocs, eps))
    # scaling check on the same mechanism
    t8 = heisenberg_task(n=8, a_odd=0.0, c_rect=0.18)
    res["tasks"].append(run_task(t8, "heisenberg_even_target_n8", allocs, eps,
                                 mc_xs_n=80, table_xs_n=250))
    # independent evaluation: different mechanism, different observable, different family
    for a_odd, tag in ((0.0, "even_target"), (1.0, "raw_target")):
        t = cluster_task(n=args.n_eval, a_odd=a_odd)
        res["tasks"].append(run_task(t, "cluster_%s_n%d" % (tag, args.n_eval), allocs, eps,
                                     mc_xs_n=80, table_xs_n=250))
    res["wall_seconds"] = round(time.time() - t0, 1)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote %s in %.1fs" % (args.out, res["wall_seconds"]))
    for tr in res["tasks"]:
        raw = tr["risk_S64"]["a0"]["R"]
        best = min((v["R"], k) for k, v in tr["risk_S64"].items())
        print("%-28s gap=%.1e  R_a0=%.5f  best=%s %.5f (%+.5f)"
              % (tr["label"], tr["max_identity_gap"], raw, best[1], best[0], best[0] - raw))


if __name__ == "__main__":
    main()
