"""A3.3-A3.5: matched-resource comparison with shared measurement records, on both mechanisms.

What the second review required, in one experiment.

Sharing (A3.3). Every deterministic policy of a finite-shot record costs nothing extra to evaluate.
Shrinkage is a rescaling of the raw estimate, so eight shrinkage levels need one raw batch, not eight;
the first version resampled per level and charged all eight. Here one calibration record is
`s shots per distinct circuit per instance`, and every policy in the arm is computed from that record.
The arms therefore differ only in how many distinct circuits their candidate set needs: the group-free
arm needs one (the identity orbit point), the symmetry arm needs |G|. That is the group's honest
measurement price, and it is a factor of |G|, not a factor of the menu size.

Two questions, reported separately (A3.4).
  (a) what the group buys: same selector, different candidate sets, matched resources;
  (b) what certification buys: same candidate set (the symmetry menu), generic plug-in selection
      (argmin of the paired mean loss, no certificate) against the certified rule.
The expectation is stated before running: the certificate here IS generic paired certification, so (b)
should show no symmetry-specific method advantage, and anything in (a) is an advantage of the candidate
set at a factor-|G| measurement price.

Selectors. `mp` is the Maurer-Pontil rule, the only one with a finite-sample guarantee, and it is
reported with its cost. `student` is descriptive and never called a certificate. `plugin` is the
generic plug-in selector: it selects whenever some candidate has a negative paired mean loss.

A2.7 stop gate. Run on the control AND on both physical mechanisms. If the symmetry arm does not beat
the strongest applicable equal-access group-free arm on both physical mechanisms at matched total
resources, the scoped negative is the finding.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from shotcert.certify import mp_bound, normal_bound, true_delta, wilson
from shotcert.core import Policy, born_prob, label_vector, orbit_expectations
from shotcert.tasks import control_task

N_DEPLOY = 1000


def sym_menu(S, G):
    """Exactly the policies whose DEPLOYED semantics match a shared s-shot record.

    A record is s shots per orbit point, so the only group policies that mean the same thing when
    scored by their deployed risk are the raw baseline and full equal-shot averaging at s shots per
    point (S = s*G). orbit_k and the mixtures allocate shots per draw rather than per orbit point, so
    evaluating them from a shared record would silently give them more shots than they pay for, and
    scoring them with their deployed risk would then compare an estimator against a different
    estimand. They are studied in the deployed-cost experiment instead. This restriction is what makes
    the arms exactly matched: the group arm's whole extra cost is (G-1)*s shots per instance.
    """
    out = [Policy("a0", "raw", S=S, orbit_size=G),
           Policy("strat", "stratified", S=S, orbit_size=G)]
    return [p for p in out if p.feasible()]


def generic_menu(S, G):
    out = [Policy("a0", "raw", S=S, orbit_size=G)]
    for g in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
        out.append(Policy("shrink%d" % int(g * 100), "shrink", S=S, gamma=g, orbit_size=G))
    return [p for p in out if p.feasible()]


def shared_record(task, xs, s, rng):
    """One record per instance: s destructive shots at each distinct circuit the arm needs.

    Returns (n, G) array of +-1-valued shot means. Preparations equal shots: every entry is s fresh
    state copies, which is the access model's own convention.
    """
    P = born_prob(np.stack([np.asarray(task.model(a(xs)), dtype=float).reshape(-1)
                            for a in task.group.actions], axis=1))
    return 2.0 * (rng.binomial(s, P) / float(s)) - 1.0


def losses_from_record(task, menu, record, y):
    """Every policy evaluated from the same record; zero additional shots."""
    out = {}
    G = record.shape[1]
    for pol in menu:
        if pol.mode == "raw":
            z = record[:, 0]
        elif pol.mode == "shrink":
            z = (1.0 - pol.gamma) * record[:, 0]
        elif pol.mode == "stratified":
            z = record[:, :G].mean(axis=1)
        else:
            raise AssertionError("policy %s is not shared-record compatible" % pol.name)
        out[pol.name] = (z - y) ** 2
    return out


def select(losses, names, a0, eps, delta, rule):
    """Return the chosen policy name, or None to fall back."""
    base = losses[a0]
    cand = [k for k in names if k != a0]
    m = max(len(cand), 1)
    if rule == "plugin":
        d = {k: float(np.mean(losses[k]) - np.mean(base)) for k in cand}
        best = min(d, key=lambda k: d[k])
        return best if d[best] < 0.0 else None
    if rule == "mp":
        ub = {k: mp_bound(losses[k] - base, delta, menu_size=m) for k in cand}
    else:
        ub = {k: normal_bound(losses[k] - base, delta / m) for k in cand}
    ok = {k: v for k, v in ub.items() if v <= eps}
    if not ok:
        return None
    return min(sorted(ok), key=lambda k: ok[k])


def run_arm(task, menu, n, s, eps, delta, reps, seed, rules=("mp", "student", "plugin")):
    G = len(task.group.actions)
    n_circ = len(set().union(*[set(p.circuit_ids) for p in menu]))
    shots_calib = n * n_circ * s
    ledger = {"instances": n, "circuits": n_circ, "shots_per_circuit": s,
              "calib_shots": shots_calib, "calib_preparations": shots_calib,
              "calib_compilations": n_circ,
              "calib_switches": n * max(n_circ - 1, 0),
              "deploy_shots": N_DEPLOY * n_circ * s,
              "deploy_preparations": N_DEPLOY * n_circ * s,
              "total_shots": shots_calib + N_DEPLOY * n_circ * s,
              "total_preparations": shots_calib + N_DEPLOY * n_circ * s}
    xs_eval = task.x_dist(400, np.random.default_rng(4040))
    truth = true_delta(task, menu, xs_eval, "a0")
    rng = np.random.default_rng(seed)
    acc = {r: {"sel": 0, "pow": 0, "viol": 0, "deltas": []} for r in rules}
    for _ in range(reps):
        xs = task.x_dist(n, rng)
        y = label_vector(task, xs)
        rec = shared_record(task, xs, s, rng)
        losses = losses_from_record(task, menu, rec, y)
        for r in rules:
            pick = select(losses, [p.name for p in menu], "a0", eps, delta, r)
            a = acc[r]
            if pick is None:
                continue
            a["sel"] += 1
            d = truth.get(pick, 0.0)
            a["deltas"].append(d)
            if d > eps:
                a["viol"] += 1
            if d <= eps:
                a["pow"] += 1
    out = {}
    for r in rules:
        a = acc[r]
        lo, hi = wilson(a["pow"], reps)
        vlo, vhi = wilson(a["viol"], reps)
        out[r] = {"selection_rate": a["sel"] / reps, "power": a["pow"] / reps,
                  "power_ci": [lo, hi], "violation_rate": a["viol"] / reps,
                  "violation_ci": [vlo, vhi],
                  "mean_chosen_true_delta": float(np.mean(a["deltas"])) if a["deltas"] else None,
                  "worst_chosen_true_delta": float(max(a["deltas"])) if a["deltas"] else None}
    return {"ledger": ledger, "truth": truth, "best_true_delta": float(min(truth.values())),
            "selectors": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shotcert/results/matched.json")
    ap.add_argument("--reps", type=int, default=150)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--tasks", default="control,heisenberg,cluster")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    t0 = time.time()
    res = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "reps": args.reps, "delta": args.delta, "n_deploy": N_DEPLOY,
           "sharing": "one record per instance per distinct circuit; all deterministic policies "
                      "evaluated from it at zero additional shot cost",
           "rows": []}

    from shotcert.physics import cluster_task, heisenberg_task

    def build(name):
        if name == "control":
            return [("control_%s" % r, control_task(regime=r), 0.0) for r in
                    ("help", "hurt", "interior")]
        if name == "heisenberg":
            probe = heisenberg_task(n=6, a_odd=0.0, c_rect=0.18)
            vy = float(np.var(label_vector(probe, probe.x_dist(2000, np.random.default_rng(90210)))))
            eps = 0.02 * vy
            return [("heisenberg_even_n6", heisenberg_task(n=6, a_odd=0.0, c_rect=0.18), eps),
                    ("heisenberg_raw_n6", heisenberg_task(n=6, a_odd=1.0, c_rect=0.18), eps)]
        probe = cluster_task(n=7, a_odd=0.0)
        vy = float(np.var(label_vector(probe, probe.x_dist(2000, np.random.default_rng(90210)))))
        eps = 0.02 * vy
        return [("cluster_even_n7", cluster_task(n=7, a_odd=0.0), eps),
                ("cluster_raw_n7", cluster_task(n=7, a_odd=1.0), eps)]

    grid = [(n, s) for s in (8, 16, 32, 64) for n in (100, 200, 400, 800, 1600)]
    for fam in [x.strip() for x in args.tasks.split(",")]:
        for (tname, task, eps) in build(fam):
            G = len(task.group.actions)
            for arm, menu_fn in (("sym", sym_menu), ("generic", generic_menu)):
                for (n, s) in grid:
                    # the group arm deploys s shots at each of G circuits; the group-free arm deploys
                    # s shots at one, so each arm's S is its own total and both cost s per circuit
                    S = s * G if arm == "sym" else s
                    menu = menu_fn(S, G)
                    r = run_arm(task, menu, n, s, eps, args.delta, args.reps,
                                991000 + 37 * n + 11 * s + 7 * len(arm) + 101 * len(tname))
                    r.update({"task": tname, "arm": arm, "n": n, "s": s, "eps": eps,
                              "policies": len(menu)})
                    res["rows"].append(r)
                    st = r["selectors"]["plugin"]
                    print("%-20s %-8s n=%4d s=%2d tot=%7d best_true=%+.5f plugin pow=%.2f "
                          "mp pow=%.2f student pow=%.2f (eps=%+.5f)"
                          % (tname, arm, n, s, r["ledger"]["total_shots"], r["best_true_delta"],
                             st["power"], r["selectors"]["mp"]["power"],
                             r["selectors"]["student"]["power"], eps), flush=True)
                    with open(args.out, "w") as f:
                        json.dump(res, f, indent=1)
    res["wall_seconds"] = round(time.time() - t0, 1)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote %s in %.1fs" % (args.out, res["wall_seconds"]))


if __name__ == "__main__":
    main()
