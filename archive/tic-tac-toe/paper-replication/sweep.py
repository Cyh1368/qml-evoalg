"""Paper replication: cemoid (l, p) sweep for tic-tac-toe QML.

Replicates the previous-work result that test accuracy grows with model size.

Model definition (from the paper / display_circuit.py):
  A model has ``l`` layers.  Each layer is one data encoding (feature map)
  followed by ``p`` repetitions of the standard "cemoid" block.  Every cemoid
  block carries its own 9 shared parameters, so a model has ``9 * l * p``
  trainable parameters.

Training protocol (from the paper):
  100 epochs, 30 steps per epoch, gradient computed on 15 games per step
  (training set size 15 * 30 = 450).  At the end of each epoch the training set
  is reshuffled and accuracy is evaluated on a fixed test set of 600 random
  games.

This sweeps l = 1..5 and p = 1..5 (25 models), records the per-epoch test
accuracy history of each, and writes a 5x5 grid plot (p on the x axis, l on the
y axis).  Each (l, p) history is cached to JSON so the sweep is resumable.

Run:
    ../.venv-shinka-ttt/bin/python sweep.py            # full 25-run sweep + plot
    ../.venv-shinka-ttt/bin/python sweep.py --plot-only # just (re)draw the plot
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pennylane as qml
from pennylane import numpy as pnp

HERE = Path(__file__).resolve().parent
TTT_DIR = HERE.parent
sys.path.insert(0, str(TTT_DIR))

# Reuse the dataset construction and label convention from the seed program.
from initial_program import (  # noqa: E402
    CLASS_NAMES,
    LABEL_VECTORS,
    build_data_splits,
)

# ---------------------------------------------------------------------------
# Grid / cemoid layout (matches display_circuit.py exactly)
#   0 -- 1 -- 2
#   |    |    |
#   7 -- 8 -- 3
#   |    |    |
#   6 -- 5 -- 4
# ---------------------------------------------------------------------------
N_QUBITS = 9
CORNERS = (0, 2, 4, 6)
EDGES = (1, 3, 5, 7)
CENTER = 8
FEATURE_SCALE = 2 * np.pi / 3

OUTER_PAIRS = [(0, 1), (0, 7), (2, 1), (2, 3), (4, 3), (4, 5), (6, 5), (6, 7)]
INNER_PAIRS = [(1, 8), (3, 8), (5, 8), (7, 8)]
DIAG_PAIRS = [(8, 0), (8, 2), (8, 4), (8, 6)]

N_CEMOID_PARAMS = 9  # cx, cz, ex, ez, mx, mz, o, i, d

# Training protocol constants.
#
# Methodology change (2026-06): the paper's fixed-100-epoch protocol stopped many
# deeper circuits *before* convergence.  We now train with a train/validation/test
# split and **early stopping on validation L2 loss** (restore-best-weights), so
# every model is trained to convergence.  Test accuracy is reported at the epoch
# with the lowest validation loss (the restored best weights) — never test-peeked.
STEPS_PER_EPOCH = 30
BATCH_SIZE = 15            # 15 games per gradient step
TRAIN_SIZE = 450          # 15 * 30
VALIDATION_SIZE = 300
TEST_SIZE = 600
LEARNING_RATE = 0.03
DATA_SEED = 2027

# Early-stopping config (env-overridable so sbatch can tune without code edits).
MAX_EPOCHS = int(os.environ.get("MAX_EPOCHS", "1000"))   # hard cap
PATIENCE = int(os.environ.get("PATIENCE", "75"))         # epochs w/o val-loss improvement
MIN_DELTA = float(os.environ.get("MIN_DELTA", "1e-4"))   # min val-loss improvement to count
# Optional soft walltime cap (seconds): stop gracefully and write partial result
# instead of being SIGKILLed mid-epoch and losing the job.  0 disables.
WALL_BUDGET_SECONDS = float(os.environ.get("WALL_BUDGET_SECONDS", "0"))

# Extended 2026-06 to {1..10} to probe whether converged accuracy keeps climbing
# toward 1.0 or saturates below it past the original 7x7 frontier (the
# accuracy-ceiling question; builds on SWEEP_LP_REPORT.md).
L_VALUES = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
P_VALUES = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

# Original square grid (already swept + reported). New frontier cells are those
# with l > 7 or p > 7; the extended SLURM array runs only these, heaviest-first,
# so the 49 cached histories are skipped and the original indexing is untouched.
_ORIG_MAX = 7
EXT_NEW_JOBS = sorted(
    ((l, p) for l in L_VALUES for p in P_VALUES if l > _ORIG_MAX or p > _ORIG_MAX),
    key=lambda lp: lp[0] * lp[1],
    reverse=True,
)

# Canonical job order for the SLURM array: heaviest (most cemoid blocks) first,
# so the long-pole models start in the first scheduling wave instead of waiting
# behind the cheap ones.  History files are keyed by (l, p), so reordering never
# disturbs caching.
JOBS_BY_COST = sorted(
    ((l, p) for l in L_VALUES for p in P_VALUES),
    key=lambda lp: lp[0] * lp[1],
    reverse=True,
)

RESULTS_DIR = HERE / "histories"
PLOT_PATH = HERE / "lp_sweep_accuracy.png"


def feature_map(boards) -> None:
    """RX data encoding, broadcast over a batch of boards (shape [B, 9])."""
    for wire in range(N_QUBITS):
        qml.RX(FEATURE_SCALE * boards[:, wire], wires=wire)


def cemoid_block(block_params) -> None:
    """One cemoid block W(theta) with 9 shared parameters."""
    theta_cx, theta_cz, theta_ex, theta_ez, theta_mx, theta_mz, theta_o, theta_i, theta_d = block_params
    for q in CORNERS:
        qml.RX(theta_cx, wires=q)
        qml.RZ(theta_cz, wires=q)
    for q in EDGES:
        qml.RX(theta_ex, wires=q)
        qml.RZ(theta_ez, wires=q)
    qml.RX(theta_mx, wires=CENTER)
    qml.RZ(theta_mz, wires=CENTER)
    for ctrl, tgt in OUTER_PAIRS:
        qml.CRY(theta_o, wires=[ctrl, tgt])
    for ctrl, tgt in INNER_PAIRS:
        qml.CRY(theta_i, wires=[ctrl, tgt])
    for ctrl, tgt in DIAG_PAIRS:
        qml.CRY(theta_d, wires=[ctrl, tgt])


_DEVICE = qml.device("default.qubit", wires=N_QUBITS, shots=None)


def make_circuit(n_layers: int, n_repeats: int):
    """Build a QNode for a model with n_layers layers, n_repeats cemoid blocks each."""

    @qml.qnode(_DEVICE, interface="autograd", diff_method="backprop")
    def circuit(boards, params):
        # params shape: (n_layers * n_repeats, 9)
        block_index = 0
        for _layer in range(n_layers):
            feature_map(boards)
            for _rep in range(n_repeats):
                cemoid_block(params[block_index])
                block_index += 1
        return [qml.expval(qml.PauliZ(wire)) for wire in range(N_QUBITS)]

    return circuit


def class_expectations(circuit, boards, params):
    """Map the 9 Z expectations to [cross, circle, draw] for a batch of boards."""
    z = pnp.stack(circuit(boards, params))  # shape (9, B)
    cross = (z[1] + z[3] + z[5] + z[7]) / 4.0
    circle = (z[0] + z[2] + z[4] + z[6]) / 4.0
    draw = z[8]
    return pnp.stack([cross, circle, draw], axis=1)  # shape (B, 3)


def l2_loss(circuit, params, boards, targets):
    predictions = class_expectations(circuit, boards, params)
    return pnp.mean(pnp.sum((predictions - targets) ** 2, axis=1))


def accuracy(circuit, params, boards, targets) -> float:
    predictions = np.asarray(class_expectations(circuit, boards, params), dtype=float)
    return float(np.mean(np.argmax(predictions, axis=1) == np.argmax(targets, axis=1)))


def _batch_indices(order, step, batch_size):
    start = (step * batch_size) % len(order)
    end = start + batch_size
    if end <= len(order):
        return order[start:end]
    return np.concatenate([order[start:], order[: end - len(order)]])


def train_model(n_layers: int, n_repeats: int, seed: int = 0) -> dict:
    """Train one (l, p) model to convergence via validation-loss early stopping.

    Protocol:
      * Train/validation/test split (sizes TRAIN_SIZE / VALIDATION_SIZE / TEST_SIZE).
      * Each epoch: minibatch SGD over the train set, then evaluate validation
        L2 loss + accuracy and test accuracy.
      * Early stopping monitors **validation L2 loss** with PATIENCE / MIN_DELTA.
        The parameters with the lowest validation loss are restored ("best
        weights").
      * ``final_test_accuracy`` is the test accuracy at the restored best-val
        epoch — chosen by validation, never by peeking at the test set.
    """
    splits = build_data_splits(
        seed=DATA_SEED,
        train_size=TRAIN_SIZE,
        validation_size=VALIDATION_SIZE,
        test_size=TEST_SIZE,
        replace=True,
    )
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

    circuit = make_circuit(n_layers, n_repeats)
    n_blocks = n_layers * n_repeats
    n_params = n_blocks * N_CEMOID_PARAMS

    rng = np.random.default_rng(seed)
    params = pnp.array(
        rng.uniform(-0.05, 0.05, size=(n_blocks, N_CEMOID_PARAMS)),
        requires_grad=True,
    )
    optimizer = qml.AdamOptimizer(stepsize=LEARNING_RATE)

    val_loss_history: list[float] = []
    val_acc_history: list[float] = []
    test_acc_history: list[float] = []

    best_val_loss = float("inf")
    best_params = params.copy()
    best_epoch = 0
    best_val_acc = 0.0
    best_test_acc = 0.0
    epochs_no_improve = 0
    stop_reason = "max_epochs"
    t0 = time.time()
    epoch = 0

    for epoch in range(1, MAX_EPOCHS + 1):
        order = rng.permutation(len(x_train))
        for step in range(STEPS_PER_EPOCH):
            ids = _batch_indices(order, step, BATCH_SIZE)
            batch_x = x_train[ids]
            batch_y = y_train[ids]
            params = optimizer.step(
                lambda p: l2_loss(circuit, p, batch_x, batch_y), params
            )

        val_loss = float(l2_loss(circuit, params, x_val, y_val))
        val_acc = accuracy(circuit, params, x_val, y_val_np)
        test_acc = accuracy(circuit, params, x_test, y_test_np)
        val_loss_history.append(val_loss)
        val_acc_history.append(val_acc)
        test_acc_history.append(test_acc)

        if val_loss < best_val_loss - MIN_DELTA:
            best_val_loss = val_loss
            best_params = params.copy()
            best_epoch = epoch
            best_val_acc = val_acc
            best_test_acc = test_acc
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= PATIENCE:
                stop_reason = "early_stopping"
                break

        if WALL_BUDGET_SECONDS and (time.time() - t0) > WALL_BUDGET_SECONDS:
            stop_reason = "walltime"
            break

    converged = stop_reason == "early_stopping"
    return {
        "l": n_layers,
        "p": n_repeats,
        "n_blocks": n_blocks,
        "n_params": n_params,
        # Reported metrics are at the restored best-validation epoch.
        "final_test_accuracy": best_test_acc,
        "validation_accuracy": best_val_acc,
        "best_val_loss": best_val_loss,
        "best_epoch": best_epoch,
        "stopped_epoch": epoch,
        "converged": converged,
        "stop_reason": stop_reason,
        # Full per-epoch traces (for convergence plots / diagnostics).
        "val_loss_history": val_loss_history,
        "val_acc_history": val_acc_history,
        "test_acc_history": test_acc_history,
        # Methodology metadata.
        "early_stopping": {
            "monitor": "val_loss",
            "patience": PATIENCE,
            "min_delta": MIN_DELTA,
            "max_epochs": MAX_EPOCHS,
            "restore_best_weights": True,
        },
        "split_sizes": {
            "train": TRAIN_SIZE,
            "validation": VALIDATION_SIZE,
            "test": TEST_SIZE,
        },
    }


def history_path(n_layers: int, n_repeats: int) -> Path:
    return RESULTS_DIR / f"history_l{n_layers}_p{n_repeats}.json"


def _assign_shards(nshards: int) -> list[list[tuple[int, int]]]:
    """Balance jobs across shards with longest-processing-time-first greedy."""
    jobs = sorted(
        ((l, p) for l in L_VALUES for p in P_VALUES),
        key=lambda lp: lp[0] * lp[1],
        reverse=True,
    )
    loads = [0] * nshards
    buckets: list[list[tuple[int, int]]] = [[] for _ in range(nshards)]
    for n_layers, n_repeats in jobs:
        target = min(range(nshards), key=lambda i: loads[i])
        buckets[target].append((n_layers, n_repeats))
        loads[target] += n_layers * n_repeats
    return buckets


def run_sweep(shard: int = 0, nshards: int = 1) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    my_jobs = _assign_shards(nshards)[shard]
    for n_layers, n_repeats in my_jobs:
        path = history_path(n_layers, n_repeats)
        if path.exists():
            print(f"[shard {shard}] l={n_layers} p={n_repeats}: cached, skipping", flush=True)
            continue
        t0 = time.time()
        print(f"[shard {shard}] l={n_layers} p={n_repeats}: training "
              f"({n_layers * n_repeats * N_CEMOID_PARAMS} params)...", flush=True)
        result = train_model(n_layers, n_repeats)
        path.write_text(json.dumps(result, indent=2))
        dt = time.time() - t0
        print(f"[shard {shard}] l={n_layers} p={n_repeats}: done in {dt:.1f}s  "
              f"final test acc = {result['final_test_accuracy']:.3f}", flush=True)


def run_one_by_index(index: int) -> None:
    """Train exactly one (l, p) pair, selected by heaviest-first array index."""
    jobs = JOBS_BY_COST
    if not 0 <= index < len(jobs):
        raise SystemExit(f"--index must be in [0, {len(jobs) - 1}], got {index}")
    n_layers, n_repeats = jobs[index]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = history_path(n_layers, n_repeats)
    if path.exists():
        print(f"index {index}: l={n_layers} p={n_repeats} cached, skipping", flush=True)
        return
    t0 = time.time()
    print(f"index {index}: l={n_layers} p={n_repeats} training "
          f"({n_layers * n_repeats * N_CEMOID_PARAMS} params)...", flush=True)
    result = train_model(n_layers, n_repeats)
    path.write_text(json.dumps(result, indent=2))
    print(f"index {index}: l={n_layers} p={n_repeats} done in {time.time() - t0:.1f}s  "
          f"final test acc = {result['final_test_accuracy']:.3f}", flush=True)


def run_one_ext_by_index(index: int) -> None:
    """Train exactly one *new frontier* (l, p) pair (l>7 or p>7), heaviest-first.

    Used by the extended SLURM array (sweep_ext_array.sbatch). Existing 7x7
    histories are skipped via the cache check, so this only fills new cells.
    """
    jobs = EXT_NEW_JOBS
    if not 0 <= index < len(jobs):
        raise SystemExit(f"--ext-index must be in [0, {len(jobs) - 1}], got {index}")
    n_layers, n_repeats = jobs[index]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = history_path(n_layers, n_repeats)
    if path.exists():
        print(f"ext-index {index}: l={n_layers} p={n_repeats} cached, skipping", flush=True)
        return
    t0 = time.time()
    print(f"ext-index {index}: l={n_layers} p={n_repeats} training "
          f"({n_layers * n_repeats * N_CEMOID_PARAMS} params)...", flush=True)
    result = train_model(n_layers, n_repeats)
    path.write_text(json.dumps(result, indent=2))
    print(f"ext-index {index}: l={n_layers} p={n_repeats} done in {time.time() - t0:.1f}s  "
          f"final test acc = {result['final_test_accuracy']:.3f}  "
          f"stop={result['stop_reason']}", flush=True)


def make_plot() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n_rows = len(L_VALUES)
    n_cols = len(P_VALUES)
    # Top-left subplot is (l=1, p=1) and bottom-right is (l=7, p=7): l increases
    # top->bottom down the rows, p increases left->right across the columns.
    fig, axes = plt.subplots(
        n_rows, n_cols, figsize=(2.4 * n_cols, 2.0 * n_rows), sharex=True, sharey=True
    )

    for row, n_layers in enumerate(L_VALUES):
        for col, n_repeats in enumerate(P_VALUES):
            ax = axes[row][col]
            # Light grey reference lines at 0.25, 0.50, 0.75 in every subplot.
            for y in (0.25, 0.50, 0.75):
                ax.axhline(y, color="0.8", linewidth=0.8, zorder=0)
            path = history_path(n_layers, n_repeats)
            if path.exists():
                data = json.loads(path.read_text())
                hist = data["test_acc_history"]
                ax.plot(range(1, len(hist) + 1), hist, color="C0", linewidth=1.0, zorder=2)
                final = data["final_test_accuracy"]
                ax.text(
                    0.95, 0.06, f"{final:.0%}", transform=ax.transAxes,
                    ha="right", va="bottom", fontsize=8, color="0.3",
                )
            ax.set_ylim(0.0, 1.0)
            ax.set_xticks([])
            ax.set_yticks([0.0, 0.5, 1.0])
            if col != 0:
                ax.set_yticklabels([])
            # Column headers (p) along the top row.
            if row == 0:
                ax.set_title(f"p = {n_repeats}", fontsize=11)
            # Row labels (l) on the left column.
            if col == 0:
                ax.set_ylabel(f"l = {n_layers}", fontsize=11)

    fig.supxlabel("epochs  (p increases left to right)", fontsize=11)
    fig.supylabel("test accuracy  (l increases top to bottom)", fontsize=11)
    fig.suptitle("cemoid (l, p) sweep — test accuracy vs. epochs", fontsize=13)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))
    fig.savefig(PLOT_PATH, dpi=150)
    print(f"Saved plot: {PLOT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-only", action="store_true", help="only (re)draw the plot")
    parser.add_argument("--shard", type=int, default=0, help="this worker's index in [0, nshards)")
    parser.add_argument("--nshards", type=int, default=1, help="total number of parallel workers")
    parser.add_argument("--no-plot", action="store_true", help="train only, do not draw the plot")
    parser.add_argument(
        "--index", type=int, default=None,
        help="run exactly one (l,p) pair selected by heaviest-first index over the "
             "full grid (used by the original SLURM job array, one task per pair)",
    )
    parser.add_argument(
        "--ext-index", type=int, default=None,
        help="run exactly one *new frontier* (l,p) pair (l>7 or p>7), heaviest-first "
             "(used by sweep_ext_array.sbatch to extend the grid to {1..10})",
    )
    args = parser.parse_args()
    if args.plot_only:
        make_plot()
        return
    if args.ext_index is not None:
        run_one_ext_by_index(args.ext_index)
        return
    if args.index is not None:
        run_one_by_index(args.index)
        return
    run_sweep(shard=args.shard, nshards=args.nshards)
    if not args.no_plot:
        make_plot()


if __name__ == "__main__":
    main()
