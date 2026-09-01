"""Perturbation / stability-region test around a converged cemoid optimum.

Experiment C from the meeting notes.  Starting from a base optimum (see
``gate_insertion_frozen.py`` / ``base_optima/seed_NN.json``), inject random
perturbations of magnitude ``r`` and re-optimize to see whether the optimizer
pulls things back toward the original optimum (a no-op).  If it does for small
``r`` but not for large ``r``, that traces out an epsilon-ball stability region
around the optimum.

Three variants:

  1. ``random_gate``  -- insert N_PERTURB_GATES extra single-qubit rotations
     (same slot/wire/type sampling as gate_insertion_frozen.py) with angles
     drawn uniformly from [-r, r] (instead of the no-op 0).  Originals frozen
     at the base optimum.  Re-optimize only the extra angles.  If the ansatz
     truly wants a no-op here, the extra angles should be driven back toward 0
     regardless of where they started.

  2. ``nearzero_gate`` -- identical mechanics to (1); only the r schedule
     differs semantically (small r).  Implemented with the same code path.

  3. ``delta_weight`` -- NO new gates.  Add a random delta ~ U[-r, r] to each
     of the 54 converged cemoid angles, then re-optimize all 54 (plain base
     circuit, no augmentation) from that perturbed start.  Measures whether
     the optimizer returns to (near) the original optimum, or lands elsewhere.

Note on angle wrapping: cemoid rotation angles are 2*pi-periodic, but per the
research request we deliberately do NOT wrap angle differences here -- all
distances/ratios below are RAW (unwrapped) differences, so a gate that drifts
by exactly 2*pi would show a large apparent "distance" despite being a no-op
functionally.  This is intentional: the meeting wants to see raw drift.

Usage
-----
  python perturbation_stability.py --index I       # run one job from the grid
  python perturbation_stability.py --plot-only      # figures + summary table
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
    STEPS_PER_EPOCH, BATCH_SIZE, MAX_EPOCHS, PATIENCE, MIN_DELTA, WALL_BUDGET_SECONDS,
    LEARNING_RATE, _batch_indices, N_CEMOID_PARAMS,
)
from gate_insertion_frozen import (  # noqa: E402
    L, P, BASE_SEEDS, POSITION_SEED_BASE,
    make_base_circuit, make_augmented_circuit, sample_positions,
    base_loss, base_acc, aug_loss, aug_acc, _load_splits, base_path,
)

# ── experiment parameters ──────────────────────────────────────────────────────
VARIANTS = ["random_gate", "nearzero_gate", "delta_weight"]
R_SCHEDULE = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 3.14]
N_PERTURB_GATES = 8   # fixed gate count for the two gate-insertion variants (from
                       # gate_insertion_frozen.N_GATES_SCHEDULE, picked as a
                       # middling/informative value without exploding cost).

RESULTS_DIR = HERE / "perturbation_results"
PLOT_PATH = HERE / "perturbation_stability_analysis.png"

# rng seeding scheme: base rng seed = 9000 + base_seed, then re-seeded per (r,
# variant) job by folding in a hash of r so different r values for the same
# base_seed draw independent (but reproducible) perturbations, while re-running
# the identical job is deterministic.
_RNG_SEED_BASE = 9000


def _rng_for(variant: str, r: float, base_seed: int) -> np.random.Generator:
    # Fold r (quantized) and a variant tag into the seed for independence
    # across the grid while remaining fully reproducible.
    r_key = int(round(r * 1e6))
    variant_tag = {"random_gate": 1, "nearzero_gate": 2, "delta_weight": 3}[variant]
    seed = (_RNG_SEED_BASE + base_seed) * 1_000_003 + r_key * 7 + variant_tag
    return np.random.default_rng(seed % (2**32 - 1))


def _r_tag(r: float) -> str:
    # sanitize r into a filename-safe token, e.g. 0.1 -> "0p10", 3.14 -> "3p14"
    return f"{r:.2f}".replace(".", "p").replace("-", "m")


def result_path(variant: str, r: float, base_seed: int) -> Path:
    return RESULTS_DIR / variant / f"r{_r_tag(r)}_base{base_seed:02d}.json"


# ── gate-insertion perturbation (random_gate / nearzero_gate) ──────────────────
def run_gate_perturbation(variant: str, r: float, base_seed: int) -> dict:
    base = json.loads(base_path(base_seed).read_text())
    base_params_np = np.asarray(base["params"], dtype=float)
    config_seed = POSITION_SEED_BASE + base_seed
    positions = sample_positions(N_PERTURB_GATES, config_seed)
    circuit = make_augmented_circuit(positions)
    xtr, ytr, xv, yv, yv_np, xte, yte_np = _load_splits()

    rng = _rng_for(variant, r, base_seed)
    init_extra_np = rng.uniform(-r, r, size=N_PERTURB_GATES)
    initial_abs_mean = float(np.mean(np.abs(init_extra_np)))

    order_rng = np.random.default_rng(base_seed)  # drives minibatch order only

    cp_frozen = pnp.array(base_params_np, requires_grad=False)
    base_val_loss = float(aug_loss(circuit, cp_frozen, pnp.zeros(N_PERTURB_GATES), xv, yv))
    base_test_acc = aug_acc(circuit, cp_frozen, pnp.zeros(N_PERTURB_GATES), xte, yte_np)
    base_val_acc = aug_acc(circuit, cp_frozen, pnp.zeros(N_PERTURB_GATES), xv, yv_np)

    extra = pnp.array(init_extra_np, requires_grad=True)
    init_val_loss = float(aug_loss(circuit, cp_frozen, extra, xv, yv))
    init_test_acc = aug_acc(circuit, cp_frozen, extra, xte, yte_np)

    opt = qml.AdamOptimizer(stepsize=LEARNING_RATE)
    best = init_val_loss
    best_extra = init_extra_np.copy(); best_ep = 0
    best_va = aug_acc(circuit, cp_frozen, extra, xv, yv_np); best_ta = init_test_acc
    noimp = 0; reason = "max_epochs"; t0 = time.time(); epoch = 0
    for epoch in range(1, MAX_EPOCHS + 1):
        order = order_rng.permutation(len(xtr))
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

    extra_abs_mean_final = float(np.mean(np.abs(best_extra)))
    extra_return_ratio = extra_abs_mean_final / initial_abs_mean if initial_abs_mean > 0 else 0.0
    recovered = bool(best < base_val_loss + MIN_DELTA)

    return {
        "variant": variant, "r": r, "base_seed": base_seed,
        "config_seed": config_seed, "positions": positions,
        "n_gates": N_PERTURB_GATES,
        "initial_extra_angles": init_extra_np.tolist(),
        "extra_abs_mean_initial": initial_abs_mean,
        "final_extra_angles": best_extra.tolist(),
        "extra_abs_mean_final": extra_abs_mean_final,
        "extra_return_ratio": extra_return_ratio,
        "base_val_loss": base_val_loss, "base_test_acc": base_test_acc, "base_val_acc": base_val_acc,
        "init_val_loss": init_val_loss, "init_test_acc": init_test_acc,
        "final_val_loss": best, "final_val_acc": best_va, "final_test_accuracy": best_ta,
        "delta_test_acc": best_ta - base_test_acc,
        "delta_val_loss": best - base_val_loss,
        "recovered": recovered,
        "best_epoch": best_ep, "stopped_epoch": epoch, "converged": reason == "early_stopping",
        "stop_reason": reason, "wall_seconds": time.time() - t0,
    }


# ── delta-weight perturbation (no new gates) ────────────────────────────────────
def run_delta_weight(r: float, base_seed: int) -> dict:
    base = json.loads(base_path(base_seed).read_text())
    base_params_np = np.asarray(base["params"], dtype=float)
    circuit = make_base_circuit()
    xtr, ytr, xv, yv, yv_np, xte, yte_np = _load_splits()

    rng = _rng_for("delta_weight", r, base_seed)
    delta = rng.uniform(-r, r, size=base_params_np.shape)
    perturbed_np = base_params_np + delta
    param_dist_to_optimum_initial = float(np.mean(np.abs(delta)))

    order_rng = np.random.default_rng(base_seed)

    base_val_loss = float(base_loss(circuit, pnp.array(base_params_np), xv, yv))
    base_test_acc = base_acc(circuit, pnp.array(base_params_np), xte, yte_np)

    params = pnp.array(perturbed_np, requires_grad=True)
    init_val_loss = float(base_loss(circuit, params, xv, yv))
    init_test_acc = base_acc(circuit, params, xte, yte_np)

    opt = qml.AdamOptimizer(stepsize=LEARNING_RATE)
    best = init_val_loss
    best_p = np.asarray(params, dtype=float).copy(); best_ep = 0
    best_va = base_acc(circuit, params, xv, yv_np); best_ta = init_test_acc
    noimp = 0; reason = "max_epochs"; t0 = time.time(); epoch = 0
    for epoch in range(1, MAX_EPOCHS + 1):
        order = order_rng.permutation(len(xtr))
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

    param_dist_to_optimum_final = float(np.mean(np.abs(best_p - base_params_np)))
    return_ratio = (param_dist_to_optimum_final / param_dist_to_optimum_initial
                     if param_dist_to_optimum_initial > 0 else 0.0)
    recovered = bool(best < base_val_loss + MIN_DELTA)

    return {
        "variant": "delta_weight", "r": r, "base_seed": base_seed,
        "delta": delta.tolist(),
        "param_dist_to_optimum_initial": param_dist_to_optimum_initial,
        "final_params": best_p.tolist(),
        "param_dist_to_optimum_final": param_dist_to_optimum_final,
        "return_ratio": return_ratio,
        "base_val_loss": base_val_loss, "base_test_acc": base_test_acc,
        "init_val_loss": init_val_loss, "init_test_acc": init_test_acc,
        "final_val_loss": best, "final_val_acc": best_va, "final_test_accuracy": best_ta,
        "delta_test_acc": best_ta - base_test_acc,
        "delta_val_loss": best - base_val_loss,
        "recovered": recovered,
        "best_epoch": best_ep, "stopped_epoch": epoch, "converged": reason == "early_stopping",
        "stop_reason": reason, "wall_seconds": time.time() - t0,
    }


# ── job indexing for SLURM ─────────────────────────────────────────────────────
def all_jobs():
    return [(v, r, bs) for v in VARIANTS for r in R_SCHEDULE for bs in BASE_SEEDS]


def run_job(variant: str, r: float, base_seed: int) -> dict:
    if variant in ("random_gate", "nearzero_gate"):
        return run_gate_perturbation(variant, r, base_seed)
    elif variant == "delta_weight":
        return run_delta_weight(r, base_seed)
    else:
        raise ValueError(f"unknown variant {variant}")


def run_index(i: int) -> None:
    js = all_jobs()
    if not 0 <= i < len(js):
        raise SystemExit(f"--index must be 0..{len(js)-1}")
    v, r, bs = js[i]
    (RESULTS_DIR / v).mkdir(parents=True, exist_ok=True)
    p = result_path(v, r, bs)
    if p.exists():
        print(f"index {i}: {v} r={r} base={bs} cached, skipping", flush=True); return
    if not base_path(bs).exists():
        raise SystemExit(f"missing base optimum for seed {bs}: {base_path(bs)}")
    t0 = time.time()
    print(f"index {i}: {v} r={r} base={bs} training...", flush=True)
    res = run_job(v, r, bs)
    p.write_text(json.dumps(res, indent=2))
    ratio_key = "extra_return_ratio" if v != "delta_weight" else "return_ratio"
    print(f"index {i}: {v} r={r} base={bs} done {time.time()-t0:.1f}s "
          f"ratio={res[ratio_key]:.4f} Δacc={res['delta_test_acc']:+.3f} "
          f"recovered={res['recovered']} stop@{res['stopped_epoch']}", flush=True)


# ── plotting ───────────────────────────────────────────────────────────────────
def make_plot() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    recs = {v: defaultdict(list) for v in VARIANTS}
    for v in VARIANTS:
        for r in R_SCHEDULE:
            for bs in BASE_SEEDS:
                p = result_path(v, r, bs)
                if p.exists():
                    recs[v][r].append(json.loads(p.read_text()))

    if not any(recs[v][r] for v in VARIANTS for r in R_SCHEDULE):
        print("no results found yet -- run some --index jobs first."); return

    def ratio_key(v):
        return "return_ratio" if v == "delta_weight" else "extra_return_ratio"

    colors = {"random_gate": "tab:blue", "nearzero_gate": "tab:green", "delta_weight": "tab:red"}
    xs = list(range(len(R_SCHEDULE)))
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    ax = axes[0]
    for v in VARIANTS:
        rk = ratio_key(v)
        m, s = [], []
        for r in R_SCHEDULE:
            R = recs[v][r]
            vals = [x[rk] for x in R] if R else [np.nan]
            m.append(np.nanmean(vals)); s.append(np.nanstd(vals))
        ax.errorbar(xs, m, yerr=s, fmt="o-", color=colors[v], capsize=4, label=v)
    ax.set_xticks(xs); ax.set_xticklabels(R_SCHEDULE); ax.set_xlabel("perturbation range r")
    ax.set_ylabel("return ratio (final/initial |perturbation|)")
    ax.set_title("Return-to-optimum ratio vs r"); ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax2 = axes[1]
    for v in VARIANTS:
        m, s = [], []
        for r in R_SCHEDULE:
            R = recs[v][r]
            vals = [x["delta_test_acc"] for x in R] if R else [np.nan]
            m.append(np.nanmean(vals)); s.append(np.nanstd(vals))
        ax2.errorbar(xs, m, yerr=s, fmt="s-", color=colors[v], capsize=4, label=v)
    ax2.axhline(0, color="0.5", ls=":", lw=1)
    ax2.set_xticks(xs); ax2.set_xticklabels(R_SCHEDULE); ax2.set_xlabel("perturbation range r")
    ax2.set_ylabel("Δ test accuracy vs. base optimum")
    ax2.set_title("Accuracy recovery vs r"); ax2.legend(fontsize=8); ax2.grid(alpha=0.3)

    ax3 = axes[2]
    for v in VARIANTS:
        m = []
        for r in R_SCHEDULE:
            R = recs[v][r]
            frac = np.mean([x["recovered"] for x in R]) if R else np.nan
            m.append(frac)
        ax3.plot(xs, m, "^-", color=colors[v], label=v)
    ax3.set_xticks(xs); ax3.set_xticklabels(R_SCHEDULE); ax3.set_xlabel("perturbation range r")
    ax3.set_ylabel("fraction recovered (val loss within MIN_DELTA of optimum)")
    ax3.set_title("Recovery fraction vs r (epsilon-ball)"); ax3.legend(fontsize=8); ax3.grid(alpha=0.3)

    fig.tight_layout(); fig.savefig(PLOT_PATH, dpi=130)
    print(f"saved {PLOT_PATH}")

    print(f"\n{'variant':>13} {'r':>6} {'n':>3} {'ratio':>8} {'Δacc':>8} {'frac_recov':>10}")
    for v in VARIANTS:
        rk = ratio_key(v)
        for r in R_SCHEDULE:
            R = recs[v][r]
            if not R:
                continue
            ratio = np.mean([x[rk] for x in R])
            dacc = np.mean([x["delta_test_acc"] for x in R])
            frac = np.mean([x["recovered"] for x in R])
            print(f"{v:>13} {r:>6} {len(R):>3} {ratio:>8.4f} {dacc:>+8.3f} {frac:>10.2f}")


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
