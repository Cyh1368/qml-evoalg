"""A4.4: measured firing surface for the distribution-free rule.

"The valid rule almost never fires" was generalised from one sweep. This measures where it does and does
not fire, over (n, |Delta|, m), so the claim can be stated with its tested region attached and compared
against the closed-form sufficient radius.

|Delta| is varied by the control task's symmetry-breaking parameter, which moves the best available true
gap; the realised gap is recorded per cell rather than assumed. m is varied by truncating the candidate
menu, which is exactly the multiplicity the simultaneous logarithm pays for.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from shotcert.certify import calibration_losses_fast, mp_bound, n_required_mp, true_delta
from shotcert.core import Policy
from shotcert.tasks import control_task


def menu_of_size(S, G, m):
    """a0 plus m candidates, mixing group and group-free actions so m is the only thing that moves."""
    pool = [Policy("strat", "stratified", S=S, orbit_size=G),
            Policy("shrink20", "shrink", S=S, gamma=0.2, orbit_size=G),
            Policy("mix50", "mix", S=S, w=0.5, orbit_size=G),
            Policy("shrink10", "shrink", S=S, gamma=0.1, orbit_size=G),
            Policy("orbit4", "orbit_k", k=4, S=S, orbit_size=G),
            Policy("shrink30", "shrink", S=S, gamma=0.3, orbit_size=G),
            Policy("mix25", "mix", S=S, w=0.25, orbit_size=G),
            Policy("shrink05", "shrink", S=S, gamma=0.05, orbit_size=G)]
    cand = [p for p in pool if p.feasible()][:m]
    return [Policy("a0", "raw", S=S, orbit_size=G)] + cand


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shotcert/results/surface.json")
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--delta", type=float, default=0.05)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    t0 = time.time()
    res = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "reps": args.reps, "delta": args.delta,
           "note": "firing = the simultaneous MP rule selects at all; eps = 0", "rows": []}
    for c_break in (0.0, 0.2, 0.35, 0.5, 0.7):
        task = control_task(c_break=c_break, regime="help")
        xs_eval = task.x_dist(400, np.random.default_rng(4040))
        G = len(task.group.actions)
        for m in (1, 3, 6):
            for S in (16, 64):
                menu = menu_of_size(S, G, m)
                truth = true_delta(task, menu, xs_eval, "a0")
                gap = abs(min(truth.values()))
                for n in (100, 400, 1600, 6400):
                    rng = np.random.default_rng(60000 + 7 * n + 11 * S + 3 * m + int(97 * c_break))
                    fires = 0
                    for _ in range(args.reps):
                        xs = task.x_dist(n, rng)
                        losses = calibration_losses_fast(task, menu, xs, rng)
                        base = losses["a0"]
                        ub = {p.name: mp_bound(losses[p.name] - base, args.delta, menu_size=m)
                              for p in menu if p.name != "a0"}
                        if any(v <= 0.0 for v in ub.values()):
                            fires += 1
                    rate = fires / args.reps
                    res["rows"].append({"c_break": c_break, "gap": float(gap), "m": m, "S": S,
                                        "n": n, "firing_rate": rate,
                                        "n_required_mp": n_required_mp(gap, m + 1, args.delta)})
                    print("gap=%.5f m=%d S=%2d n=%5d firing=%.2f  (sufficient n=%s)"
                          % (gap, m, S, n, rate, n_required_mp(gap, m + 1, args.delta)), flush=True)
                    with open(args.out, "w") as f:
                        json.dump(res, f, indent=1)
    res["wall_seconds"] = round(time.time() - t0, 1)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote %s in %.1fs" % (args.out, res["wall_seconds"]))


if __name__ == "__main__":
    main()
