# Gate-Insertion Robustness Analysis
## cemoid Ansatz — L=3, P=2

---

## 1. Motivation

The evolutionary sweep over L (layers) and P (cemoid block repetitions) identified **L=3, P=2** as a high-performing configuration for the tic-tac-toe quantum classifier (test accuracy 0.663 in the sweep; mean 0.679 across 50 random initialisations).

A natural question is: *how robust is this solution?*  A truly optimal circuit should act as a stable attractor in the loss landscape — any perturbation should relax back towards the same solution.  We test this by inserting additional, freely trainable rotation gates into the circuit.  Under the optimality hypothesis:

> **If the trained L=3, P=2 solution is globally optimal, any extra gate inserted anywhere should converge to rotation angle = 0 (a perfect no-op).**

If the learned angles are *not* near zero, the optimizer has found a *different* but equally valid solution — evidence that the loss landscape contains multiple degenerate attractors.

---

## 2. Methods

### 2.1 Base circuit

The cemoid circuit for L=3, P=2 consists of three identical layers, each containing one RX data-encoding block followed by two cemoid ansatz blocks (9 shared trainable parameters each).  Total parameters: 3 × 2 × 9 = **54 gate parameters**.

### 2.2 Insertion procedure

**Slot enumeration.** For L=3, P=2 we define insertion slots between every circuit segment:

```
Layer 1: [slot 0] → feature_map → [slot 1] → cemoid → [slot 2] → cemoid → [slot 3]
Layer 2: [slot 4] → feature_map → [slot 5] → cemoid → [slot 6] → cemoid → [slot 7]
Layer 3: [slot 8] → feature_map → [slot 9] → cemoid → [slot 10]
```

This yields **10 slots** × **9 qubits** × **3 gate types** (RX, RY, RZ) = **270 distinct positions**.

**Gate sampling.** For each gate count N ∈ {1, 2, 3, 5, 8, 13, 21}, N positions are drawn uniformly at random without replacement using a fixed configuration seed (seed = 42), ensuring the same circuit topology is compared across all training seeds.

**Initialisation.** Extra gate angles are initialised to **exactly 0** — a perfect no-op at the start of training.  Cemoid parameters are initialised from a small uniform distribution (as in the baseline), using 10 independent training seeds per gate count.

**Joint optimisation.** All parameters (cemoid blocks + extra gates) are concatenated into a single flat vector and optimised jointly with Adam (lr = 0.03), 100 epochs, 30 steps/epoch, batch size 15.

### 2.3 Baseline

For comparison, 50 independent random initialisations of the unmodified L=3, P=2 circuit were trained under identical conditions (Experiment 1 — seed robustness sweep).

### 2.4 Compute

All jobs ran on the Bouchet HPC cluster (Yale) via SLURM.  The baseline sweep used 50 array tasks; the gate-insertion sweep used 70 array tasks (7 gate counts × 10 seeds), each allocated 8 CPUs and 12 GB RAM.

---

## 3. Results

### 3.1 Before vs. After — training dynamics

**Figure 1** compares the full training trajectories (100 epochs) between the baseline (no extra gates, n=50) and the augmented circuit (+5 extra gates, n=10).

![Before vs After training curves](fig1_before_after.png)

Both conditions converge along nearly identical trajectories and plateau at statistically indistinguishable final accuracies:

| Condition | n | Mean final acc | Std |
|---|---|---|---|
| Baseline (no extra gates) | 50 | 0.679 | 0.048 |
| +5 extra gates | 10 | 0.662 | 0.026 |

The difference of 0.017 is within one standard deviation of either distribution.  Adding 5 extra parameters does not measurably harm performance.

### 3.2 Circuit diagram — augmented circuit

**Figure 2** shows the full schematic of the L=3, P=2 cemoid circuit with the 5 inserted gates highlighted in orange.  Each layer contains one feature-map block (FM, light blue) followed by two cemoid blocks (CB, light purple).  The 5 extra gates (RX/RY/RZ) are inserted at specific slot–wire positions determined by config seed 42; their final learned angles are annotated on each gate.

![Augmented circuit schematic](fig3_augmented_circuit.png)

The slots where extra gates land span all three layers: one gate sits at the very start of the circuit (before layer 1's feature map, slot 0), two gates share the same slot between layers 1 and 2 (slot 4, targeting different wires), one gate precedes the feature map of layer 2 (slot 6), and one sits inside layer 2 between its two cemoid blocks (slot 7).

### 3.3 Showcase: angles of the 5 inserted gates

**Figure 3** examines a single high-performing run from the +5 gates condition (train seed 1, final accuracy = **0.715** — above the baseline mean).

![Angles of inserted gates and training curve](fig2_angles_and_curve.png)

The five inserted gates and their learned angles are:

| Gate | Type | Qubit | Circuit slot | Final angle (rad) | Significant? |
|------|------|-------|-------------|-------------------|--------------|
| 1 | RZ | q7 | 0 (before layer 1) | ≈ 0.000 | No |
| 2 | RZ | q2 | 4 (before layer 2) | +0.060 | Yes |
| 3 | RY | q3 | 4 (before layer 2) | +0.117 | Yes |
| 4 | RY | q4 | 6 (after cemoid, layer 2) | −0.158 | Yes |
| 5 | RZ | q5 | 7 (after cemoid, layer 2) | −0.321 | Yes |

**Four of five gates learned non-trivial angles** (|θ| > 0.05 rad), as also visible in the circuit diagram above.  This directly contradicts the optimality hypothesis: if the original solution were a strict global minimum, gradient descent initialised at angle = 0 would not move.  Instead, the optimizer found a neighbouring solution of comparable quality with non-zero extra parameters.

The training curve (right panel) shows clean convergence to 0.715, confirming the augmented model is not just memorising noise.

### 3.4 Sweep across gate counts

**Figure 4** shows mean accuracy and mean absolute extra-gate angle across all gate counts.

![Gate insertion sweep](gate_insertion_analysis.png)

| Extra gates | Mean accuracy | Std | Mean \|θ_extra\| (rad) |
|-------------|--------------|-----|------------------------|
| 1 | 0.679 | 0.039 | 0.349 |
| 2 | 0.677 | 0.040 | 0.212 |
| 3 | 0.682 | 0.048 | 0.095 |
| 5 | 0.662 | 0.026 | 0.092 |
| 8 | 0.676 | 0.034 | 0.232 |
| 13 | 0.662 | 0.033 | 0.262 |
| 21 | 0.657 | 0.027 | 0.188 |

Two findings stand out:

1. **Accuracy is stable across all gate counts.** The mean ranges from 0.657 to 0.682 — a spread of only 0.025 — compared to the baseline of 0.679.  Even 21 extra parameters do not degrade performance, indicating no barren plateau effects at this scale.

2. **Extra gate angles are consistently non-zero.** Mean |θ_extra| ranges from 0.09 to 0.35 rad across all conditions.  There is no monotonic trend with gate count, suggesting that different circuit topologies (determined by config seed 42) find different non-zero configurations rather than uniformly larger distortions.

---

## 4. Interpretation

The gate-insertion experiment reveals two complementary properties of the L=3, P=2 cemoid solution:

**Practical robustness:** Accuracy is insensitive to circuit augmentation.  The model can absorb additional free parameters without performance loss, a desirable property for near-term quantum hardware where gate errors are unavoidable.

**Solution non-uniqueness:** The original trained solution is not a strict global minimum — it is one point in a family of equivalent solutions connected by continuous deformations.  The extra gates consistently drift to non-zero values because the loss landscape contains flat directions (degenerate minima or a manifold of equally good solutions).  This is consistent with the broad accuracy distribution seen in the seed robustness sweep (range 0.565–0.788), where different initialisations find different but comparably performing solutions.

**Implication for ansatz design:** The degeneracy is not necessarily harmful — it means the model is expressive enough to represent many equivalent classifiers.  However, it complicates interpretability: the specific gate angles of any single trained instance should not be treated as physically meaningful without further analysis (e.g., gradient-based importance scoring or parameter freezing experiments).

---

## 5. Summary

| Question | Finding |
|---|---|
| Does accuracy hold with extra gates? | Yes — stable within ±0.025 across 1–21 extra gates |
| Do extra gates converge to zero? | No — mean \|θ\| = 0.09–0.35 rad, well above zero |
| Is the original solution uniquely optimal? | No — multiple equivalent attractors exist |
| Is the model robust for practical use? | Yes — performance is consistently near 0.67–0.68 regardless of initialisation or extra parameters |

---

## 6. EA-Evolved Circuits: Same Analysis

### 6.1 Motivation

The cemoid ansatz is a hand-designed, regular circuit.  The EA search produces circuits whose structure is discovered automatically via evolutionary pressure on the tic-tac-toe classification task.  We now ask: **do EA-evolved circuits exhibit the same robustness properties as the hand-crafted cemoid ansatz?**

Two complementary failure modes are possible:

- **High variance across seeds** → the EA circuit found a narrow, fragile optimum that is hard to re-discover with random initialisation.
- **Large extra-gate angles** → the circuit is under-constrained; the EA arrived at a degenerate family of solutions rather than a unique one.

### 6.2 EA Programs Analysed

Top-3 programs from the evolutionary run `ttt_qml_cli_20260605_124906`, ranked by held-out test accuracy:

| Rank | Program ID | Generation | Val acc | Test acc | Params | Depth |
|------|-----------|------------|---------|----------|--------|-------|
| 1 | `cec1d47c` | 17 | 0.567 | 0.533 | 66 | 70 |
| 2 | `9da56dab` | 13 | 0.550 | 0.517 | 84 | 132 |
| 3 | `a6487a61` | 3 | 0.533 | 0.517 | 78 | 70 |

All three use the same re-upload structure as cemoid (N\_UPLOADS=3, N\_REPEATS=2), giving an identical 10-slot circuit skeleton and 270 possible gate-insertion positions.

### 6.3–6.5 Superseded (2026-07-18): converged-EA analyses completed under separate reports

The 150-run / 210-run arrays planned above for the **quick-protocol** programs
(`cec1d47c`, `9da56dab`, `a6487a61`) were never executed
(`ea_robustness_histories/` and `ea_gate_insertion_results/` are empty), and
running them is no longer scientifically justified: the 2026-06-18 protocol
correction deemed quick-eval rankings unreliable, and the whole §6 question was
re-asked — and answered — for the **converged-objective EA winner** (`b6ba28a0`,
66 params, gen 16 of `cemoid_ea_converged`) at larger scale:

| Analysis | Report | Headline |
|---|---|---|
| Seed robustness (**500** seeds) | `SU2_ROBUSTNESS_500SEED_REPORT.md` | **0.730 ± 0.041** (median 0.735, range 0.598–0.815), unimodal (dip p = 0.29) but left-skewed (Shapiro p < 10⁻⁵). **+0.032 mean over cemoid** at the same L=3, P=2 geometry, marginally tighter spread. |
| Frozen gate insertion (10 bases → 140 runs) | `SU2_GATE_INSERTION_FROZEN_REPORT.md` | Frozen Δacc = **−0.0022 ± 0.0094** (zero); median learned \|θ\| = **0.024 rad**; joint control +0.0051 ± 0.0215 (also zero). Same constrained-optimum behaviour as cemoid. |

**Resolution of §6.5's three hypotheses** (for the converged winner): none of the
failure modes applies. The evolved circuit is (1) *not* brittle — 500-seed spread
is as tight as cemoid's; (2) *not* lower-capacity at this geometry — it is
*more* accurate on average; and (3) it shows the same
constrained-optimum/degenerate-landscape signature as cemoid (near-zero inserted
angles, flat accuracy under augmentation). The 0.52–0.53 accuracies quoted in
§6.2 were artifacts of the quick protocol's truncated training, not properties
of the circuits.

---

## 7. Combined Summary

| Question | Cemoid L=3,P=2 | EA prog #1 | EA prog #2 | EA prog #3 |
|---|---|---|---|---|
| Mean test accuracy (50 seeds) | 0.679 | — | — | — |
| Seed std | 0.048 | — | — | — |
| Accuracy stable with extra gates? | Yes | — | — | — |
| Extra gates converge to zero? | No (0.09–0.35 rad) | — | — | — |
| Loss landscape: degenerate? | Yes | — | — | — |

*Dashes to be filled after cluster fetch.*

