"""Is the certification frontier statistics or inequality? Compare two certificates head to head.

The empirical-Bernstein bound is distribution-free but carries a range term that swamps small-n
calibration. The Studentised bound is far tighter but its coverage at a given n is an empirical
claim, so it is only admissible if the measured violation rate stays at or below delta. Running both
turns "certification needs ~400 preparations" into either (a) a real resource statement, if the tight
bound also fails to certify at smaller n, or (b) a property of the inequality we happened to use.
"""
from __future__ import annotations
import argparse, json, os, time
import numpy as np
from shotcert.certify import calibration_losses, certify
from shotcert.core import exact_risk
from shotcert.experiments.exp_control import menu
from shotcert.tasks import control_task

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shotcert/results/bound.json")
    ap.add_argument("--reps", type=int, default=400)
    ap.add_argument("--delta", type=float, default=0.05)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    t0 = time.time()
    res = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "delta": args.delta, "rows": [], "wall_seconds": None}
    for reg in ("help", "hurt", "interior"):
        task = control_task(regime=reg)
        for S in (8, 32, 128):
            xs_eval = task.x_dist(600, np.random.default_rng(4040))
            pol_menu = menu(S)
            base = exact_risk(task, pol_menu[0], xs_eval)
            truth = {p.name: exact_risk(task, p, xs_eval) - base for p in pol_menu[1:]}
            for n in (25, 50, 100, 200, 400):
                for bound in ("eb", "normal"):
                    rng = np.random.default_rng(5150000 + n * 13 + S * 7 + len(bound))
                    viol = better = fb = 0
                    for _ in range(args.reps):
                        xs = task.x_dist(n, rng)
                        cl = calibration_losses(task, pol_menu, xs, rng)
                        dec = certify(cl, pol_menu, "a0", eps=0.0, delta=args.delta, bound=bound)
                        if dec.status == "fallback":
                            fb += 1; continue
                        if truth.get(dec.chosen, 0.0) > 1e-12: viol += 1
                        else: better += 1
                    res["rows"].append({"regime": reg, "S": S, "n": n, "bound": bound,
                                        "violation_rate": viol/args.reps,
                                        "power": better/args.reps,
                                        "fallback_rate": fb/args.reps,
                                        "best_true_delta": min(truth.values())})
                    r = res["rows"][-1]
                    print("%-9s S=%3d n=%3d %-6s viol=%.3f power=%.3f fb=%.3f"
                          % (reg, S, n, bound, r["violation_rate"], r["power"], r["fallback_rate"]),
                          flush=True)
    res["wall_seconds"] = round(time.time() - t0, 1)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote %s in %.1fs" % (args.out, res["wall_seconds"]))

if __name__ == "__main__":
    main()
