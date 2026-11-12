"""Optimizer benchmark on the cemoid L=3, P=2 robustness task.

Runs the SAME validation-loss early-stopping protocol as ``sweep.train_model``
(default settings: lr 0.03, patience 75, min_delta 1e-4, max 1000 epochs,
restore-best-weights, data seed 2027, balanced 450/300/600 split) but with a
selectable optimizer, across N_SEEDS independent initialisation seeds.

Included optimizers (all verified to work with our cost — see optimizer_probe.py):
  gradient-based: GradientDescent, Momentum, Nesterov, Adagrad, RMSProp, Adam
  gradient-free : SPSA

NOT included — QML-specific optimizers are infeasible for this objective:
  QNG / MomentumQNG / QNSPSA require the objective to be a single QNode and use
  the state's metric tensor; our cost is a classical MSE over 9 PauliZ
  expectations with data re-uploading (input-dependent metric) and parameters
  shared across many gates.  Rotosolve needs each parameter's frequency spectrum,
  which the shared-parameter structure does not provide.  Rotoselect reselects
  gate types (not applicable to a fixed ansatz) and ShotAdaptive needs shots!=None
  (we use exact statevector).  optimizer_probe.py demonstrates each failure.

Usage:
  python optimizer_benchmark.py --index 0       # one (optimizer, seed) SLURM task
  python optimizer_benchmark.py --opt Adam --seed 3
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pennylane as qml
from pennylane import numpy as pnp

import sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sweep import (  # noqa: E402
    make_circuit, l2_loss, accuracy, _batch_indices, build_data_splits,
    N_CEMOID_PARAMS, TRAIN_SIZE, VALIDATION_SIZE, TEST_SIZE, DATA_SEED,
    LEARNING_RATE, STEPS_PER_EPOCH, BATCH_SIZE,
    MAX_EPOCHS, PATIENCE, MIN_DELTA, WALL_BUDGET_SECONDS,
)

L, P = 3, 2
N_SEEDS = 50
OPTIMIZERS = ["GradientDescent", "Momentum", "Nesterov", "Adagrad", "RMSProp", "Adam", "SPSA"]
RESULTS_DIR = HERE / "optimizer_histories"


def make_opt(name: str):
    lr = LEARNING_RATE
    if name == "GradientDescent": return qml.GradientDescentOptimizer(lr)
    if name == "Momentum":        return qml.MomentumOptimizer(lr)
    if name == "Nesterov":        return qml.NesterovMomentumOptimizer(lr)
    if name == "Adagrad":         return qml.AdagradOptimizer(lr)
    if name == "RMSProp":         return qml.RMSPropOptimizer(lr)
    if name == "Adam":            return qml.AdamOptimizer(lr)
    if name == "SPSA":            return qml.SPSAOptimizer(maxiter=MAX_EPOCHS * STEPS_PER_EPOCH)
    raise ValueError(f"unknown optimizer {name!r}")


def result_path(opt: str, seed: int) -> Path:
    return RESULTS_DIR / opt / f"seed_{seed:03d}.json"


def train(opt_name: str, seed: int) -> dict:
    splits = build_data_splits(seed=DATA_SEED, train_size=TRAIN_SIZE,
                               validation_size=VALIDATION_SIZE, test_size=TEST_SIZE, replace=True)
    x_train, y_train, _ = splits["train"]
    x_val, y_val, _ = splits["validation"]
    x_test, y_test, _ = splits["test"]
    x_train = pnp.array(x_train, dtype=float, requires_grad=False)
    y_train = pnp.array(y_train, dtype=float, requires_grad=False)
    x_val = pnp.array(x_val, dtype=float, requires_grad=False)
    y_val = pnp.array(y_val, dtype=float, requires_grad=False)
    y_val_np = np.asarray(y_val, dtype=float)
    x_test = pnp.array(x_test, dtype=float, requires_grad=False)
    y_test_np = np.asarray(y_test, dtype=float)

    circuit = make_circuit(L, P)
    n_blocks = L * P
    rng = np.random.default_rng(seed)
    params = pnp.array(rng.uniform(-0.05, 0.05, size=(n_blocks, N_CEMOID_PARAMS)), requires_grad=True)
    opt = make_opt(opt_name)

    vlh, vah, tah = [], [], []
    best = float("inf"); best_params = params.copy(); best_epoch = 0
    best_va = 0.0; best_ta = 0.0; noimp = 0; reason = "max_epochs"
    t0 = time.time(); epoch = 0
    for epoch in range(1, MAX_EPOCHS + 1):
        order = rng.permutation(len(x_train))
        for step in range(STEPS_PER_EPOCH):
            ids = _batch_indices(order, step, BATCH_SIZE)
            bx, by = x_train[ids], y_train[ids]
            params = opt.step(lambda p: l2_loss(circuit, p, bx, by), params)
        vl = float(l2_loss(circuit, params, x_val, y_val))
        va = accuracy(circuit, params, x_val, y_val_np)
        ta = accuracy(circuit, params, x_test, y_test_np)
        vlh.append(vl); vah.append(va); tah.append(ta)
        if vl < best - MIN_DELTA:
            best = vl; best_params = params.copy(); best_epoch = epoch
            best_va = va; best_ta = ta; noimp = 0
        else:
            noimp += 1
            if noimp >= PATIENCE:
                reason = "early_stopping"; break
        if WALL_BUDGET_SECONDS and (time.time() - t0) > WALL_BUDGET_SECONDS:
            reason = "walltime"; break
    return {
        "optimizer": opt_name, "l": L, "p": P, "seed": seed,
        "final_test_accuracy": best_ta, "validation_accuracy": best_va,
        "best_val_loss": best, "best_epoch": best_epoch, "stopped_epoch": epoch,
        "converged": reason == "early_stopping", "stop_reason": reason,
        "wall_seconds": time.time() - t0, "learning_rate": LEARNING_RATE,
        "val_loss_history": vlh, "val_acc_history": vah, "test_acc_history": tah,
        "early_stopping": {"monitor": "val_loss", "patience": PATIENCE,
                           "min_delta": MIN_DELTA, "max_epochs": MAX_EPOCHS,
                           "restore_best_weights": True},
    }


def jobs():
    return [(o, s) for o in OPTIMIZERS for s in range(N_SEEDS)]


def run_index(i: int) -> None:
    js = jobs()
    if not 0 <= i < len(js):
        raise SystemExit(f"--index must be 0..{len(js) - 1}")
    opt, seed = js[i]
    (RESULTS_DIR / opt).mkdir(parents=True, exist_ok=True)
    p = result_path(opt, seed)
    if p.exists():
        print(f"index {i}: {opt} seed {seed} cached, skipping", flush=True)
        return
    t0 = time.time()
    print(f"index {i}: {opt} seed {seed} training...", flush=True)
    r = train(opt, seed)
    p.write_text(json.dumps(r, indent=2))
    print(f"index {i}: {opt} seed {seed} done {time.time() - t0:.1f}s "
          f"acc={r['final_test_accuracy']:.3f} stop@{r['stopped_epoch']} "
          f"converged={r['converged']}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, default=None)
    ap.add_argument("--opt", type=str, default=None)
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args()
    if a.index is not None:
        run_index(a.index)
    elif a.opt is not None and a.seed is not None:
        (RESULTS_DIR / a.opt).mkdir(parents=True, exist_ok=True)
        result_path(a.opt, a.seed).write_text(json.dumps(train(a.opt, a.seed), indent=2))
    else:
        raise SystemExit("need --index OR (--opt and --seed)")


if __name__ == "__main__":
    main()
