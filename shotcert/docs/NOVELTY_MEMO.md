# Novelty and theorem-feasibility memo — shot-budgeted symmetry decisions

**Date:** 12 Nov 2026 · **Gate:** weeks 1–2 of `reports/Certified symmetry decisions.md`
**Verdict at the end:** proceed, with the *certificate demoted from contribution to requirement*, and
one kill condition moved to the front.

Sources actually consulted (metadata and full text retrieved, not recalled): arXiv
`2608.24891` (Catak), `2609.11470v1` (Chen, *Statistical Symmetry Release*),
`2610.00157v1` (Chen, *Symmetry Discovery*), `2610.01874v1` (Wang et al., *Fourier
Symmetrization*). Theorem titles were extracted from the arXiv HTML of the two closest papers; the
matrix below cites those titles, so a reader can check each cell against the source.

## 1. What the closest work already owns

| Source | Result that bites | Consequence for us |
|---|---|---|
| Catak 2608.24891, Thm 3 | Distribution-free bound on `R(M) − R̂_{n,S}(M)` separating a sample term `√(d/n)` from a shot term `√(log n / S)` | The "shots cannot substitute for instances" decomposition **for a generalization gap** is taken. Not available as our theorem. |
| Catak 2608.24891, Thm 4 | Closed-form allocation `n* = 2√(2dB/log(2B/δ))`, `S* = B/n*` minimising a conservative surrogate; worst-case rate `B^{−1/4}` | Joint (n,S) allocation under `B = nS` is taken **for that objective**. Any allocation rule we write must be for a *different* objective or we are renaming. |
| Catak 2608.24891, stated assumption | Thm 3 "assumes that M is chosen **independently** of the measurement outcomes used to compute the observed empirical risk"; the paper lists "fully adaptive shot-noisy training" as open | **This is our opening.** A policy selected using shot-noisy losses violates exactly this assumption, because for a stochastic deployed predictor the shot noise is part of the *estimand*, not only of its estimate. |
| Chen 2609.11470, §5 Thms 5–7 | "Safe release certificate with first-order terms", "Simultaneous release certificate", "Certified descent along an empirical release direction" | Certified symmetry decisions with simultaneous confidence bounds are taken. A "certified symmetry choice" wrapper is unavailable. |
| Chen 2609.11470, §7 Thms 6–8 | "Post-selection oracle inequality for adaptive candidate families", "Fast validation along nested release paths", "Finite-shot rejection of exponentially flat release branches" | Adaptive-candidate validation with finite shots is taken. Our calibration/selection layer cannot be the novelty. |
| Chen 2609.11470, §4 Thms 4–5, 8 | "Twirl–swap release gate" (two-copy access, dimension-independent copy count), "Gate noise floor", "Pauli locality and grouped-measurement shot cost" | Shared/two-copy measurement primitives and grouped-measurement shot accounting are taken. We must state our access model and may not silently deny a competitor a primitive. |
| Chen 2610.00157 | Finite-measurement inference of the group from candidate transformations | "First symmetry discovery from finite probes" is unavailable. |
| Wang 2610.01874; Cai 2021 | Orbit/Fourier symmetrization; randomized symmetry implementation with bias–sampling tradeoffs | Random group draws and bias/cost balancing are not novel by themselves. |
| Learn-then-Test; confidence sequences; quantum conformal prediction | Generic risk calibration, optional stopping, finite-shot quantum uncertainty | A finite menu plus a concentration bound is a baseline, not a result. |

## 2. The object nobody in this set has, stated precisely

Every cited work treats the **risk of a model** (or a release decision about a model) and uses shots
to *estimate* it. Our object is different in one specific way that changes the mathematics:

> For a **deployed stochastic predictor** `Z_a(X)` — one that draws `k` group elements and `S` shots
> per prediction — the risk `R_S(a) = E[(Z_a(X) − Y)²]` is a **functional of the allocation itself**.
> Spending the same `S` differently does not change how well we *know* the risk; it changes *which*
> risk we have.

Three consequences, each checkable:

1. **Risk-at-budget, not risk-approximating-an-ideal.** There is no ideal-limit target being
   approximated: `S → ∞` at fixed `k` does not reach the twirled predictor, because the group-draw
   randomness remains. So the comparison "policy a vs raw a₀ at the same S" is a comparison of three
   distinct functionals, and the classical stratified-allocation result (which minimises a variance
   at fixed weights) does not select among them.
2. **The selection step is not independent of the noise**, so Catak's Theorem 3 does not apply to
   it, and Chen's post-selection machinery certifies *model-level release improvement* under
   two-copy access, not per-prediction deployed risk under scalar shots. What we need is a paired
   certificate whose target is `R_S(a) − R_S(a₀)` — both terms being allocation-dependent.
3. **A new, non-reducible variance component.** Splitting `S` into `k` orbit draws of `S/k` shots
   trades within-draw shot variance `∝ σ²k/S` for group-draw variance `Var_g[μ_g(x)]` that is
   **invariant to S**. Hence an interior optimum `k*(x)` at fixed total shots, vanishing when the
   predictor is already invariant and diverging when the orbit spread dominates. This is the
   quantitative statement the paper should be built on; the proposal's own note ("drawing a new
   group element per shot and reusing one element for a batch of shots have different variance
   components") is exactly this, and I found it stated nowhere in the four sources.

## 3. What we therefore claim, and what we explicitly do not

**Claim (candidate contribution).** A risk-at-budget decomposition for orbit-randomised finite-shot
predictors with three separately measurable components — between-instance, within-draw shot, and
group-draw — from which follow (i) an interior `k*(S)` allocation optimum, (ii) a lower bound on
*labeled state preparations* for certifying a policy difference that is independent of shots per
instance, and (iii) a measurable prediction of when symmetry structure lowers total shots-to-certify
relative to generic paired calibration, and when it does not.

**Do not claim.** A certified symmetry decision procedure (Chen); the n-vs-S generalization split
(Catak); stratified allocation `S_g ∝ |w_g|σ_g` (classical); any quantum advantage; a first
finite-shot validation of anything.

**Kill conditions, evaluated in this order.**
1. *Access-model honesty:* if the advantage disappears when the strongest baseline is given the same
   access (scalar shots, or shared measurements where permitted) → stop.
2. *Non-vacuity:* if the valid certificate falls back to raw prediction at every feasible budget →
   stop (a formally correct, powerless certificate is not a result).
3. *Novelty of the decomposition:* if the group-draw term reduces to classical stratified variance
   under any relabelling → demote the theory to validation and seek the benchmark contribution
   instead.

## 4. Feasibility on available resources

Dense statevector simulation with explicit Kraus noise channels and binomial shot sampling covers
the whole control and both physical tasks at 2–9 qubits; no GPU and no device access is required.
Exact deployed risks are enumerable at 2 qubits (all outcomes × all group draws), which lets the
theory be **verified against brute force rather than merely illustrated** — the failure mode that
killed the previous submission. Certification experiments are cheap: a few thousand independent
calibration repetitions per budget point. Device results are out of scope and will not be promised.

**Decision: proceed to the access-model document and the 2-qubit control.** The theory contribution
is the risk-at-budget decomposition and the group-draw non-reducibility, not the certificate.
