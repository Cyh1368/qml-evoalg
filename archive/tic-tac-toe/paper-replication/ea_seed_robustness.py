"""Seed robustness for the top-3 EA-evolved circuits.

Re-runs each EA program with 50 independent parameter-initialisation seeds
(data split fixed at DATA_SEED=2027), recording final test accuracy per seed.
Produces a histogram comparison across programs and vs. the cemoid baseline.

Usage:
    python ea_seed_robustness.py --prog-idx 0 --seed 7   # one SLURM task
    python ea_seed_robustness.py --plot-only              # after all jobs finish
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE     = Path(__file__).resolve().parent
PROG_DIR = HERE / "ea_programs"
RESULTS_DIR = HERE / "ea_robustness_histories"
PLOT_PATH   = HERE / "ea_fig1_seed_distribution.png"
MANIFEST    = json.loads((PROG_DIR / "manifest.json").read_text())

N_SEEDS = 25
DATA_SEED = 2027


def _load_program(prog_idx: int):
    """Import an EA program module in isolation and return its run_experiment fn."""
    info = MANIFEST[prog_idx]
    path = PROG_DIR / f"prog_{info['short_id']}.py"
    spec = importlib.util.spec_from_file_location(f"ea_prog_{prog_idx}", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run_experiment, info


def result_path(prog_idx: int, seed: int) -> Path:
    info = MANIFEST[prog_idx]
    return RESULTS_DIR / f"prog{prog_idx}_{info['short_id']}_seed{seed:03d}.json"


def run_one(prog_idx: int, seed: int) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = result_path(prog_idx, seed)
    if path.exists():
        print(f"cached prog={prog_idx} seed={seed}", flush=True)
        return
    run_experiment, info = _load_program(prog_idx)
    t0 = time.time()
    print(f"training prog={prog_idx} ({info['short_id']}) seed={seed}...", flush=True)
    result = run_experiment(seed=seed, data_seed=DATA_SEED, verbose=False)
    out = {
        "prog_idx":   prog_idx,
        "prog_id":    info["id"],
        "short_id":   info["short_id"],
        "seed":       seed,
        "test_accuracy":  result["test_accuracy"],
        "val_accuracy":   result["validation_accuracy"],
        "train_accuracy": result["train_accuracy"],
        "n_params":       result["n_params"],
    }
    path.write_text(json.dumps(out, indent=2))
    print(f"done {time.time()-t0:.1f}s  test={result['test_accuracy']:.3f}", flush=True)


def all_jobs():
    return [(pi, s) for pi in range(len(MANIFEST)) for s in range(N_SEEDS)]


def run_by_index(index: int) -> None:
    jobs = all_jobs()
    if not 0 <= index < len(jobs):
        raise SystemExit(f"--index must be 0..{len(jobs)-1}")
    run_one(*jobs[index])


def make_plot() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Load cemoid baseline
    baseline_accs = [
        json.loads(p.read_text())["final_test_accuracy"]
        for p in sorted((HERE / "robustness_histories").glob("seed_*.json"))
    ]
    baseline_mean = np.mean(baseline_accs)
    baseline_std  = np.std(baseline_accs)

    colors = ["#2196F3", "#4CAF50", "#FF9800"]
    fig, axes = plt.subplots(1, len(MANIFEST) + 1, figsize=(14, 4.5), sharey=False)

    # Cemoid baseline panel
    ax0 = axes[0]
    ax0.hist(baseline_accs, bins=14, color="#9E9E9E", edgecolor="white")
    ax0.axvline(baseline_mean, color="#616161", lw=1.8, ls="--",
                label=f"mean={baseline_mean:.3f}")
    ax0.set_title("Cemoid L=3,P=2\n(baseline, n=50)", fontsize=9)
    ax0.set_xlabel("Test accuracy"); ax0.set_ylabel("Count")
    ax0.legend(fontsize=8)

    for pi, info in enumerate(MANIFEST):
        accs = []
        missing = 0
        for s in range(N_SEEDS):
            p = result_path(pi, s)
            if p.exists():
                accs.append(json.loads(p.read_text())["test_accuracy"])
            else:
                missing += 1
        ax = axes[pi + 1]
        if accs:
            mu, sd = np.mean(accs), np.std(accs)
            ax.hist(accs, bins=14, color=colors[pi], edgecolor="white", alpha=0.85)
            ax.axvline(mu, color=colors[pi], lw=1.8, ls="--", label=f"mean={mu:.3f}")
            ax.axvline(baseline_mean, color="#9E9E9E", lw=1.2, ls=":",
                       label=f"cemoid={baseline_mean:.3f}")
        title = (f"EA prog #{pi+1}\n(gen {info['generation']}, "
                 f"n={len(accs)}{f', {missing} missing' if missing else ''})")
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("Test accuracy")
        ax.legend(fontsize=8)

    fig.suptitle("Seed robustness: EA-evolved circuits vs. cemoid baseline\n"
                 "50 random parameter initialisations, fixed data split", fontsize=11)
    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=150)
    print(f"Saved {PLOT_PATH}")

    print(f"\n{'prog':>6}  {'n':>4}  {'mean':>7}  {'std':>6}  {'min':>6}  {'max':>6}")
    print(f"{'cemoid':>6}  {len(baseline_accs):>4}  {baseline_mean:>7.3f}  "
          f"{baseline_std:>6.3f}  {np.min(baseline_accs):>6.3f}  {np.max(baseline_accs):>6.3f}")
    for pi, info in enumerate(MANIFEST):
        accs = [json.loads(result_path(pi, s).read_text())["test_accuracy"]
                for s in range(N_SEEDS) if result_path(pi, s).exists()]
        if accs:
            print(f"{'ea#'+str(pi+1):>6}  {len(accs):>4}  {np.mean(accs):>7.3f}  "
                  f"{np.std(accs):>6.3f}  {np.min(accs):>6.3f}  {np.max(accs):>6.3f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prog-idx", type=int, default=None)
    parser.add_argument("--seed",     type=int, default=0)
    parser.add_argument("--index",    type=int, default=None)
    parser.add_argument("--plot-only", action="store_true")
    args = parser.parse_args()

    if args.plot_only:
        make_plot(); return
    if args.index is not None:
        run_by_index(args.index); return
    if args.prog_idx is not None:
        run_one(args.prog_idx, args.seed); return
    for pi, s in all_jobs():
        run_one(pi, s)
    make_plot()


if __name__ == "__main__":
    main()
