# Response to the third referee report

We thank the referee for a report that located a real and serious defect, and for saying plainly which
parts of the work survive. The principal objection was correct, we reproduced it numerically before
touching anything, and it invalidates every group-arm power figure in the previous version. Protocol
Addendum A6 was written and committed (`3499bb16`) before any A6 analysis was run.

---

## 1. The calibration and scored predictors differ

**The referee is right, and the size is exactly as predicted.**

In `experiments/exp_matched.py` line 203 the group arm set `S = s * G`, while `shared_record()`
collected `s` shots per orbit point and `losses_from_record()` scored the raw baseline from
`record[:, 0]` — an `s`-shot mean. The calibration contrast therefore estimated

    E[D_cal] = R_{2s}(strat) − R_s(raw) = Δ_{2s} − E[σ₀²(X)]/(2s),

not the `Δ_{2s}` used as truth. On `heisenberg_raw_n6` at `s = 8` we measured:

| quantity | value |
|---|---|
| `Δ_{2s}` (the reported "truth") | **+0.00160** |
| `E[D_cal]` (what calibration measured) | **−0.05097** |
| predicted offset `σ₀²/(2s)` | **0.05258** |
| measured difference | **−0.05258** |

The offset matches the referee's formula to five decimal places. The calibration record favoured the
group policy by roughly **thirty times** the effect under study. As the referee noted, the group-free
arm has no such mismatch, so the asymmetry contaminated every group-versus-group-free selection and
every group-arm power figure. No group-arm power number survives; they are withdrawn.

**Repair (A6.1).** Every candidate is now defined at a common total `S`. The orbit block holds `S/G`
shots at each of the `G` orbit points, which is exactly what the stratified policy deploys; because the
identity circuit appears there with only `S/G` shots, an additional block of `S − S/G` identity shots
is collected and size-combined with it, so the raw baseline receives exactly `S` identity shots. Cost
per calibration instance is `S(2 − 1/G)`, which is `3s` for `G = 2` with `s = S/2` — the referee's
bound, and it is asserted in a test rather than stated in prose. The reuse of the first `S/G` identity
outcomes inside the baseline creates within-instance dependence between the two terms of the paired
difference; that is permitted because the Maurer–Pontil certificate requires only boundedness of the
paired difference, and it is now documented in the module rather than hidden.

**Audit (A6.2, stop gate (a)).** `shotcert/record.py::audit` compares the record's expected loss for
every policy against `reference_risk_x`, which enumerates draw sequences and binomial outcomes and was
written without reference to `core._estimator_moments`. Across three tasks (control, Heisenberg,
cluster) at `S ∈ {4, 8, 16, 64}` and four policies per arm, the maximum disagreement is **5.6e-17**.
The audit is a permanent test (`test_record.py`, 5 tests), and it earned its keep immediately: it
failed loudly when we added shrinkage of the *orbit* estimator, because the independent enumerator had
no branch for that estimator and would otherwise have silently agreed with a different one. The
regression itself is pinned numerically — the test asserts that the old `s`-shot baseline is off by
exactly `σ₀²/(2s)`.

---

## 2. The reported negative is not yet a matched-budget comparison

**Accepted, and the conclusion changes.**

The referee is right that quoting each arm's best risk difference at a common shots-per-circuit let the
group arm deploy `2s` shots against the group-free arm's `s`, and that a frontier whose grid starts at
`n = 100, s = 8` mechanically produces a factor of two when both arms cross at their first grid point.

A6.3 fixes the budget instead of the grid: `B = calibration preparations + deployment preparations` is
fixed, each arm chooses its `n`, its per-prediction total `S` and its admissible policies subject to
`B`, and the reported endpoint is **absolute realised deployed risk**, not a difference against an
arm-specific baseline. Realised risk is exact rather than simulated — the only randomness is the
calibration record, and each candidate's `R_S(a)` is available in closed form and verified against
enumeration to 1e-17 — so what is Monte-Carlo is only the selection.

Two further unfairnesses the referee's framing exposed, both now removed:

- **Menu cardinality.** The group arm had 2 candidates and the group-free arm 6. The arms now carry
  **seven candidates each**, drawn from the same two families (unshrunk, and shrinkage toward the
  declared constant at five strengths), differing in exactly one structural respect: whether the base
  estimator uses the orbit.
- **A second variance-reduction device.** Shrinkage had been given only to the group-free arm. The
  `Policy` class gained a `base` field so shrinkage can be applied to the orbit estimator too; without
  this the group-free arm had two ways to buy variance reduction and the group arm one.

**The blanket negative does not survive the repair.** With parallel menus at equal total budget the
result is **mixed**: across 18 (task, budget) cells the group arm attains lower realised risk in **10**
and the group-free arm in **8**, with violation probability 0.000 in every cell for both. For example on
`cluster_n7` at `B = 16000` the group arm attains **0.06536** against the group-free arm's **0.06629**,
while on `heisenberg_raw_n6` at `B = 64000` the group-free arm wins (**0.02638** vs **0.02937**). The
abstract's "cheaper on six of seven tasks" is therefore withdrawn, along with the corresponding
contribution sentence; the repaired statement is scoped to the tested tasks and budgets and reports both
directions. The old matched table is retained in the manuscript but explicitly marked superseded, with
the defect's magnitude generated from a reproduction script rather than quoted from memory. As the
referee put it, A2.7 properly prohibits an *advantage* claim, but its failure never established that
symmetry spending is dominated.

Because the endpoint is absolute realised risk at a fixed total budget, and because the group arm's
extra calibration cost (`S(2 − 1/G)` per instance) is charged rather than assumed away, this is the
comparison the referee asked for; we report it as neither arm dominating.

---

## 3. No top-tier contribution: the structural result (A5, A6.5)

We agree the risk identity, the calibration split and the Maurer–Pontil radius are bookkeeping, and we
no longer present them as contributions. Two results replace them.

**(a) The repayment boundary, in closed form.** From the verified risk functional, the mixture spending
`wS` shots across the orbit and `(1−w)S` on raw has variance `[wσ̄² + (1−w)σ₀²]/S` — linear in `w` —
and discrepancy `D₀ + 2wB + w²A`, so

    R_S(w) = D₀ + σ₀²/S + 2wB + w²A + wV/S,   R″(w) = 2A > 0,
    w*(S) = (Δ_ideal + A)/(2A) − V/(2AS),

with `Δ_ideal = D₀ − D_G = −2B − A` and `V = σ̄² − σ₀²`. This is not a restatement of the variance
identity: it solves the allocation problem, and it has three checkable consequences. Symmetry is a
**luxury good** when `V > 0` (`dw*/dS = V/2AS² > 0`) and worth **nothing** below
`S_on = V/(Δ_ideal + A)`; full symmetrisation is optimal only above `S_full = V/(Δ_ideal − A)`, so
partial symmetrisation occupies an explicit band — which is the pattern the physical risk tables showed
empirically *before* the derivation existed; and when `V ≤ 0` symmetry pays at every budget. The
grid-argmin of the **enumerated** risk agrees with `w*` to within one grid step on every task.

The non-obvious case is the interesting one: on `heisenberg_raw_n6`, `Δ_ideal = −0.001635` and
`V = +0.000763` (the values in the artifact backing the table), so symmetrisation **hurts** the ideal
predictor and full averaging is worse than using no symmetry at all — yet `w* = 0.383`, and the
enumerated risk's argmin is 0.36–0.37. Both coefficients are expectations estimated from a finite input
sample, and they move with the sample (`Δ_ideal` was `−0.00213` on a 120-instance draw and `−0.001635`
on the frozen 300-instance one); the *sign* is what the argument uses and it is stable, which is exactly
why the rule must estimate these quantities from shots rather than assume them. Estimated from shots by cross-fitted
half-record products (each quadratic functional formed as a product of one statistic from each of two
independent half-records, which is unbiased without any bias correction), the rule attains **0.00563**
against raw **0.00660** and full averaging **0.00887** at the same `S = 256`. Its noise is reported
rather than smoothed: standard deviation 0.4 and regret 3e-3 at `S = 16`, versus ≤0.05 and <2e-4 at
`S = 256`.

**(b) The general boundary the referee asked for.** Neyman allocation of the orbit share replaces
`V = σ̄² − σ₀²` with `(mean_g σ_g)² − σ₀²`, and by Cauchy–Schwarz the recoverable amount is exactly

    Var_g(σ) = (1/G)Σσ_g² − ((1/G)Σσ_g)².

Writing `μ_g(x) = f(a_g x)`: **if the group action preserves the input law, `μ_g(X)` and `μ₀(X)` are
identically distributed, `E[σ_g²]` is the same at every orbit point, and `Var_g(σ) = 0`** — so on a
measure-preserving orbit no allocation recovers anything and the cost `V` prices is irreducible. Every
action in this study is measure-preserving, which is why the effect is absent rather than small. We
built the counterpart to show the mechanism is real and not missing: the same label, model and group
with an input law the action does *not* preserve gives `σ = (0.7044, 0.4601)`, `Var_g(σ) = 0.014924`,
and a measured gain of **+0.000058** at `S = 256` against the predicted `Var_g(σ)/S = 0.000058`. On the
five measure-preserving tasks the gain is `−0.000000`, i.e. integer rounding only.

That is the shape the referee described: a calculable quantity that determines attainable risk, a
matching method, and a proof of when the advantage vanishes — rather than a local null.

---

## 4. Mechanisms that are not actually independent

**Accepted.** We verified `cluster_even` and `cluster_raw` are numerically identical
(`R_a0 = 0.011375`, `strat = 0.009340` for both) and they are now reported as one mechanism. A6.4
requires any mechanism claim to carry the measured odd component and shot variance of each mechanism,
and to say "one mechanism was tested" where they cannot be made distinct. The Heisenberg input flip is
retained only as a paired control transformation, per our own round-two correction, and the new text
describes it as a denoising control rather than a symmetry decision.

---

## 5. Stop gate

Adopted verbatim in force as A6.6: (a) calibrated and deployed estimands agree exactly — **passes**, to
5.6e-17 with the audit pinned as a test; (b) at least one nonvacuous finite-sample-valid decision at a
feasible cost; (c) either a material matched-budget gain or a substantive lower-bound explanation of
why none is possible. On (c) we now report both: a material matched-budget gain exists for the
theorem-derived partial weight on `heisenberg_raw_n6` and for the group arm on `cluster_n7` at
`B = 16000`, and the boundary result explains when neither can exist. If (b) fails in the completed
frontier run, the selector is stopped and archived rather than revised again, and the paper will say so.

---

## 6. Presentation and verification

All accepted and fixed:

- The historical appendix reused the live labels `sec:certify` and `sec:ledger`; those occurrences are
  now `sec:certify_hist` and `sec:ledger_hist`, checked mechanically.
- The reproducibility paragraph claimed the pre-A2 test count. It now states the real number, and the
  number is **generated** by counting `def test_` in the test files rather than typed, so it cannot go
  stale again: **35 tests**.
- On the number checker: the referee is exactly right that a presence check cannot catch a value paired
  with the wrong quantity — that is precisely how the `s`-shot baseline survived. Headline sentences in
  the new sections are therefore **generated from the result JSON** (`make_alloc_tab.py`,
  `make_profile_tab.py`), so prose cannot misattribute a number in the first place, and the remaining
  prose is covered by semantic claim binding that pins each sentence to an artifact, task, budget and
  statistic.

## What we now claim, and what we do not

Claimed: the closed-form repayment boundary `w*(S)` with its thresholds, verified against independent
enumeration; that `Var_g(σ)` is exactly the recoverable part of the symmetrisation cost and vanishes for
measure-preserving orbits, with both sides demonstrated; a common-estimand calibration record whose
expected contrast equals the deployed-risk difference to machine precision, with the ledger cost
`S(2 − 1/G)`; and a mixed equal-total-budget frontier.

Not claimed: that symmetry spending is dominated (withdrawn); any group-arm power figure from the
contaminated sweep (withdrawn); that the boundary covers policies outside the convex allocation class;
and any transfer of the `Var_g(σ)` gain to a measure-preserving physical task, where it is provably zero.
