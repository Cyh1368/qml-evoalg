"""Quantify the magnitude of original converged rotation angles.

This script measures the order of magnitude of the *original* cemoid circuit
angles, and compares them against how far *inserted* gates drift, to answer:
"What is the order of magnitude of the original gates' rotation angles?
Is a small inserted-gate drift meaningful relative to that native scale?"

Data
----
  - base_optima/seed_*.json: converged cemoid angles (6×9 nested list in "params")
  - gate_insertion_frozen_results/{frozen,joint}/ng*_base*.json: learned inserted
    gate angles ("final_extra_angles" list)

Output
------
  - Prints summary table: per-type statistics (mean, median, p90, max |θ|,
    fraction <0.1 rad) for original angles and inserted-gate angles.
  - Saves angle_magnitude_baseline.png: histogram overlay of original vs inserted
    magnitudes, plus bar chart of mean |θ| per cemoid param type (cx,cz,ex,ez,mx,mz,o,i,d).

Usage
-----
  python angle_magnitude_baseline.py --plot-only
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BASE_DIR = HERE / "base_optima"
RESULTS_DIR = HERE / "gate_insertion_frozen_results"
PLOT_PATH = HERE / "angle_magnitude_baseline.png"

# Cemoid param slot names (9 per block)
PARAM_NAMES = ["cx", "cz", "ex", "ez", "mx", "mz", "o", "i", "d"]

# Base seeds (10 independent runs)
BASE_SEEDS = list(range(10))


def load_base_angles():
    """Load all original cemoid angles from base optima.

    Returns
    -------
    angles : np.ndarray
        All 54 original angles (flat), shape (n_angles,)
    angles_by_type : dict
        Mapping param_name -> np.ndarray of all angles of that type
    """
    all_angles = []
    by_type = {name: [] for name in PARAM_NAMES}

    for seed in BASE_SEEDS:
        p = BASE_DIR / f"seed_{seed:02d}.json"
        if not p.exists():
            continue
        data = json.loads(p.read_text())
        params = np.asarray(data["params"], dtype=float)  # shape (6, 9)

        # Flatten and collect
        params_flat = params.flatten()
        all_angles.extend(params_flat)

        # Collect by param type (column)
        for col_idx, name in enumerate(PARAM_NAMES):
            by_type[name].extend(params[:, col_idx].tolist())

    all_angles = np.asarray(all_angles, dtype=float)
    for name in PARAM_NAMES:
        by_type[name] = np.asarray(by_type[name], dtype=float)

    return all_angles, by_type


def load_inserted_angles(condition: str = "frozen"):
    """Load learned inserted-gate angles.

    Parameters
    ----------
    condition : str
        Either "frozen" or "joint"

    Returns
    -------
    angles : np.ndarray
        All inserted angles (flat), shape (n_angles,)
    """
    all_angles = []
    cond_dir = RESULTS_DIR / condition

    if not cond_dir.exists():
        return np.asarray([], dtype=float)

    for p in sorted(cond_dir.glob("ng*.json")):
        data = json.loads(p.read_text())
        angles = np.asarray(data["final_extra_angles"], dtype=float)
        all_angles.extend(angles)

    return np.asarray(all_angles, dtype=float)


def compute_stats(angles):
    """Compute statistics on angle magnitudes.

    Parameters
    ----------
    angles : np.ndarray
        Array of angles (any shape, will be flattened)

    Returns
    -------
    stats : dict
        Keys: "mean", "median", "p90", "max", "frac_below_01"
    """
    angles = np.asarray(angles).flatten()
    abs_angles = np.abs(angles)

    return {
        "mean": float(np.mean(abs_angles)),
        "median": float(np.median(abs_angles)),
        "p90": float(np.percentile(abs_angles, 90)),
        "max": float(np.max(abs_angles)),
        "frac_below_01": float(np.mean(abs_angles < 0.1)),
        "count": len(abs_angles),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plot-only", action="store_true",
                    help="Only generate plots and summary table (default)")
    a = ap.parse_args()

    if not a.plot_only and not a.plot_only:
        # Default to plot-only
        pass

    # Load data
    print("Loading base optima...", flush=True)
    orig_angles, orig_by_type = load_base_angles()

    print("Loading inserted-gate angles (frozen condition)...", flush=True)
    frozen_angles = load_inserted_angles("frozen")

    print("Loading inserted-gate angles (joint condition)...", flush=True)
    joint_angles = load_inserted_angles("joint")

    # Compute statistics
    print("\nComputing statistics...", flush=True)
    orig_stats = compute_stats(orig_angles)
    frozen_stats = compute_stats(frozen_angles) if len(frozen_angles) > 0 else None
    joint_stats = compute_stats(joint_angles) if len(joint_angles) > 0 else None

    # Per-type statistics for original angles
    orig_by_type_stats = {}
    for name in PARAM_NAMES:
        orig_by_type_stats[name] = compute_stats(orig_by_type[name])

    # Print summary table
    print("\n" + "="*90)
    print("ANGLE MAGNITUDE BASELINE ANALYSIS")
    print("="*90)

    print("\n--- ORIGINAL CONVERGED ANGLES (6 blocks × 9 params = 54 total) ---")
    print(f"{'Metric':<20} {'Mean |θ|':<12} {'Median |θ|':<12} {'p90 |θ|':<12} {'Max |θ|':<12} {'Frac <0.1':<12}")
    print("-" * 80)
    print(f"{'Overall':<20} {orig_stats['mean']:<12.5f} {orig_stats['median']:<12.5f} "
          f"{orig_stats['p90']:<12.5f} {orig_stats['max']:<12.5f} {orig_stats['frac_below_01']:<12.3f}")

    print("\n--- ORIGINAL ANGLES BY PARAM TYPE ---")
    print(f"{'Param Type':<12} {'Mean |θ|':<12} {'Median |θ|':<12} {'Max |θ|':<12} {'Count':<8}")
    print("-" * 60)
    for name in PARAM_NAMES:
        s = orig_by_type_stats[name]
        print(f"{name:<12} {s['mean']:<12.5f} {s['median']:<12.5f} {s['max']:<12.5f} {s['count']:<8}")

    if frozen_stats is not None and len(frozen_angles) > 0:
        print("\n--- INSERTED ANGLES (FROZEN CONDITION) ---")
        print(f"{'Metric':<20} {'Mean |θ|':<12} {'Median |θ|':<12} {'p90 |θ|':<12} {'Max |θ|':<12} {'Frac <0.1':<12}")
        print("-" * 80)
        print(f"{'Overall':<20} {frozen_stats['mean']:<12.5f} {frozen_stats['median']:<12.5f} "
              f"{frozen_stats['p90']:<12.5f} {frozen_stats['max']:<12.5f} {frozen_stats['frac_below_01']:<12.3f}")

    if joint_stats is not None and len(joint_angles) > 0:
        print("\n--- INSERTED ANGLES (JOINT CONDITION) ---")
        print(f"{'Metric':<20} {'Mean |θ|':<12} {'Median |θ|':<12} {'p90 |θ|':<12} {'Max |θ|':<12} {'Frac <0.1':<12}")
        print("-" * 80)
        print(f"{'Overall':<20} {joint_stats['mean']:<12.5f} {joint_stats['median']:<12.5f} "
              f"{joint_stats['p90']:<12.5f} {joint_stats['max']:<12.5f} {joint_stats['frac_below_01']:<12.3f}")

    print("\n" + "="*90)

    # Generate plot
    print("\nGenerating plots...", flush=True)
    make_plot(orig_angles, frozen_angles, joint_angles, orig_by_type_stats)


def make_plot(orig_angles, frozen_angles, joint_angles, orig_by_type_stats):
    """Generate comparison plots.

    Parameters
    ----------
    orig_angles : np.ndarray
        Original angle magnitudes
    frozen_angles : np.ndarray
        Frozen inserted-gate angle magnitudes
    joint_angles : np.ndarray
        Joint inserted-gate angle magnitudes
    orig_by_type_stats : dict
        Per-type statistics for original angles
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(16, 5.5))

    # Panel 1: Histogram overlay of original vs inserted magnitudes
    ax = axes[0]
    abs_orig = np.abs(orig_angles)
    abs_frozen = np.abs(frozen_angles) if len(frozen_angles) > 0 else None

    bins = np.linspace(0, max(abs_orig.max(), abs_frozen.max() if abs_frozen is not None else 1.0), 40)

    ax.hist(abs_orig, bins=bins, alpha=0.6, label="original params", color="tab:blue", density=True)
    if abs_frozen is not None and len(abs_frozen) > 0:
        ax.hist(abs_frozen, bins=bins, alpha=0.6, label="inserted (frozen)", color="tab:red", density=True)

    # Add median lines
    orig_median = np.median(abs_orig)
    ax.axvline(orig_median, color="tab:blue", linestyle="--", linewidth=2, label=f"median original: {orig_median:.4f} rad")

    if abs_frozen is not None and len(abs_frozen) > 0:
        frozen_median = np.median(abs_frozen)
        ax.axvline(frozen_median, color="tab:red", linestyle="--", linewidth=2, label=f"median inserted: {frozen_median:.4f} rad")

    ax.set_xlabel("Rotation angle magnitude |θ| (rad)", fontsize=11)
    ax.set_ylabel("Density", fontsize=11)
    ax.set_title("Original vs. Inserted-Gate Angle Magnitudes", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)

    # Panel 2: Bar chart of mean |θ| per cemoid param type
    ax2 = axes[1]
    names = PARAM_NAMES
    means = [orig_by_type_stats[name]["mean"] for name in names]
    maxs = [orig_by_type_stats[name]["max"] for name in names]

    xs = np.arange(len(names))
    ax2.bar(xs, means, alpha=0.7, color="tab:blue", label="mean |θ|")
    ax2.errorbar(xs, means, yerr=maxs, fmt="none", ecolor="black", capsize=3, alpha=0.5)

    ax2.set_xticks(xs)
    ax2.set_xticklabels(names, rotation=0, fontsize=10)
    ax2.set_ylabel("Angle magnitude |θ| (rad)", fontsize=11)
    ax2.set_xlabel("Cemoid parameter type", fontsize=11)
    ax2.set_title("Mean Rotation Angle by Param Type (original circuit)", fontsize=12, fontweight="bold")
    ax2.legend(fontsize=9)
    ax2.grid(alpha=0.3, axis="y")

    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=130)
    print(f"saved {PLOT_PATH}", flush=True)


if __name__ == "__main__":
    main()
