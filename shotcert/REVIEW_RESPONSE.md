# Response to the referee report on *Symmetry Spending Under a Quantum Shot Budget*

**Summary.** The referee is right on all six major concerns. Each was verified in our source before we
accepted it, and each was real. None is a matter of interpretation. We have corrected the bound,
built the resource ledger the paper lacked, retracted the switching result, written an independent
enumeration to replace the one we mislabelled, repaired the physical symmetry claim and the
confirmatory definitions, and added the matched-resource comparison that was missing. Two of the
corrections reverse claims we made; both reversals are in the paper. The corrected study now contains
a positive matched-resource result (§3 below) and a cost statement we did not expect (§4).

Everything below was pre-declared in `shotcert/docs/PROTOCOL.md` **Addendum A2**, committed as
`5a06fed0` before any new analysis was run, together with an explicit list of the prior results that
the defects invalidate rather than quietly replace.

---

## 1. The claimed distribution-free certificate was invalid — **confirmed, corrected**

Verified in `certify.py`: the logarithm was `log(LOSS_RANGE/(delta*n))`, i.e. `log(4/(δn))` after the
caller had already divided δ by the candidate count. At n=400, m=11, δ=0.05 this gives **0.79** where
`log(2m/δ)` is **6.09** — the referee's arithmetic reproduced exactly. There is no `1/n` inside that
logarithm; it shrank with n and went negative past `n > 4/δ`, which is why a **negative range term**
appears in the generated variance table. A negative quantity is not a one-sided confidence radius. The
range was also wrong: `D = L_a − L_0` with each squared loss in `[0,4]` lies in `[−4,+4]`, width **8**,
not 4.

**Fix.** `mp_bound(D, delta, menu_size)` implements Maurer–Pontil Corollary 5 with `ln = log(2m/δ)`
and `b−a = 8`, scaling from the `[0,1]` statement so that the square-root term picks up no `(b−a)`
factor (it cancels against the rescaled variance) and the linear term picks up exactly one. The old
function is retained as `eb_bound_broken` solely so the withdrawal is reproducible. At the referee's
illustrative point the corrected radius is **0.2836** against the broken **0.0149** — a factor of 19.

Consequences, reported rather than buried: every coverage, power and frontier number produced by the
old bound is invalid and is marked as such in A2.0. Coverage and power are now reported with Wilson
intervals over the declared repetition count, since quoting `0.000` over 400 repetitions is how the
first version overstated a null. We agree with the referee that the Studentised bound's violation
frequency on our simulated tasks is diagnostic evidence and not a certificate for a new task
distribution; the paper now says that in the same paragraph as the numbers, and uses the Studentised
bound only for the sweep, with the distribution-free statement expressed as a cost (§4).

## 2. Calibration resource accounting omitted policy evaluations — **confirmed, corrected**

`calibration_losses()` evaluates every candidate and the baseline on every instance, so calibration
costs `n · Σ_p shots_used(p) ≈ n·S·m`, not `n·S`. Calling `n` the preparation count while drawing S
shots on each of m policies also conflated labelled instances with physical state copies.

**Fix (A2.2).** Five quantities are now counted separately at every frontier point: labelled
`instances`, `preparations` (per shot-batch executed, since repeated shots need repeated state copies),
`shots`, `switches` (circuit-setting changes within one prediction), `compilations`. The ledger is
recomputed per point because the menu depends on S, and the sweep is at matched
`B_total = shots_calib + n_deploy · S` for a declared deployment count of 1000. A point from the new
table, to make the scale concrete: `n=50, S=8, m=8` → 3,200 calibration shots, 400 calibration
preparations, 12 compilations, 11,200 total shots including deployment. The old label would have called
this a 400-shot budget.

## 3. The interior switching optimum was produced by charging circuits that do not exist — **confirmed, retracted**

`Policy.circuits` returned `min(k, orbit_size·4)`, reaching **8** for a two-element group, and the
switching experiment charged `min(k, 4|G|)`. The referee is right that with two circuits every `k ≥ 2`
costs the same, so a per-circuit price cannot produce an interior optimum at all.

**Fix and result (A2.3).** `circuits` is now `min(k, orbit_size)`; switching cost is charged from an
explicit schedule (shot sequence = chosen orbit indices in nondecreasing order; switches = adjacent
pairs that differ), with the grouped count reported because it is the minimum over schedules and
therefore most favourable to the policy. Re-running the full price sweep gives, over 144 cells:

| charged resource | cells | interior optimum in k | max distinct circuits |
|---|---|---|---|
| per distinct circuit | 72 | **0 (0.0%)** | 2 |
| per switch | 72 | **18 (25.0%)** | 2 |

An interior optimum survives only as a per-switch cost on an interleaved schedule, in a narrow cost
window (at `c=1.0`, `k*=2`; at `c=4.0` the optimum returns to the boundary). The abstract's second
"consequence" is retracted and the section is titled as a retraction.

## 4. The "brute-force enumeration" was not independent — **confirmed, replaced**

`exact_risk()` and `components()` both consume `_estimator_moments()`, so their 1e-17 agreement is
algebraic consistency between two related code paths. The docstring said so; the abstract did not, and
the abstract was wrong.

**Fix (A2.4).** `shotcert/reference.py` enumerates the predictor: every group-draw sequence through its
multinomial count vector, and for each, every combination of binomial success counts, weighted by
`scipy.stats.binom.pmf`. It imports only the task's orbit expectations; a unit test asserts that
`_estimator_moments` and `components` are absent from its namespace, so the reference cannot be
"fixed" by calling the thing it verifies. Agreement with `exact_risk` is **< 1e-12** across
`S ∈ {2,4,6,8}`, `k ∈ {1,2,3,4}` and all policy modes.

Writing it found three defects, which is the point of an independent reference:
- we initially passed the ±1 readout mean to `binom.pmf` as a probability (nan for `|mu| → 1`);
- a `zip(..., [0])` truncated the raw branch's enumeration to one outcome;
- **a real bug in the estimator**: at `S=2, w=0.75` rounding gives `S_a=2, S_0=0`, so a mixture kept
  weight 0.25 on a branch with no shots and divided by zero. Such mixtures are now infeasible, excluded
  from the menu, and the exclusion is reported.

The paper now distinguishes the three checks explicitly: closed-form vs closed-form (algebraic
consistency), closed-form vs enumeration (verification of the predictor), and Monte-Carlo
(independent at a distance, less precise).

## 5. Physical action, target and confirmatory threshold — **confirmed, repaired; the symmetry claim is downgraded**

The referee asked for the operator relation. We measured it, and it goes against us:

| quantity tested | residual |
|---|---|
| `‖M H(λ) M − H(−λ)‖` (Hamiltonian only) | **8.9e-16** — holds |
| `‖M|ψ₀⟩ − |ψ₀⟩‖` (Néel preparation) | **1.41 = √2** — fails |
| `‖M Z₀ M − Z₀‖` (site-0 readout) | **2.0** — fails |
| `|⟨Z₀⟩_t(λ) − ⟨Z_{n−1}⟩_t(−λ)|` (transformed experiment) | **1.0e-15** — holds |
| `|⟨Z₀⟩_t(λ) − ⟨Z₀⟩_t(−λ)|` (fixed readout, as we claimed) | **0.19** — fails |

So `Δ → −Δ` is **not** the mirror of the deployed experiment. The relation that holds describes a
different experiment (mirrored preparation *and* mirrored readout). The paper now calls `Δ → −Δ` a
paired control transformation whose odd component is measurable and cancellable, and states that the
risk decomposition is unaffected because it needs the response functions `μ_g`, not a physical group
action. (The first `mirror_operator` we wrote was the identity — it reversed nothing — and reported a
Hamiltonian residual of 3.0 and a state residual of 0.0. `M² = I` and `M ≠ I` are now asserted.)

**Confirmatory definitions.** `eps = 0.01` was indeed a silent substitution for the frozen
`0.02·Var(Y)`; it is recorded as a protocol deviation in A2.0 and restored, computed and printed:
`Var(Y) = 0.108733 → eps = 0.0021747`. Violation is now "the certificate fires **and** the selected
policy's true `Δ > eps`" (was `> 0`); power is "probability of selecting a policy with true
`Δ ≤ eps`", with fallback counting against it; `selection_rate`, `fallback_rate`, and the chosen
policy's mean and worst true `Δ` are all reported. The cluster family's inability to exercise the
sign-reversal mechanism is stated in the limitations, not presented as confirmation.

## 6. Novelty and consequence — **the matched-resource comparison now exists, and it separates**

We added exactly the comparison the referee asked for: the same certificate and the same calibration
protocol applied to a menu containing **no symmetry policy at all** (raw plus shrinkage toward a
declared constant — one circuit, zero switches, no group calibration), at matched total cost with the
m-factor counted.

| task | symmetry menu | generic menu (no group) |
|---|---|---|
| `control_help` | power **1.000** at 20,800 total shots | best power **0.14**, never certifies |
| `control_interior` | power **1.000** at 96,000 total shots | best power **0.10**, never certifies |
| `control_hurt` | does not certify (correct abstention) | does not certify |

Maximum violation rate over all 108 points: **0.015** against nominal 0.05. The separation is
structural, and we say why: shrinkage moves the prediction toward a constant, so it adds bias and
cannot produce a policy that beats raw by more than ε; only the group changes the bias term of
Eq. (1). This is a matched-resource advantage of group-based over group-free paired certification for
this estimand, which is the "measurable resource separation" the original brief required.

Second, the cost result the referee's correction produced. With the **correct** simultaneous bound, the
range term with `b−a = 8` and `ln = log(2m/δ)` decays as `1/n`, and closing a gap of
`|Δ| ≈ 0.008` needs **5,109 to 20,679 labelled preparations** regardless of shot allocation. That is a
quantified negative: distribution-free simultaneous certification of decisions this fine is not
available at budgets this study can pay, and a paper that certified them with a looser-looking bound
was not doing distribution-free certification. We think this is the most useful single number in the
revision, and it exists only because the referee found the bound.

On "elementary": we accept that Eq. (1) is a conditional bias–variance decomposition and that the
calibration split is the law of total variance. The paper no longer presents either as a theorem
contribution; they are the estimand and the accounting that make the two results above checkable. We
have not produced a lower bound or an instance-dependent allocation theorem, and we say so in
§"What is and is not claimed" rather than implying otherwise.

**Reconciliation.** "Preparation-limited at fixed total budget" is removed from §6; the surviving
bound-independent statement is the law-of-total-variance split, stated as such, next to the withdrawal
that explains why the frontier's *location* is a property of the inequality.

## Presentation points — all adopted

- The first term is now "integrated squared discrepancy"; equal-weight and independent-draw
  assumptions for Eq. (1) are stated where Eq. (1) appears.
- Physical-task selection rates, chosen-policy true risks, fallback rates and resource counts are in
  the manuscript; oracle-best risks are labelled as the simulator-exact reference they are.
- Raw, full averaging and best partial mixture are shown side by side (new table), because a
  best-policy-only table cannot display a sign flip.
- Protocol amendments and the ε substitution are documented in A2, with the invalidation list.

## What we are not claiming

No new concentration inequality; no joint sample/shot allocation rule for a generalization bound
(Catak); no certified symmetry release, post-selection oracle inequality for adaptive families, or
two-copy primitive (Chen); no symmetry discovery from finite probes; no device results and no quantum
advantage. Chen's independent validation and scalar-probe access are why the comparison above is run
under identical access and identical certificate rather than against a weakened baseline.

## Reproducibility

20 unit tests pass, including the enumeration agreement, the budget-feasibility properties, the
mirror-operator sanity checks, and a guard that the reference does not import the code it verifies.
The vectorised calibration path used for the 108-point sweep is **bit-identical** to the loop version
on the same RNG stream, which is asserted in a test rather than assumed. Every number in the manuscript
is emitted by `shotcert/paper/make_tabs.py` from the result JSONs; no number is typed by hand.
