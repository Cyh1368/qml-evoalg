# Rotation-Angle Magnitude Baseline — cemoid L=3, P=2

**Question (07-03 meeting, action item 1):** What is the order of magnitude of the
rotation angles in the *original* converged cemoid circuit — ~0.0005 rad or ~0.5 rad?
Without this scale, the ~0.05 rad drift observed on inserted gates cannot be judged
"large" or "negligible."

**Headline result.** Original converged angles are **O(1 rad)**: mean |θ| = **0.824 rad**,
median 0.667 rad, and only **10.2%** of them fall below 0.1 rad. Inserted gates, by
contrast, settle at mean |θ| = **0.039 rad** (frozen) / **0.045 rad** (joint), with a
**median of exactly 0.000 rad**. The inserted-gate drift is therefore roughly **20×
smaller** than a typical original angle — about **4.7%** of the native angle scale. The
0.05 rad drift is **not significant**; it is a near-no-op residue, which corroborates
the frozen-optimality conclusion of `GATE_INSERTION_FROZEN_REPORT.md` rather than
undermining it.

---

## 1. Motivation

`GATE_INSERTION_FROZEN_REPORT.md` reported that inserted gates "barely leave their
no-op start," with mean learned |θ| ≈ 0.039 rad. But "barely" is only meaningful
relative to the circuit's own angle scale. If the original cemoid angles were themselves
O(0.01 rad), a 0.039 rad drift would be a *large* excursion and the frozen-optimality
reading would collapse. If the originals are O(1 rad), the drift is noise.

This report measures that scale directly.

## 2. Methodology

- **Script:** `angle_magnitude_baseline.py` (runs locally; no cluster job — it only
  reads already-computed optima and inserted-gate angles).
- **Original angles:** the 54 converged cemoid parameters from each of the 10 base
  optima in `base_optima/seed_NN.json` (L=3 layers × P=2 blocks = 6 blocks × 9 shared
  params). Pooled: 10 seeds × 54 = **540 angles**.
- **Inserted angles:** `final_extra_angles` from `gate_insertion_frozen_results/{frozen,joint}/`,
  pooled across the `n_gates ∈ {1,2,3,5,8,13,21}` schedule × 10 base seeds (70 runs per
  condition).
- **Statistic:** absolute angle |θ|, reported as mean / median / p90 / max, plus the
  fraction below 0.1 rad. Angles are **not** wrapped to (−π, π]; see §5.
- **Figure:** `angle_magnitude_baseline.png`.

## 3. Results

### 3.1 Original converged angles (540 values)

| Metric | Mean \|θ\| | Median \|θ\| | p90 \|θ\| | Max \|θ\| | Frac < 0.1 rad |
|---|---|---|---|---|---|
| Overall | **0.8239** | 0.6673 | 1.7221 | 6.9585 | 0.102 |

The distribution is centered near **0.7–0.8 rad** with a tail reaching ~7 rad (one
parameter exceeds 2π, an unwrapped multi-turn value). Roughly **90% of original angles
exceed 0.1 rad** — the circuit genuinely uses large rotations.

### 3.2 Original angles by parameter slot

Each cemoid block has 9 shared parameters. Pooled over 10 seeds × 6 blocks = 60 values
per slot:

| Param | Mean \|θ\| | Median \|θ\| | Max \|θ\| | Count |
|---|---|---|---|---|
| `cx` | 0.8643 | 0.7727 | 2.3820 | 60 |
| `cz` | 0.8777 | 0.6557 | 3.4628 | 60 |
| `ex` | **1.0958** | 1.0763 | 3.4310 | 60 |
| `ez` | 0.9124 | 0.7120 | 3.5864 | 60 |
| `mx` | 1.0344 | 1.0102 | 2.9876 | 60 |
| `mz` | 0.9365 | 0.6908 | **6.9585** | 60 |
| `o`  | 0.6702 | 0.6823 | 1.6122 | 60 |
| `i`  | **0.4623** | 0.3308 | 2.7497 | 60 |
| `d`  | 0.5613 | 0.4896 | 1.5610 | 60 |

Every slot sits in the **0.46–1.10 rad** band. The rotation-carrying slots (`ex`, `mx`,
`ez`, `mz`, `cx`, `cz`) are the largest; `i` and `d` are the smallest but still ~10×
the inserted-gate scale. No slot is anywhere near 0.0005 rad.

### 3.3 Inserted-gate angles

| Condition | Mean \|θ\| | Median \|θ\| | p90 \|θ\| | Max \|θ\| | Frac < 0.1 rad |
|---|---|---|---|---|---|
| Frozen | 0.0389 | **0.0000** | 0.1178 | 1.1824 | 0.875 |
| Joint  | 0.0448 | **0.0000** | 0.1255 | 1.2658 | 0.872 |

A **median of exactly zero** means more than half of all inserted gates never move off
their no-op initialisation at all. About **87%** stay below 0.1 rad. The p90 (~0.12 rad)
is roughly where the *bottom decile* of original angles begins.

### 3.4 The comparison that answers the question

| Quantity | Value |
|---|---|
| Typical original angle (mean \|θ\|) | 0.824 rad |
| Typical inserted angle, frozen (mean \|θ\|) | 0.039 rad |
| Ratio | **21× smaller** |
| Inserted drift as % of native scale | **4.7%** |

Answering the meeting question directly: the original angles are **~0.5–1 rad**, *not*
~0.0005 rad. A 0.05 rad drift is therefore ≈5% of a typical rotation.

## 4. Interpretation

- The inserted gates are **functionally near-no-op**. Their angles are a small fraction
  of the rotations the circuit actually relies on, and over half are exactly zero.
- This **strengthens** the frozen-optimality hypothesis. Combined with the frozen
  Δ test-accuracy of −0.0003 ± 0.0073 (statistically zero), the picture is consistent:
  added gates neither move meaningfully nor buy accuracy.
- The residual ~0.04 rad is best read as **optimizer noise along flat directions**, not
  as evidence of unexploited circuit capacity. §3.3's long tail (max ≈ 1.2 rad) shows a
  minority of gates do move substantially — those are the flat-direction excursions that
  `DEGENERACY_PCA_REPORT.md` characterises.
- Frozen and joint conditions give nearly identical inserted-angle statistics
  (0.039 vs 0.045 rad; both median 0). Letting the originals co-adapt does **not**
  liberate the inserted gates to do more work.

## 5. Caveats

- **Angles are unwrapped.** Rotation angles are 2π-periodic, so the max of 6.96 rad in
  `mz` is functionally equivalent to 6.96 − 2π ≈ 0.68 rad. The unwrapped convention is
  deliberate (the meeting asked for raw drift), but it **inflates the mean and max** of
  the original-angle distribution. The *median* (0.667 rad) is the robust statistic and
  is unaffected by this — it independently confirms the O(1 rad) scale, so the headline
  conclusion does not depend on the wrapping choice.
- Inserted-angle statistics pool across all `n_gates` values. Per-gate-count behaviour
  is broken out in `GATE_INSERTION_FROZEN_REPORT.md`; pooling is appropriate here
  because the question is about scale, not about the gate-count trend.
- All 10 base optima come from the same (L=3, P=2) architecture and the same training
  protocol. The O(1 rad) scale is a property of *this* ansatz at convergence and should
  not be assumed for other (l, p).

## 6. Reproduce

```bash
cd tic-tac-toe/paper-replication
../.venv-shinka-ttt/bin/python angle_magnitude_baseline.py
# reads base_optima/ and gate_insertion_frozen_results/; writes angle_magnitude_baseline.png
```

## 7. Bottom line

Original cemoid angles live at **~0.5–1 rad**. Inserted gates settle at **~0.04 rad**,
median exactly zero. The drift that earlier reports flagged is **~5% of the native angle
scale** — small enough that it should be treated as flat-direction noise, and it does
**not** indicate that the converged ansatz left capacity on the table.
