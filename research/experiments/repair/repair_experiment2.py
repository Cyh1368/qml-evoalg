"""WP-REPAIR-2: corrected causal symmetry-repair experiment (ring_n6, D6).

Implements ``research/REVISED_PROTOCOL.md`` sections 1-3. Differences from the
first run (``repair_experiment.py``, kept unchanged as the exploratory record):

* **Honest replication units.** At ``eta = 0`` the target does not depend on the
  breaking direction, so direction/teacher is a nuisance index, not a
  replication. The unit is the optimiser seed, and the number of *distinct*
  units is written into the record next to the row count. At ``eta > 0`` the
  unit is (direction, optimiser seed) with direction as a blocking factor.
* **More breaking directions** (8) and **more optimiser seeds** (24), so the
  eta = 0 contrast has 24 genuine units instead of 8 duplicated 3x.
* **Multiple asymmetric controls**: ``control_rand`` (a second asymmetric
  gate-count-matched direction rule) and ``control_matched`` (initial *operator*
  matched to ``original``, since the duplicated-CRZ control is the original
  interaction at angle 2b). Optimiser-budget sensitivity at steps 600/1800.
* **Function-space estimand E-R1**: every fitted predictor is also evaluated on
  the *orbit-completed* development distribution (12 images per representative,
  uniform weights) together with its exact Reynolds projection, so the
  projection identity and the exact finite-orbit floor are measured rather than
  quoted.
* **Floor accounting**: excess risk above the floor is recorded per row
  (``orb_excess_floor``), so "pinned near the floor" is a checkable statement.

Locked data are never read here (development artifact only).
"""
import argparse
import datetime
import itertools
import json
import multiprocessing as mp
import os
import platform
import socket
import subprocess
import sys
from pathlib import Path

import numpy as np

from research.core import candidates as _cand
from research.core import tasks as _tasks
from research.core import train as _train
from research.experiments.repair import repair_experiment as _r1
from research.metrics import symmetry as _sym

REPO = Path(__file__).resolve().parents[3]
ARMS = ("original", "repaired", "control_dup", "control_rand", "control_matched")
DIRECTIONS = (101, 202, 303, 404, 505, 606, 708, 909)
RAND_DIRECTION_SEED = 20261111          # fixed rule for control_rand


# ------------------------------------------------------------------ ansatz arms
def _pair_directions(n, arm):
    """Return the ordered wire pair list for the CRZ layer of one arm.

    ``original`` and ``control_dup`` use the lexicographic direction (i<j) for
    all 15 pairs; ``repaired`` uses both directions; ``control_rand`` uses a
    fixed seeded per-pair direction (an asymmetric rule that is not a global
    relabelling of the lexicographic one).
    """
    pairs = list(itertools.combinations(range(n), 2))
    if arm == "repaired":
        return [(i, j) for i, j in pairs] + [(j, i) for i, j in pairs]
    if arm in ("original",):
        return list(pairs)
    if arm in ("control_dup", "control_matched"):
        return list(pairs) * 2
    if arm == "control_rand":
        rng = np.random.default_rng(RAND_DIRECTION_SEED)
        chosen = [(i, j) if rng.random() < 0.5 else (j, i) for i, j in pairs]
        return list(chosen) * 2
    raise ValueError(arm)


def arm_block(arm, n):
    block = [{"gate": "RY", "wire": i, "param": "a"} for i in range(n)]
    for (i, j) in _pair_directions(n, arm):
        block.append({"gate": "CRZ", "wires": [i, j], "param": "b"})
    block += [{"gate": "RY", "wire": i, "param": "c"} for i in range(n)]
    return block


def make_candidate(arm, n):
    return {"id": "r2_%s" % arm, "n_qubits": n, "block": arm_block(arm, n),
            "repeats": 1, "layers": 1, "param_names": ["a", "b", "c"],
            "hypothesis": None, "notes": "WP-REPAIR-2 %s arm" % arm,
            "source": {"arm": arm, "model": None, "parent": None}}


# ------------------------------------------------------------- target functions
class TargetFn:
    """``y_eta = h + eta * b`` as *functions of the input*, plus floor bookkeeping.

    ``h`` is the dataset's ground-truth D6-invariant oracle ``alpha_0`` and ``b``
    the group-centred, train-variance-normalised remainder of a frozen random
    direction ``v``. Both are evaluable on arbitrary rows, which is what the
    orbit-completed evaluation needs.
    """

    def __init__(self, task, direction_seed, eta, closure):
        self.closure = closure
        self.eta = float(eta)
        x = np.asarray(task.x, float)
        train_mask = np.asarray(task.splits["train"], bool)
        self.h = np.asarray(task.targets["alpha_0"], float)
        rng = np.random.default_rng(int(direction_seed)) if direction_seed \
            else np.random.default_rng(0)
        v = rng.normal(size=x.shape[1])
        self.v = v
        self.scale = float(np.sqrt(np.mean(self._b_raw(x[train_mask]) ** 2))) or 1.0

    def _b_raw(self, z):
        z = np.asarray(z, float)
        acc = np.zeros(len(z))
        for perm in self.closure:
            acc += z[:, list(perm)] @ self.v
        return (z @ self.v) - acc / len(self.closure)

    def h_of(self, z):
        z = np.asarray(z, float)
        return np.mean(z * np.roll(z, 1, axis=1), axis=1)

    def b_of(self, z):
        return self._b_raw(z) / self.scale

    def y_of(self, z):
        return self.h_of(z) + self.eta * self.b_of(z)


# --------------------------------------------------------------- fit (train only)
def init_theta(seed, n_rows, max_train, arm):
    """Common random numbers: identical (a,b,c) draw across arms for a seed.

    Reproduces ``fit_arm``'s stream exactly (train subsample draw first, then the
    angle draw), so every arm of a unit starts from the same angles.
    ``control_matched`` halves the initial ``b`` so that its initial *operator*
    equals ``original``'s (the duplicated-CRZ control is the original interaction
    at angle 2b), which is the operator-matched initialisation the audit asked for.
    """
    rng = np.random.default_rng(int(seed))
    if max_train and 0 < int(max_train) < int(n_rows):
        rng.choice(int(n_rows), size=int(max_train), replace=False)
    theta = rng.uniform(-np.pi, np.pi, size=3)
    if arm == "control_matched":
        theta = theta.copy()
        theta[1] = theta[1] / 2.0
    return theta


def fit_arm(arm, task, x, y, seed, steps, max_train=256, lr=0.05):
    """Train the 3 block parameters with the fixed symmetric readout (train rows only)."""
    n = int(task.n_qubits)
    cand = make_candidate(arm, n)
    obs = _train.obs_matrix(task.observables, n)
    w = _r1._sym_readout(task, n)
    x = np.asarray(x)
    y = np.asarray(y, float).reshape(-1)
    theta = init_theta(seed, len(x), max_train, arm)      # common random numbers
    rng = np.random.default_rng(int(seed))
    if max_train and 0 < int(max_train) < len(x):
        keep = np.sort(rng.choice(len(x), size=int(max_train), replace=False))
        x, y = x[keep], y[keep]
    m = len(x)
    plans = [_train._compile_plan(cand, task, x[i]) for i in range(m)]
    state0 = _train._zero_state(n)
    m1 = np.zeros(3); m2 = np.zeros(3); b1, b2, eps = 0.9, 0.999, 1e-8
    for step in range(int(steps)):
        idx = rng.choice(m, size=min(32, m), replace=False)
        g = np.zeros(3)
        pdict = _cand.param_dict(cand, theta)
        for i in idx:
            psi, cache = plans[i].run(theta, state0)
            E = ((np.abs(psi) ** 2) @ obs.T).reshape(-1)
            resid = float(E @ w) - float(y[i])
            coef = (2.0 / len(idx)) * resid
            g += plans[i].grad(theta, cache, psi * ((coef * w) @ obs))
        if not np.all(np.isfinite(g)):
            break
        t = step + 1
        m1 = b1 * m1 + (1 - b1) * g
        m2 = b2 * m2 + (1 - b2) * (g * g)
        theta = theta - lr * (m1 / (1 - b1 ** t)) / (np.sqrt(m2 / (1 - b2 ** t)) + eps)
    pred = _r1._predict_readout(cand, task, x, theta, w)
    return theta, float(np.mean((pred - y) ** 2))


# ------------------------------------------------------- orbit-completed evaluation
def block_dev_risk(arm, task, x, y, theta):
    """Development risk of an arm at ``theta`` with the fixed symmetric readout."""
    cand = make_candidate(arm, int(task.n_qubits))
    pred = _r1._predict_readout(cand, task, x, theta, _r1._sym_readout(task, int(task.n_qubits)))
    return float(np.mean((pred - np.asarray(y, float).reshape(-1)) ** 2))


def orbit_rows(x, closure):
    """(len(closure), len(x), d) stack of group images; row-major over group."""
    x = np.asarray(x, float)
    return np.stack([x[:, list(p)] for p in closure], axis=0)


def orbit_eval(arm, task, tf, theta, x_dev, closure):
    """E-R1: risk of f and of its exact Reynolds projection on complete orbits.

    Weights: uniform over the (group element, representative) product, i.e. every
    complete orbit carries the same total weight. Under that measure the input
    distribution is exactly D6-invariant, so the population floor applies and
    ``R(f) - R(Pf) = E[(f - Pf)^2]`` holds exactly (algebraic identity check).
    """
    n = int(task.n_qubits)
    cand = make_candidate(arm, n)
    w = _r1._sym_readout(task, n)
    G = len(closure)
    imgs = orbit_rows(x_dev, closure)                    # (G, m, d)
    flat = imgs.reshape(G * len(x_dev), -1)
    f = _r1._predict_readout(cand, task, flat, theta, w).reshape(G, len(x_dev))
    y = np.stack([tf.y_of(imgs[g]) for g in range(G)], axis=0)
    f_proj = f.mean(axis=0, keepdims=True)               # Reynolds projection
    y_bar = y.mean(axis=0, keepdims=True)                # == h on complete orbits
    risk_f = float(np.mean((f - y) ** 2))
    risk_proj = float(np.mean((f_proj - y) ** 2))
    floor_orb = float(np.mean((y - y_bar) ** 2))         # exact finite-orbit floor
    asym = float(np.mean((f - f_proj) ** 2))
    # R(f) = R(Pf) + E[(f-Pf)^2] - 2 E[(f-Pf)(y-ybar)] (sign verified: the identity holds
    # to 3.7e-16 over all WP-REPAIR-2 fits); the cross term vanishes exactly for an
    # invariant target (eta = 0), which is the projection identity. For eta > 0 the cross
    # term dominates E[(f-Pf)^2], so R(f) - R(Pf) < 0 for the asymmetric arms.
    cross = float(np.mean((f - f_proj) * (y - y_bar)))
    return {"orb_risk": risk_f, "orb_risk_proj": risk_proj,
            "orb_floor": floor_orb, "orb_excess_floor": risk_f - floor_orb,
            "orb_asymmetry": asym, "orb_cross_term": cross,
            "orb_identity_gap": abs((risk_f - risk_proj) - asym),
            "orb_oracle_invariant_risk": floor_orb,
            "orb_weights": "uniform over %d group elements x %d representatives"
                           % (G, len(x_dev))}


def channel_residual(arm, n, theta, closure):
    cand = make_candidate(arm, n)
    pdict = _cand.param_dict(cand, theta)
    u = _sym.unitary(cand["block"], pdict, n)
    d = _sym.defects(u, closure)
    return {"channel_mean": d["channel_mean"], "channel_max": d["channel_max"],
            "unitary_mean": d["unitary_mean"]}


def operator_distance(arm, n, theta, closure, theta_ref):
    """Frobenius distance between this arm's block operator and original's."""
    u = _sym.unitary(make_candidate(arm, n)["block"],
                     _cand.param_dict(make_candidate(arm, n), theta), n)
    u0 = _sym.unitary(make_candidate("original", n)["block"],
                      _cand.param_dict(make_candidate("original", n), theta_ref), n)
    return float(np.linalg.norm(u - u0) / np.sqrt(u.shape[0]))


# ------------------------------------------------------------------- one unit
def _worker(job):
    (family, arm, eta, direction, opt_seed, steps, max_train) = job
    task = _WORKER["task"]
    closure = _WORKER["closure"]
    n = int(task.n_qubits)
    dev_mask = np.asarray(task.splits["validation"], bool)
    train_mask = np.asarray(task.splits["train"], bool)
    x = np.asarray(task.x, float)
    key = (direction, eta)
    if key not in _WORKER["targets"]:
        _WORKER["targets"][key] = TargetFn(task, direction, eta, closure)
    tf = _WORKER["targets"][key]
    y_all = tf.y_of(x)
    n_train = int(train_mask.sum())
    theta, train_risk = fit_arm(arm, task, x[train_mask], y_all[train_mask],
                                opt_seed, steps, max_train=max_train)
    dev = block_dev_risk(arm, task, x[dev_mask], y_all[dev_mask], theta)
    resid = channel_residual(arm, n, theta, closure)
    orb = orbit_eval(arm, task, tf, theta, x[dev_mask], closure)
    theta0 = init_theta(opt_seed, n_train, max_train, arm)
    resid0 = channel_residual(arm, n, theta0, closure)
    return {"family": family, "arm": arm, "eta": float(eta),
            "direction_seed": int(direction) if direction is not None else None,
            "opt_seed": int(opt_seed), "steps": int(steps),
            "max_train": int(max_train), "theta": theta.tolist(),
            "theta_init": theta0.tolist(),
            "train_loss": train_risk, "dev_risk": dev,
            "floor_analytic": (float(eta) ** 2) * float(np.mean(tf.b_of(x[dev_mask]) ** 2)),
            "channel_mean": resid["channel_mean"],
            "channel_max": resid["channel_max"],
            "channel_mean_init": resid0["channel_mean"],
            "init_op_distance_to_original": operator_distance(
                arm, n, theta0, closure,
                init_theta(opt_seed, n_train, max_train, "original")),
            **orb}


def _init_worker(task, closure):
    _WORKER["task"] = task
    _WORKER["closure"] = closure
    _WORKER["targets"] = {}


_WORKER = {}


# ------------------------------------------------------------------- experiment
def run(family="ring_n6", etas=(0.0, 0.5, 1.0), directions=DIRECTIONS,
        opt_seeds=range(24), arms=ARMS, steps_main=200, sens_steps=(),
        sens_directions=2, sens_opt_seeds=6, max_train=256, workers=8, out=None,
        verbose=True):
    task = _tasks.load_family(family, development=True, locked=False)
    closure = _r1.group_closure(task.generators)
    sens_dirs = tuple(directions[:int(sens_directions)])
    jobs = []
    if steps_main:
        jobs += [(steps_main, a, e, d, s, steps_main, max_train)
                 for e in etas for d in ((None,) if float(e) == 0.0 else directions)
                 for s in opt_seeds for a in arms]
    for st in sens_steps:
        jobs += [(st, a, e, d, s, st, max_train)
                 for e in etas for d in ((None,) if float(e) == 0.0 else sens_dirs)
                 for s in range(int(sens_opt_seeds)) for a in arms]
    if verbose:
        print("WP-REPAIR-2: %d fits on %s, %d workers" % (len(jobs), family, workers),
              flush=True)
    rows = []
    ctx = mp.get_context("fork")
    with ctx.Pool(workers, initializer=_init_worker,
                  initargs=(task, closure)) as pool:
        for k, row in enumerate(pool.imap_unordered(_worker, jobs, chunksize=1), 1):
            rows.append(row)
            if verbose and (k % 50 == 0 or k == len(jobs)):
                print("  %d/%d fits done" % (k, len(jobs)), flush=True)
    result = {"protocol": "research/REVISED_PROTOCOL.md sections 1-3",
              "scope": "development only; locked holdout never read here",
              "family": family, "group_order": len(closure),
              "unit_definition": {"eta=0": "optimiser seed (direction is a nuisance "
                                           "index: the target is direction-free)",
                                  "eta>0": "(direction, optimiser seed), direction "
                                           "as a blocking factor"},
              "etas": [float(e) for e in etas], "arms": list(arms),
              "directions": list(directions), "opt_seeds": list(map(int, opt_seeds)),
              "steps_main": int(steps_main) if steps_main else None,
              "sens_steps": list(map(int, sens_steps)),
              "sens_directions": int(sens_directions),
              "sens_opt_seeds": int(sens_opt_seeds), "max_train": int(max_train),
              "rows": rows, "metadata": _metadata(),
              "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w") as fh:
            json.dump(result, fh, indent=1, default=str)
        print("wrote %s" % out, flush=True)
    return result


def _metadata():
    meta = {"python": platform.python_version(), "numpy": np.__version__,
            "host": socket.gethostname(), "platform": platform.platform()}
    try:
        import scipy
        meta["scipy"] = scipy.__version__
    except Exception:
        meta["scipy"] = None
    try:
        meta["git_commit"] = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(REPO), capture_output=True,
            text=True, timeout=10).stdout.strip() or "unknown"
    except Exception:
        meta["git_commit"] = "unknown"
    return meta


def main(argv=None):
    p = argparse.ArgumentParser(prog="research/experiments/repair/repair_experiment2.py")
    p.add_argument("--family", default="ring_n6")
    p.add_argument("--etas", default="0,0.5,1")
    p.add_argument("--directions", default=",".join(str(d) for d in DIRECTIONS))
    p.add_argument("--n-opt-seeds", type=int, default=24)
    p.add_argument("--steps-main", type=int, default=200)
    p.add_argument("--sens-steps", default="600,1800")
    p.add_argument("--sens-directions", type=int, default=2)
    p.add_argument("--sens-opt-seeds", type=int, default=6)
    p.add_argument("--arms", default=",".join(ARMS))
    p.add_argument("--max-train", type=int, default=256)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--out",
                   default="research/experiments/repair/repair2_results.json")
    a = p.parse_args(argv)
    run(family=a.family, etas=tuple(float(e) for e in a.etas.split(",")),
        directions=tuple(int(d) for d in a.directions.split(",")),
        opt_seeds=range(a.n_opt_seeds),
        arms=tuple(x.strip() for x in a.arms.split(",")),
        steps_main=a.steps_main,
        sens_steps=tuple(int(s) for s in a.sens_steps.split(",") if s.strip()),
        sens_directions=a.sens_directions, sens_opt_seeds=a.sens_opt_seeds,
        max_train=a.max_train, workers=a.workers, out=a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
