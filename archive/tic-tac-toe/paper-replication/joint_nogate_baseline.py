"""Joint no-gate baseline: overfitting-artifact control for gate_insertion_frozen.py.

The ``joint`` condition in gate_insertion_frozen.py shows a small accuracy/parameter
drift when gates are inserted and the 54 original cemoid angles are also retrained
starting from the converged base optimum. This script isolates whether that drift is
caused by the inserted gates, or is merely an artifact of training the originals for
MORE epochs (overfitting past the point the base-optimum early-stopping run reached).

For each base seed: load the converged base optimum's 54 params, unfreeze them,
insert ZERO gates, and retrain with the SAME Adam + early-stopping protocol used by
``build_base``/the joint branch of ``run_insertion``. If this ``joint_nogate``
baseline drifts (Δacc, Δval-loss, param movement) about as much as the real ``joint``
insertion runs, the drift is a training artifact rather than a gate effect.

Usage
-----
  python joint_nogate_baseline.py --index 3      # base_seed = BASE_SEEDS[3]
  python joint_nogate_baseline.py --plot-only     # comparison table
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pennylane as qml
from pennylane import numpy as pnp

from gate_insertion_frozen import (  # noqa: E402
    make_base_circuit, base_loss, base_acc, _load_splits, base_path,
    L, P, BASE_SEEDS,
    N_CEMOID_PARAMS,
    STEPS_PER_EPOCH, BATCH_SIZE, LEARNING_RATE, MAX_EPOCHS, PATIENCE, MIN_DELTA,
    WALL_BUDGET_SECONDS, _batch_indices,
)

HERE = Path(__file__).resolve().parent
RESULTS_DIR = HERE / "joint_nogate_results"


def result_path(base_seed: int) -> Path:
    return RESULTS_DIR / f"base_{base_seed:02d}.json"


def run_joint_nogate(base_seed: int) -> dict:
    base = json.loads(base_path(base_seed).read_text())
    base_params_np = np.asarray(base["params"], dtype=float)
    n_blocks = L * P

    circuit = make_base_circuit()
    xtr, ytr, xv, yv, yv_np, xte, yte_np = _load_splits()
    rng = np.random.default_rng(base_seed)  # drives minibatch order only

    # Starting point == the base optimum exactly, now trainable.
    params = pnp.array(base_params_np, requires_grad=True)
    base_val_loss = float(base_loss(circuit, params, xv, yv))
    base_val_acc = base_acc(circuit, params, xv, yv_np)
    base_test_acc = base_acc(circuit, params, xte, yte_np)

    opt = qml.AdamOptimizer(stepsize=LEARNING_RATE)
    best = base_val_loss
    best_p = np.asarray(params, dtype=float).copy(); best_ep = 0
    best_va = base_val_acc; best_ta = base_test_acc
    noimp = 0; reason = "max_epochs"; t0 = time.time(); epoch = 0
    for epoch in range(1, MAX_EPOCHS + 1):
        order = rng.permutation(len(xtr))
        for step in range(STEPS_PER_EPOCH):
            ids = _batch_indices(order, step, BATCH_SIZE)
            bx, by = xtr[ids], ytr[ids]
            params = opt.step(lambda p: base_loss(circuit, p, bx, by), params)
        vl = float(base_loss(circuit, params, xv, yv))
        if vl < best - MIN_DELTA:
            best = vl; best_p = np.asarray(params, dtype=float).copy(); best_ep = epoch
            best_va = base_acc(circuit, params, xv, yv_np)
            best_ta = base_acc(circuit, params, xte, yte_np); noimp = 0
        else:
            noimp += 1
            if noimp >= PATIENCE:
                reason = "early_stopping"; break
        if WALL_BUDGET_SECONDS and (time.time() - t0) > WALL_BUDGET_SECONDS:
            reason = "walltime"; break

    param_abs_change_mean = float(np.mean(np.abs(best_p.ravel() - base_params_np.ravel())))

    return {
        "base_seed": base_seed, "l": L, "p": P,
        "base_val_loss": base_val_loss, "base_val_acc": base_val_acc, "base_test_acc": base_test_acc,
        "final_val_loss": best, "final_val_acc": best_va, "final_test_accuracy": best_ta,
        "delta_test_acc": best_ta - base_test_acc,
        "delta_val_loss": best - base_val_loss,
        "param_abs_change_mean": param_abs_change_mean,
        "best_epoch": best_ep, "stopped_epoch": epoch, "converged": reason == "early_stopping",
        "stop_reason": reason, "wall_seconds": time.time() - t0,
    }


def run_index(i: int) -> None:
    if not 0 <= i < len(BASE_SEEDS):
        raise SystemExit(f"--index must be 0..{len(BASE_SEEDS)-1}")
    bs = BASE_SEEDS[i]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    p = result_path(bs)
    if p.exists():
        print(f"index {i}: base={bs} cached, skipping", flush=True); return
    t0 = time.time()
    print(f"index {i}: base={bs} training (joint, no gates)...", flush=True)
    r = run_joint_nogate(bs)
    p.write_text(json.dumps(r, indent=2))
    print(f"index {i}: base={bs} done {time.time()-t0:.1f}s "
          f"acc={r['final_test_accuracy']:.3f} Δacc={r['delta_test_acc']:+.3f} "
          f"|Δθ|mean={r['param_abs_change_mean']:.4f} stop@{r['stopped_epoch']}", flush=True)


def make_plot() -> None:
    recs = []
    for bs in BASE_SEEDS:
        p = result_path(bs)
        if p.exists():
            recs.append(json.loads(p.read_text()))

    if not recs:
        print("no joint_nogate results found yet — nothing to summarize.")
        return

    dacc = np.array([r["delta_test_acc"] for r in recs])
    dvl = np.array([r["delta_val_loss"] for r in recs])
    dth = np.array([r["param_abs_change_mean"] for r in recs])

    print(f"\njoint_nogate baseline: {len(recs)}/{len(BASE_SEEDS)} base seeds")
    print(f"{'metric':>22} {'mean':>9} {'std':>9}")
    print(f"{'delta_test_acc':>22} {dacc.mean():>+9.4f} {dacc.std():>9.4f}")
    print(f"{'delta_val_loss':>22} {dvl.mean():>+9.4f} {dvl.std():>9.4f}")
    print(f"{'param_abs_change_mean':>22} {dth.mean():>9.4f} {dth.std():>9.4f}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(5, 4))
        ax.bar(["Δtest_acc", "Δval_loss", "|Δθ|_mean"],
               [dacc.mean(), dvl.mean(), dth.mean()],
               yerr=[dacc.std(), dvl.std(), dth.std()], capsize=4, color="tab:gray")
        ax.axhline(0, color="0.5", ls=":", lw=1)
        ax.set_title("joint_nogate baseline (no inserted gates)")
        fig.tight_layout()
        out = HERE / "joint_nogate_analysis.png"
        fig.savefig(out, dpi=130)
        print(f"saved {out}")
    except Exception as e:  # pragma: no cover - plotting is best-effort
        print(f"(plot skipped: {e})")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--index", type=int, default=None)
    ap.add_argument("--plot-only", action="store_true")
    a = ap.parse_args()
    if a.plot_only:
        make_plot()
    elif a.index is not None:
        run_index(a.index)
    else:
        raise SystemExit("need --index I | --plot-only")


if __name__ == "__main__":
    main()
