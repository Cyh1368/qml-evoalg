"""Frozen-original gate-insertion test on the evolved SU2-like L=3, P=2 circuit.

Counterpart to ``gate_insertion_frozen.py`` for the converged ShinkaEvolve
winner (the *Symmetry-grouped RX+RY rotations (SU2-like)* block). The protocol is
identical — only the per-block ansatz (the 11-param evolved block instead of the
9-param cemoid block) changes:

  1.  Train the base L=3,P=2 EA circuit to convergence -> an optimal solution
      for a given seed; save its 66 angles.
  2.  Freeze those angles.
  3.  Insert N extra single-qubit rotations (RX/RY/RZ) at random slots/wires,
      angles initialised to exactly 0 (a no-op, so the augmented circuit at init
      reproduces the base optimum exactly).
  4.  Optimize only the new gate angles (frozen) — plus a ``joint`` control in
      which the originals are also re-optimized from the base optimum.

Interpretation: extra angles staying ~0 with ΔAccuracy ~0 means the converged
optimum is "complete"; angles drifting with accuracy rising means the ansatz left
capacity on the table.

Usage:
  python gate_insertion_frozen_ea.py --build-base 3   # stage A: one base optimum
  python gate_insertion_frozen_ea.py --index 17       # stage B: one insertion job
  python gate_insertion_frozen_ea.py --plot-only      # figures + summary table
"""
from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pennylane as qml
from pennylane import numpy as pnp

import sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sweep import (  # noqa: E402
    N_QUBITS, FEATURE_SCALE,
    STEPS_PER_EPOCH, BATCH_SIZE, TRAIN_SIZE, VALIDATION_SIZE, TEST_SIZE,
    DATA_SEED, LEARNING_RATE, MAX_EPOCHS, PATIENCE, MIN_DELTA, WALL_BUDGET_SECONDS,
    _batch_indices, build_data_splits,
)
from sweep_ea import ea_block, N_EA_PARAMS  # noqa: E402

# ── experiment parameters (identical schedule to the cemoid frozen test) ────────
L, P = 3, 2
BASE_SEEDS = list(range(10))
N_GATES_SCHEDULE = [1, 2, 3, 5, 8, 13, 21]
CONDITIONS = ["frozen", "joint"]
POSITION_SEED_BASE = 1000

BASE_DIR = HERE / "base_optima_ea"
RESULTS_DIR = HERE / "gate_insertion_frozen_ea_results"
PLOT_PATH = HERE / "gate_insertion_frozen_ea_analysis.png"

_GATE_TYPES = ["RX", "RY", "RZ"]
_N_SLOTS = L * (1 + P) + 1   # 10 for L=3, P=2
_GATE_FN = {"RX": qml.RX, "RY": qml.RY, "RZ": qml.RZ}
_DEVICE = qml.device("default.qubit", wires=N_QUBITS, shots=None)


def _all_positions():
    return [(slot, wire, gt)
            for slot in range(_N_SLOTS) for wire in range(N_QUBITS) for gt in _GATE_TYPES]


ALL_POSITIONS = _all_positions()  # 10*9*3 = 270


def sample_positions(n_gates: int, config_seed: int):
    rng = np.random.default_rng(config_seed)
    idx = rng.choice(len(ALL_POSITIONS), size=n_gates, replace=False)
    return [ALL_POSITIONS[i] for i in sorted(idx)]


def feature_map(boards):
    for wire in range(N_QUBITS):
        qml.RX(FEATURE_SCALE * boards[:, wire], wires=wire)


def make_base_circuit():
    @qml.qnode(_DEVICE, interface="autograd", diff_method="backprop")
    def circuit(boards, params):
        bi = 0
        for _ in range(L):
            feature_map(boards)
            for _ in range(P):
                ea_block(params[bi]); bi += 1
        return [qml.expval(qml.PauliZ(w)) for w in range(N_QUBITS)]
    return circuit


def make_augmented_circuit(positions):
    slot_gates = defaultdict(list)
    for k, (slot, wire, gt) in enumerate(positions):
        slot_gates[slot].append((wire, gt, k))

    def _apply_extras(slot_id, extra):
        for wire, gt, k in slot_gates.get(slot_id, []):
            _GATE_FN[gt](extra[k], wires=wire)

    @qml.qnode(_DEVICE, interface="autograd", diff_method="backprop")
    def circuit(boards, block_params, extra):
        slot = 0; bi = 0
        for _ in range(L):
            _apply_extras(slot, extra); slot += 1
            feature_map(boards)
            for _ in range(P):
                _apply_extras(slot, extra); slot += 1
                ea_block(block_params[bi]); bi += 1
        _apply_extras(slot, extra)
        return [qml.expval(qml.PauliZ(w)) for w in range(N_QUBITS)]
    return circuit


def _class_exp_base(circuit, boards, params):
    z = pnp.stack(circuit(boards, params))
    return pnp.stack([(z[1]+z[3]+z[5]+z[7])/4.0, (z[0]+z[2]+z[4]+z[6])/4.0, z[8]], axis=1)


def _class_exp_aug(circuit, boards, cp, ea):
    z = pnp.stack(circuit(boards, cp, ea))
    return pnp.stack([(z[1]+z[3]+z[5]+z[7])/4.0, (z[0]+z[2]+z[4]+z[6])/4.0, z[8]], axis=1)


def base_loss(circuit, params, bx, by):
    return pnp.mean(pnp.sum((_class_exp_base(circuit, bx, params) - by) ** 2, axis=1))


def base_acc(circuit, params, bx, by_np):
    pred = np.asarray(_class_exp_base(circuit, bx, params), dtype=float)
    return float(np.mean(np.argmax(pred, axis=1) == np.argmax(by_np, axis=1)))


def aug_loss(circuit, cp, ea, bx, by):
    return pnp.mean(pnp.sum((_class_exp_aug(circuit, bx, cp, ea) - by) ** 2, axis=1))


def aug_acc(circuit, cp, ea, bx, by_np):
    pred = np.asarray(_class_exp_aug(circuit, bx, cp, ea), dtype=float)
    return float(np.mean(np.argmax(pred, axis=1) == np.argmax(by_np, axis=1)))


def _load_splits():
    s = build_data_splits(seed=DATA_SEED, train_size=TRAIN_SIZE,
                          validation_size=VALIDATION_SIZE, test_size=TEST_SIZE, replace=True)
    xtr, ytr, _ = s["train"]; xv, yv, _ = s["validation"]; xte, yte, _ = s["test"]
    return (pnp.array(xtr, dtype=float, requires_grad=False),
            pnp.array(ytr, dtype=float, requires_grad=False),
            pnp.array(xv, dtype=float, requires_grad=False),
            pnp.array(yv, dtype=float, requires_grad=False), np.asarray(yv, dtype=float),
            pnp.array(xte, dtype=float, requires_grad=False), np.asarray(yte, dtype=float))


# ── stage A: base optima ───────────────────────────────────────────────────────
def base_path(seed: int) -> Path:
    return BASE_DIR / f"seed_{seed:02d}.json"


def build_base(seed: int) -> dict:
    xtr, ytr, xv, yv, yv_np, xte, yte_np = _load_splits()
    circuit = make_base_circuit()
    n_blocks = L * P
    rng = np.random.default_rng(seed)
    params = pnp.array(rng.uniform(-0.05, 0.05, size=(n_blocks, N_EA_PARAMS)), requires_grad=True)
    opt = qml.AdamOptimizer(stepsize=LEARNING_RATE)
    best = float("inf"); best_p = params.copy(); best_ep = 0
    best_va = 0.0; best_ta = 0.0; noimp = 0; reason = "max_epochs"
    t0 = time.time(); epoch = 0
    for epoch in range(1, MAX_EPOCHS + 1):
        order = rng.permutation(len(xtr))
        for step in range(STEPS_PER_EPOCH):
            ids = _batch_indices(order, step, BATCH_SIZE)
            bx, by = xtr[ids], ytr[ids]
            params = opt.step(lambda p: base_loss(circuit, p, bx, by), params)
        vl = float(base_loss(circuit, params, xv, yv))
        if vl < best - MIN_DELTA:
            best = vl; best_p = params.copy(); best_ep = epoch
            best_va = base_acc(circuit, params, xv, yv_np)
            best_ta = base_acc(circuit, params, xte, yte_np); noimp = 0
        else:
            noimp += 1
            if noimp >= PATIENCE:
                reason = "early_stopping"; break
        if WALL_BUDGET_SECONDS and (time.time() - t0) > WALL_BUDGET_SECONDS:
            reason = "walltime"; break
    return {
        "seed": seed, "l": L, "p": P,
        "params": np.asarray(best_p, dtype=float).tolist(),
        "base_val_loss": best, "base_val_acc": best_va, "base_test_acc": best_ta,
        "best_epoch": best_ep, "stopped_epoch": epoch, "converged": reason == "early_stopping",
        "stop_reason": reason, "wall_seconds": time.time() - t0,
    }


def run_build_base(seed: int) -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    p = base_path(seed)
    if p.exists():
        print(f"base seed {seed} cached, skipping", flush=True); return
    print(f"building base optimum seed {seed}...", flush=True)
    r = build_base(seed)
    p.write_text(json.dumps(r, indent=2))
    print(f"base seed {seed} done: test_acc={r['base_test_acc']:.3f} "
          f"val_loss={r['base_val_loss']:.4f} epoch={r['best_epoch']} "
          f"converged={r['converged']}", flush=True)


# ── stage B: gate insertion (frozen / joint) ───────────────────────────────────
def insert_path(condition: str, n_gates: int, base_seed: int) -> Path:
    return RESULTS_DIR / condition / f"ng{n_gates:02d}_base{base_seed:02d}.json"


def run_insertion(condition: str, n_gates: int, base_seed: int) -> dict:
    base = json.loads(base_path(base_seed).read_text())
    base_params_np = np.asarray(base["params"], dtype=float)
    config_seed = POSITION_SEED_BASE + base_seed
    positions = sample_positions(n_gates, config_seed)
    circuit = make_augmented_circuit(positions)
    xtr, ytr, xv, yv, yv_np, xte, yte_np = _load_splits()
    rng = np.random.default_rng(base_seed)

    n_blocks = L * P
    n_block_flat = n_blocks * N_EA_PARAMS

    cp_frozen = pnp.array(base_params_np, requires_grad=False)
    base_val_loss = float(aug_loss(circuit, cp_frozen, pnp.zeros(n_gates), xv, yv))
    base_test_acc = aug_acc(circuit, cp_frozen, pnp.zeros(n_gates), xte, yte_np)
    base_val_acc = aug_acc(circuit, cp_frozen, pnp.zeros(n_gates), xv, yv_np)

    opt = qml.AdamOptimizer(stepsize=LEARNING_RATE)

    if condition == "frozen":
        extra = pnp.array(np.zeros(n_gates), requires_grad=True)
        best = base_val_loss
        best_extra = np.zeros(n_gates); best_ep = 0
        best_va = base_val_acc; best_ta = base_test_acc
        noimp = 0; reason = "max_epochs"; t0 = time.time(); epoch = 0
        for epoch in range(1, MAX_EPOCHS + 1):
            order = rng.permutation(len(xtr))
            for step in range(STEPS_PER_EPOCH):
                ids = _batch_indices(order, step, BATCH_SIZE)
                bx, by = xtr[ids], ytr[ids]
                extra = opt.step(lambda e: aug_loss(circuit, cp_frozen, e, bx, by), extra)
            vl = float(aug_loss(circuit, cp_frozen, extra, xv, yv))
            if vl < best - MIN_DELTA:
                best = vl; best_extra = np.asarray(extra, dtype=float).copy(); best_ep = epoch
                best_va = aug_acc(circuit, cp_frozen, extra, xv, yv_np)
                best_ta = aug_acc(circuit, cp_frozen, extra, xte, yte_np); noimp = 0
            else:
                noimp += 1
                if noimp >= PATIENCE:
                    reason = "early_stopping"; break
            if WALL_BUDGET_SECONDS and (time.time() - t0) > WALL_BUDGET_SECONDS:
                reason = "walltime"; break
        final_extra = best_extra.tolist()
        final_block_change = 0.0

    else:  # joint
        packed = pnp.array(np.concatenate([base_params_np.ravel(), np.zeros(n_gates)]),
                           requires_grad=True)

        def packed_loss(pk, bx, by):
            cp = pnp.reshape(pk[:n_block_flat], (n_blocks, N_EA_PARAMS))
            return aug_loss(circuit, cp, pk[n_block_flat:], bx, by)

        def unpack(pk):
            return (pnp.reshape(pk[:n_block_flat], (n_blocks, N_EA_PARAMS)),
                    pk[n_block_flat:])

        best = base_val_loss
        best_pk = np.asarray(packed, dtype=float).copy(); best_ep = 0
        best_va = base_val_acc; best_ta = base_test_acc
        noimp = 0; reason = "max_epochs"; t0 = time.time(); epoch = 0
        for epoch in range(1, MAX_EPOCHS + 1):
            order = rng.permutation(len(xtr))
            for step in range(STEPS_PER_EPOCH):
                ids = _batch_indices(order, step, BATCH_SIZE)
                bx, by = xtr[ids], ytr[ids]
                packed = opt.step(lambda p: packed_loss(p, bx, by), packed)
            cp, ea = unpack(packed)
            vl = float(aug_loss(circuit, cp, ea, xv, yv))
            if vl < best - MIN_DELTA:
                best = vl; best_pk = np.asarray(packed, dtype=float).copy(); best_ep = epoch
                best_va = aug_acc(circuit, cp, ea, xv, yv_np)
                best_ta = aug_acc(circuit, cp, ea, xte, yte_np); noimp = 0
            else:
                noimp += 1
                if noimp >= PATIENCE:
                    reason = "early_stopping"; break
            if WALL_BUDGET_SECONDS and (time.time() - t0) > WALL_BUDGET_SECONDS:
                reason = "walltime"; break
        final_extra = best_pk[n_block_flat:].tolist()
        final_block_change = float(np.mean(np.abs(best_pk[:n_block_flat] - base_params_np.ravel())))

    return {
        "condition": condition, "n_gates": n_gates, "base_seed": base_seed,
        "config_seed": config_seed, "positions": positions,
        "base_test_acc": base_test_acc, "base_val_acc": base_val_acc, "base_val_loss": base_val_loss,
        "final_test_accuracy": best_ta, "final_val_acc": best_va, "final_val_loss": best,
        "delta_test_acc": best_ta - base_test_acc,
        "delta_val_loss": best - base_val_loss,
        "final_extra_angles": final_extra,
        "final_extra_abs_mean": float(np.mean(np.abs(final_extra))),
        "final_extra_abs_max": float(np.max(np.abs(final_extra))),
        "block_abs_change_mean": final_block_change,
        "best_epoch": best_ep, "stopped_epoch": epoch, "converged": reason == "early_stopping",
        "stop_reason": reason, "wall_seconds": time.time() - t0,
    }


def all_jobs():
    return [(c, ng, bs) for c in CONDITIONS for ng in N_GATES_SCHEDULE for bs in BASE_SEEDS]


def run_index(i: int) -> None:
    js = all_jobs()
    if not 0 <= i < len(js):
        raise SystemExit(f"--index must be 0..{len(js)-1}")
    c, ng, bs = js[i]
    (RESULTS_DIR / c).mkdir(parents=True, exist_ok=True)
    p = insert_path(c, ng, bs)
    if p.exists():
        print(f"index {i}: {c} ng={ng} base={bs} cached, skipping", flush=True); return
    t0 = time.time()
    print(f"index {i}: {c} ng={ng} base={bs} training...", flush=True)
    r = run_insertion(c, ng, bs)
    p.write_text(json.dumps(r, indent=2))
    print(f"index {i}: {c} ng={ng} base={bs} done {time.time()-t0:.1f}s "
          f"acc={r['final_test_accuracy']:.3f} Δacc={r['delta_test_acc']:+.3f} "
          f"|θ|mean={r['final_extra_abs_mean']:.4f} stop@{r['stopped_epoch']}", flush=True)


def make_plot() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    recs = {c: defaultdict(list) for c in CONDITIONS}
    for c in CONDITIONS:
        for ng in N_GATES_SCHEDULE:
            for bs in BASE_SEEDS:
                p = insert_path(c, ng, bs)
                if p.exists():
                    recs[c][ng].append(json.loads(p.read_text()))
    bases = [json.loads(base_path(s).read_text()) for s in BASE_SEEDS if base_path(s).exists()]
    base_mean = float(np.mean([b["base_test_acc"] for b in bases])) if bases else None

    ngs = N_GATES_SCHEDULE
    xs = list(range(len(ngs)))
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    ax = axes[0]
    for c, col in [("frozen", "tab:blue"), ("joint", "tab:red")]:
        m = [np.mean([r["final_test_accuracy"] for r in recs[c][ng]]) for ng in ngs]
        s = [np.std([r["final_test_accuracy"] for r in recs[c][ng]]) for ng in ngs]
        ax.errorbar(xs, m, yerr=s, fmt="o-", color=col, capsize=4, label=f"{c} (mean±std, 10 bases)")
    if base_mean is not None:
        ax.axhline(base_mean, color="black", ls="--", lw=1.3, label=f"base optima (no gates, {base_mean:.3f})")
    ax.set_xticks(xs); ax.set_xticklabels(ngs); ax.set_xlabel("number of inserted gates")
    ax.set_ylabel("final test accuracy"); ax.set_title("EA SU2-like: accuracy vs. inserted gates")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax2 = axes[1]
    for c, col in [("frozen", "tab:blue"), ("joint", "tab:red")]:
        m = [np.mean([r["delta_test_acc"] for r in recs[c][ng]]) for ng in ngs]
        s = [np.std([r["delta_test_acc"] for r in recs[c][ng]]) for ng in ngs]
        ax2.errorbar(xs, m, yerr=s, fmt="s-", color=col, capsize=4, label=f"{c}")
    ax2.axhline(0, color="0.5", ls=":", lw=1)
    ax2.set_xticks(xs); ax2.set_xticklabels(ngs); ax2.set_xlabel("number of inserted gates")
    ax2.set_ylabel("Δ test accuracy vs. base optimum"); ax2.set_title("Improvement over the frozen optimum")
    ax2.legend(fontsize=8); ax2.grid(alpha=0.3)

    ax3 = axes[2]
    for c, col in [("frozen", "tab:blue"), ("joint", "tab:red")]:
        m, s = [], []
        for ng in ngs:
            vals = np.concatenate([np.abs(r["final_extra_angles"]) for r in recs[c][ng]]) if recs[c][ng] else np.array([0.0])
            m.append(vals.mean()); s.append(vals.std())
        ax3.errorbar(xs, m, yerr=s, fmt="^-", color=col, capsize=4, label=f"{c}")
    ax3.axhline(0, color="0.5", ls=":", lw=1)
    ax3.set_xticks(xs); ax3.set_xticklabels(ngs); ax3.set_xlabel("number of inserted gates")
    ax3.set_ylabel("mean |learned extra angle| (rad)"); ax3.set_title("How far the new gates move from no-op")
    ax3.legend(fontsize=8); ax3.grid(alpha=0.3)

    fig.tight_layout(); fig.savefig(PLOT_PATH, dpi=130)
    print(f"saved {PLOT_PATH}")

    print(f"\n{'cond':>7} {'ng':>3} {'n':>3} {'acc':>7} {'Δacc':>8} {'|θ|':>7} {'Δvalloss':>9}")
    for c in CONDITIONS:
        for ng in ngs:
            R = recs[c][ng]
            if not R:
                continue
            acc = np.mean([r["final_test_accuracy"] for r in R])
            dacc = np.mean([r["delta_test_acc"] for r in R])
            th = np.mean(np.concatenate([np.abs(r["final_extra_angles"]) for r in R]))
            dvl = np.mean([r["delta_val_loss"] for r in R])
            print(f"{c:>7} {ng:>3} {len(R):>3} {acc:>7.3f} {dacc:>+8.3f} {th:>7.4f} {dvl:>+9.4f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build-base", type=int, default=None)
    ap.add_argument("--index", type=int, default=None)
    ap.add_argument("--plot-only", action="store_true")
    a = ap.parse_args()
    if a.plot_only:
        make_plot()
    elif a.build_base is not None:
        run_build_base(a.build_base)
    elif a.index is not None:
        run_index(a.index)
    else:
        raise SystemExit("need --build-base SEED | --index I | --plot-only")


if __name__ == "__main__":
    main()
