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

---

## Addendum A2 (pre-declared 2026-11-12, before any A2 analysis was run)

A sixth-round review identified six defects. All six were verified in source before being accepted,
and all six are real. This addendum amends the protocol. Nothing below was chosen after seeing new
results; the affected prior results are marked invalid rather than quietly replaced.

**A2.0 Invalidated results.** `results/control.json` (Q2 coverage, Q3 frontier, switching/F2),
`results/physics.json` (frontier), `results/variance.json` (eb_split columns) and `results/bound.json`
are **invalid for any certificate claim**: the bound was wrong (A2.1), the calibration budget was
understated by a factor of the menu size (A2.2), and the switching optimum charged circuits that do
not exist (A2.3). The exact risk tables and the decomposition identity survive, with the caveat in
A2.4 about what the identity check actually establishes.

**A2.1 Correct simultaneous certificate.** For paired contrasts `D_i` in `[a,b]` (here `a=-4`,
`b=+4`, width `b-a=8`, since each squared loss lies in `[0,4]`), Maurer-Pontil Corollary 5 with a
union bound over the `m` candidates of a *fixed* menu gives, with probability at least `1-delta`,
simultaneously for all candidates:

    E[D] <= mean(D) + sqrt(2 * var(D) * ln / n) + 7 * (b-a) * ln / (3 * (n-1)),
    ln = log(2 * m / delta).

There is no `1/n` inside the logarithm. The previous `log(LOSS_RANGE/(delta*n))` shrank with `n` and
went negative for `n > 4/(delta)`, which is why a negative range term appeared in the generated
variance table; that term is not a confidence radius and the results built on it are withdrawn.
`eb_bound` is replaced by `mp_bound(menu_size=m)`; the old function is kept as `eb_bound_broken`
solely so the withdrawal is reproducible. Coverage and power are reported with Monte-Carlo
uncertainty (Wilson intervals over the declared number of repetitions).

**A2.2 Resource ledger, calibration included.** Five quantities are counted separately and never
conflated: `instances` (independent labelled task inputs), `preparations` (physical state copies,
counted per shot-batch executed), `shots`, `switches` (circuit-setting changes within one
prediction's shot sequence), `compilations` (distinct circuits built once and reused). A calibration
run evaluates the whole menu on every instance, so

    shots_calib = n * sum over policies p of shots_used(p),

which is `n*S*m`, not `n*S`. Because the menu depends on `S`, this is recomputed at every frontier
point. The frontier is then swept at matched **total** cost
`B_total = shots_calib + n_deploy * shots_deploy` for a declared deployment count, and every point
reports the full five-tuple. Any comparison that is not at matched `B_total` is labelled as such.

**A2.3 Circuits and switches are different resources, and both are bounded by the orbit.** With
`|G| = 2` at most **two** distinct circuits exist; `min(k, 4|G|)` is retracted. `Policy.circuits`
becomes `min(k, orbit_size)` for randomised draws and `orbit_size` for full averaging. Switching cost
is charged from an explicit schedule: the shot sequence for one prediction is the sorted list of
chosen orbit indices, and `switches` is the number of adjacent pairs that differ. The F2 question is
re-asked as: *does a per-switch cost `c` produce an interior optimum in `k`?* with `circuits` charged
at its true maximum. If the optimum is at the boundary under the corrected charge, that is the
result.

**A2.4 What the identity check does and does not establish.** `exact_risk` and `components` both
consume `_estimator_moments`, so their agreement to 1e-17 is an algebraic consistency check between
two related code paths, not an independent enumeration. A2.4 adds `reference_risk()`, written
against the same task interface but *independently*: it enumerates every group-draw sequence and, for
each, every binomial outcome count for genuinely small `(S,k)` (e.g. `S <= 8`, `k <= 4`), using
multi-start integer compositions rather than the moment formulas. The paper must report
`exact_risk` vs `reference_risk` as the verification, and the Monte-Carlo check as the second,
independent-at-a-distance check, and must stop calling the closed-form agreement "brute-force
enumeration".

**A2.5 Physical action and confirmatory definitions.** The claim that `Delta -> -Delta` is *the chain
mirror* is downgraded unless the operator relation
`M H(Delta) M = H(-Delta)` holds for the **full** experiment, i.e. for the bond-alternating
Hamiltonian, the N\'eel preparation *and* the site-0 observable. `physics.py` gains
`mirror_relation_residual()` which evaluates the residual numerically; if it is nonzero the paper
calls `Delta -> -Delta` a paired input transformation with a measured odd-component cancellation and
makes no symmetry claim. Confirmatory definitions are aligned with the declared `epsilon`:
`violation` = the certificate fires and the selected policy's true `Delta > epsilon` (not `> 0`);
`power` = probability of selecting a policy with true `Delta <= epsilon` when at least one exists;
`selection_rate`, the chosen policy's true risk, and `fallback_rate` are all reported. The physical
`epsilon` is restored to the frozen `0.02 * Var(Y)`, computed and printed, and the `epsilon = 0.01`
substitution is recorded here as a protocol deviation that had already occurred.

**A2.6 Matched-resource comparison, and the reconciliation.** The comparison set is extended with
`generic paired certification`: the *same* certificate and the *same* calibration protocol applied to
a menu that contains no symmetry policy at all (raw plus a non-symmetry smoothing baseline), and with
`symmetry menu + same certificate`, both at matched `B_total` per A2.2. Section 6's phrase
"preparation-limited at fixed total budget" is reconciled with the Section 5.1 withdrawal by
removing it; the surviving bound-independent statement is the law-of-total-variance split, and it is
stated as such.

**A2.7 Stop gate.** If, at matched `B_total`, the symmetry menu does not beat generic paired
certification on both physical mechanisms, the paper reports a scoped negative as its operational
finding and does not describe the study as demonstrating an advantage.

---

## Addendum A3 (pre-declared 2026-11-12, before any A3 analysis was run)

A second review found six further problems. All six were verified in source before being accepted; all
six are real, including two numerical statements in our own response that do not match our own JSON.
This addendum amends the protocol. A2.0's invalidation list is extended, not revised.

**A3.0 Additional invalidation.** Every certificate number produced before A2 (the `control.json`
Q2/Q3 frontier, `bound.json`, the `variance.json` bound split) is invalid for any certificate claim, as
of A2.0, **and must no longer appear in the submitted argument**. Under A2 they were marked withdrawn
in one subsection while still being quoted in the abstract, Section 4 and two tables; that mixing is
itself the defect. They move to a clearly labelled historical appendix and are excluded from the
abstract, the contribution list and every table the paper argues from.

**A3.1 Prose may not quote a number that is not in a generated table.** The response and Section 4.1
said the symmetry menu reaches "power 1.000 at 20,800 shots" (`control_help`) and "1.000 at 96,000"
(`control_interior`). `results/ledger.json` says **0.900 at 20,800** and **0.960 at 96,000**; power
1.000 needs 59,200 and 160,000. This is the exact failure mode the old project's number checker
existed to prevent, and it recurred the moment that checker was left behind. A3.1 adds
`paper/check_numbers.py`: every number in the manuscript above a threshold must appear in a generated
table or in `results/*.json`, or the build fails. Verdict words ("never certifies", "reaches",
"at least") are checked against the same generated values.

**A3.2 Preparations are counted per destructive shot.** The access model is scalar single-copy
measurement: each shot consumes a freshly prepared state. `calib_ledger()` counted one preparation per
policy *batch* (400 preparations for 3,200 shots), contradicting its own docstring. Preparations now
equal shots for destructive single-copy measurement, with any declared non-destructive sharing stated
explicitly rather than assumed. Compilations are the number of **distinct** circuits across the whole
menu (two for a two-element group), not the sum over policies (twelve). Switches are derived from the
schedule actually executed for the calibration run and the selected deployment policy, not summed over
candidates that were never run.

**A3.3 Deterministic policies must share one measurement record.** Every `shrink` policy is a
deterministic rescaling of the same raw finite-shot estimate, so one raw batch evaluates all of them.
The first version resampled a full raw batch per coefficient and charged all of them, inflating the
group-free comparator's cost by the number of shrinkage levels. A3.3 adds a shared-record evaluator:
one measurement record per instance per *distinct circuit*, from which every deterministic function of
that record is computed at zero additional shot cost. The same sharing is applied wherever symmetry
policies read the same orbit-point records. Dependence among policies computed from one record is
handled by the simultaneous bound over the menu, which is valid regardless of dependence; the paired
contrast per policy remains an average over independent instances.

**A3.4 The comparison must isolate what it is said to isolate.** Two distinct questions are separated
and both are reported:
  (a) *What does the group buy?* Same procedure, different candidate sets, matched resources, with
      group-free menus that are resource-efficient (shared-record shrinkage, and a raw-only menu).
  (b) *What does certification buy?* Same candidate set (the symmetry menu), generic plug-in selection
      (argmin of the paired mean loss, no certificate) versus certified selection, matched resources.
The honest expectation, stated before running: our certificate **is** generic paired certification, so
(b) should show no method-level advantage from symmetry-awareness, and any advantage in (a) is an
advantage of the candidate set. If (b) shows nothing, the paper says the procedure is generic and
claims nothing else.

**A3.5 A2.7 is applied where A2.7 says it applies.** The stop gate names **both physical mechanisms**.
The A2 ledger covered only the three synthetic control regimes. A3.5 runs the matched-resource
comparison, with the A3.2 ledger and A3.3 sharing, on the Heisenberg mechanism and on the cluster
mechanism. If the symmetry menu does not beat the strongest applicable equal-access group-free
comparator on both, the paper reports the scoped negative as its operational finding and removes the
advantage language from the contribution list.

**A3.6 Language.** "Certifies" is reserved for the Maurer-Pontil rule, whose finite-sample validity is
assumed and whose cost is reported. The Studentised sweep is described as a selector that selected
useful policies frequently in these simulations, never as a certificate. The `n_required_mp` figure is
described as the cost of that particular conservative bound, not as a lower bound for the statistical
problem or a measurement-complexity result. The first term of Eq. (1) is renamed integrated squared
discrepancy, and the access section states the preparation convention used by the ledger.

---

## Addendum A4 (pre-declared 2026-11-13, before any A4 analysis was run)

A third review accepted the corrections and found six remaining problems. All six were verified before
being accepted; the two numerical ones reproduce exactly (menu sizes 2 vs 9; the two cluster tasks
identical to six decimals). A4 defines the experiments the review asks for and fixes the claims they
will be allowed to support.

**A4.1 Matched certification comparison.** The A3 "what certification buys" comparison is withdrawn as
a result and re-run as a pre-specified one. Defects found: the two arms were deployed at different
total shots (16 vs 8 per prediction); the generic menu's best shrinkage level moved with `s`, so "the
same candidate set" was not the same set across arms; and the plug-in rule carries no `delta`, so a
comparison of it against a `delta`-valid rule is not an equal-confidence comparison. The corrected
experiment holds fixed: one common candidate menu, the same menu size and therefore the same
multiplicity `m` for every selector, the same total shots per prediction `S`, the same calibration
instances, the same total calibration shots. Selectors: plug-in, Studentised, simultaneous
Maurer-Pontil, and a split-sample calibrated rule (pick on one half, certify on the other, so
multiplicity is paid once). Reported for every cell: selection rate, near-optimality
`Pr[R(sel) - min_R <= eps]`, non-degradation `Pr[R(sel) - R(a0) <= eps]`, fallback rate, mean excess
risk `E[R(sel) - min_R]`, and failure rate `Pr[R(sel) - R(a0) > eps]`. Confidence statements are made
only between rules with comparable guarantees, and the guarantee of each rule is named.

**A4.2 Equal multiplicity and a non-trivial group menu.** The A3 group arm contained two candidates
(`a0`, `strat`) against nine group-free candidates. Every comparison in A4 uses menus of equal size and
equal deployment cost. The group arm is `{a0, strat, mix25, mix50, mix75, orbit2, orbit4}` and the
group-free arm is `{a0, shrink at six levels}`: seven candidates each, every policy costing exactly `S`
shots per prediction, calibration cost `n * sum_p shots_used(p)` identical across arms. Sharing is not
used here because these policies differ in shot *allocation*, which is the resource under study; the
shared-record experiment is kept, labelled as the case where policies are deterministic functions of one
record.

**A4.3 Mechanism counting.** The two Heisenberg tasks differ only by a target weight and the two
cluster tasks are numerically identical, so the physical evidence is one mechanism with three target
settings plus one degenerate task. A4 reports physical mechanisms separately, never as a pooled count,
and a task whose even and raw targets coincide is reported as degenerate and excluded from any
cross-mechanism claim. A second mechanism with genuine odd content is constructed and verified to have
a non-zero odd component before it is used.

**A4.4 Scope of the certification-cost claim.** "The valid rule almost never fires" is replaced by a
measured firing surface over `(n, S, |Delta|, m)` with the tested region stated, plus the closed-form
sufficient radius. No claim is made outside the sampled region.

**A4.5 Switching.** The retraction is about the earlier *deployment-cost and optimisation* claim. The
mathematical fact that a grouped and an interleaved schedule give different risk at fixed total shots
stands and is stated as such.

**A4.6 Scope of the negative.** The negative result is scoped to the tested menus, mechanisms, shot
ranges and the two-circuit case. "The second circuit is not worth buying" is replaced by a statement
about the tested group actions at the tested budgets.
