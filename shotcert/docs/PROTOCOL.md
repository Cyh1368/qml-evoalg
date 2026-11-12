# ShotCert protocol v1 — frozen before implementation (12 Nov 2026)

Governs the new study. Nothing here may be changed after final outcomes exist; amendments are
appended with a date and a reason, never edited in place.

## 0. Access model (stated first, because comparisons are meaningless without it)

**Scalar single-copy shots.** One labeled quantum state preparation per calibration instance, one
circuit execution batch per prediction, computational-basis measurement of a diagonal observable
`O = Σ_x o(x)|x⟩⟨x|`. No two-copy access, no shared Pauli measurements, no classical shadows, no
mid-circuit reuse. Every baseline in this study receives exactly this access; where a published
method needs more (e.g. a twirl–swap test), it is compared only after we say so, and never given
strictly less than we use ourselves.

**Costs are counted separately and never conflated.**
`shots` = measurement repetitions; `preparations` = independently prepared labeled states;
`circuits` = distinct parameterised circuits compiled (each distinct group element applied to the
ansatz is one circuit); `calibration_labels` = labeled instances spent on calibration;
`switching` = fixed overhead `c > 0` per distinct circuit, varied as a declared stress parameter.
Total deployment cost per prediction is `S shots + c·(distinct circuits)`. A method that gets free
calibration or free state knowledge invalidates the comparison.

## 1. The deployed object and its risk

For input `x`, group element `g` from the policy's orbit set `G_a`, let
`μ_g(x) = E[shot outcome | g, x]` and `σ²_g(x) = Var[shot outcome | g, x]`.
A policy `a = (G_a, k, S, w, allocation)` draws `k` elements, spends `S` shots in total across them
with weights `w` summing to one, and outputs `Z_a(x)`. With equal weights and `S/k` shots per draw:

```
R_S(a) = E_x[(Z_a(X) − Y)²]
       = Bias(a)²  +  V_G(a)/k  +  Σ(a)/S
Bias(a) = E_x[(E_{g∈G_a} μ_g(x) − y)²]^{1/2}      (orbit-mean bias; independent of k, S)
V_G(a)  = E_x[ Var_{g∈G_a}( μ_g(x) ) ]            (group-draw term; killed by k, not by S)
Σ(a)    = E_x[ E_{g∈G_a} σ²_g(x) ]                (shot term; killed by S, not by k)
```

Two structural facts, both to be **verified against brute-force enumeration** rather than asserted:

* **(F1) The split is free in shots.** At fixed total `S`, `Σ(a)/S` is invariant to `k`; only
  `V_G(a)/k` moves. So under a pure shot budget with `c = 0`, `k = S` weakly dominates `k < S`.
* **(F2) Circuit switching is the real tradeoff.** With `c > 0`, distinct circuits cost, and
  `(k, S/k)` has an interior optimum. The optimum is *not* classical stratified allocation: it
  trades a variance term against a per-circuit overhead, and it is the object this study measures.

## 2. Estimands

* **Primary:** `Δ_S(a) = R_S(a) − R_S(a₀)` at **matched total shots** `S`, against the raw policy
  `a₀` (identity, `k = 1`, all `S` shots). Risk is of the deployed stochastic predictor, not of an
  ideal expectation value.
* **Operational primary:** `N_cert(ε, δ)` = number of calibration preparations needed for the
  certificate in §4 to select a policy with `Pr[R_S(a_sel) − R_S(a₀) ≤ ε] ≥ 1 − δ` **and**
  acceptance power ≥ `1 − β` when a useful policy exists. Fallback to `a₀` counts as a safe
  abstention, not as success.
* **Secondary:** realized deployed MSE, fallback rate, distinct circuits, wall time.

`ε` is fixed in task units before any confirmatory run: `ε = 0.01` in squared-outcome units for the
control (≈ the interior-policy gain scale measured in the pilot) and `ε = 0.02·Var(Y)` for the
physical tasks, with `δ = 0.05`, `β = 0.20`. Declaring `ε` before outcomes is what makes a negative
`ε` a claim of improvement rather than of non-degradation.

## 3. Policy menu — frozen before calibration

`a₀` raw identity · `A_full` full orbit average (stratified, all `|G_a|` elements) ·
`A_sub` declared proper subgroup · `A_rand(k)` orbit-randomised, `k ∈ {1, 2, 4, 8, S/4, S/2, S}` ·
`A_mix(w)` weight `w ∈ {0.25, 0.5, 0.75}` between raw and orbit-averaged prediction ·
`A_strat` equal-shot stratification · `A_oracle` allocation chosen from 10⁴ offline shots
(reference only, never a competitor). The menu is finite and fixed before calibration; no policy is
generated from calibration losses (that would require Chen-style post-selection accounting, which we
do not claim).

## 4. Certificate, and the five errors that killed the previous submission

Paired calibration on `n` **independent labeled instances** (the independence unit; shots and
optimizer seeds are not instances). For instance `i`, draw paired finite-shot outcomes for `a` and
`a₀` and record `D_i = (Z_a − Y)² − (Z₀ − Y)²`. Certify with an empirical-Bernstein bound on
`E[D]` (variance-adaptive, explicit about sub-exponential tails of squared loss), select the best
certified policy, fall back to `a₀` otherwise.

Rules carried over from `research/ARCHIVED.md`, enforced in code and tests:

1. A calibration panel with fewer than a prespecified number of relevant cases returns
   **"unsupported"**, never "no admissible setting". Panel support is printed with every decision.
2. Calibration data and evaluation data are disjoint **at the instance level**, and the whole
   calibration exercise is repeated on independent datasets to estimate violation frequency.
3. Estimand conditioning equals estimator conditioning. Effect magnitudes are conditioned on the
   events the theorem names.
4. No confidence set is built from an observed p-value. Equivalence, if needed, uses two one-sided
   tests with the family correction applied to the p-values.
5. A verdict may not be broader than the table it is computed from. Regimes absent from a mixture
   are excluded from the sentence describing it.
6. Ties are ties: policies are compared by **regret against `a₀`** with paired uncertainty and a
   practical margin, never by unique argmin over names.

## 5. Tasks

* **Control (2 qubits).** Three predeclared regimes — orbit averaging helps, hurts, and an interior
  partial-averaging policy is best at matched `S` — with `R_S` enumerable exactly (all outcomes ×
  all draws). Purpose: verify F1/F2 and the estimator against known truth, and check certificate
  coverage across independent repetitions.
* **Physical primary (6–8 qubits).** Bond-alternating Heisenberg response regression: labels defined
  by an independently computed observable expectation, not by a symmetry label assigned after the
  symmetry is broken. Inhomogeneous fields/disorder and amplitude-damping plus readout asymmetry are
  varied **separately**.
* **Independent evaluation (7–9 qubits).** Cluster-Ising diagnostic recognition, different task
  mechanism, split before generating symmetry images or shots. Public device data, if used at all,
  is an external check only: shots of one state are measurement replicates, not task instances.

## 6. Stop gates

Stop the method claim if (i) the advantage vanishes when a baseline gets equal access; (ii) the
valid certificate falls back at every feasible budget; (iii) the group-draw term collapses to
classical stratified variance under relabelling; (iv) the best evidence would be another synthetic
label perturbation of the kind already rejected; or (v) the only result is failure to reject a null.
