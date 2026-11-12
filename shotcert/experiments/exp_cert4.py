"""A4.1/A4.2: matched certification comparison. One menu, one cost, several selectors.

The A3 comparison of "certified" against "plug-in" is withdrawn and re-run here as pre-specified. Its
defects, all found by review: the two arms deployed at different total shots (16 vs 8 per prediction);
the group-free menu's best shrinkage level moved with s, so "the same candidate set" was not one set;
the group arm had two candidates and the group-free arm nine, so the multiplicity log(2m/delta) that the
certified rule pays was different in the two arms; and the plug-in rule carries no delta, so comparing
it against a delta-valid rule is not an equal-confidence comparison.

Held fixed in every cell: one candidate menu, hence the same menu size and the same multiplicity m for
every selector; the same total shots S per prediction for every policy (each policy in both menus spends
exactly S, differing only in how it allocates them, so calibration cost n*sum_p shots_used(p) = n*m*S is
identical across arms); the same calibration instances and the same total calibration shots for every
selector.

Selectors, with the guarantee each one actually has:
  plugin   argmin of the paired mean loss; no confidence guarantee at all.
  student  Studentised simultaneous bound; asymptotic, no distribution-free guarantee.
  mp       simultaneous Maurer-Pontil, ln = log(2m/delta); distribution-free, pays for m.
  split    pick on half the instances, certify that one candidate on the other half with m=1, so the
           multiplicity is paid once instead of inside every bound. Distribution-free.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from shotcert.certify import (calibration_losses_fast, mp_bound, normal_bound, true_delta, wilson)
from shotcert.core import Policy
from shotcert.tasks import control_task

N_DEPLOY = 1000


def group_menu(S, G):
    """Seven candidates, each costing exactly S shots: a0, full averaging, three mixtures, two orbit
    randomisations. Mixtures split S between the orbit branch and the raw branch, so total is S."""
    out = [Policy("a0", "raw", S=S, orbit_size=G),
           Policy("strat", "stratified", S=S, orbit_size=G),
           Policy("mix25", "mix", S=S, w=0.25, orbit_size=G),
           Policy("mix50", "mix", S=S, w=0.50, orbit_size=G),
           Policy("mix75", "mix", S=S, w=0.75, orbit_size=G),
           Policy("orbit2", "orbit_k", k=2, S=S, orbit_size=G),
           Policy("orbit4", "orbit_k", k=4, S=S, orbit_size=G)]
    return [p for p in out if p.feasible()]


def generic_menu(S, G):
    """Seven candidates, each costing exactly S shots: a0 plus six shrinkage levels."""
    out = [Policy("a0", "raw", S=S, orbit_size=G)]
    for g in (0.05, 0.1, 0.2, 0.3, 0.4, 0.5):
        out.append(Policy("shrink%d" % int(g * 100), "shrink", S=S, gamma=g, orbit_size=G))
    return [p for p in out if p.feasible()]


def choose(losses, cand, a0, eps, delta, rule, m):
    """Return the chosen candidate name or None. `cand` excludes a0."""
    base = losses[a0]
    if rule == "plugin":
        d = {k: float(np.mean(losses[k]) - np.mean(base)) for k in cand}
        best = min(d, key=lambda k: d[k])
        return best if d[best] < 0.0 else None
    if rule == "mp":
        ub = {k: mp_bound(losses[k] - base, delta, menu_size=m) for k in cand}
    elif rule == "student":
        ub = {k: normal_bound(losses[k] - base, delta / m) for k in cand}
    elif rule == "split":
        h = len(base) // 2
        pick = None
        bestv = 0.0
        for k in cand:                                   # stage 1: pick on the first half
            v = float(np.mean(losses[k][:h]) - np.mean(base[:h]))
            if v < bestv:
                bestv, pick = v, k
        if pick is None:
            return None
        ub = {pick: mp_bound(losses[pick][h:] - base[h:], delta, menu_size=1)}   # stage 2: certify
        return pick if ub[pick] <= eps else None
    else:
        raise ValueError("unknown rule %r" % rule)
    ok = {k: v for k, v in ub.items() if v <= eps}
    if not ok:
        return None
    return min(sorted(ok), key=lambda k: ok[k])


def run_cell(task, menu, n, S, eps, delta, reps, seed, rules, xs_eval):
    truth = true_delta(task, menu, xs_eval, "a0")
    names = [p.name for p in menu]
    cand = [k for k in names if k != "a0"]
    m = len(cand)
    min_true = min(truth.values())
    rng = np.random.default_rng(seed)
    acc = {r: {"sel": 0, "near": 0, "nondeg": 0, "fail": 0, "excess": []} for r in rules}
    for _ in range(reps):
        xs = task.x_dist(n, rng)
        losses = calibration_losses_fast(task, menu, xs, rng)
        for r in rules:
            pick = choose(losses, cand, "a0", eps, delta, r, m)
            a = acc[r]
            if pick is None:
                continue
            d = truth.get(pick, 0.0)
            a["sel"] += 1
            a["excess"].append(d - min_true)
            if d - min_true <= eps:
                a["near"] += 1
            if d <= eps:
                a["nondeg"] += 1
            if d > eps:
                a["fail"] += 1
    out = {}
    for r in rules:
        a = acc[r]
        lo, hi = wilson(a["near"], reps)
        nlo, nhi = wilson(a["fail"], reps)
        out[r] = {"selection_rate": a["sel"] / reps,
                  "near_optimal_rate": a["near"] / reps, "near_optimal_ci": [lo, hi],
                  "non_degradation_rate": a["nondeg"] / reps,
                  "fallback_rate": 1.0 - a["sel"] / reps,
                  "mean_excess_risk": float(np.mean(a["excess"])) if a["excess"] else None,
                  "failure_rate": a["fail"] / reps, "failure_ci": [nlo, nhi]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shotcert/results/cert4.json")
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--rules", default="plugin,student,mp,split")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    t0 = time.time()
    rules = [r.strip() for r in args.rules.split(",")]
    res = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "reps": args.reps, "delta": args.delta, "n_deploy": N_DEPLOY, "rules": rules,
           "menus": "group and group-free, both 7 candidates, every policy costs exactly S shots",
           "rows": []}
    xs_eval = None
    grid = [(n, S) for S in (16, 32, 64) for n in (100, 200, 400, 800, 1600)]
    for reg in ("help", "hurt", "interior"):
        task = control_task(regime=reg)
        xs_eval = task.x_dist(400, np.random.default_rng(4040))
        for mname, mfn in (("group", group_menu), ("generic", generic_menu)):
            for (n, S) in grid:
                menu = mfn(S, len(task.group.actions))
                # eps = 0 asks for certified non-degradation against raw; the near-optimality column
                # is reported at the same eps so the two are not conflated.
                sel = run_cell(task, menu, n, S, 0.0, args.delta, args.reps,
                               4240000 + 31 * n + 7 * S + 101 * len(mname) + 13 * len(reg),
                               rules, xs_eval)
                truth = true_delta(task, menu, xs_eval, "a0")
                row = {"task": "control_%s" % reg, "menu": mname, "n": n, "S": S,
                       "policies": len(menu), "multiplicity": len(menu) - 1,
                       "calib_shots": n * sum(p.shots_used for p in menu),
                       "best_true_delta": float(min(truth.values())),
                       "selectors": sel}
                res["rows"].append(row)
                g = sel["plugin"]
                print("%-16s %-8s n=%4d S=%2d m=%d calib=%6d best=%+.5f | "
                      "plugin near=%.2f fail=%.3f | mp near=%.2f sel=%.2f | split near=%.2f sel=%.2f"
                      % (row["task"], mname, n, S, len(menu) - 1, row["calib_shots"],
                         row["best_true_delta"], g["near_optimal_rate"], g["failure_rate"],
                         sel["mp"]["near_optimal_rate"], sel["mp"]["selection_rate"],
                         sel["split"]["near_optimal_rate"], sel["split"]["selection_rate"]),
                      flush=True)
                with open(args.out, "w") as f:
                    json.dump(res, f, indent=1)
    res["wall_seconds"] = round(time.time() - t0, 1)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote %s in %.1fs" % (args.out, res["wall_seconds"]))


if __name__ == "__main__":
    main()
