# Perturbation Stability — can the optimizer pull injected noise back to the optimum?

**Question (07-03 meeting, action item 3):** Perturb a converged cemoid optimum three
ways — (1) insert gates at fully random angles, (2) insert gates at near-zero angles,
(3) add random deltas to the 54 converged weights with no new gates — and sweep the
perturbation radius `r`. Does the optimizer pull the injected noise back toward the no-op
optimum? Is there an ε-ball of stability inside which everything returns?

**Headline result.** Yes, up to a radius, and the mechanism is **an absolute attractor,
not proportional shrinkage**. For inserted gates, the final mean angle lands at
**≈0.046–0.095 rad regardless of where it started**, for every `r` from 0.01 up to 1.0 rad
— a fixed floor, not a fixed fraction. The **stability boundary sits between r = 0.5 and
r = 1.0** for the weight-perturbation variant (return ratio 0.53 → 1.42, recovery
0.70 → 0.30) and **breaks down entirely at r = π**, where the system never returns
(delta-weight: final distance 1.71 rad, recovery 0.10, Δacc −0.060). The gate variants
tolerate large `r` far better than the weight variant, because their originals stay frozen.

---

## 1. Motivation & hypothesis

If the converged point is a genuine attractor of the training dynamics, small displacements
should be undone: the optimizer should walk back. The meeting's specific interest was
whether inserted gates initialised at *nonzero* angles get pulled back to their no-op value
— which would explain why gates initialised at zero stay at zero — and whether there is a
radius beyond which the system escapes to a different solution.

> **ε-ball hypothesis.** There exists `r*` such that for `r < r*` the perturbed start
> re-converges to (near) the original optimum, and for `r > r*` it lands elsewhere.

## 2. Methodology

- **Script:** `perturbation_stability.py`; SLURM array `cluster/perturbation_array.sbatch`
  (job name `pert`, **210 tasks, all `COMPLETED`**).
- **Grid:** 3 variants × 7 radii × 10 base optima = **210 runs**.
  - `R_SCHEDULE = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 3.14]` rad
  - `BASE_SEEDS = 0..9` → `base_optima/seed_NN.json` (cemoid L=3, P=2, 54 angles)
- **Variants:**
  1. **`random_gate`** — insert `N_PERTURB_GATES = 8` rotation gates at angles drawn
     `U[−r, r]`. The 54 original angles are **frozen** (`requires_grad=False`); only the
     8 inserted angles train.
  2. **`nearzero_gate`** — *identical code path*, angles drawn `U[−r, r]`, different RNG
     stream. See §5 — this is a replication, not a distinct treatment.
  3. **`delta_weight`** — **no new gates**. Add `U[−r, r]` to each of the 54 converged
     angles and re-optimise all 54 from that perturbed start.
- **Training:** Adam lr = 0.03, 30 steps/epoch, batch 15, `MAX_EPOCHS` = 1000, early stop
  on validation loss with `PATIENCE` = 75, `MIN_DELTA` = 1e-4, restore-best-weights.
- **Metrics:**
  - **return ratio** — gate variants: `mean|θ_final| / mean|θ_initial|` over the 8 inserted
    angles. Delta-weight: `mean|θ_final − θ_base| / mean|θ_initial − θ_base|` over the 54.
    **< 1 means it moved back toward the no-op / optimum.**
  - **`recovered`** — boolean: best validation loss < base validation loss + `MIN_DELTA`
    (1e-4). `frac_recov` is the fraction of the 10 seeds that recovered.
  - **Δacc** — test accuracy(final) − test accuracy(base optimum).
- Distances are **raw / unwrapped** (deliberate; the meeting asked for raw drift).
- **Figure:** `perturbation_stability_analysis.png`.

## 3. Results

### 3.1 `random_gate` (8 inserted gates, originals frozen)

| r | init \|θ\| | final \|θ\| | ratio | Δacc | frac_recov | Δval |
|---|---|---|---|---|---|---|
| 0.01 | 0.0044 | **0.0456** | 10.542 | −0.0018 | 0.80 | −0.00098 |
| 0.05 | 0.0247 | **0.0543** | 2.362 | −0.0025 | 0.60 | −0.00066 |
| 0.10 | 0.0506 | **0.0807** | 1.629 | −0.0060 | 0.40 | +0.00047 |
| 0.20 | 0.0961 | **0.0943** | 1.009 | −0.0045 | 0.50 | −0.00001 |
| 0.50 | 0.2473 | **0.0868** | 0.361 | −0.0050 | 0.40 | +0.00050 |
| 1.00 | 0.5250 | **0.0837** | 0.159 | −0.0050 | 0.40 | +0.00051 |
| 3.14 | 1.6496 | **0.8944** | 0.531 | −0.0335 | 0.30 | +0.08672 |

### 3.2 `nearzero_gate` (same construction, independent RNG)

| r | init \|θ\| | final \|θ\| | ratio | Δacc | frac_recov | Δval |
|---|---|---|---|---|---|---|
| 0.01 | 0.0048 | **0.0459** | 9.476 | −0.0018 | 0.90 | −0.00099 |
| 0.05 | 0.0248 | **0.0569** | 2.151 | −0.0005 | 0.50 | −0.00077 |
| 0.10 | 0.0497 | **0.0773** | 1.577 | −0.0048 | 0.50 | −0.00053 |
| 0.20 | 0.1037 | **0.0865** | 0.842 | −0.0050 | 0.40 | +0.00050 |
| 0.50 | 0.2635 | **0.0848** | 0.329 | −0.0043 | 0.40 | +0.00050 |
| 1.00 | 0.5196 | **0.0946** | 0.190 | −0.0050 | 0.40 | +0.00033 |
| 3.14 | 1.6936 | **0.8237** | 0.511 | −0.0083 | 0.40 | +0.01582 |

### 3.3 `delta_weight` (no gates; all 54 angles perturbed and retrained)

| r | init dist | final dist | ratio | Δacc | frac_recov | Δval |
|---|---|---|---|---|---|---|
| 0.01 | 0.0051 | 0.0191 | 3.733 | −0.0048 | 0.80 | −0.00095 |
| 0.05 | 0.0246 | 0.1006 | 4.139 | −0.0075 | 0.80 | −0.00594 |
| 0.10 | 0.0516 | 0.0958 | 1.864 | −0.0057 | 0.80 | −0.00515 |
| 0.20 | 0.0975 | 0.1025 | 1.037 | +0.0043 | 0.80 | −0.00672 |
| 0.50 | 0.2571 | **0.1340** | **0.534** | −0.0035 | 0.70 | −0.00749 |
| 1.00 | 0.5325 | **0.7483** | **1.424** | −0.0317 | 0.30 | +0.00933 |
| 3.14 | 1.5641 | **1.7114** | 1.098 | −0.0598 | 0.10 | +0.12810 |

### 3.4 The key structural finding: an *absolute* floor, not proportional return

Read the `final |θ|` column of §3.1/§3.2 across radii:

```
r        0.01   0.05   0.10   0.20   0.50   1.00  |  3.14
final|θ| 0.046  0.054  0.081  0.094  0.087  0.084 |  0.894
```

Over a **100× range in starting radius** (0.01 → 1.0), the final inserted-gate angle varies
by only about 2× and sits in a narrow **0.046–0.095 rad** band. The optimizer is not
shrinking the perturbation by a constant factor — it is pulling every start onto the same
small absolute neighbourhood of zero.

This reframes the return ratios entirely. **Ratio > 1 at small `r` is not amplification.**
At `r = 0.01` the start is 0.0044 rad from zero and the endpoint is 0.046 rad; the ratio of
10.5 is large only because the denominator is tiny. Both the start and the endpoint are
negligible on the circuit's native **0.824 rad** angle scale (see
`ANGLE_MAGNITUDE_REPORT.md`). The correct statement is: *inserted gates end up at ~0.05 rad
no matter where they start*, which is exactly the value reported for gates started at
θ = 0 in `GATE_INSERTION_FROZEN_REPORT.md` (mean 0.039 rad). The floor is the same.

At `r = π` the floor breaks: final |θ| jumps to ~0.85 rad and Δval turns sharply positive
(+0.087). The optimizer no longer finds its way back.

### 3.5 Where the ε-ball ends

`delta_weight` is the cleanest probe of the ball, since it perturbs the actual solution
vector rather than adding new axes:

| r | ratio | frac_recov | verdict |
|---|---|---|---|
| ≤ 0.20 | 1.04–4.14 | **0.80** | returns to an equally-good point; final dist pinned at ~0.10 rad |
| 0.50 | **0.534** | 0.70 | genuine contraction — moves back toward the optimum |
| 1.00 | 1.424 | **0.30** | escapes; validation loss now *rises* (+0.009) |
| 3.14 | 1.098 | **0.10** | fully lost; Δacc −0.060, Δval +0.128 |

The stability boundary is **between r = 0.5 and r = 1.0 rad**. Below it, ≥70% of seeds
recover to within `MIN_DELTA` of the base validation loss and accuracy is unharmed. Above
it, recovery collapses to 30% then 10%, and both validation loss and test accuracy degrade
materially.

Note the same "absolute floor" signature: for `r ≤ 0.5` the *final* distance to the optimum
sits at **0.019–0.134 rad** irrespective of the start. The system returns to a shell of
radius ~0.1 rad around the optimum, not to the optimum itself — consistent with a flat
valley of equally-good solutions rather than a sharp basin. `DEGENERACY_PCA_REPORT.md`
characterises that valley's geometry directly.

### 3.6 Gates tolerate perturbation better than weights

At `r = 1.0`, the gate variants still return to ~0.084 rad (ratio 0.16–0.19) with 40%
recovery and Δacc ≈ −0.005, while `delta_weight` has escaped (ratio 1.42, 30% recovery,
Δacc −0.032). The asymmetry is expected: in the gate variants the **54 original angles are
frozen at the optimum**, so the model can never lose more than the inserted gates cost it,
and the inserted gates have a guaranteed no-op setting (θ = 0) available. In `delta_weight`
the solution itself is displaced and there is no anchor.

## 4. Interpretation

- **The optimizer does pull injected noise back to the no-op**, and it does so onto a fixed
  absolute scale (~0.05–0.09 rad) rather than by proportional contraction. This directly
  answers the meeting's question and explains why gates initialised at zero stay near zero:
  zero is already inside the attractor's floor.
- **An ε-ball exists, with ε between 0.5 and 1.0 rad** for whole-solution perturbations.
  This is a large ball — half a radian is a substantial fraction of the 0.82 rad mean angle
  — so the converged solution is *robustly* attracting, not marginally so.
- **The ball's interior is a valley, not a point.** Returns land ~0.1 rad from the optimum,
  not on it, and validation loss at those points is equal or better. Different weights,
  same accuracy — precisely the instability the meeting anticipated, and the entry point
  for the degeneracy analysis.
- **Near-zero and fully-random initialisation behave the same** at matched `r` (compare
  §3.1 and §3.2 row by row: final |θ| agrees to within ~0.01 rad at every radius). At the
  only radius where they are semantically different — `r = π`, where `random_gate` is truly
  uniform over the circle — the random variant is worse (Δacc −0.034 vs −0.008,
  Δval +0.087 vs +0.016).

## 5. Caveats

- **`random_gate` and `nearzero_gate` are the same experiment at every `r` except π.** Both
  draw `U[−r, r]` through one shared code path (`run_gate_perturbation`), differing only in
  RNG seed via a variant tag. The script's own docstring says so: *"Implemented with the
  same code path... differs semantically (small r)."* They should be read as an **internal
  replication** — and the close agreement of §3.1 and §3.2 is a useful consistency check on
  run-to-run noise — **not** as two distinct treatments. Only at `r = π` does `random_gate`
  mean "fully random angle" in the intended sense.
- **n = 10 per cell.** `frac_recov` is a mean of 10 booleans, so it moves in steps of 0.10
  and has a standard error of ~0.15. The non-monotone wiggles (e.g. 0.40 → 0.50 → 0.40 in
  §3.1) are **within noise** and should not be interpreted. Only the large-scale collapse
  at r ≥ 1.0 is resolvable.
- **`recovered` is a strict threshold** (val loss within 1e-4 of base). A run can land at an
  excellent but marginally worse point and score `recovered = False`. Note at `r = 0.01`,
  Δval is *negative* (−0.001, an improvement) yet `frac_recov` is only 0.80 — the threshold,
  not the quality, is what fails. Read `frac_recov` alongside Δval and Δacc, never alone.
- **Distances are unwrapped.** At `r = π` a gate can be perturbed to near ±π, and a return
  "the long way round" registers as a large distance despite being functionally close. This
  inflates the apparent failure at `r = π` for the gate variants. The `delta_weight`
  collapse at `r ≥ 1.0` does not suffer this (max displacement stays below π) and is the
  more trustworthy evidence for the ball boundary.
- The 8 inserted-gate positions are fixed per base seed (`sample_positions` with
  `config_seed = POSITION_SEED_BASE + base_seed`), so position effects are not marginalised
  within a seed.

## 6. Reproduce

```bash
cd tic-tac-toe/paper-replication
bash cluster/deploy_and_run.sh meeting-status         # confirm pert array COMPLETED (210)
bash cluster/deploy_and_run.sh meeting-fetch          # rsync + regenerate figures
../.venv-shinka-ttt/bin/python perturbation_stability.py --plot-only
```

Single task: `python perturbation_stability.py --index I` for `I ∈ [0, 209]`
(grid order: variant → radius → base seed).

## 7. Bottom line

The optimizer **pulls injected noise back onto an absolute floor** — inserted gates finish
at ~0.05–0.09 rad whether they started at 0.004 rad or 0.52 rad, matching the ~0.04 rad
seen when they start at exactly zero. A **stability ball of radius ≈0.5–1.0 rad** surrounds
the converged solution: inside it ≥70% of perturbed starts return to an equally-good point,
outside it (r ≥ 1.0, and decisively at r = π) recovery collapses and accuracy degrades.
Returns land on a ~0.1 rad **shell**, not on the optimum itself — same loss, different
weights — which is the signature of a degenerate flat valley, quantified next in
`DEGENERACY_PCA_REPORT.md`.
