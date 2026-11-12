"""A6.5: when can variance-adaptive orbit allocation actually repay, and when can it not?

Neyman allocation over the orbit replaces the shot-variance coefficient mean_g sigma_g^2 with
(mean_g sigma_g)^2, so the recoverable amount is exactly Var_g(sigma_g) -- the dispersion of the orbit's
shot standard deviations. On every task in this study that dispersion came out near zero and Neyman
allocation bought nothing, which would be an uninteresting null unless the reason is identified.

The reason is structural. Write mu_g(x) = f(a_g x). If the group action a_g preserves the input
distribution, then mu_g(X) and mu_0(X) have the same law, so E[sigma_g^2] = 1 - E[mu_g^2] is the same
for every orbit point, and Var_g(sigma) is zero by construction. Measure-preserving orbits therefore
have flat variance profiles, and no allocation across them can recover anything: the symmetrisation cost
is irreducible. This script checks the prediction on the study's tasks and then builds the counterpart
-- the same label, model and group, but an input distribution the action does NOT preserve -- to show
the mechanism is real rather than absent.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from shotcert.core import Group, Policy, Task, exact_risk, orbit_expectations, shot_var_from_mu
from shotcert.core import sign_flip_group
from shotcert.physics import cluster_task, heisenberg_task
from shotcert.reference import reference_risk_x
from shotcert.tasks import control_task
from shotcert.theory import dispersion, neyman_alloc, sigma_profile


def asymmetric_control(c_break=0.35, regime="help"):
    """The control task with phi drawn from [0, 1.2]: phi -> -phi is no longer measure-preserving."""
    a = {"help": 0.0, "hurt": -0.55, "interior": -0.12}[regime]

    def label(x):
        return np.cos(np.asarray(x, dtype=float)[..., 0]) + a * np.sin(np.asarray(x, dtype=float)[..., 0])

    def model(x):
        phi = np.asarray(x, dtype=float)[..., 0]
        return np.cos(phi + c_break * phi ** 2)

    def x_dist(n, rng):
        phi = rng.uniform(0.0, 1.2, size=(n, 2))     # support is NOT symmetric under phi -> -phi
        return phi

    return Task(name="control_asym", dim=2, label=label, model=model, x_dist=x_dist,
                group=sign_flip_group(),
                note="same label, model and group as control_task; input law not action-invariant")


def profile_gap(task, xs):
    """max_g E[sigma_g^2] - min_g E[sigma_g^2]: zero when the action preserves the input law."""
    acc = None
    for x in np.atleast_2d(np.asarray(xs, dtype=float)):
        sv = np.asarray(shot_var_from_mu(np.asarray(orbit_expectations(task, x), dtype=float)),
                        dtype=float)
        acc = sv if acc is None else acc + sv
    e = acc / len(np.atleast_2d(xs))
    return float(e.max() - e.min())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shotcert/results/profile.json")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    t0 = time.time()
    tasks = [("control_help", control_task(regime="help")),
             ("control_interior", control_task(regime="interior")),
             ("heisenberg_even_n6", heisenberg_task(n=6, a_odd=0.0, c_rect=0.18)),
             ("heisenberg_raw_n6", heisenberg_task(n=6, a_odd=1.0, c_rect=0.18)),
             ("cluster_n7", cluster_task(n=7, a_odd=0.0)),
             ("control_asym_help", asymmetric_control(regime="help")),
             ("control_asym_interior", asymmetric_control(regime="interior"))]
    res = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "claim": "recoverable shot variance = Var_g(sigma); zero for measure-preserving orbits",
           "rows": []}
    for (tname, task) in tasks:
        G = len(task.group.actions)
        xs = task.x_dist(400, np.random.default_rng(21))
        sg = sigma_profile(task, xs)
        gap = profile_gap(task, xs)
        for S in (16, 64, 256):
            ney = neyman_alloc(sg, S)
            if ney is None:
                continue
            pu = Policy("uni", "alloc", S=S, orbit_size=G, alloc=tuple([S // G] * G))
            pn = Policy("ney", "alloc", S=S, orbit_size=G, alloc=ney)
            if not (pu.feasible() and pn.feasible()):
                continue
            ru, rn = exact_risk(task, pu, xs), exact_risk(task, pn, xs)
            # independent check that the allocation risk itself is right
            ref = float(np.mean([reference_risk_x(task, x, pn) for x in xs]))
            row = {"task": tname, "S": S, "sigma": [float(v) for v in sg],
                   "var_g_sigma": dispersion(sg), "profile_gap": gap,
                   "alloc": list(ney), "risk_uniform": ru, "risk_neyman": rn,
                   "gain": ru - rn, "enumerated_neyman": ref,
                   "enum_abs_diff": abs(ref - rn)}
            res["rows"].append(row)
            print("%-22s S=%3d sigma=%s Var_g=%.6f gap=%.6f gain=%+.6f alloc=%s"
                  % (tname, S, np.array2string(sg, precision=4), dispersion(sg), gap, ru - rn, ney),
                  flush=True)
            with open(args.out, "w") as f:
                json.dump(res, f, indent=1)
    res["wall_seconds"] = round(time.time() - t0, 1)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote %s in %.1fs" % (args.out, res["wall_seconds"]))


if __name__ == "__main__":
    main()
