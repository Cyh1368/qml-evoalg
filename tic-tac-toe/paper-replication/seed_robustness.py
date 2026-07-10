"""Robustness sweep: 50 random seeds for the fixed (L=3, P=2) cemoid model.

Each run uses a different RNG seed for initial gate parameters while keeping
the training data split fixed (DATA_SEED=2027).  Results are cached per-seed
so the sweep is resumable.

Run locally (single seed):
    ../.venv-shinka-ttt/bin/python seed_robustness.py --seed 0

Plot distribution after all seeds are collected:
    ../.venv-shinka-ttt/bin/python seed_robustness.py --plot-only
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

# Reuse model and training machinery from sweep.py
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sweep import train_model  # noqa: E402

N_SEEDS = 500
L = 3
P = 2

HERE = Path(__file__).resolve().parent
RESULTS_DIR = HERE / "robustness_histories"
PLOT_PATH = HERE / "robustness_seed_distribution.png"


def result_path(seed: int) -> Path:
    return RESULTS_DIR / f"seed_{seed:03d}.json"


def run_seed(seed: int) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = result_path(seed)
    if path.exists():
        print(f"seed {seed}: cached, skipping", flush=True)
        return
    t0 = time.time()
    print(f"seed {seed}: training L={L} P={P}...", flush=True)
    result = train_model(n_layers=L, n_repeats=P, seed=seed)
    result["seed"] = seed
    path.write_text(json.dumps(result, indent=2))
    print(f"seed {seed}: done in {time.time() - t0:.1f}s  "
          f"final test acc = {result['final_test_accuracy']:.3f}", flush=True)


def make_plot() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    accs = []
    missing = []
    for seed in range(N_SEEDS):
        p = result_path(seed)
        if p.exists():
            data = json.loads(p.read_text())
            accs.append(data["final_test_accuracy"])
        else:
            missing.append(seed)

    if missing:
        print(f"WARNING: {len(missing)} seeds not yet computed: {missing}")

    accs = np.array(accs)
    print(f"N={len(accs)}  mean={accs.mean():.3f}  std={accs.std():.3f}  "
          f"min={accs.min():.3f}  max={accs.max():.3f}")

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(accs, bins=15, color="C0", edgecolor="white", linewidth=0.6)
    ax.axvline(accs.mean(), color="C1", linewidth=1.8, linestyle="--", label=f"mean = {accs.mean():.3f}")
    ax.axvline(accs.mean() - accs.std(), color="C1", linewidth=1.0, linestyle=":",
               label=f"±1 std  ({accs.std():.3f})")
    ax.axvline(accs.mean() + accs.std(), color="C1", linewidth=1.0, linestyle=":")
    ax.set_xlabel("Final test accuracy")
    ax.set_ylabel("Count")
    ax.set_title(f"cemoid L={L} P={P} — accuracy distribution over {len(accs)} random seeds")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=150)
    print(f"Saved plot: {PLOT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=None,
                        help="run a single seed (used by the SLURM array task)")
    parser.add_argument("--plot-only", action="store_true",
                        help="only draw the distribution plot")
    args = parser.parse_args()

    if args.plot_only:
        make_plot()
        return
    if args.seed is not None:
        run_seed(args.seed)
        return
    # Local fallback: run all seeds sequentially
    for seed in range(N_SEEDS):
        run_seed(seed)
    make_plot()


if __name__ == "__main__":
    main()
