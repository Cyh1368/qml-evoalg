"""Robustness analysis via random gate insertion into the L=3, P=2 cemoid circuit.

Hypothesis: if the trained L=3,P=2 solution is truly optimal, any extra rotation
gate (RX/RY/RZ) inserted anywhere in the circuit should converge to angle=0.
If the learned extra angles are NOT near zero, the landscape has other attractors.

Experiment design
-----------------
* Base circuit: L=3, P=2 cemoid (same as sweep.py).
* Extra gates: N randomly placed single-qubit rotations (RX/RY/RZ on a random
  wire), sampled via `config_seed`.  Their angles are *separate* trainable
  parameters, initialised to 0 (a perfect no-op start).
* Training seeds: 10 independent seeds control the *cemoid* parameter
  initialisation; extra-gate angles always start at 0.
* For each (N, config_seed, train_seed) triplet we record:
    - final test accuracy
    - final absolute angles of the inserted gates  (to detect non-zero drift)

Slot enumeration for L=3, P=2
-------------------------------
Within each of the 3 layers the segments are:
  [feature_map  cemoid_0  cemoid_1]
We define slots *between* segments (including before and after the layer):
  slot 0  – before feature_map of layer 0
  slot 1  – after  feature_map of layer 0  (before cemoid_0)
  slot 2  – after  cemoid_0 of layer 0      (before cemoid_1)
  slot 3  – after  cemoid_1 of layer 0      (= before layer 1 starts)
  slot 4  – before feature_map of layer 1
  ...
For L=3, P=2 this gives 3*(1+P)+1 = 10 slots.
Each slot can receive a gate on any of 9 qubits with any of 3 rotation types
→ 10 * 9 * 3 = 270 distinct positions.

Command-line usage
------------------
  # run one (n_gates, config_seed, train_seed) triplet:
  python gate_insertion.py --n-gates 3 --config-seed 0 --train-seed 5

  # plot results after all jobs finish:
  python gate_insertion.py --plot-only
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sweep import (  # noqa: E402
    N_QUBITS, CORNERS, EDGES, CENTER,
    OUTER_PAIRS, INNER_PAIRS, DIAG_PAIRS,
    FEATURE_SCALE, N_CEMOID_PARAMS,
    N_EPOCHS, STEPS_PER_EPOCH, BATCH_SIZE, TRAIN_SIZE, TEST_SIZE,
    DATA_SEED, LEARNING_RATE,
    _batch_indices,
)
from initial_program import build_data_splits  # noqa: E402

# ── experiment parameters ──────────────────────────────────────────────────────
L = 3
P = 2
N_TRAIN_SEEDS = 10
# How many extra gates to try (one config_seed per count, 10 train_seeds each)
N_GATES_SCHEDULE = [1, 2, 3, 5, 8, 13, 21]
CONFIG_SEED = 42          # fixed: same gate positions across all train_seeds

HERE = Path(__file__).resolve().parent
RESULTS_DIR = HERE / "gate_insertion_results"
PLOT_PATH   = HERE / "gate_insertion_analysis.png"

# ── slot / position enumeration ───────────────────────────────────────────────
_GATE_TYPES = ["RX", "RY", "RZ"]
_N_SLOTS    = L * (1 + P) + 1   # 10 for L=3, P=2

def _all_positions():
    """Return list of (slot, wire, gate_type) covering all 270 positions."""
    pos = []
    for slot in range(_N_SLOTS):
        for wire in range(N_QUBITS):
            for gt in _GATE_TYPES:
                pos.append((slot, wire, gt))
    return pos

ALL_POSITIONS = _all_positions()


def sample_positions(n_gates: int, config_seed: int):
    """Draw n_gates distinct positions without replacement."""
    rng = np.random.default_rng(config_seed)
    idx = rng.choice(len(ALL_POSITIONS), size=n_gates, replace=False)
    return [ALL_POSITIONS[i] for i in sorted(idx)]   # sorted by slot for readability


# ── circuit builder ───────────────────────────────────────────────────────────

def feature_map(boards):
    for wire in range(N_QUBITS):
        qml.RX(FEATURE_SCALE * boards[:, wire], wires=wire)


def cemoid_block(block_params):
    cx, cz, ex, ez, mx, mz, o, i, d = block_params
    for q in CORNERS:
        qml.RX(cx, wires=q); qml.RZ(cz, wires=q)
    for q in EDGES:
        qml.RX(ex, wires=q); qml.RZ(ez, wires=q)
    qml.RX(mx, wires=CENTER); qml.RZ(mz, wires=CENTER)
    for ctrl, tgt in OUTER_PAIRS:
        qml.CRY(o, wires=[ctrl, tgt])
    for ctrl, tgt in INNER_PAIRS:
        qml.CRY(i, wires=[ctrl, tgt])
    for ctrl, tgt in DIAG_PAIRS:
        qml.CRY(d, wires=[ctrl, tgt])


_GATE_FN = {"RX": qml.RX, "RY": qml.RY, "RZ": qml.RZ}

_DEVICE = qml.device("default.qubit", wires=N_QUBITS, shots=None)


def make_augmented_circuit(positions):
    """Build a QNode that has the base L=3,P=2 circuit + extra gates at `positions`.

    Args
        positions: list of (slot, wire, gate_type) from sample_positions()

    The QNode signature is circuit(boards, cemoid_params, extra_angles):
        cemoid_params : shape (L*P, 9)
        extra_angles  : shape (n_gates,)
    """
    # Build a lookup: slot_id -> list of (wire, gate_type, extra_param_index)
    from collections import defaultdict
    slot_gates: dict[int, list] = defaultdict(list)
    for k, (slot, wire, gt) in enumerate(positions):
        slot_gates[slot].append((wire, gt, k))

    def _apply_extras(slot_id, extra_angles):
        for wire, gt, k in slot_gates.get(slot_id, []):
            _GATE_FN[gt](extra_angles[k], wires=wire)

    @qml.qnode(_DEVICE, interface="autograd", diff_method="backprop")
    def circuit(boards, cemoid_params, extra_angles):
        slot = 0
        block_index = 0
        for _layer in range(L):
            _apply_extras(slot, extra_angles); slot += 1
            feature_map(boards)
            for _rep in range(P):
                _apply_extras(slot, extra_angles); slot += 1
                cemoid_block(cemoid_params[block_index])
                block_index += 1
        _apply_extras(slot, extra_angles)   # final slot after last layer
        return [qml.expval(qml.PauliZ(w)) for w in range(N_QUBITS)]

    return circuit


# ── training ──────────────────────────────────────────────────────────────────

def class_expectations(circuit, boards, cemoid_params, extra_angles):
    z = pnp.stack(circuit(boards, cemoid_params, extra_angles))  # (9, B)
    cross  = (z[1] + z[3] + z[5] + z[7]) / 4.0
    circle = (z[0] + z[2] + z[4] + z[6]) / 4.0
    draw   = z[8]
    return pnp.stack([cross, circle, draw], axis=1)   # (B, 3)


def l2_loss(circuit, cemoid_params, extra_angles, boards, targets):
    pred = class_expectations(circuit, boards, cemoid_params, extra_angles)
    return pnp.mean(pnp.sum((pred - targets) ** 2, axis=1))


def accuracy_fn(circuit, cemoid_params, extra_angles, boards, targets_np) -> float:
    pred = np.asarray(class_expectations(circuit, boards, cemoid_params, extra_angles), dtype=float)
    return float(np.mean(np.argmax(pred, axis=1) == np.argmax(targets_np, axis=1)))


def train(n_gates: int, config_seed: int, train_seed: int) -> dict:
    positions = sample_positions(n_gates, config_seed)
    circuit   = make_augmented_circuit(positions)

    splits = build_data_splits(
        seed=DATA_SEED, train_size=TRAIN_SIZE,
        validation_size=300, test_size=TEST_SIZE, replace=True,
    )
    x_train, y_train, _ = splits["train"]
    x_test,  y_test,  _ = splits["test"]
    x_train = pnp.array(x_train, dtype=float, requires_grad=False)
    y_train = pnp.array(y_train, dtype=float, requires_grad=False)
    x_test  = pnp.array(x_test,  dtype=float, requires_grad=False)
    y_test_np = np.asarray(y_test, dtype=float)

    n_blocks = L * P
    rng = np.random.default_rng(train_seed)
    cemoid_params = pnp.array(
        rng.uniform(-0.05, 0.05, size=(n_blocks, N_CEMOID_PARAMS)),
        requires_grad=True,
    )
    # Extra gates start at exactly 0 (perfect no-op)
    extra_angles = pnp.array(np.zeros(n_gates), requires_grad=True)

    optimizer = qml.AdamOptimizer(stepsize=LEARNING_RATE)

    # Pack both parameter arrays into one flat vector so AdamOptimizer.step
    # can jointly optimise them, then unpack after each step.
    n_cemoid_flat = n_blocks * N_CEMOID_PARAMS

    def packed_loss(packed, bx, by):
        cp = pnp.reshape(packed[:n_cemoid_flat], (n_blocks, N_CEMOID_PARAMS))
        ea = packed[n_cemoid_flat:]
        return l2_loss(circuit, cp, ea, bx, by)

    packed = pnp.array(
        np.concatenate([np.asarray(cemoid_params).ravel(), np.zeros(n_gates)]),
        requires_grad=True,
    )

    test_acc_history = []
    for epoch in range(1, N_EPOCHS + 1):
        order = rng.permutation(len(x_train))
        for step in range(STEPS_PER_EPOCH):
            ids = _batch_indices(order, step, BATCH_SIZE)
            bx, by = x_train[ids], y_train[ids]
            packed = optimizer.step(lambda p: packed_loss(p, bx, by), packed)
        cemoid_params = pnp.reshape(packed[:n_cemoid_flat], (n_blocks, N_CEMOID_PARAMS))
        extra_angles  = packed[n_cemoid_flat:]
        acc = accuracy_fn(circuit, cemoid_params, extra_angles, x_test, y_test_np)
        test_acc_history.append(acc)

    cemoid_params = pnp.reshape(packed[:n_cemoid_flat], (n_blocks, N_CEMOID_PARAMS))
    extra_angles  = packed[n_cemoid_flat:]

    final_extra = np.asarray(extra_angles, dtype=float).tolist()
    return {
        "n_gates":          n_gates,
        "config_seed":      config_seed,
        "train_seed":       train_seed,
        "positions":        positions,
        "final_extra_angles": final_extra,
        "final_extra_abs_mean": float(np.mean(np.abs(final_extra))),
        "test_acc_history": test_acc_history,
        "final_test_accuracy": test_acc_history[-1],
    }


# ── I/O helpers ───────────────────────────────────────────────────────────────

def result_path(n_gates: int, config_seed: int, train_seed: int) -> Path:
    return RESULTS_DIR / f"ng{n_gates:02d}_cs{config_seed:03d}_ts{train_seed:02d}.json"


def run_one(n_gates: int, config_seed: int, train_seed: int) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = result_path(n_gates, config_seed, train_seed)
    if path.exists():
        print(f"cached — skipping ng={n_gates} cs={config_seed} ts={train_seed}", flush=True)
        return
    t0 = time.time()
    print(f"training ng={n_gates} cs={config_seed} ts={train_seed}...", flush=True)
    result = train(n_gates, config_seed, train_seed)
    path.write_text(json.dumps(result, indent=2))
    print(
        f"done in {time.time()-t0:.1f}s  "
        f"acc={result['final_test_accuracy']:.3f}  "
        f"mean|extra|={result['final_extra_abs_mean']:.4f}",
        flush=True,
    )


# ── flat job list for SLURM array ─────────────────────────────────────────────

def all_jobs():
    """Ordered list of (n_gates, config_seed, train_seed) for the SLURM array."""
    jobs = []
    for ng in N_GATES_SCHEDULE:
        for ts in range(N_TRAIN_SEEDS):
            jobs.append((ng, CONFIG_SEED, ts))
    return jobs


def run_by_index(index: int) -> None:
    jobs = all_jobs()
    if not 0 <= index < len(jobs):
        raise SystemExit(f"--index must be in [0, {len(jobs)-1}], got {index}")
    ng, cs, ts = jobs[index]
    run_one(ng, cs, ts)


# ── plotting ──────────────────────────────────────────────────────────────────

def make_plot() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    records = []
    for ng in N_GATES_SCHEDULE:
        for ts in range(N_TRAIN_SEEDS):
            p = result_path(ng, CONFIG_SEED, ts)
            if p.exists():
                records.append(json.loads(p.read_text()))

    if not records:
        print("No results found yet."); return

    from collections import defaultdict
    by_ng: dict[int, list] = defaultdict(list)
    by_ng_angles: dict[int, list] = defaultdict(list)
    for r in records:
        by_ng[r["n_gates"]].append(r["final_test_accuracy"])
        by_ng_angles[r["n_gates"]].extend(np.abs(r["final_extra_angles"]).tolist())

    ngs      = sorted(by_ng)
    means    = [np.mean(by_ng[ng])       for ng in ngs]
    stds     = [np.std(by_ng[ng])        for ng in ngs]
    angle_means = [np.mean(by_ng_angles[ng]) for ng in ngs]
    angle_stds  = [np.std(by_ng_angles[ng])  for ng in ngs]

    # ── baseline: L=3, P=2 with no extra gates (from robustness_histories)
    baseline_accs = []
    rh = HERE / "robustness_histories"
    if rh.exists():
        import glob
        for f in glob.glob(str(rh / "seed_*.json")):
            d = json.loads(Path(f).read_text())
            baseline_accs.append(d["final_test_accuracy"])
    baseline_mean = np.mean(baseline_accs) if baseline_accs else None

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)

    # Top: accuracy vs n_extra_gates
    xs = list(range(len(ngs)))
    ax1.errorbar(xs, means, yerr=stds, fmt="o-", color="C0",
                 capsize=4, linewidth=1.5, label="mean ± std (10 seeds)")
    if baseline_mean is not None:
        ax1.axhline(baseline_mean, color="C1", linestyle="--", linewidth=1.4,
                    label=f"baseline (no extra gates, mean={baseline_mean:.3f})")
    ax1.set_ylabel("Final test accuracy")
    ax1.set_title("Gate-insertion robustness — L=3, P=2 cemoid")
    ax1.legend(fontsize=9)
    ax1.set_xticks(xs)
    ax1.set_xticklabels(ngs)
    ax1.set_ylim(0.4, 1.0)

    # Bottom: mean |extra angle| vs n_extra_gates
    ax2.errorbar(xs, angle_means, yerr=angle_stds, fmt="s-", color="C2",
                 capsize=4, linewidth=1.5, label="mean |θ_extra| ± std")
    ax2.axhline(0, color="0.6", linewidth=0.8, linestyle=":")
    ax2.set_xlabel("Number of inserted extra gates")
    ax2.set_ylabel("Mean |extra gate angle| (rad)")
    ax2.legend(fontsize=9)
    ax2.set_xticks(xs)
    ax2.set_xticklabels(ngs)

    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=150)
    print(f"Saved plot: {PLOT_PATH}")

    # Print summary table
    print(f"\n{'n_gates':>8}  {'n_done':>6}  {'acc_mean':>9}  {'acc_std':>8}  {'|θ|_mean':>9}")
    for ng in ngs:
        n_done = len(by_ng[ng])
        print(f"{ng:>8}  {n_done:>6}  {np.mean(by_ng[ng]):>9.3f}  "
              f"{np.std(by_ng[ng]):>8.3f}  {np.mean(by_ng_angles[ng]):>9.4f}")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-gates",     type=int, default=None)
    parser.add_argument("--config-seed", type=int, default=CONFIG_SEED)
    parser.add_argument("--train-seed",  type=int, default=0)
    parser.add_argument("--index",       type=int, default=None,
                        help="SLURM array index into all_jobs()")
    parser.add_argument("--plot-only",   action="store_true")
    args = parser.parse_args()

    if args.plot_only:
        make_plot(); return
    if args.index is not None:
        run_by_index(args.index); return
    if args.n_gates is not None:
        run_one(args.n_gates, args.config_seed, args.train_seed); return
    # Local sequential fallback
    for ng, cs, ts in all_jobs():
        run_one(ng, cs, ts)
    make_plot()


if __name__ == "__main__":
    main()
