"""Training-set-size sweep for cemoid and evolved (SU2-like) ansatzes at L=3, P=2.

Purpose: put our circuits on the same axes as the two external references —
Meyer et al. (arXiv 2205.06217) and Baumann & Linnhoff-Popien (arXiv
2606.20316) report test accuracy vs. TRAINING-SET SIZE over
{30, 60, 120, 240, 450, 600} examples with a fixed 600-board test set. All our
converged-protocol results so far are single points at train_size = 450.

Design: model in {cemoid (54p), ea (66p)} x train_size in
{30, 60, 120, 240, 450, 600} x 20 seeds = 240 jobs. Validation (300) and test
(600) splits stay fixed at the repo convention (DATA_SEED 2027); only the
training split size varies. Converged protocol (val-loss early stopping,
patience 75, restore-best-weights, 1000-epoch cap).

Comparability note: external baselines at 600 training examples — Meyer
edge/D4 ~0.69, Baumann edge+lines/D4 ~0.80 (their splits/protocols differ in
detail; treat as reference curves, not exact controls).

Usage
-----
  python train_size_sweep.py --index I     # one job (SLURM array, I in 0..239)
  python train_size_sweep.py --analyze     # summary table + figure
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
    STEPS_PER_EPOCH, BATCH_SIZE, VALIDATION_SIZE, TEST_SIZE, DATA_SEED,
    LEARNING_RATE, MAX_EPOCHS, PATIENCE, MIN_DELTA, WALL_BUDGET_SECONDS,
    N_CEMOID_PARAMS, _batch_indices, build_data_splits,
    make_circuit as make_cemoid_circuit, l2_loss, accuracy,
)
from sweep_ea import make_circuit as make_ea_circuit, N_EA_PARAMS  # noqa: E402

# ── experiment parameters ──────────────────────────────────────────────────────
L, P = 3, 2
N_BLOCKS = L * P
TRAIN_SIZES = [30, 60, 120, 240, 450, 600]
SEEDS = list(range(20))
MODELS = {
    "cemoid": (make_cemoid_circuit, N_CEMOID_PARAMS),
    "ea": (make_ea_circuit, N_EA_PARAMS),
}

RESULTS_DIR = HERE / "train_size_results"
PLOT_PATH = HERE / "train_size_sweep.png"

# External reference points at 600 training examples (see docstring caveat).
EXTERNAL_REFS = {
    "Meyer edge/D4 (@600)": 0.69,
    "Baumann edge+lines/D4 (@600)": 0.80,
}


def _load_splits_sized(train_size: int):
    s = build_data_splits(seed=DATA_SEED, train_size=train_size,
                          validation_size=VALIDATION_SIZE, test_size=TEST_SIZE,
                          replace=True)
    xtr, ytr, _ = s["train"]; xv, yv, _ = s["validation"]; xte, yte, _ = s["test"]
    return (pnp.array(xtr, dtype=float, requires_grad=False),
            pnp.array(ytr, dtype=float, requires_grad=False),
            pnp.array(xv, dtype=float, requires_grad=False),
            pnp.array(yv, dtype=float, requires_grad=False), np.asarray(yv, dtype=float),
            pnp.array(xte, dtype=float, requires_grad=False), np.asarray(yte, dtype=float))


def run_training(model: str, train_size: int, seed: int) -> dict:
    make, n_block_params = MODELS[model]
    circuit = make(L, P)
    xtr, ytr, xv, yv, yv_np, xte, yte_np = _load_splits_sized(train_size)

    rng = np.random.default_rng(seed)
    params = pnp.array(
        rng.uniform(-0.05, 0.05, size=(N_BLOCKS, n_block_params)), requires_grad=True)
    opt = qml.AdamOptimizer(stepsize=LEARNING_RATE)

    best = float("inf"); best_p = params.copy(); best_ep = 0
    best_va = 0.0; best_ta = 0.0; best_tra = 0.0
    noimp = 0; reason = "max_epochs"; t0 = time.time(); epoch = 0
    for epoch in range(1, MAX_EPOCHS + 1):
        order = rng.permutation(len(xtr))
        for step in range(STEPS_PER_EPOCH):
            ids = _batch_indices(order, step, BATCH_SIZE)
            bx, by = xtr[ids], ytr[ids]
            params = opt.step(lambda p: l2_loss(circuit, p, bx, by), params)
        vl = float(l2_loss(circuit, params, xv, yv))
        if vl < best - MIN_DELTA:
            best = vl; best_p = params.copy(); best_ep = epoch
            best_va = accuracy(circuit, params, xv, yv_np)
            best_ta = accuracy(circuit, params, xte, yte_np)
            best_tra = accuracy(circuit, params, xtr, np.asarray(ytr, dtype=float))
            noimp = 0
        else:
            noimp += 1
            if noimp >= PATIENCE:
                reason = "early_stopping"; break
        if WALL_BUDGET_SECONDS and (time.time() - t0) > WALL_BUDGET_SECONDS:
            reason = "walltime"; break

    return {
        "model": model, "train_size": train_size, "seed": seed,
        "n_params": N_BLOCKS * MODELS[model][1],
        "final_val_loss": best, "final_val_acc": best_va,
        "final_test_accuracy": best_ta, "final_train_accuracy": best_tra,
        "generalization_gap": best_tra - best_ta,
        "best_epoch": best_ep, "stopped_epoch": epoch,
        "converged": reason == "early_stopping", "stop_reason": reason,
        "wall_seconds": time.time() - t0,
    }


# ── job indexing for SLURM ─────────────────────────────────────────────────────
def all_jobs():
    return [(m, ts, s) for m in MODELS for ts in TRAIN_SIZES for s in SEEDS]


def job_path(model: str, train_size: int, seed: int) -> Path:
    return RESULTS_DIR / model / f"ts{train_size:03d}_seed{seed:02d}.json"


def run_index(i: int) -> None:
    js = all_jobs()
    if not 0 <= i < len(js):
        raise SystemExit(f"--index must be 0..{len(js)-1}")
    m, ts, s = js[i]
    p = job_path(m, ts, s)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        print(f"index {i}: {m} ts={ts} seed={s} cached, skipping", flush=True); return
    t0 = time.time()
    print(f"index {i}: {m} ts={ts} seed={s} training...", flush=True)
    r = run_training(m, ts, s)
    p.write_text(json.dumps(r, indent=2))
    print(f"index {i}: {m} ts={ts} seed={s} done {time.time()-t0:.1f}s "
          f"acc={r['final_test_accuracy']:.3f} gap={r['generalization_gap']:+.3f} "
          f"stop@{r['stopped_epoch']} ({r['stop_reason']})", flush=True)


# ── analysis ───────────────────────────────────────────────────────────────────
def analyze() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    recs = {m: {ts: [] for ts in TRAIN_SIZES} for m in MODELS}
    for m in MODELS:
        for ts in TRAIN_SIZES:
            for s in SEEDS:
                p = job_path(m, ts, s)
                if p.exists():
                    recs[m][ts].append(json.loads(p.read_text()))

    print(f"{'model':>8} {'ts':>4} {'n':>3} {'test acc':>16} {'gap':>7}")
    for m in MODELS:
        for ts in TRAIN_SIZES:
            R = recs[m][ts]
            if not R:
                continue
            a = np.array([r["final_test_accuracy"] for r in R])
            g = np.mean([r["generalization_gap"] for r in R])
            print(f"{m:>8} {ts:>4} {len(R):>3} {a.mean():>7.3f} +/- {a.std():5.3f} {g:>+7.3f}")

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for m, col in [("cemoid", "tab:blue"), ("ea", "tab:red")]:
        xs, mu, sd = [], [], []
        for ts in TRAIN_SIZES:
            R = recs[m][ts]
            if R:
                xs.append(ts)
                a = np.array([r["final_test_accuracy"] for r in R])
                mu.append(a.mean()); sd.append(a.std())
        if xs:
            ax.errorbar(xs, mu, yerr=sd, fmt="o-", color=col, capsize=4,
                        label=f"{m} (L={L}, P={P})")
    for label, y in EXTERNAL_REFS.items():
        ax.axhline(y, ls=":", lw=1, color="0.4")
        ax.annotate(label, (TRAIN_SIZES[0], y), fontsize=7, va="bottom")
    ax.set_xscale("log"); ax.set_xticks(TRAIN_SIZES); ax.set_xticklabels(TRAIN_SIZES)
    ax.set_xlabel("training examples"); ax.set_ylabel("test accuracy (mean ± std, 20 seeds)")
    ax.set_title("Accuracy vs. training-set size (converged protocol)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(PLOT_PATH, dpi=130)
    print(f"saved {PLOT_PATH}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--index", type=int, default=None)
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--list-jobs", action="store_true")
    a = ap.parse_args()
    if a.analyze:
        analyze()
    elif a.list_jobs:
        js = all_jobs()
        print(f"{len(js)} jobs")
    elif a.index is not None:
        run_index(a.index)
    else:
        raise SystemExit("need --index I | --analyze | --list-jobs")


if __name__ == "__main__":
    main()
