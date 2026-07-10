"""Degeneracy / latent-space analysis around converged cemoid optima.

Experiment D from the meeting notes. Starting from a converged base optimum
(see ``gate_insertion_frozen.py`` / ``base_optima/seed_NN.json``), jointly
perturb ALL 54 cemoid angles with small independent uniform deltas, many
Monte-Carlo times, and re-converge each perturbed start with the same
early-stopping + restore-best-weights protocol used in
``perturbation_stability.run_delta_weight``. Then run PCA on the converged
displacements (converged_params - base_optimum) to find:

  * the eigenvalue spectrum of the local landscape geometry around the
    optimum -- flat/soft (degenerate) directions vs. tightly-constrained ones;
  * the participation ratio / effective dimensionality (Simpson-index style):
    (sum(lambda))^2 / sum(lambda^2), i.e. the number of "active" degenerate
    directions out of the nominal 54;
  * whether movement along the top PCs is loss-neutral (a hallmark of
    degeneracy, e.g. individually-degenerate factors in (a+b)*c) by checking
    the spread of final validation loss across re-converged samples.

Also produces a "latent space" scatter: start displacements (perturbed -
optimum) vs. converged displacements (re-converged - optimum), projected onto
the base optimum's own top-2 PCA directions, to visualize the perturbation
ball collapsing onto (or spreading along) the degenerate subspace.

Note on angle wrapping: cemoid rotation angles are 2*pi-periodic, but per the
research request we deliberately do NOT wrap angle differences here -- all
displacement vectors / distances below are RAW (unwrapped), consistent with
``perturbation_stability.py``. A parameter that drifts by exactly 2*pi shows
up as a large apparent displacement despite being a functional no-op; this is
intentional.

Usage
-----
  python degeneracy_pca.py --index I     # run one job from the 10 x MC_SAMPLES grid
  python degeneracy_pca.py --analyze     # PCA + figures + summary tables (no training)
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
    STEPS_PER_EPOCH, BATCH_SIZE, MAX_EPOCHS, PATIENCE, MIN_DELTA, WALL_BUDGET_SECONDS,
    LEARNING_RATE, _batch_indices,
)
from gate_insertion_frozen import (  # noqa: E402
    L, P, BASE_SEEDS, make_base_circuit, base_loss, base_acc, _load_splits, base_path,
    N_CEMOID_PARAMS,
)

# ── experiment parameters ──────────────────────────────────────────────────────
MC_R = 0.1          # fixed small perturbation range (rad), uniform U[-MC_R, MC_R]
                     # added independently to each of the 54 params. Small enough
                     # to stay in the local basin (per the meeting's "test
                     # everything with small perturbation").
MC_SAMPLES = 50      # Monte-Carlo perturbation samples per base optimum.

RESULTS_DIR = HERE / "degeneracy_results"
PLOT_PATH = HERE / "degeneracy_pca_analysis.png"


def _rng_for(base_seed: int, sample_idx: int) -> np.random.Generator:
    return np.random.default_rng(7000 * base_seed + sample_idx)


def sample_dir(base_seed: int) -> Path:
    return RESULTS_DIR / f"base{base_seed:02d}"


def sample_path(base_seed: int, sample_idx: int) -> Path:
    return sample_dir(base_seed) / f"sample{sample_idx:03d}.json"


# ── job indexing for SLURM ─────────────────────────────────────────────────────
def all_jobs():
    return [(bs, si) for bs in BASE_SEEDS for si in range(MC_SAMPLES)]


# ── core training: perturb all 54 params, re-converge, restore best ────────────
def run_mc_sample(base_seed: int, sample_idx: int) -> dict:
    base = json.loads(base_path(base_seed).read_text())
    base_params_np = np.asarray(base["params"], dtype=float)
    circuit = make_base_circuit()
    xtr, ytr, xv, yv, yv_np, xte, yte_np = _load_splits()

    rng = _rng_for(base_seed, sample_idx)
    delta = rng.uniform(-MC_R, MC_R, size=base_params_np.shape)
    perturbed_np = base_params_np + delta
    start_displacement = delta  # perturbed_start - optimum (raw/unwrapped)

    order_rng = np.random.default_rng(base_seed)  # minibatch order, repo convention

    base_val_loss = float(base_loss(circuit, pnp.array(base_params_np), xv, yv))
    base_test_acc = base_acc(circuit, pnp.array(base_params_np), xte, yte_np)

    params = pnp.array(perturbed_np, requires_grad=True)
    init_val_loss = float(base_loss(circuit, params, xv, yv))

    opt = qml.AdamOptimizer(stepsize=LEARNING_RATE)
    best = init_val_loss
    best_p = np.asarray(params, dtype=float).copy(); best_ep = 0
    best_ta = base_acc(circuit, params, xte, yte_np)
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
            best_ta = base_acc(circuit, params, xte, yte_np); noimp = 0
        else:
            noimp += 1
            if noimp >= PATIENCE:
                reason = "early_stopping"; break
        if WALL_BUDGET_SECONDS and (time.time() - t0) > WALL_BUDGET_SECONDS:
            reason = "walltime"; break

    converged_displacement = best_p - base_params_np  # raw/unwrapped
    param_dist_final = float(np.mean(np.abs(converged_displacement)))
    recovered = bool(best < base_val_loss + MIN_DELTA)

    return {
        "base_seed": base_seed, "sample_idx": sample_idx,
        "perturbed_start": perturbed_np.ravel().tolist(),
        "converged_params": best_p.ravel().tolist(),
        "start_displacement": start_displacement.ravel().tolist(),
        "converged_displacement": converged_displacement.ravel().tolist(),
        "param_dist_final": param_dist_final,
        "base_val_loss": base_val_loss,
        "final_val_loss": best,
        "delta_val_loss": best - base_val_loss,
        "base_test_acc": base_test_acc,
        "final_test_accuracy": best_ta,
        "delta_test_acc": best_ta - base_test_acc,
        "recovered": recovered,
        "best_epoch": best_ep, "stopped_epoch": epoch, "converged": reason == "early_stopping",
        "stop_reason": reason, "wall_seconds": time.time() - t0,
    }


def run_index(i: int) -> None:
    js = all_jobs()
    if not 0 <= i < len(js):
        raise SystemExit(f"--index must be 0..{len(js)-1}")
    bs, si = js[i]
    sample_dir(bs).mkdir(parents=True, exist_ok=True)
    p = sample_path(bs, si)
    if p.exists():
        print(f"index {i}: base={bs} sample={si} cached, skipping", flush=True); return
    if not base_path(bs).exists():
        raise SystemExit(f"missing base optimum for seed {bs}: {base_path(bs)}")
    t0 = time.time()
    print(f"index {i}: base={bs} sample={si} training...", flush=True)
    res = run_mc_sample(bs, si)
    p.write_text(json.dumps(res, indent=2))
    print(f"index {i}: base={bs} sample={si} done {time.time()-t0:.1f}s "
          f"|Δp|={res['param_dist_final']:.4f} Δvalloss={res['delta_val_loss']:+.5f} "
          f"recovered={res['recovered']} stop@{res['stopped_epoch']}", flush=True)


# ── PCA analysis ────────────────────────────────────────────────────────────────
def _pca_numpy(X: np.ndarray):
    """Mean-centered SVD-based PCA. Returns (mean, components, singular_values,
    explained_variance_ratio). components rows are unit PCs, sorted descending."""
    mean = X.mean(axis=0)
    Xc = X - mean
    # full_matrices=False gives economy SVD: Xc = U @ diag(S) @ Vt
    _, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    var = S ** 2
    evr = var / var.sum() if var.sum() > 0 else var
    return mean, Vt, S, evr


def _participation_ratio(var: np.ndarray) -> float:
    s = var.sum()
    if s <= 0:
        return 0.0
    return float((s ** 2) / np.sum(var ** 2))


def _n_pcs_for_threshold(evr: np.ndarray, thresh: float) -> int:
    cum = np.cumsum(evr)
    idx = np.searchsorted(cum, thresh) + 1
    return int(min(idx, len(evr)))


def load_seed_records(base_seed: int) -> list[dict]:
    d = sample_dir(base_seed)
    if not d.exists():
        return []
    recs = []
    for p in sorted(d.glob("sample*.json")):
        recs.append(json.loads(p.read_text()))
    return recs


def analyze() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    per_seed = {}
    for bs in BASE_SEEDS:
        recs = load_seed_records(bs)
        if len(recs) < 2:
            print(f"base_seed={bs}: only {len(recs)} sample(s) available, "
                  f"PCA needs >=2 -- skipping.")
            continue
        X = np.array([r["converged_displacement"] for r in recs], dtype=float)
        starts = np.array([r["start_displacement"] for r in recs], dtype=float)
        losses = np.array([r["final_val_loss"] for r in recs], dtype=float)
        dlosses = np.array([r["delta_val_loss"] for r in recs], dtype=float)
        mean, components, S, evr = _pca_numpy(X)
        eff_dim = _participation_ratio(S ** 2)
        n90 = _n_pcs_for_threshold(evr, 0.90)
        n99 = _n_pcs_for_threshold(evr, 0.99)
        per_seed[bs] = {
            "n_samples": len(recs), "mean": mean, "components": components,
            "singular_values": S, "evr": evr, "eff_dim": eff_dim,
            "n90": n90, "n99": n99, "X": X, "starts": starts,
            "losses": losses, "dlosses": dlosses,
        }

    if not per_seed:
        print("no base optima with >=2 samples -- nothing to analyze.")
        return

    # ── per-seed table ──────────────────────────────────────────────────────
    n_params = None
    for bs, d in per_seed.items():
        n_params = d["X"].shape[1]
        break
    print(f"\nnominal parameter dimensionality: {n_params}")
    print(f"{'base_seed':>9} {'n':>4} {'eff_dim':>8} {'n90':>4} {'n99':>4} "
          f"{'val_loss_std':>13} {'val_loss_range':>15}")
    for bs in sorted(per_seed):
        d = per_seed[bs]
        vl_std = float(np.std(d["losses"]))
        vl_range = float(d["losses"].max() - d["losses"].min())
        print(f"{bs:>9} {d['n_samples']:>4} {d['eff_dim']:>8.2f} {d['n90']:>4} "
              f"{d['n99']:>4} {vl_std:>13.6f} {vl_range:>15.6f}")

    eff_dims = [d["eff_dim"] for d in per_seed.values()]
    print(f"\npooled summary over {len(per_seed)} base optima:")
    print(f"  mean effective dimensionality (participation ratio): "
          f"{np.mean(eff_dims):.2f} +/- {np.std(eff_dims):.2f} "
          f"(out of nominal {n_params})")
    print(f"  mean #PCs for 90% variance: "
          f"{np.mean([d['n90'] for d in per_seed.values()]):.2f}")
    print(f"  mean #PCs for 99% variance: "
          f"{np.mean([d['n99'] for d in per_seed.values()]):.2f}")

    # ── figures ──────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    # (a) scree plot: variance fraction per PC, overlaid across seeds
    ax = axes[0]
    for bs in sorted(per_seed):
        d = per_seed[bs]
        xs = np.arange(1, len(d["evr"]) + 1)
        ax.plot(xs, d["evr"], alpha=0.4, lw=1, color="tab:blue")
    # average curve (pad shorter ones with 0)
    maxlen = max(len(d["evr"]) for d in per_seed.values())
    padded = np.array([np.pad(d["evr"], (0, maxlen - len(d["evr"]))) for d in per_seed.values()])
    ax.plot(np.arange(1, maxlen + 1), padded.mean(axis=0), color="tab:red", lw=2.5,
            label="mean across base optima")
    ax.set_xlabel("PC index"); ax.set_ylabel("fraction of variance explained")
    ax.set_title("Scree plot: converged-displacement PCA spectrum")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    # (b) latent-space scatter for one representative seed: start vs converged
    # displacements projected onto that seed's top-2 PCs
    rep_bs = sorted(per_seed, key=lambda k: per_seed[k]["n_samples"], reverse=True)[0]
    d = per_seed[rep_bs]
    pc1, pc2 = d["components"][0], d["components"][1]
    start_proj = d["starts"] @ np.stack([pc1, pc2], axis=1)
    conv_proj = d["X"] @ np.stack([pc1, pc2], axis=1)
    ax2 = axes[1]
    ax2.scatter(start_proj[:, 0], start_proj[:, 1], c="tab:gray", alpha=0.6,
                label="start (perturbed)", marker="x", s=40)
    ax2.scatter(conv_proj[:, 0], conv_proj[:, 1], c="tab:red", alpha=0.7,
                label="converged", marker="o", s=40)
    ax2.axhline(0, color="0.5", lw=0.8, ls=":"); ax2.axvline(0, color="0.5", lw=0.8, ls=":")
    ax2.set_xlabel("PC1 (of converged displacements)"); ax2.set_ylabel("PC2")
    ax2.set_title(f"Latent space: base_seed={rep_bs} (n={d['n_samples']})")
    ax2.legend(fontsize=8); ax2.grid(alpha=0.3)

    # (c) histogram of per-sample final val-loss spread (pooled, or rep seed)
    ax3 = axes[2]
    all_dloss = np.concatenate([per_seed[bs]["dlosses"] for bs in per_seed])
    ax3.hist(all_dloss, bins=30, color="tab:purple", alpha=0.75)
    ax3.axvline(0, color="black", ls="--", lw=1)
    ax3.set_xlabel("delta_val_loss (final - base)")
    ax3.set_ylabel("count (pooled over all base optima)")
    ax3.set_title("Iso-loss check: tight spread => degeneracy, not suboptimality")
    ax3.grid(alpha=0.3)

    fig.tight_layout(); fig.savefig(PLOT_PATH, dpi=130)
    print(f"\nsaved {PLOT_PATH}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--index", type=int, default=None)
    ap.add_argument("--analyze", action="store_true")
    a = ap.parse_args()
    if a.analyze:
        analyze()
    elif a.index is not None:
        run_index(a.index)
    else:
        raise SystemExit("need --index I | --analyze")


if __name__ == "__main__":
    main()
