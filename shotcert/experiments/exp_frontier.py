"""A6.3: optimized frontiers at equal TOTAL budget.

The previous frontier fixed shots per circuit and let each arm's total follow, which built the
factor-of-two into the arm definitions. Here the budget B is fixed -- calibration preparations plus
deployment preparations -- and each arm chooses its instance count n, its per-prediction shot total S
and its admissible policies subject to B. The reported quantity is ABSOLUTE realised deployed risk,
not a risk difference against an arm-specific baseline, because differences against different baselines
are not comparable across arms.

Realised risk is exact rather than simulated: the only randomness is the calibration record, which
determines the selection, and each candidate's deployed risk R_S(a) is available in closed form and
verified against independent enumeration to 1e-17. So

    realised risk = E over calibration records of R_S(selected policy),

computed exactly, with Monte Carlo only over the calibration draw.

Cost accounting, per calibration instance: the group arm pays S(2 - 1/G) because the raw baseline it
must be compared against needs S identity shots while the orbit block supplies only S/G of them
(A6.1); the group-free arm pays S. Deployment costs S per prediction for either arm, since every
candidate in either menu is defined at the same total S. Oracle risks are reported for interpretation
only and are never used for selection.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import time

import numpy as np

from shotcert.certify import mp_bound, true_delta, wilson
from shotcert.core import Policy, exact_risk
from shotcert.record import common_record, record_losses
from shotcert.tasks import control_task


# A6.3 parallel menus. Both arms get seven candidates at the same total S, drawn from the same two
# families (no shrinkage, and shrinkage toward the declared constant 0 at five strengths). They differ
# in exactly one structural respect: the group arm's base estimator uses the orbit, the group-free
# arm's does not. Giving shrinkage to only one arm would hand it a second variance-reduction device and
# repeat the unfairness class that produced the earlier mismatch.
GAMMAS = (0.1, 0.2, 0.3, 0.4, 0.5)


def group_menu(S, G):
    return ([Policy("a0", "raw", S=S, orbit_size=G),
             Policy("strat", "stratified", S=S, orbit_size=G)]
            + [Policy("gshr%02d" % int(10 * g), "shrink", S=S, gamma=g, orbit_size=G, base="strat")
               for g in GAMMAS])


def free_menu(S, G):
    return ([Policy("a0", "raw", S=S, orbit_size=G)]
            + [Policy("shr%02d" % int(10 * g), "shrink", S=S, gamma=g, orbit_size=G, base="raw")
               for g in GAMMAS]
            + [Policy("shr06", "shrink", S=S, gamma=0.6, orbit_size=G, base="raw")])


def cost_per_instance(arm, S, G):
    return S * (2.0 - 1.0 / G) if arm == "sym" else float(S)


def feasible_designs(arm, B, N, G, S_max=256):
    """(n, S) pairs whose calibration plus deployment cost fits the budget B."""
    out = []
    S = G
    while S <= S_max:
        cpi = cost_per_instance(arm, S, G)
        n = int((B - N * S) // cpi)
        if n >= 20:
            out.append((n, S))
        S *= 2
    return out


def select(losses, names, eps, delta, m):
    """Return (chosen, fired). mp fires only when a simultaneous bound clears eps."""
    best = min(names, key=lambda k: float(np.mean(losses[k])))
    if best != "a0":
        return best, True
    for nm in names:
        if nm == "a0":
            continue
        d = losses[nm] - losses["a0"]
        if mp_bound(d, delta, menu_size=m) <= eps:
            return nm, True
    return "a0", False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shotcert/results/frontier.json")
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--ndeploy", type=int, default=1000)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    t0 = time.time()
    from shotcert.physics import cluster_task, heisenberg_task
    tasks = [("control_help", control_task(regime="help")),
             ("control_interior", control_task(regime="interior")),
             ("control_hurt", control_task(regime="hurt")),
             ("heisenberg_even_n6", heisenberg_task(n=6, a_odd=0.0, c_rect=0.18)),
             ("heisenberg_raw_n6", heisenberg_task(n=6, a_odd=1.0, c_rect=0.18)),
             ("cluster_n7", cluster_task(n=7, a_odd=0.0))]
    res = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "reps": args.reps, "delta": args.delta, "N_deploy": args.ndeploy,
           "budget": "B = calibration preparations + deployment preparations",
           "endpoint": "absolute realised deployed risk (exact per-candidate risk, MC over calibration)",
           "rows": []}
    for (tname, task) in tasks:
        G = len(task.group.actions)
        xs_ev = task.x_dist(600, np.random.default_rng(4040))
        yvar = float(np.var([float(np.asarray(task.label(x)).reshape(-1)[0]) for x in xs_ev]))
        eps = 0.02 * yvar
        for B in (4000, 16000, 64000):
            for arm, menu_fn in (("sym", group_menu), ("free", free_menu)):
                designs = feasible_designs(arm, B, args.ndeploy, G)
                if not designs:
                    continue
                best = None
                for (n, S) in designs:
                    menu = menu_fn(S, G)
                    risk = {p.name: exact_risk(task, p, xs_ev) for p in menu}
                    r0 = risk["a0"]
                    realized, useful, viol, fb = [], [], [], []
                    rng = np.random.default_rng(int(1e5 * eps) + 7 * n + 13 * S)
                    for _ in range(args.reps):
                        xs = task.x_dist(n, rng)
                        rec = common_record(task, xs, S, rng)
                        losses = record_losses(task, menu, rec,
                                               np.array([float(np.asarray(task.label(x)).reshape(-1)[0])
                                                         for x in xs]))
                        pick, fired = select(losses, [p.name for p in menu], eps, args.delta,
                                             len(menu) - 1)
                        realized.append(risk[pick])
                        useful.append(risk[pick] < r0 - 1e-12)
                        viol.append(risk[pick] > r0 + eps)
                        fb.append(pick == "a0")
                    row = {"task": tname, "arm": arm, "B": B, "n": n, "S": S,
                           "cost": int(n * cost_per_instance(arm, S, G) + args.ndeploy * S),
                           "eps": eps, "realised_risk": float(np.mean(realized)),
                           "realised_risk_se": float(np.std(realized) / np.sqrt(args.reps)),
                           "a0_risk": r0, "oracle_risk": float(min(risk.values())),
                           "useful": float(np.mean(useful)),
                           "violation": float(np.mean(viol)),
                           "fallback": float(np.mean(fb)),
                           "risk_table": risk}
                    res["rows"].append(row)
                    if best is None or row["realised_risk"] < best["realised_risk"]:
                        best = row
                if best:
                    print("%-18s %-4s B=%6d best n=%4d S=%3d realised=%.5f (se %.5f) a0=%.5f "
                          "oracle=%.5f useful=%.2f viol=%.3f fb=%.2f"
                          % (tname, arm, B, best["n"], best["S"], best["realised_risk"],
                             best["realised_risk_se"], best["a0_risk"], best["oracle_risk"],
                             best["useful"], best["violation"], best["fallback"]), flush=True)
                with open(args.out, "w") as f:
                    json.dump(res, f, indent=1)
    res["wall_seconds"] = round(time.time() - t0, 1)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote %s in %.1fs" % (args.out, res["wall_seconds"]))


if __name__ == "__main__":
    main()
