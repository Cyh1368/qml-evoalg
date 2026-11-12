# Degeneracy & Latent-Space PCA — how many directions does the solution actually use?

**Question (07-03 meeting, action item 4):** Perturb all 54 converged cemoid angles jointly
with small random deltas, many Monte-Carlo times, re-converge each, and run PCA on the
converged displacements. Testing all pairs of weights is exponential; Monte-Carlo joint
perturbation reveals the degenerate dimensions empirically. What does the convergence
geometry look like — a ball, or something smaller and odd-shaped?

**Headline result.** The converged solutions collapse onto a **near-one-dimensional
manifold**. Median effective dimensionality (participation ratio) is **1.15 out of a nominal
54**; the median seed needs **1 principal component for 90%** of the displacement variance
and 3 for 99%. Across 500 re-convergences the validation loss is essentially constant
(std 0.044 pooled; **1e-6 to 3e-3 within a seed**). The cemoid ansatz at (L=3, P=2) is
**massively over-parameterised**: an isotropic 54-dimensional perturbation ball collapses,
under retraining, onto roughly **one flat direction per optimum**. Same loss, different
weights — the meeting's exact prediction, now measured.

---

## 1. Motivation & hypothesis

From the meeting: *"it is possible to see same accuracy but a different set of weights —
this means weights are not stable."* And: *"in `(a+b)·c = r`, `a` and `b` are degenerate
axes; their sum is fixed but individual values are arbitrary."* For a circuit we cannot
write down the degeneracy analytically, but we can find it empirically — perturb every
weight jointly, re-converge, and look at where the endpoints live.

> **Degeneracy hypothesis.** If the ansatz is over-parameterised, converged displacements
> from many random starts will not fill the 54-dimensional perturbation ball. They will
> concentrate on a low-dimensional subspace — the flat directions along which the loss is
> invariant. The number of such directions is the ansatz's *effective* dimensionality.

## 2. Methodology

- **Script:** `degeneracy_pca.py`; SLURM array `cluster/degeneracy_array.sbatch`
  (job name `degen`, **500 tasks, all `COMPLETED`**).
- **Design:** for each of 10 base optima (`base_optima/seed_NN.json`, cemoid L=3, P=2,
  6 blocks × 9 = **54 angles**), draw `MC_SAMPLES = 50` independent perturbations
  `δ ~ U[−MC_R, MC_R]^54` with **`MC_R = 0.1` rad** ("test everything with small
  perturbation"), start training from `θ_base + δ`, and re-converge.
  Total **10 × 50 = 500** runs.
- **Training:** identical to `perturbation_stability.run_delta_weight` — all 54 angles
  trainable, no inserted gates. Adam lr = 0.03, 30 steps/epoch, batch 15,
  `MAX_EPOCHS` = 1000, early stop `PATIENCE` = 75 / `MIN_DELTA` = 1e-4, restore-best.
- **Recorded per run:** `start_displacement` = δ, `converged_displacement` = θ_final − θ_base
  (both raw / unwrapped), `final_val_loss`, `delta_test_acc`, `recovered`.
- **PCA:** per base optimum, mean-centre the 50 converged displacements and take the SVD.
  - **Effective dimensionality** = participation ratio of the eigenvalue spectrum
    (Simpson-index style): `(Σλᵢ)² / Σλᵢ²`. Equals `k` for `k` equal eigenvalues, and 1 for
    a spectrum dominated by a single mode.
  - `n90` / `n99` = number of PCs needed for 90% / 99% of explained variance.
- **Latent-space figure:** start displacements and converged displacements projected onto
  the base optimum's own top-2 PCA directions (`degeneracy_pca_analysis.png`), plus a scree
  plot of the spectrum.

**Sanity check on the perturbation.** For `δ ~ U[−0.1, 0.1]^54` the expected norm is
`√(54 · 0.1² / 3) = 0.4243`. Measured mean `‖start‖ = 0.4252` across all 500 runs — the
perturbation is being applied exactly as specified.

## 3. Results

### 3.1 Per-base-optimum spectrum

| base seed | n | eff_dim | n90 | n99 | val-loss std | val-loss range |
|---|---|---|---|---|---|---|
| 0 | 50 | 1.01 | 1 | 1 | 0.000001 | 0.000006 |
| 1 | 50 | 1.02 | 1 | 1 | 0.000692 | 0.002777 |
| 2 | 50 | 1.09 | 1 | 2 | 0.003163 | 0.009744 |
| 3 | 50 | **10.62** | **13** | **21** | 0.001592 | 0.006047 |
| 4 | 50 | 2.69 | 3 | 6 | 0.000228 | 0.001066 |
| 5 | 50 | 1.58 | 2 | 4 | 0.001004 | 0.004327 |
| 6 | 50 | 1.15 | 1 | 3 | 0.000490 | 0.001649 |
| 7 | 50 | 1.15 | 1 | 4 | 0.000674 | 0.003075 |
| 8 | 50 | 1.07 | 1 | 2 | 0.000115 | 0.000473 |
| 9 | 50 | 1.40 | 2 | 3 | 0.000398 | 0.002025 |

**Pooled:** mean eff_dim **2.28 ± 2.82** (nominal 54); mean n90 = 2.60; mean n99 = 4.70.
**Median eff_dim = 1.15; median n90 = 1; median n99 = 3.**

The mean is misleading — it is dominated by the single outlier seed 3 (eff_dim 10.62). The
**median is the honest summary: 8 of 10 optima have eff_dim < 1.6**, i.e. they are
effectively one-dimensional. **Six** seeds need exactly **one** principal component to
explain 90% of all convergence spread.

**Validation loss is flat everywhere.** Within a seed, the loss across all 50 re-converged
endpoints varies by 1e-6 to 3e-3 — while the endpoints themselves are separated by
0.3–4.5 rad in parameter space. This is the definition of a degenerate direction: large
parameter motion, no loss change.

### 3.2 Convergence geometry — the ball does not stay a ball

| base seed | ‖start‖ | ‖converged‖ | ratio | PC1 evr | PC2 evr | Δacc | frac recov |
|---|---|---|---|---|---|---|---|
| 0 | 0.4251 | 0.3648 | 0.858 | **0.994** | 0.006 | +0.0200 | 1.00 |
| 1 | 0.4281 | 0.6682 | 1.561 | 0.992 | 0.007 | −0.0069 | 1.00 |
| 2 | 0.4297 | **4.4737** | **10.412** | 0.956 | 0.043 | −0.0600 | 1.00 |
| 3 | 0.4348 | 0.3252 | 0.748 | **0.181** | 0.135 | −0.0089 | 0.64 |
| 4 | 0.4271 | 0.2696 | 0.631 | 0.534 | 0.255 | +0.0283 | 0.00 |
| 5 | 0.4205 | **2.1300** | **5.065** | 0.779 | 0.156 | −0.0214 | 1.00 |
| 6 | 0.4194 | 0.3507 | 0.836 | 0.932 | 0.036 | +0.0166 | 1.00 |
| 7 | 0.4210 | 1.1671 | 2.772 | 0.932 | 0.036 | −0.0412 | 1.00 |
| 8 | 0.4188 | 0.3154 | 0.753 | 0.969 | 0.022 | +0.0016 | 0.00 |
| 9 | 0.4274 | 0.6361 | 1.488 | 0.832 | 0.145 | +0.0085 | 1.00 |

Two regimes, five seeds each:

- **Contracting (0, 3, 4, 6, 8):** ratio 0.63–0.86. The perturbation ball shrinks. These
  behave like a conventional basin of attraction.
- **Expanding (1, 2, 5, 7, 9):** ratio 1.49–**10.4**. The endpoints travel *farther* from
  the optimum than they started — seed 2's converged displacements average **4.47 rad**,
  more than 10× the 0.42 rad start.

The expansion is **not isotropic**. For seeds 1, 2, 5, 7, 9 the PC1 explained-variance ratio
is 0.78–0.99: essentially *all* the motion is along a **single direction**. The optimizer is
not diffusing outward in all 54 dimensions — it is **sliding along one flat valley**. A ball
goes in; a nearly one-dimensional needle comes out. That is exactly the "smaller or oddly
shaped ball" the meeting anticipated, and it is the geometric signature of degeneracy.

**These are not 2π wrap artifacts.** Because displacements are recorded raw, a parameter
drifting by exactly 2π would masquerade as a huge distance. It is not happening: across all
2700 coordinates of seed 2, **zero** exceed π in absolute value (max = 2.707 rad), and only
4 exceed 2 rad. Wrapping the displacements to (−π, π] leaves the mean unchanged
(0.4223 → 0.4223). Seed 5's max is 1.070 rad. The large drifts are **genuine collective
motion along a flat direction**, not periodicity.

### 3.3 Which parameters are degenerate?

Mean |converged displacement| by parameter slot, pooled over all 500 runs (54 = 6 blocks × 9):

| Param | mean \|Δθ\| | | Param | mean \|Δθ\| |
|---|---|---|---|---|
| `cz` | **0.1403** | | `mz` | 0.1302 |
| `cx` | **0.1362** | | `ex` | 0.0829 |
| `mx` | 0.1355 | | `d` | 0.0640 |
| `ez` | 0.1311 | | `o` | 0.0548 |
| | | | `i` | **0.0484** |

A clean split. The six rotation-carrying slots (`cx`, `cz`, `ex`, `ez`, `mx`, `mz`) move
**0.083–0.140 rad**, while `o`, `i`, `d` move only **0.048–0.064 rad** — roughly **2.5–3×
less**. The flat directions are concentrated in the `c*`/`m*`/`e*` rotation family; `i` is
the most tightly constrained parameter in the ansatz.

Cross-check against `ANGLE_MAGNITUDE_REPORT.md`: `i` also has the *smallest* converged
magnitude (mean |θ| = 0.462 rad) and `ex` the largest (1.096 rad). So `i` is both small and
pinned, while the large rotations are also the loose ones. Redundancy lives where the
circuit does its work.

### 3.4 Accuracy and recovery

Pooled across 500 runs: **Δacc = −0.0063**, **frac recovered = 0.76**. Re-converging from a
0.1 rad joint perturbation costs essentially nothing in test accuracy, and three quarters of
runs return to within `MIN_DELTA` (1e-4) of the base validation loss.

The per-seed Δacc column of §3.2 spans −0.060 (seed 2) to +0.028 (seed 4) — and the two
extremes are instructive. Seed 2 is the maximally-expanding seed: sliding 4.5 rad down its
flat valley eventually does cost ~6 points of test accuracy, i.e. the valley is flat in
*validation loss* but not perfectly flat in *test accuracy*. Seed 4 *gains* 2.8 points. The
valley is a **loss-degenerate but not generalisation-degenerate** manifold.

## 4. Interpretation

- **The cemoid (L=3, P=2) ansatz is severely over-parameterised.** 54 nominal parameters;
  a median effective dimensionality of **1.15**. The solution is pinned in ~53 directions
  and free in ~1. This is "over-constraining" in the meeting's vocabulary: overlapping
  parameters that trade off against each other without touching the loss.
- **Degeneracy is the mechanism behind the other three subtasks.** It explains why:
  - the no-gate control drifts as much as the joint gate-insertion condition
    (`JOINT_NOGATE_BASELINE_REPORT.md`) — both are sliding along the same flat valley;
  - perturbed starts return to a ~0.1 rad *shell* rather than to the optimum itself
    (`PERTURBATION_STABILITY_REPORT.md`) — there is no point to return to, only a valley;
  - inserted gates settle at a small absolute angle floor — they land somewhere on the
    valley, and the valley is broad.
- **Same accuracy, different weights — confirmed and quantified.** Within a seed, validation
  loss varies by ≲3e-3 while parameters move by up to 4.5 rad. The weights are *not* a
  stable identifier of the solution.
- **Practical consequence for the EA search.** If ~53 of 54 directions are stiff and ~1 is
  free, the ansatz's expressive capacity is not where its parameter count suggests. A
  smaller ansatz, or one that removes the `c*`/`m*` redundancy, could plausibly reach the
  same accuracy with far fewer parameters. Identifying and quotienting out the degenerate
  direction would let the solution "converge to an even smaller ball," exactly as the
  meeting proposed.
- **Seed 3 is the interesting exception** (eff_dim 10.62, n99 = 21, PC1 evr only 0.181, and
  the only seed with partial recovery at 0.64). Its optimum sits somewhere with a genuinely
  higher-dimensional flat subspace. Whether that is a different basin, a saddle, or a
  poorly-converged point is **not resolved by this experiment** and is the obvious follow-up.

## 5. Caveats

- **`eff_dim` mean ± std is not a useful summary.** 2.28 ± 2.82 has a std larger than the
  mean because the distribution is one outlier (10.62) plus a tight cluster near 1.1. Quote
  the **median (1.15)**. The pooled mean is reported above only for continuity with the
  script's printed output.
- **Likewise `‖converged‖` pooled ratio (2.517) is meaningless** — it averages a contracting
  group (0.63–0.86) with an expanding one (1.49–10.41). The bimodality in §3.2 is the
  finding; the pooled number is an artifact of averaging across it.
- **50 samples in 54 dimensions.** PCA on 50 points can support at most 49 non-trivial PCs,
  so `n99 = 21` for seed 3 is measurable, but the *tail* of the spectrum is undersampled.
  The low-eff_dim seeds are safe (a 1-D structure is easy to establish with 50 points); the
  claim "seed 3 has effective dimension ~10.6" is the least certain number in this report.
- **`MC_R = 0.1` rad probes only the local geometry.** §3.2's expanding seeds show endpoints
  travelling far outside that radius, so the *manifold* is explored well beyond 0.1 rad —
  but the *sampling* of starting points is local. Degenerate directions that only open up
  further away would be missed. `PERTURBATION_STABILITY_REPORT.md` sweeps radius explicitly
  and locates the escape boundary at r ≈ 0.5–1.0 rad.
- **Displacements are raw/unwrapped** by design. §3.2 verifies directly that no coordinate
  exceeds π, so no conclusion here rests on the wrapping convention.
- **`recovered` is a strict 1e-4 validation-loss threshold**, and seeds 4 and 8 score 0.00
  despite small displacements and *positive* Δacc (+0.028, +0.002). Their base validation
  loss simply was not re-attained to 1e-4. Read `frac_recov` next to Δacc, not alone.
- All results are for a single architecture (L=3, P=2) and one dataset split. Effective
  dimensionality is expected to scale with (l, p) and is not measured here.

## 6. Reproduce

```bash
cd tic-tac-toe/paper-replication
bash cluster/deploy_and_run.sh meeting-status        # confirm degen array COMPLETED (500)
bash cluster/deploy_and_run.sh meeting-fetch         # rsync results back
../.venv-shinka-ttt/bin/python degeneracy_pca.py --analyze   # PCA + figures, no training
```

Single task: `python degeneracy_pca.py --index I` for `I ∈ [0, 499]`
(grid order: base seed → MC sample).

## 7. Bottom line

Perturb all 54 cemoid angles by ±0.1 rad, 500 times, and re-converge: the endpoints do not
fill a 54-dimensional ball. They collapse onto **a single flat direction** (median effective
dimensionality **1.15**, median 1 PC for 90% of variance), along which validation loss is
constant to ~1e-3 while parameters travel up to 4.5 rad. Five of ten optima *expand* along
that direction rather than contract. The rotation slots `cx`/`cz`/`mx`/`mz`/`ez` carry the
degeneracy; `i` is the most constrained. The ansatz is over-parameterised by roughly a
factor of 50 in effective dimension — and this degeneracy is the common cause of the drift,
the shell-not-point returns, and the near-zero inserted-gate angles documented in the other
three reports.
