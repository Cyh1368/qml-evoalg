"""A2.2 + A2.5 + A2.6: matched-TOTAL-cost certification, symmetry menu vs generic menu.

The first version of this study labelled n*S the calibration budget while calibration_losses()
evaluated every candidate on every instance, understating calibration shots by a factor of the menu
size, and it counted a "violation" as any selected policy worse than raw rather than one that broke
the declared epsilon. Both are fixed here, and the comparison is made at matched total cost with the
corrected simultaneous bound, with Monte-Carlo intervals on every rate.

Two menus, same certificate, same calibration protocol:
  sym     : raw + orbit_k(k) + stratified + mixtures          (uses the group)
  generic : raw + shrinkage toward a declared constant        (uses no group at all)
The generic menu is the honest comparator for "does spending shots on symmetry earn its keep": it
buys variance reduction the same way, with one circuit, zero switches, and no group calibration.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from shotcert.certify import (calib_ledger, calibration_losses_fast, certify, mp_bound,
                            n_required_mp, true_delta, wilson)
from shotcert.core import Policy
from shotcert.tasks import control_task

N_DEPLOY = 1000          # declared deployment count: the certificate is bought to serve these


def sym_menu(S, G):
    out = [Policy("a0", "raw", S=S, orbit_size=G)]
    for k in (2, 4, 8, 16, 32, 64):
        out.append(Policy("orbit%d" % k, "orbit_k", k=k, S=S, orbit_size=G))
    out.append(Policy("strat", "stratified", S=S, orbit_size=G))
    for w in (0.25, 0.5, 0.75):
        out.append(Policy("mix%d" % int(w * 100), "mix", S=S, w=w, orbit_size=G))
    return [p for p in out if p.feasible()]


def generic_menu(S, G):
    out = [Policy("a0", "raw", S=S, orbit_size=G)]
    for g in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
        out.append(Policy("shrink%d" % int(g * 100), "shrink", S=S, gamma=g, orbit_size=G))
    return [p for p in out if p.feasible()]


MENUS = {"sym": sym_menu, "generic": generic_menu}


def run_point(task, menu_fn, n, S, eps, delta, reps, rng_seed, bound="normal"):
    """One frontier point: certify `reps` times on n instances, report rates with intervals."""
    G = len(task.group.actions)
    menu = menu_fn(S, G)
    ledger = calib_ledger(menu, n)
    ledger["switches_per_prediction"] = int(sum(p.max_switches for p in menu))
    ledger["deploy_shots"] = int(N_DEPLOY * min(p.shots_used for p in menu))
    ledger["total_shots"] = int(ledger["shots_total"] + N_DEPLOY * S)
    ledger["total_preparations"] = int(ledger["preparations_total"] + N_DEPLOY)

    xs_eval = task.x_dist(300, np.random.default_rng(4040))
    truth = true_delta(task, menu, xs_eval, "a0")
    useful = [k for k, v in truth.items() if v <= eps]
    rng = np.random.default_rng(rng_seed)
    n_viol = n_pow = n_fb = n_sel = 0
    chosen_risks = []
    for _ in range(reps):
        xs = task.x_dist(n, rng)
        losses = calibration_losses_fast(task, menu, xs, rng)
        dec = certify(losses, menu, "a0", eps=eps, delta=delta, bound=bound)
        if dec.status != "selected":
            n_fb += 1
            continue
        n_sel += 1
        d = truth.get(dec.chosen, 0.0)
        chosen_risks.append(d)
        if d > eps:                          # A2.5: violation is against the DECLARED epsilon
            n_viol += 1
        if d <= eps:
            n_pow += 1
    lo, hi = wilson(n_viol, reps)
    plo, phi = wilson(n_pow, reps)
    return {"n_instances": n, "S": S, "eps": eps, "bound": bound, "policies": len(menu),
            "n_required_mp": n_required_mp(min(truth.values()), len(menu), delta),
            "ledger": ledger,
            "n_useful_policies": len(useful),
            "best_true_delta": float(min(truth.values())),
            "violation_rate": n_viol / reps, "violation_ci": [lo, hi],
            "power": n_pow / reps, "power_ci": [plo, phi],
            "fallback_rate": n_fb / reps, "selection_rate": n_sel / reps,
            "mean_chosen_true_delta": float(np.mean(chosen_risks)) if chosen_risks else None,
            "worst_chosen_true_delta": float(max(chosen_risks)) if chosen_risks else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shotcert/results/ledger.json")
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--regimes", default="help,hurt,interior")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    t0 = time.time()
    res = {"regimes": args.regimes, "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "reps": args.reps, "delta": args.delta, "n_deploy": N_DEPLOY,
           "bound_swept": "normal (Studentised, coverage audited with Wilson intervals)",
           "bound_reference": "mp (Maurer-Pontil Cor 5, log(2m/delta), contrast width 8): vacuous at "
                              "these effect sizes, cost reported analytically as n_required_mp",
           "rows": []}

    # Control: epsilon declared as 0 (a claim of non-degradation, not of improvement).
    # The sweep is over (n, S) pairs chosen to reach comparable TOTAL cost, and the ledger is
    # reported at every point so the reader can check the match rather than trust the label.
    allocs = [(n, S) for S in (8, 32, 64) for n in (50, 100, 200, 400, 800, 1600)]
    for reg in [r.strip() for r in args.regimes.split(",") if r.strip()]:
        task = control_task(regime=reg)
        for mname, mfn in MENUS.items():
            for (n, S) in allocs:
                r = run_point(task, mfn, n, S, eps=0.0, delta=args.delta, reps=args.reps,
                              rng_seed=777000 + 31 * n + 7 * S + 1000 * len(mname) + len(reg),
                              bound="normal")
                r.update({"task": "control_%s" % reg, "menu": mname})
                res["rows"].append(r)
                print("%-16s %-8s n=%3d S=%2d m=%2d tot_shots=%7d pow=%.3f[%.3f,%.3f] "
                      "viol=%.3f[%.3f,%.3f] fb=%.3f"
                      % (r["task"], mname, n, S, r["policies"], r["ledger"]["total_shots"],
                         r["power"], r["power_ci"][0], r["power_ci"][1],
                         r["violation_rate"], r["violation_ci"][0], r["violation_ci"][1],
                         r["fallback_rate"]), flush=True)
                with open(args.out, "w") as f:
                    json.dump(res, f, indent=1)
    res["wall_seconds"] = round(time.time() - t0, 1)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote %s in %.1fs" % (args.out, res["wall_seconds"]))


if __name__ == "__main__":
    main()
