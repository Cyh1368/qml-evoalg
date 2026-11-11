"""EA-evolved ansatz (l, p) sweep for tic-tac-toe QML.

Counterpart to ``sweep.py``, but the per-block circuit is the **converged
ShinkaEvolve winner** — the *Symmetry-grouped RX+RY rotations (SU2-like)* block
documented in ``EA_CONVERGED_RERUN_REPORT.md`` (best program
``b6ba28a0-c603-4aa9-802b-3501115b3967``, generation 16). Everything else — the
RX feature map, the [cross/circle/draw] Z-readout, the converged training
protocol (450/300/600 splits, Adam lr 0.03, validation-loss early stopping,
restore-best-weights, 1000-epoch cap) — is identical to ``sweep.py`` so the two
sweeps are directly comparable.

Model definition:
  A model has ``l`` layers. Each layer is one RX data encoding followed by ``p``
  repetitions of the evolved SU2-like block. Every block carries its own 11
  shared parameters, so a model has ``11 * l * p`` trainable parameters. The
  evolved winner itself is the L=3, P=2 instance (6 blocks, 66 params).

Run:
    ../.venv-shinka-ttt/bin/python sweep_ea.py --index 0   # one (l,p) SLURM task
    ../.venv-shinka-ttt/bin/python sweep_ea.py --plot-only # just (re)draw the plot
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

# Reuse every ansatz-independent piece from the cemoid sweep so the two analyses
# share an identical data pipeline, readout, loss, and training protocol.
from sweep import (  # noqa: E402
    N_QUBITS, CORNERS, EDGES, CENTER, FEATURE_SCALE,
    feature_map, class_expectations, l2_loss, accuracy, _batch_indices,
    build_data_splits,
    STEPS_PER_EPOCH, BATCH_SIZE, TRAIN_SIZE, VALIDATION_SIZE, TEST_SIZE,
    LEARNING_RATE, DATA_SEED, MAX_EPOCHS, PATIENCE, MIN_DELTA, WALL_BUDGET_SECONDS,
    L_VALUES, P_VALUES,
)

# ── evolved SU2-like block ──────────────────────────────────────────────────────
# 11 shared parameters per block, in this fixed order:
#   rx_corner, rx_edge, rx_center, ry_corner, ry_edge, ry_center,
#   crz_outer, crx_inner, rz_corner, rz_edge, rz_center
N_EA_PARAMS = 11

# CRZ nearest-neighbour ring over the 8 outer qubits (one shared angle).
EA_RING_PAIRS = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 0)]
# CRX hub: each edge qubit -> center (one shared angle).
EA_HUB_PAIRS = [(1, 8), (3, 8), (5, 8), (7, 8)]


def ea_block(bp) -> None:
    """One evolved SU2-like block W(theta) with 11 shared parameters."""
    (rx_corner, rx_edge, rx_center,
     ry_corner, ry_edge, ry_center,
     crz_outer, crx_inner,
     rz_corner, rz_edge, rz_center) = bp
    # RX layer (symmetry-grouped)
    for q in CORNERS:
        qml.RX(rx_corner, wires=q)
    for q in EDGES:
        qml.RX(rx_edge, wires=q)
    qml.RX(rx_center, wires=CENTER)
    # RY layer (symmetry-grouped)
    for q in CORNERS:
        qml.RY(ry_corner, wires=q)
    for q in EDGES:
        qml.RY(ry_edge, wires=q)
    qml.RY(ry_center, wires=CENTER)
    # CRZ nearest-neighbour ring (outer 8 qubits)
    for ctrl, tgt in EA_RING_PAIRS:
        qml.CRZ(crz_outer, wires=[ctrl, tgt])
    # CRX hub: each edge -> center
    for ctrl, tgt in EA_HUB_PAIRS:
        qml.CRX(crx_inner, wires=[ctrl, tgt])
    # Final local RZ layer (symmetry-grouped)
    for q in CORNERS:
        qml.RZ(rz_corner, wires=q)
    for q in EDGES:
        qml.RZ(rz_edge, wires=q)
    qml.RZ(rz_center, wires=CENTER)


_DEVICE = qml.device("default.qubit", wires=N_QUBITS, shots=None)


def make_circuit(n_layers: int, n_repeats: int):
    """Build a QNode for an EA model: n_layers layers, n_repeats blocks each."""

    @qml.qnode(_DEVICE, interface="autograd", diff_method="backprop")
    def circuit(boards, params):
        block_index = 0
        for _layer in range(n_layers):
            feature_map(boards)
            for _rep in range(n_repeats):
                ea_block(params[block_index])
                block_index += 1
        return [qml.expval(qml.PauliZ(wire)) for wire in range(N_QUBITS)]

    return circuit


RESULTS_DIR = HERE / "histories_ea"
PLOT_PATH = HERE / "lp_sweep_ea_accuracy.png"

JOBS_BY_COST = sorted(
    ((l, p) for l in L_VALUES for p in P_VALUES),
    key=lambda lp: lp[0] * lp[1],
    reverse=True,
)


def train_model(n_layers: int, n_repeats: int, seed: int = 0) -> dict:
    """Train one EA (l, p) model to convergence via validation-loss early stopping.

    Identical protocol to ``sweep.train_model`` — only the per-block circuit and
    the 11-vs-9 parameter count differ.
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
    n_params = n_blocks * N_EA_PARAMS

    rng = np.random.default_rng(seed)
    params = pnp.array(
        rng.uniform(-0.05, 0.05, size=(n_blocks, N_EA_PARAMS)),
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
        "final_test_accuracy": best_test_acc,
        "validation_accuracy": best_val_acc,
        "best_val_loss": best_val_loss,
        "best_epoch": best_epoch,
        "stopped_epoch": epoch,
        "converged": converged,
        "stop_reason": stop_reason,
        "val_loss_history": val_loss_history,
        "val_acc_history": val_acc_history,
        "test_acc_history": test_acc_history,
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


def run_one_by_index(index: int) -> None:
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
          f"({n_layers * n_repeats * N_EA_PARAMS} params)...", flush=True)
    result = train_model(n_layers, n_repeats)
    path.write_text(json.dumps(result, indent=2))
    print(f"index {index}: l={n_layers} p={n_repeats} done in {time.time() - t0:.1f}s  "
          f"final test acc = {result['final_test_accuracy']:.3f}  "
          f"stop={result['stop_reason']}", flush=True)


def make_plot() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n_rows = len(L_VALUES)
    n_cols = len(P_VALUES)
    fig, axes = plt.subplots(
        n_rows, n_cols, figsize=(2.4 * n_cols, 2.0 * n_rows), sharex=True, sharey=True
    )
    for row, n_layers in enumerate(L_VALUES):
        for col, n_repeats in enumerate(P_VALUES):
            ax = axes[row][col]
            for y in (0.25, 0.50, 0.75):
                ax.axhline(y, color="0.8", linewidth=0.8, zorder=0)
            path = history_path(n_layers, n_repeats)
            if path.exists():
                data = json.loads(path.read_text())
                hist = data["test_acc_history"]
                ax.plot(range(1, len(hist) + 1), hist, color="C2", linewidth=1.0, zorder=2)
                final = data["final_test_accuracy"]
                ax.text(0.95, 0.06, f"{final:.0%}", transform=ax.transAxes,
                        ha="right", va="bottom", fontsize=8, color="0.3")
            ax.set_ylim(0.0, 1.0)
            ax.set_xticks([])
            ax.set_yticks([0.0, 0.5, 1.0])
            if col != 0:
                ax.set_yticklabels([])
            if row == 0:
                ax.set_title(f"p = {n_repeats}", fontsize=11)
            if col == 0:
                ax.set_ylabel(f"l = {n_layers}", fontsize=11)

    fig.supxlabel("epochs  (p increases left to right)", fontsize=11)
    fig.supylabel("test accuracy  (l increases top to bottom)", fontsize=11)
    fig.suptitle("EA SU2-like (l, p) sweep — test accuracy vs. epochs", fontsize=13)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))
    fig.savefig(PLOT_PATH, dpi=150)
    print(f"Saved plot: {PLOT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-only", action="store_true")
    parser.add_argument("--index", type=int, default=None,
                        help="run exactly one (l,p) pair, heaviest-first index over the full grid")
    args = parser.parse_args()
    if args.plot_only:
        make_plot()
        return
    if args.index is not None:
        run_one_by_index(args.index)
        return
    raise SystemExit("need --index I | --plot-only")


if __name__ == "__main__":
    main()
