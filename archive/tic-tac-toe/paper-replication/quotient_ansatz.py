"""Quotient-ansatz experiment: does degeneracy-guided parameter tying survive
training from scratch?

Motivation (07-17 meeting + DEGENERACY_PCA_REPORT.md): the converged cemoid
(L=3, P=2) solution has median effective dimensionality ~1.15 of 54 — the
ansatz is massively over-parameterised, and the flat directions live almost
entirely (88-98% of their norm) in the six single-qubit *rotation* slots
(cx, cz, ex, ez, mx, mz), while the entangling slots (o, i, d) are pinned.

A pre-experiment structural probe (--analyze-structure) additionally shows:
  * per-optimum flat directions do NOT agree across basins (pairwise |cos|
    mostly < 0.4) -> no single global linear constraint exists;
  * the 10 base optima span an essentially full-rank affine subspace
    (pairwise distance ~1.0-1.5 rad) -> solutions do not share a subspace.

Therefore the quotient must be *structural*: impose interpretable tying
patterns (weight sharing across the 6 blocks = depth-sharing) and retrain
FROM SCRATCH under the converged protocol. This is the falsifiable step of
the "overparameterize -> analyze degeneracy -> quotient" pipeline: if the
local degeneracy reflects genuine structural redundancy, aggressive
cross-block tying should match the 54-param baseline (0.698 +/- 0.042 over
500 seeds, ROBUSTNESS_500SEED_REPORT.md).

Note this tying axis (across depth/blocks) is orthogonal to the spatial
orbit-sharing axis studied by Meyer et al. 2205.06217 and Baumann et al.
2606.20316 — the cemoid block is already D4 orbit-shared within a block.

Variants (k = free parameter count):
  full        54  control arm, protocol-identical from-scratch baseline
  block_tied   9  all 9 slots tied across all 6 blocks (maximal quotient)
  repeat_tied 18  tied across the 3 uploads, untied across the P=2 repeats
  upload_tied 27  tied across the P=2 repeats within an upload, untied across uploads
  rot_tied    24  the 6 rotation slots tied across all blocks (6 global) +
                  entangling slots untied (6 blocks x 3) — degeneracy-guided:
                  ties exactly where the flat directions live
  ent_tied    39  control: ties only the *pinned* slots (o, i, d -> 3 global)
                  + rotations untied (36). If the degeneracy analysis is
                  predictive, ent_tied should cost MORE accuracy per removed
                  parameter than rot_tied.

Usage
-----
  python quotient_ansatz.py --analyze-structure   # local probe, no training
  python quotient_ansatz.py --index I             # one training job (SLURM array)
  python quotient_ansatz.py --analyze             # post-training summary + figure
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
    LEARNING_RATE, N_CEMOID_PARAMS, _batch_indices,
)
from gate_insertion_frozen import (  # noqa: E402
    L, P, make_base_circuit, base_loss, base_acc, _load_splits, base_path, BASE_SEEDS,
)

# ── experiment parameters ──────────────────────────────────────────────────────
N_BLOCKS = L * P            # 6
SLOT_NAMES = ["cx", "cz", "ex", "ez", "mx", "mz", "o", "i", "d"]
ROT_SLOTS = [0, 1, 2, 3, 4, 5]
ENT_SLOTS = [6, 7, 8]

SEEDS_PER_VARIANT = 20
FULL_SEEDS = 10             # smaller control arm; the real baseline is the 500-seed report

RESULTS_DIR = HERE / "quotient_results"
STRUCTURE_JSON = HERE / "quotient_structure.json"
PLOT_PATH = HERE / "quotient_analysis.png"


# ── tying matrices ─────────────────────────────────────────────────────────────
def _tying_matrix(assign: np.ndarray) -> np.ndarray:
    """Build the 54 x k 0/1 tying matrix from a (block, slot) -> group map."""
    groups = sorted(set(assign.ravel().tolist()))
    remap = {g: j for j, g in enumerate(groups)}
    T = np.zeros((N_BLOCKS * N_CEMOID_PARAMS, len(groups)))
    for b in range(N_BLOCKS):
        for s in range(N_CEMOID_PARAMS):
            T[b * N_CEMOID_PARAMS + s, remap[assign[b, s]]] = 1.0
    return T


def _assign_full():
    return np.arange(N_BLOCKS * N_CEMOID_PARAMS).reshape(N_BLOCKS, N_CEMOID_PARAMS)


def _assign_block_tied():
    a = np.zeros((N_BLOCKS, N_CEMOID_PARAMS), dtype=int)
    for b in range(N_BLOCKS):
        a[b, :] = np.arange(N_CEMOID_PARAMS)
    return a


def _assign_repeat_tied():
    # untied across the P repeat positions, tied across the L uploads
    a = np.zeros((N_BLOCKS, N_CEMOID_PARAMS), dtype=int)
    for b in range(N_BLOCKS):
        repeat_pos = b % P
        a[b, :] = repeat_pos * N_CEMOID_PARAMS + np.arange(N_CEMOID_PARAMS)
    return a


def _assign_upload_tied():
    # tied across the P repeats within an upload, untied across uploads
    a = np.zeros((N_BLOCKS, N_CEMOID_PARAMS), dtype=int)
    for b in range(N_BLOCKS):
        upload = b // P
        a[b, :] = upload * N_CEMOID_PARAMS + np.arange(N_CEMOID_PARAMS)
    return a


def _assign_rot_tied():
    # rotation slots global (6 groups), entangling slots per-block (18 groups)
    a = np.zeros((N_BLOCKS, N_CEMOID_PARAMS), dtype=int)
    next_id = len(ROT_SLOTS)
    for b in range(N_BLOCKS):
        for s in range(N_CEMOID_PARAMS):
            if s in ROT_SLOTS:
                a[b, s] = ROT_SLOTS.index(s)
            else:
                a[b, s] = next_id + b * len(ENT_SLOTS) + ENT_SLOTS.index(s)
    return a


def _assign_ent_tied():
    # entangling slots global (3 groups), rotation slots per-block (36 groups)
    a = np.zeros((N_BLOCKS, N_CEMOID_PARAMS), dtype=int)
    next_id = len(ENT_SLOTS)
    for b in range(N_BLOCKS):
        for s in range(N_CEMOID_PARAMS):
            if s in ENT_SLOTS:
                a[b, s] = ENT_SLOTS.index(s)
            else:
                a[b, s] = next_id + b * len(ROT_SLOTS) + ROT_SLOTS.index(s)
    return a


VARIANTS = {
    "full": _assign_full,
    "block_tied": _assign_block_tied,
    "repeat_tied": _assign_repeat_tied,
    "upload_tied": _assign_upload_tied,
    "rot_tied": _assign_rot_tied,
    "ent_tied": _assign_ent_tied,
}


def variant_matrix(name: str) -> np.ndarray:
    return _tying_matrix(VARIANTS[name]())


# ── training ───────────────────────────────────────────────────────────────────
def run_training(variant: str, seed: int) -> dict:
    T = variant_matrix(variant)  # plain np.ndarray constant; autograd traces phi only
    k = T.shape[1]
    circuit = make_base_circuit()
    xtr, ytr, xv, yv, yv_np, xte, yte_np = _load_splits()

    def expand(phi):
        return pnp.reshape(pnp.dot(T, phi), (N_BLOCKS, N_CEMOID_PARAMS))

    def loss(phi, bx, by):
        return base_loss(circuit, expand(phi), bx, by)

    rng = np.random.default_rng(seed)
    phi = pnp.array(rng.uniform(-0.05, 0.05, size=k), requires_grad=True)
    opt = qml.AdamOptimizer(stepsize=LEARNING_RATE)

    best = float("inf"); best_phi = np.asarray(phi, dtype=float).copy(); best_ep = 0
    best_va = 0.0; best_ta = 0.0; noimp = 0; reason = "max_epochs"
    t0 = time.time(); epoch = 0
    for epoch in range(1, MAX_EPOCHS + 1):
        order = rng.permutation(len(xtr))
        for step in range(STEPS_PER_EPOCH):
            ids = _batch_indices(order, step, BATCH_SIZE)
            bx, by = xtr[ids], ytr[ids]
            phi = opt.step(lambda p: loss(p, bx, by), phi)
        vl = float(loss(phi, xv, yv))
        if vl < best - MIN_DELTA:
            best = vl; best_phi = np.asarray(phi, dtype=float).copy(); best_ep = epoch
            best_va = base_acc(circuit, expand(pnp.array(best_phi)), xv, yv_np)
            best_ta = base_acc(circuit, expand(pnp.array(best_phi)), xte, yte_np)
            noimp = 0
        else:
            noimp += 1
            if noimp >= PATIENCE:
                reason = "early_stopping"; break
        if WALL_BUDGET_SECONDS and (time.time() - t0) > WALL_BUDGET_SECONDS:
            reason = "walltime"; break

    return {
        "variant": variant, "seed": seed, "k": k,
        "phi": best_phi.tolist(),
        "final_val_loss": best, "final_val_acc": best_va, "final_test_accuracy": best_ta,
        "best_epoch": best_ep, "stopped_epoch": epoch,
        "converged": reason == "early_stopping", "stop_reason": reason,
        "wall_seconds": time.time() - t0,
    }


# ── job indexing for SLURM ─────────────────────────────────────────────────────
def all_jobs():
    jobs = []
    for variant in VARIANTS:
        n = FULL_SEEDS if variant == "full" else SEEDS_PER_VARIANT
        jobs.extend((variant, s) for s in range(n))
    return jobs


def job_path(variant: str, seed: int) -> Path:
    return RESULTS_DIR / variant / f"seed{seed:02d}.json"


def run_index(i: int) -> None:
    js = all_jobs()
    if not 0 <= i < len(js):
        raise SystemExit(f"--index must be 0..{len(js)-1}")
    variant, seed = js[i]
    job_path(variant, seed).parent.mkdir(parents=True, exist_ok=True)
    p = job_path(variant, seed)
    if p.exists():
        print(f"index {i}: {variant} seed={seed} cached, skipping", flush=True); return
    t0 = time.time()
    print(f"index {i}: {variant} (k={variant_matrix(variant).shape[1]}) seed={seed} training...", flush=True)
    r = run_training(variant, seed)
    p.write_text(json.dumps(r, indent=2))
    print(f"index {i}: {variant} seed={seed} done {time.time()-t0:.1f}s "
          f"acc={r['final_test_accuracy']:.3f} val_loss={r['final_val_loss']:.4f} "
          f"stop@{r['stopped_epoch']} ({r['stop_reason']})", flush=True)


# ── structure probe (local, no training) ───────────────────────────────────────
def _slot_collective(slot_idx: int) -> np.ndarray:
    v = np.zeros((N_BLOCKS, N_CEMOID_PARAMS)); v[:, slot_idx] = 1.0
    v = v.ravel(); return v / np.linalg.norm(v)


def _family_basis(slot_indices) -> np.ndarray:
    cols = []
    for b in range(N_BLOCKS):
        for s in slot_indices:
            e = np.zeros(N_BLOCKS * N_CEMOID_PARAMS); e[b * N_CEMOID_PARAMS + s] = 1.0
            cols.append(e)
    return np.stack(cols, axis=1)


def _load_displacements(seed: int) -> np.ndarray:
    d = HERE / "degeneracy_results" / f"base{seed:02d}"
    return np.asarray(
        [json.loads(p.read_text())["converged_displacement"] for p in sorted(d.glob("sample*.json"))],
        dtype=float,
    )


def analyze_structure() -> None:
    rot_B = _family_basis(ROT_SLOTS)
    ent_B = _family_basis(ENT_SLOTS)
    out = {"per_seed": {}, "notes": []}
    pc1s = {}
    for seed in BASE_SEEDS:
        X = _load_displacements(seed)
        if len(X) < 2:
            continue
        Xc = X - X.mean(0)
        _, S, Vt = np.linalg.svd(Xc, full_matrices=False)
        evr = (S ** 2) / (S ** 2).sum()
        pc1 = Vt[0]; pc1s[seed] = pc1
        out["per_seed"][seed] = {
            "pc1_evr": float(evr[0]),
            "pc1_rot_fraction": float(np.linalg.norm(rot_B.T @ pc1) ** 2),
            "pc1_ent_fraction": float(np.linalg.norm(ent_B.T @ pc1) ** 2),
            "pc1_slot_collective_cos": {
                SLOT_NAMES[s]: float(abs(pc1 @ _slot_collective(s)))
                for s in range(N_CEMOID_PARAMS)
            },
        }
    seeds = sorted(pc1s)
    cross = np.array([[abs(float(pc1s[i] @ pc1s[j])) for j in seeds] for i in seeds])
    optima = np.stack([
        np.asarray(json.loads(base_path(s).read_text())["params"], float).ravel()
        for s in BASE_SEEDS if base_path(s).exists()
    ])
    _, S_opt, _ = np.linalg.svd(optima - optima.mean(0), full_matrices=False)
    out["cross_seed_pc1_abs_cos"] = cross.tolist()
    out["cross_seed_pc1_abs_cos_offdiag_median"] = float(
        np.median(cross[~np.eye(len(seeds), dtype=bool)])
    )
    out["optima_span_singular_values"] = S_opt.tolist()
    rot_fracs = [d["pc1_rot_fraction"] for d in out["per_seed"].values()]
    out["notes"] = [
        f"PC1 rotation-subspace fraction: median {np.median(rot_fracs):.2f} "
        f"(range {min(rot_fracs):.2f}-{max(rot_fracs):.2f}) — flat directions live in "
        "the single-qubit rotation slots.",
        f"Cross-seed PC1 |cos| off-diagonal median "
        f"{out['cross_seed_pc1_abs_cos_offdiag_median']:.2f} — flat directions are "
        "basin-specific; no universal linear constraint.",
        f"Optima-span singular values {['%.1f' % v for v in S_opt]} — the 10 optima do "
        "not share a low-dimensional affine subspace; quotient must be structural "
        "(tying), not subspace projection.",
    ]
    STRUCTURE_JSON.write_text(json.dumps(out, indent=2))
    for note in out["notes"]:
        print("*", note)
    print(f"saved {STRUCTURE_JSON}")


# ── post-training analysis ─────────────────────────────────────────────────────
BASELINE_500 = {"mean": 0.698, "std": 0.042}   # ROBUSTNESS_500SEED_REPORT.md


def analyze() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    recs = {}
    for variant in VARIANTS:
        rs = []
        for p in sorted((RESULTS_DIR / variant).glob("seed*.json")) if (RESULTS_DIR / variant).exists() else []:
            rs.append(json.loads(p.read_text()))
        if rs:
            recs[variant] = rs
    if not recs:
        print("no results yet"); return

    print(f"{'variant':>12} {'k':>3} {'n':>3} {'test acc':>16} {'val loss':>10} {'conv':>5}")
    rows = []
    for variant, rs in recs.items():
        accs = np.array([r["final_test_accuracy"] for r in rs])
        vls = np.array([r["final_val_loss"] for r in rs])
        conv = np.mean([r["converged"] for r in rs])
        k = rs[0]["k"]
        rows.append((variant, k, accs))
        print(f"{variant:>12} {k:>3} {len(rs):>3} {accs.mean():>7.3f} +/- {accs.std():5.3f} "
              f"{vls.mean():>10.4f} {conv:>5.2f}")
    print(f"\n500-seed full-cemoid reference: {BASELINE_500['mean']:.3f} +/- {BASELINE_500['std']:.3f}")

    rows.sort(key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ks = [r[1] for r in rows]
    means = [r[2].mean() for r in rows]
    stds = [r[2].std() for r in rows]
    ax.errorbar(ks, means, yerr=stds, fmt="o-", capsize=4, color="tab:blue")
    for (variant, k, accs) in rows:
        ax.annotate(variant, (k, accs.mean()), textcoords="offset points",
                    xytext=(6, 6), fontsize=8)
    ax.axhspan(BASELINE_500["mean"] - BASELINE_500["std"],
               BASELINE_500["mean"] + BASELINE_500["std"],
               color="tab:gray", alpha=0.25, label="500-seed full baseline ±1σ")
    ax.set_xlabel("free parameters k"); ax.set_ylabel("test accuracy (mean ± std)")
    ax.set_title(f"Quotient ansatz: accuracy vs. parameter count (cemoid L={L}, P={P})")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(PLOT_PATH, dpi=130)
    print(f"saved {PLOT_PATH}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--index", type=int, default=None)
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--analyze-structure", action="store_true")
    ap.add_argument("--list-jobs", action="store_true")
    a = ap.parse_args()
    if a.analyze_structure:
        analyze_structure()
    elif a.analyze:
        analyze()
    elif a.list_jobs:
        js = all_jobs()
        print(f"{len(js)} jobs")
        for i, (v, s) in enumerate(js):
            print(i, v, s)
    elif a.index is not None:
        run_index(a.index)
    else:
        raise SystemExit("need --index I | --analyze | --analyze-structure | --list-jobs")


if __name__ == "__main__":
    main()
