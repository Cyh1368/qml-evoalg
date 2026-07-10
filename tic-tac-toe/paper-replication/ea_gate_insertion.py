"""Gate-insertion robustness for the top-3 EA-evolved circuits.

Inserts N random RX/RY/RZ gates into each EA circuit at random slot+wire
positions, trains jointly (extra angles start at 0), and records final
test accuracy + final extra-gate angles.

Slot structure for N_UPLOADS=3, N_REPEATS=2 (mirrors cemoid analysis):
    Layer k: [slot 3k] FM [slot 3k+1] SPEC [slot 3k+2] SPEC
    Final:   [slot 9]
→ 10 slots × 9 qubits × 3 gate types = 270 possible positions (same as cemoid).

Usage:
    python ea_gate_insertion.py --prog-idx 0 --index 14   # SLURM task
    python ea_gate_insertion.py --plot-only                 # after all jobs
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from collections import defaultdict

import numpy as np
import pennylane as qml
from pennylane import numpy as pnp

HERE     = Path(__file__).resolve().parent
PROG_DIR = HERE / "ea_programs"
RESULTS_DIR = HERE / "ea_gate_insertion_results"
PLOT_PATH   = HERE / "ea_fig2_gate_insertion.png"
MANIFEST    = json.loads((PROG_DIR / "manifest.json").read_text())

# Match cemoid experiment exactly
N_GATES_SCHEDULE = [1, 2, 3, 5, 8, 13, 21]
N_TRAIN_SEEDS    = 10
CONFIG_SEED      = 42
DATA_SEED        = 2027

# Training hyperparams (same as cemoid / initial_program.py defaults)
N_QUBITS        = 9
N_UPLOADS       = 3   # re-upload count
N_REPEATS       = 2   # spec repetitions per upload
N_EPOCHS        = 50
STEPS_PER_EPOCH = 30
BATCH_SIZE      = 15
LEARNING_RATE   = 0.03
TRAIN_SIZE      = 450
TEST_SIZE       = 600

_GATE_TYPES = ["RX", "RY", "RZ"]
_N_SLOTS    = N_UPLOADS * (1 + N_REPEATS) + 1   # 10

def _all_positions():
    return [(slot, wire, gt)
            for slot in range(_N_SLOTS)
            for wire in range(N_QUBITS)
            for gt   in _GATE_TYPES]

ALL_POSITIONS = _all_positions()
_GATE_FN = {"RX": qml.RX, "RY": qml.RY, "RZ": qml.RZ}


def sample_positions(n_gates: int, config_seed: int):
    rng = np.random.default_rng(config_seed)
    idx = rng.choice(len(ALL_POSITIONS), size=n_gates, replace=False)
    return [ALL_POSITIONS[i] for i in sorted(idx)]


def _load_program(prog_idx: int):
    """Import EA program module and return (apply_ansatz_block, N_PARAMS_PER_BLOCK, run_experiment, build_data_splits)."""
    info = MANIFEST[prog_idx]
    path = PROG_DIR / f"prog_{info['short_id']}.py"
    spec = importlib.util.spec_from_file_location(f"ea_prog_{prog_idx}", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_augmented_circuit(mod, positions):
    """Build a QNode that runs the EA circuit + extra gates at the given positions."""
    slot_gates: dict[int, list] = defaultdict(list)
    for k, (slot, wire, gt) in enumerate(positions):
        slot_gates[slot].append((wire, gt, k))

    def _extras(slot_id, extra_angles):
        for wire, gt, k in slot_gates.get(slot_id, []):
            _GATE_FN[gt](extra_angles[k], wires=wire)

    device = qml.device("default.qubit", wires=N_QUBITS, shots=None)

    @qml.qnode(device, interface="autograd", diff_method="backprop")
    def circuit(board, ansatz_params, extra_angles):
        slot = 0
        for upload_idx in range(N_UPLOADS):
            _extras(slot, extra_angles); slot += 1
            mod.feature_map(board)
            for repeat_idx in range(N_REPEATS):
                _extras(slot, extra_angles); slot += 1
                block_idx = upload_idx * N_REPEATS + repeat_idx
                mod.apply_ansatz_block(ansatz_params, block_idx)
        _extras(slot, extra_angles)   # final slot
        return [qml.expval(qml.PauliZ(w)) for w in range(N_QUBITS)]

    return circuit


def class_expectations(circuit, board, ansatz_params, extra_angles):
    z = pnp.stack(circuit(board, ansatz_params, extra_angles))
    cross  = (z[1] + z[3] + z[5] + z[7]) / 4.0
    circle = (z[0] + z[2] + z[4] + z[6]) / 4.0
    draw   = z[8]
    return pnp.stack([cross, circle, draw])


def predict_batch(circuit, boards, ansatz_params, extra_angles):
    return pnp.stack([class_expectations(circuit, b, ansatz_params, extra_angles)
                      for b in boards])


def l2_loss(circuit, ansatz_params, extra_angles, boards, targets):
    pred = predict_batch(circuit, boards, ansatz_params, extra_angles)
    tgt  = pnp.array(targets, requires_grad=False)
    return pnp.mean(pnp.sum((pred - tgt) ** 2, axis=1))


def accuracy_fn(circuit, ansatz_params, extra_angles, boards, targets_np) -> float:
    pred = np.asarray(predict_batch(circuit, boards, ansatz_params, extra_angles), dtype=float)
    return float(np.mean(np.argmax(pred, axis=1) == np.argmax(targets_np, axis=1)))


def train(prog_idx: int, n_gates: int, config_seed: int, train_seed: int) -> dict:
    mod = _load_program(prog_idx)
    positions = sample_positions(n_gates, config_seed)
    circuit   = make_augmented_circuit(mod, positions)

    splits = mod.build_data_splits(
        seed=DATA_SEED, train_size=TRAIN_SIZE,
        validation_size=300, test_size=TEST_SIZE, replace=True,
    )
    x_train, y_train, _ = splits["train"]
    x_test,  y_test,  _ = splits["test"]

    n_blocks = N_UPLOADS * N_REPEATS
    rng = np.random.default_rng(train_seed)
    ansatz_params = pnp.array(
        rng.uniform(-0.05, 0.05, size=mod.N_PARAMS),
        requires_grad=True,
    )
    # Pack ansatz params + extra angles into one flat vector
    n_ap = mod.N_PARAMS
    packed = pnp.array(
        np.concatenate([np.asarray(ansatz_params).ravel(), np.zeros(n_gates)]),
        requires_grad=True,
    )

    def packed_loss(p, bx, by):
        ap = pnp.array(p[:n_ap], requires_grad=False)
        ea = p[n_ap:]
        return l2_loss(circuit, ap, ea, bx, by)

    optimizer = qml.AdamOptimizer(stepsize=LEARNING_RATE)
    test_acc_history = []

    for epoch in range(1, N_EPOCHS + 1):
        order = rng.permutation(len(x_train))
        for step in range(STEPS_PER_EPOCH):
            start = (step * BATCH_SIZE) % len(order)
            end   = start + BATCH_SIZE
            ids   = order[start:end] if end <= len(order) else np.concatenate([order[start:], order[:end - len(order)]])
            bx, by = x_train[ids], y_train[ids]
            packed = optimizer.step(lambda p: packed_loss(p, bx, by), packed)
        # Eval-opt: only evaluate test accuracy at the final epoch. The trained
        # model is identical to per-epoch eval; only the (unused) intermediate
        # history curve is dropped. Plots use final_test_accuracy only.
        if epoch == N_EPOCHS:
            ap = pnp.array(packed[:n_ap], requires_grad=False)
            ea = packed[n_ap:]
            acc = accuracy_fn(circuit, ap, ea, x_test, np.asarray(y_test, dtype=float))
            test_acc_history.append(acc)

    final_ea = np.asarray(packed[n_ap:], dtype=float).tolist()
    return {
        "prog_idx":    prog_idx,
        "short_id":    MANIFEST[prog_idx]["short_id"],
        "n_gates":     n_gates,
        "config_seed": config_seed,
        "train_seed":  train_seed,
        "positions":   positions,
        "final_extra_angles":    final_ea,
        "final_extra_abs_mean":  float(np.mean(np.abs(final_ea))),
        "test_acc_history":      test_acc_history,
        "final_test_accuracy":   test_acc_history[-1],
    }


def result_path(prog_idx: int, n_gates: int, train_seed: int) -> Path:
    sid = MANIFEST[prog_idx]["short_id"]
    return RESULTS_DIR / f"p{prog_idx}_{sid}_ng{n_gates:02d}_ts{train_seed:02d}.json"


def run_one(prog_idx: int, n_gates: int, train_seed: int) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = result_path(prog_idx, n_gates, train_seed)
    if path.exists():
        print(f"cached prog={prog_idx} ng={n_gates} ts={train_seed}", flush=True)
        return
    t0 = time.time()
    print(f"training prog={prog_idx} ng={n_gates} ts={train_seed}...", flush=True)
    result = train(prog_idx, n_gates, CONFIG_SEED, train_seed)
    path.write_text(json.dumps(result, indent=2))
    print(f"done {time.time()-t0:.1f}s  acc={result['final_test_accuracy']:.3f}  "
          f"mean|ea|={result['final_extra_abs_mean']:.4f}", flush=True)


def all_jobs():
    return [
        (pi, ng, ts)
        for pi in range(len(MANIFEST))
        for ng in N_GATES_SCHEDULE
        for ts in range(N_TRAIN_SEEDS)
    ]


def run_by_index(index: int) -> None:
    jobs = all_jobs()
    if not 0 <= index < len(jobs):
        raise SystemExit(f"--index must be 0..{len(jobs)-1}")
    run_one(*jobs[index])


def make_plot() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Load cemoid gate-insertion results for comparison
    cemoid_by_ng: dict[int, list] = defaultdict(list)
    cemoid_angles: dict[int, list] = defaultdict(list)
    for p in sorted((HERE / "gate_insertion_results").glob("ng*.json")):
        r = json.loads(p.read_text())
        cemoid_by_ng[r["n_gates"]].append(r["final_test_accuracy"])
        cemoid_angles[r["n_gates"]].extend(np.abs(r["final_extra_angles"]).tolist())

    colors = ["#2196F3", "#4CAF50", "#FF9800"]
    ngs    = N_GATES_SCHEDULE

    fig, axes = plt.subplots(2, len(MANIFEST) + 1, figsize=(16, 8))

    def _plot_col(col, label, by_ng, ang_by_ng, color):
        xs = list(range(len(ngs)))
        means   = [np.mean(by_ng[ng])      if by_ng[ng]      else np.nan for ng in ngs]
        stds    = [np.std(by_ng[ng])       if by_ng[ng]      else np.nan for ng in ngs]
        ameans  = [np.mean(ang_by_ng[ng])  if ang_by_ng[ng]  else np.nan for ng in ngs]

        ax1 = axes[0][col]
        ax1.errorbar(xs, means, yerr=stds, fmt="o-", color=color,
                     capsize=4, lw=1.5, label="mean±std")
        ax1.set_xticks(xs); ax1.set_xticklabels(ngs)
        ax1.set_ylim(0.3, 0.9)
        ax1.set_title(label, fontsize=9)
        ax1.set_ylabel("Test accuracy") if col == 0 else None
        ax1.grid(True, alpha=0.25)

        ax2 = axes[1][col]
        ax2.plot(xs, ameans, "s-", color=color, lw=1.5)
        ax2.axhline(0, color="grey", lw=0.7, ls=":")
        ax2.set_xticks(xs); ax2.set_xticklabels(ngs)
        ax2.set_xlabel("Extra gates")
        ax2.set_ylabel("Mean |θ_extra| (rad)") if col == 0 else None
        ax2.grid(True, alpha=0.25)

    # Cemoid column
    _plot_col(0, "Cemoid L=3,P=2\n(baseline)", cemoid_by_ng, cemoid_angles, "#9E9E9E")

    # EA program columns
    for pi, info in enumerate(MANIFEST):
        by_ng: dict[int, list] = defaultdict(list)
        ang_by_ng: dict[int, list] = defaultdict(list)
        for ng in ngs:
            for ts in range(N_TRAIN_SEEDS):
                p = result_path(pi, ng, ts)
                if p.exists():
                    r = json.loads(p.read_text())
                    by_ng[ng].append(r["final_test_accuracy"])
                    ang_by_ng[ng].extend(np.abs(r["final_extra_angles"]).tolist())
        label = (f"EA prog #{pi+1}\n(gen {info['generation']}, "
                 f"test={info['test_acc']:.3f})")
        _plot_col(pi + 1, label, by_ng, ang_by_ng, colors[pi])

    fig.suptitle("Gate-insertion robustness: EA circuits vs. cemoid baseline\n"
                 "Top row: accuracy | Bottom row: mean |extra gate angle|", fontsize=11)
    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=150)
    print(f"Saved {PLOT_PATH}")

    # Summary table
    print(f"\n{'circuit':>12}  {'n_gates':>8}  {'mean_acc':>9}  {'std':>6}  {'mean|θ|':>8}")
    for pi in range(-1, len(MANIFEST)):
        if pi == -1:
            label = "cemoid"
            by_ng = cemoid_by_ng
            ang   = cemoid_angles
        else:
            label = f"ea#{pi+1}"
            by_ng = defaultdict(list)
            ang   = defaultdict(list)
            for ng in ngs:
                for ts in range(N_TRAIN_SEEDS):
                    p = result_path(pi, ng, ts)
                    if p.exists():
                        r = json.loads(p.read_text())
                        by_ng[ng].append(r["final_test_accuracy"])
                        ang[ng].extend(np.abs(r["final_extra_angles"]).tolist())
        for ng in ngs:
            if by_ng[ng]:
                print(f"{label:>12}  {ng:>8}  {np.mean(by_ng[ng]):>9.3f}  "
                      f"{np.std(by_ng[ng]):>6.3f}  {np.mean(ang[ng]):>8.4f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prog-idx", type=int, default=None)
    parser.add_argument("--n-gates",  type=int, default=None)
    parser.add_argument("--train-seed", type=int, default=0)
    parser.add_argument("--index",    type=int, default=None)
    parser.add_argument("--plot-only", action="store_true")
    args = parser.parse_args()

    if args.plot_only:
        make_plot(); return
    if args.index is not None:
        run_by_index(args.index); return
    if args.prog_idx is not None and args.n_gates is not None:
        run_one(args.prog_idx, args.n_gates, args.train_seed); return
    for pi, ng, ts in all_jobs():
        run_one(pi, ng, ts)
    make_plot()


if __name__ == "__main__":
    main()
