"""A2.3: does a switching cost produce an interior optimum in k, once circuits are counted honestly?

The first version charged `min(k, 4|G|)` distinct circuits, which for the two-element control group
reached eight. With eight circuits to pay for, k=2 looked optimal at large c. But a two-element group
can compile at most TWO circuits, so a per-circuit price is flat for every k >= 2 and cannot create an
interior optimum; the reported one was an artefact.

What can create one is the cost of *changing* circuit settings inside a single prediction's shot
sequence. Two schedules are priced:
  grouped    : all shots for one circuit, then the next -> switches = distinct touched - 1
  interleaved: one shot per drawn circuit in draw order  -> switches = k - 1 in the worst case
The grouped count is the minimum over schedules, so it is the most favourable to the policy; if the
optimum is at the boundary even under interleaved pricing, the interior-optimum claim is dead.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from shotcert.core import Policy, exact_risk
from shotcert.tasks import control_task


def optimum(task, xs, S, c, schedule, cost_unit, cost_scale=64.0):
    """argmin over feasible k of R_S(orbit_k) + c * (switches or circuits) / cost_unit."""
    G = len(task.group.actions)
    rows = {}
    for k in range(1, min(S, 64) + 1):
        p = Policy("k%d" % k, "orbit_k", k=k, S=S, orbit_size=G)
        if not p.feasible():
            continue
        sw = p.max_switches if schedule == "grouped" else max(k - 1, 0)
        charge = sw if cost_unit == "switch" else p.circuits
        R = exact_risk(task, p, xs)
        rows[k] = {"R": R, "circuits": p.circuits, "switches": sw,
                   "objective": R + c * charge / float(cost_scale)}
    if not rows:
        return None
    best = min(rows, key=lambda k: (rows[k]["objective"], k))   # ties to smaller k
    return {"k_star": best, "objective": rows[best]["objective"],
            "k_star_risk_only": min(rows, key=lambda k: rows[k]["R"]),
            "interior": 1 < best < max(rows),
            "max_circuits": max(r["circuits"] for r in rows.values()),
            "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shotcert/results/switch.json")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    t0 = time.time()
    res = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "note": "circuits bounded by |G|; per-circuit charge is flat for k>=2 by construction",
           "cost_scale": 64.0, "runs": {}}
    cost_scale = 64.0
    for reg in ("help", "hurt", "interior"):
        task = control_task(regime=reg)
        xs = task.x_dist(400, np.random.default_rng(2024))
        for S in (32, 64):
            for schedule in ("grouped", "interleaved"):
                for cost_unit in ("switch", "circuit"):
                    for c in (0.0, 0.25, 0.5, 1.0, 2.0, 4.0):
                        o = optimum(task, xs, S, c, schedule, cost_unit, cost_scale)
                        if o is None:
                            continue
                        key = "%s_S%d_%s_%s" % (reg, S, schedule, cost_unit)
                        res["runs"].setdefault(key, {})[str(c)] = {
                            "k_star": o["k_star"], "interior": o["interior"],
                            "objective": o["objective"], "R": o["rows"][o["k_star"]]["R"],
                            "max_circuits": o["max_circuits"],
                            "k_star_risk_only": o["k_star_risk_only"]}
                        if c in (0.0, 1.0, 4.0):
                            print("%-32s c=%.2f k*=%2d interior=%s max_circuits=%d"
                                  % (key, c, o["k_star"], o["interior"], o["max_circuits"]),
                                  flush=True)
    res["wall_seconds"] = round(time.time() - t0, 1)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote %s in %.1fs" % (args.out, res["wall_seconds"]))


if __name__ == "__main__":
    main()
