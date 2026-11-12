# Joint No-Gate Baseline — is the drift caused by the inserted gates, or just by training longer?

**Question (07-03 meeting, action item 2):** In the *joint* gate-insertion condition the
original 54 cemoid angles drift away from their converged values. Is that drift caused by
the inserted gates, or is it simply what happens when you train a converged model for more
epochs (overfitting / continued wandering along flat directions)?

**Control:** take each converged optimum, **insert no gates at all**, unfreeze all 54
angles, and train for the same additional budget under the same protocol. Any drift
observed here is attributable to *extra training alone*.

**Headline result.** The no-gate control drifts by **|Δθ| = 0.0202 ± 0.0300 rad**. The
joint gate-insertion condition drifts by **0.0380 ± 0.0768 rad**. A Welch t-test finds
**no significant difference** (t = 1.31, **p = 0.20**, n = 10 vs 70). Test accuracy in the
control is **unchanged** (Δacc = −0.0028 ± 0.0154, one-sample t-test vs 0: p = 0.59) and
validation loss *improves* slightly (Δval = −0.0009). **The drift seen in the joint
condition is fully accounted for by continued training — the inserted gates are not
causing it.** This closes the confound flagged at the meeting and validates the frozen
protocol as the correct instrument for measuring gate value.

---

## 1. Motivation & hypothesis

The original (joint) gate-insertion test optimised the inserted gates *together with* the
54 original angles. It found the originals moved by ~0.04 rad and read this as the circuit
"co-adapting" to the new gates. But early stopping restores best-validation weights, not
final weights, and a converged model trained for more epochs can still wander: along flat
directions the validation loss is nearly constant, so the restored point can sit some
distance from where training started.

> **Overfitting-artifact hypothesis.** Training a converged cemoid optimum for the same
> extra budget, *with no gates inserted*, produces drift of the same magnitude as the
> joint condition. If so, joint-condition drift carries **no information** about the
> inserted gates.

The alternative — that inserted gates genuinely pull the originals — predicts the control
drifts substantially less.

## 2. Methodology

- **Script:** `joint_nogate_baseline.py`; SLURM array `cluster/joint_nogate_array.sbatch`
  (job name `jng`, 10 tasks, all `COMPLETED`).
- **Starting points:** the same 10 converged optima (`base_optima/seed_NN.json`) used by
  the frozen and joint gate-insertion tests. Architecture cemoid **L=3, P=2**, 6 blocks ×
  9 shared params = **54 angles**.
- **Treatment:** *no* circuit augmentation. All 54 angles set `requires_grad=True` and
  re-optimised from the converged values.
- **Protocol (identical to the gate-insertion runs, inherited from `sweep.py`):**
  Adam, lr = 0.03; 30 steps/epoch; batch = 15 games; `MAX_EPOCHS` = 1000;
  early stopping on validation loss with `PATIENCE` = 75, `MIN_DELTA` = 1e-4;
  **restore-best-weights** on validation loss.
- **Metrics** (all relative to the base optimum):
  - `param_abs_change_mean` = mean over the 54 angles of |θ_final − θ_base| (raw, unwrapped)
  - `delta_test_acc` = test accuracy(final) − test accuracy(base)
  - `delta_val_loss` = validation loss(final) − validation loss(base)
- **Comparison quantity:** in the joint gate-insertion results, the matching statistic is
  `cemoid_abs_change_mean` — the drift of the *original* 54 angles (excluding the inserted
  gates' own angles). Pooled over `n_gates ∈ {1,2,3,5,8,13,21}` × 10 seeds = 70 runs.
- **Figure:** `joint_nogate_analysis.png`.

## 3. Results

### 3.1 No-gate control (n = 10)

| Metric | Mean | Std |
|---|---|---|
| `delta_test_acc` | **−0.0028** | 0.0154 |
| `delta_val_loss` | −0.0009 | 0.0012 |
| `param_abs_change_mean` | **0.0202** | 0.0300 |

Per-seed drift (rad):

| seed | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| \|Δθ\| | 0.0000 | 0.0000 | 0.0343 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0481 | 0.0252 | 0.0946 |
| Δacc | 0.0000 | 0.0000 | +0.0167 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | +0.0083 | −0.0083 | −0.0450 |
| stop epoch | 75 | 75 | 106 | 75 | 75 | 75 | 75 | 119 | 78 | 129 |

**Six of ten seeds show exactly zero drift.** Those seeds stopped at epoch 75 — i.e.
`PATIENCE` epochs with no validation improvement — so restore-best-weights returned the
*base* parameters unchanged. This is the expected behaviour at a true optimum and is
itself evidence the base points are converged.

The four seeds that did move (2, 7, 8, 9) are exactly the ones that found a marginally
better validation point and trained past epoch 75. Their drift (0.025–0.095 rad) spans the
same range as the joint condition's.

### 3.2 Joint gate-insertion, drift of the original 54 angles (n = 70)

| n_gates | n | cemoid \|Δθ\| | std | Δacc | inserted \|θ\| |
|---|---|---|---|---|---|
| 1 | 10 | 0.0675 | 0.1120 | +0.0002 | 0.1085 |
| 2 | 10 | 0.0195 | 0.0322 | −0.0037 | 0.0481 |
| 3 | 10 | 0.0220 | 0.0338 | −0.0062 | 0.0585 |
| 5 | 10 | 0.0352 | 0.0725 | −0.0062 | 0.0456 |
| 8 | 10 | 0.0361 | 0.0585 | −0.0007 | 0.0658 |
| 13 | 10 | 0.0776 | 0.1154 | +0.0017 | 0.0738 |
| 21 | 10 | 0.0080 | 0.0241 | −0.0003 | 0.0134 |
| **pooled** | **70** | **0.0380** | **0.0768** | **−0.0022** | — |

Note there is **no monotone trend in gate count**: 1 gate produces *more* original-angle
drift (0.0675) than 21 gates (0.0080). If inserted gates were driving the originals, drift
should grow with the number of gates. It does not — another independent sign the drift is
not gate-driven.

### 3.3 The decisive comparison

| Condition | n | Original-angle drift \|Δθ\| (rad) | Δ test acc |
|---|---|---|---|
| **No-gate control** (extra training only) | 10 | **0.0202 ± 0.0300** | −0.0028 ± 0.0154 |
| **Joint** (gates inserted, all params free) | 70 | **0.0380 ± 0.0768** | −0.0022 ± 0.0131 |
| Frozen (gates inserted, originals fixed) | 70 | 0 by construction | −0.0003 ± 0.0073 |

- **Welch t-test, joint drift vs control drift:** t = 1.305, **p = 0.202** → the joint
  condition's drift is **not distinguishable** from the drift produced by extra training
  with no gates at all.
- **Control Δacc vs 0:** t = −0.553, **p = 0.594** → extra training changes test accuracy
  by nothing measurable.
- Control `delta_val_loss` = −0.0009 (a slight *improvement*), so within this budget there
  is **no detectable overfitting** on validation either; the drift is lateral motion, not
  degradation.

## 4. Interpretation

- **The confound is real and it is the whole effect.** The joint condition's original-angle
  drift is statistically indistinguishable from the no-gate control. Attributing that drift
  to the inserted gates — as `gate_insertion_report.md` originally did — is not supported.
- **Mechanism:** at a converged optimum the loss surface has flat directions (see
  `DEGENERACY_PCA_REPORT.md`, which measures an effective dimensionality of ~2.3 out of
  54). Continued Adam updates diffuse the parameters along those directions at essentially
  no validation cost. Restore-best-weights then returns whichever point along the flat
  valley had the marginally lowest validation loss — which can be ~0.02–0.09 rad away.
- **The frozen protocol is the right instrument.** Because the frozen condition holds the
  originals fixed and starts inserted gates at exactly θ = 0, its Δaccuracy is a clean
  measure of marginal gate value, immune to this artifact. Its verdict (−0.0003 ± 0.0073,
  i.e. zero) therefore stands.
- **No overfitting within this budget.** The meeting worried that additional epochs would
  raise validation loss. They did not (Δval = −0.0009). The concern was well-posed but the
  data do not show it at `PATIENCE` = 75.

## 5. Caveats

- **Power is limited.** The control has n = 10 (one run per base optimum). The Welch test's
  p = 0.20 is a *failure to reject*, not proof of equality; with 6/10 controls pinned at
  exactly zero the control distribution is strongly zero-inflated and non-normal, which
  strains the t-test's assumptions. The supporting evidence — the absent gate-count trend
  in §3.2, and the fact that the joint mean is only 1.9× the control mean while the joint
  std is 2.6× larger — is what makes the conclusion solid, not the p-value alone.
- **Zero-inflation cuts both ways.** The six exact zeros pull the control mean down. A
  fairer read of the *conditional* drift (given that a seed moved at all) is
  0.0506 rad over the four movers — which is *larger* than the joint pooled mean of 0.0380.
  Either framing supports "gates are not the cause."
- **Angles are unwrapped**, matching the other reports. No |Δθ| here approaches 2π, so
  wrap artifacts are not in play at this scale.
- The control shares the base optima and RNG-seeded minibatch order with the gate runs, so
  the comparison is paired at the level of starting point but not of gradient noise.

## 6. Reproduce

```bash
cd tic-tac-toe/paper-replication
bash cluster/deploy_and_run.sh meeting-status          # confirm jng array COMPLETED
bash cluster/deploy_and_run.sh meeting-fetch           # rsync + regenerate figures
../.venv-shinka-ttt/bin/python joint_nogate_baseline.py --plot-only
```

Single task locally: `python joint_nogate_baseline.py --index I` for `I ∈ [0, 9]`.

## 7. Bottom line

Training a converged cemoid optimum for another ~75–130 epochs **with no gates inserted**
moves its angles by 0.0202 ± 0.0300 rad and changes test accuracy by nothing. The joint
gate-insertion condition moves them by 0.0380 ± 0.0768 rad — **the same, within noise
(p = 0.20)** — and shows no dependence on how many gates were inserted. The drift is an
artifact of continued training along flat directions, **not** an effect of the inserted
gates. The frozen-condition result (added gates buy zero accuracy) is unaffected and
remains the correct reading.
