# A new project: symmetry decisions under a quantum shot budget

**Proposal to the authors · 12 November 2026**

Your current results are worth archiving as a transparent technical record. The next paper should address a different question: **given a frozen quantum predictor and a fixed number of physical measurement shots per prediction, when should one spend those shots on symmetry-related circuits, and how can that choice be certified from an affordable, independent calibration experiment?** The contribution must be about the *risk and resource cost of the finite-shot predictor actually deployed*. A guarantee for an ideal expectation value, followed by deployment with a different shot-limited estimator, would miss the question.

This is a **candidate research direction, not a verified novelty claim**. The closest 2026 work already covers finite-shot certified symmetry release and independent validation. Spend the first two weeks trying to disprove this proposal's novelty. If the intended theorem is already a corollary of that work and generic risk calibration, stop before a large experiment.

## Why this question, and what the literature already owns

The five review rounds exposed a recurring mismatch between architectural symmetry, target symmetry, and measured predictive benefit. They also showed that a validity screen can reject useful approximate-symmetry repairs and that finite-shot cost was absent from the main estimand. This suggests a deployment decision under a real resource constraint. The authors already have symmetry diagnostics, group actions, circuit simulation, and experience auditing adaptive selection; those are useful foundations, though the old results do not establish the new claim.

Several tempting versions of the project are occupied:

| Existing work | What it already contributes | Boundary for this proposal |
|---|---|---|
| [Meyer et al., PRX Quantum 2023](https://doi.org/10.1103/PRXQuantum.4.010328) and [Nguyen et al., PRX Quantum 2024](https://doi.org/10.1103/PRXQuantum.5.020328) | Constructing symmetry-respecting quantum models | A group average or equivariant circuit is a baseline. |
| [Chen, *Statistical Symmetry Release*, 2026 preprint](https://arxiv.org/html/2609.11470v1) | Finite-data and finite-measurement certified release, shared measurements, adaptive-candidate validation, and measurement-complexity comparisons | Generic “certified symmetry choice” or “first finite-shot validation” is unavailable. Compare its §§2.2, 5, and 7.5 theorem by theorem. |
| [Chen, *Symmetry Discovery in Quantum Learning*, 2026 preprint](https://arxiv.org/html/2610.00157v1) | Finite-measurement task and observable symmetry inference | Discovering a group from finite probes is not the proposed contribution. |
| [Wang et al., *Fourier Symmetrization*, 2026 preprint](https://arxiv.org/html/2610.01874v1) and [Cai, *Symmetry Expansion*, 2021](https://arxiv.org/abs/2101.03151) | Randomized symmetry implementation and symmetry-related bias/sampling tradeoffs | Sampling random group elements and balancing bias against cost are not novel by themselves. |
| [Learn then Test](https://arxiv.org/html/2110.01052v4), [time-uniform confidence sequences](https://doi.org/10.1214/20-AOS1991), and [quantum conformal prediction](https://arxiv.org/abs/2304.03398) | Generic risk calibration, optional-stopping tools, and finite-shot quantum uncertainty | A finite menu plus a concentration bound is a required baseline, not a new theorem. |
| [AEQuO](https://quantum-journal.org/papers/q-2023-01-26-906/), [iCANS](https://quantum-journal.org/papers/q-2020-05-11-263/), [Refoqus](https://arxiv.org/abs/2211.04965), and [Measurement-Budget Allocation in Quantum Learning](https://arxiv.org/abs/2608.24891) | Adaptive quantum measurement and sample-versus-shot allocation | A generic allocation rule or worst-case budget exponent is unlikely to suffice. |

The specific possible gap is **joint selection and measurement allocation for a stochastic deployed predictor at the same total deployment shot budget**, including group-draw randomness, hardware-dependent measurement variance, and the calibration cost needed to make the decision. This is my inference from the sources, not an assertion of priority. A changing access model alone is not enough: the paper must prove or demonstrate a meaningful advantage over the strongest applicable methods.

## The proposed research question

Freeze a trained circuit and a finite menu of inference policies. A policy specifies a group or subgroup, a weight between raw and averaged predictions, a way to sample group elements, and an allocation of a fixed total of **S circuit shots per prediction**. Different transformed circuits may have different variance, depth, switching cost, and device noise. For a new input, the policy returns the random finite-shot output `Z_a(X)`.

The primary risk is

`R_S(a) = E[(Z_a(X) − Y)^2]`,

where the expectation includes new task instances, measurement outcomes, any randomized group selection, and stationary device noise under the stated access model. Compare each policy with the raw policy `a0` using **the same S**. The initial target is a distributional certificate

`P_calibration{R_S(a_selected) − R_S(a0) ≤ ε} ≥ 1 − δ`,

with a fallback to `a0` when the data cannot support a choice. Define ε in task units before confirmatory testing; `ε=0` means non-degradation, while a negative ε requires evidence of useful improvement. This is an average-risk statement for the declared data/device distribution, not pointwise safety or robustness to unmodeled device drift.

**Sharper scientific question:** Can the structure of symmetry-related quantum measurements reduce the *total shots required to certify and obtain* a useful deployed policy, relative to generic paired risk calibration and standard allocation, when the symmetry is approximate or hardware noise is not covariant? The safety bound alone is established in generic form. The novel part must be a nontrivial estimator, allocation strategy, or lower/upper-bound separation tied to this measurement problem.

### A derivation the authors should start from

If a shot-limited estimator is unbiased conditional on `x`, then

`E[(Z_a−y)^2 | x,y] = (E[Z_a|x]−y)^2 + Var(Z_a|x)`.

The deployment loss includes its shot variance. Subtracting estimated variance to recover an ideal-circuit loss changes the estimand. For independent stratified shots on transformed circuits, weights `w_g`, variances `σ_g²`, and allocations `S_g`, the variance term is `Σ_g w_g² σ_g²/S_g`. With known variances and no other constraints, the continuous optimum `S_g ∝ |w_g|σ_g` is classical stratified allocation; **do not claim it as new**. Unknown variances, randomized orbit subsets, biased hardware channels, discrete shot counts, and calibration cost create the real technical problem. Compare stratification with drawing a new group element per shot and with reusing one element for a batch of shots; they have different variance components.

A generic rigorous starting point is a frozen finite action menu and independent calibration inputs. For each input, draw paired finite-shot outcomes for a policy and raw baseline and record their loss difference. Simultaneous valid upper bounds plus fallback give a baseline certificate, including selection from that frozen menu. Adaptive creation of policies from the same calibration losses needs a separate guarantee or an independent split. Time-uniform bounds can support stopping, but using them is not novel without a sharper resource result.

A publishable theory target would show an **instance-dependent shot or copy complexity advantage** from exploiting orbit/measurement structure over black-box paired calibration, while retaining the certificate for actual finite-shot deployed risk. It should separate between-instance uncertainty from within-instance shot uncertainty and state when extra shots on the same state cannot replace independent labeled states. A lower bound, matching oracle allocation, or sharp condition under which the advantage vanishes would make the result more credible. If all that remains is a union bound over a small menu, treat theory as validation and seek a separately consequential benchmark contribution.

## Work plan and early stop gates

### Weeks 1–2: establish a real gap

Write a one-page access model and estimand before implementing anything. State whether the method has single-copy scalar outcomes, shared Pauli measurements, classical shadows, two-copy operations, or all of these; do not compare methods under mismatched access without saying so. Make a theorem-by-theorem matrix against Chen's statistical symmetry release, Wang's randomized symmetrization, generic Learn then Test, and adaptive shot allocation. Reproduce one closest baseline in a small control case.

**Stop or redirect** if Chen's independent-validation result plus standard allocation already gives the claimed guarantee and complexity; if the only difference is renaming a parameter; or if the claimed advantage depends on withholding an available measurement primitive from a competitor. A useful alternative would be to derive a new lower bound under a clearly motivated restricted access model.

### Weeks 3–4: prove the estimator and validate the measurement ledger

Build a 2–4-qubit control with exact means and enumerated deployed risks. It needs three cases: full averaging helps, full averaging hurts, and an interior partial-averaging choice is best at the same S. Check that simulated independent shots recover the predicted bias and variance, that shared randomness is used only where physically justified, and that the certificate covers its target in independent repetitions. Fix the circuit action, transformed input/state, label action, and measurement observable explicitly; otherwise “symmetry” can be a relabeling bug.

Run a low-cost pilot over a small policy menu, realistic calibration-label budgets, and several shot budgets. **Stop** if the valid certificate almost always falls back to raw prediction at attainable budgets, or if uniform allocation and generic paired calibration use essentially the same shots for the same power. A vacuous but formally correct certificate is not an impactful result.

### Weeks 5–8: physical task and freeze

Use a primary task where task and hardware mismatch have physical meaning. One candidate is a 6–8-qubit bond-alternating Heisenberg response or phase-related regression problem, building on the equivariant phase-classification setting in [Nguyen et al.](https://doi.org/10.1103/PRXQuantum.5.020328). Define labels through an independently computed observable or diagnostic. Vary inhomogeneous fields/disorder and amplitude-damping/readout asymmetry separately. Do not assign a protected-phase label to a state after breaking its defining symmetry without a valid physical argument. If phase terminology is unstable, use regression to the precisely defined observable.

Freeze the circuit family, policy menu, allocation algorithm, calibration sample size, ε/δ, resource ledger, primary contrast, and analysis before generating final outcomes. Include an independent review of split units and information flow. Start with simulator shots and explicit noise channels; profile before promising larger qubit counts or density-matrix sweeps.

### Weeks 9–12: independent evaluation

Use a separate task mechanism, such as 7–9-qubit cluster-Ising diagnostic recognition, motivated by the [superconducting QCNN study](https://www.nature.com/articles/s41467-022-31679-5) and its [public data](https://doi.org/10.3929/ethz-b-000530297). Treat public experimental data as a limited external check unless it contains enough independently prepared states; shots of one state are measurement replicates, not task instances. A real-device study can strengthen impact but is optional if the theorem is strong and noise simulations are carefully specified.

Split **independent Hamiltonian/preparation instances** before generating symmetry images or shots. Keep separate training, design, calibration, and final evaluation pools. Repeat the *whole calibration exercise* on independent datasets to estimate the frequency of safety violations; do not count multiple shot strings or optimizer seeds on one dataset as independent task replications. Block/interleave measurements by device time if drift is present, and report that drift as a stress test unless it is in the theorem. Release all failed policies, abstentions, and invalid group proposals.

## Baselines and outcomes that make the test fair

At each fixed total deployment-shot budget include raw identity, full averaging, uniform random group sampling, fixed-grid partial averaging, and equal-shot stratification. Compare the proposed selector with generic simultaneous paired risk bounds or Learn then Test. Include a shot-adaptive method without symmetry structure and an oracle allocation/choice computed from extensive offline shots **as a reference only**. Where access permits, compare with shared-measurement methods and Chen's closest applicable procedure. For predictive utility, include a constructive equivariant model, a symmetry-agnostic model, and a direct physical observable/classical measured-feature baseline; none needs to be beaten to claim quantum advantage, which is not the proposed aim.

Measure the primary outcome as **total physical shots or state preparations needed to certify a useful policy** at the declared ε/δ and a fixed acceptance-power target. Report the full risk-versus-resource frontier: calibration labels and shots, deployment shots, number of transformed circuits, compilation/switching overhead, wall time, fallback rate, and realized deployed MSE. State an inference horizon if certification cost is amortized across many predictions. A resource comparison is invalid if one method receives free calibration or full-state knowledge.

For uncertainty, report paired effects at the independent-instance level and variability across independent calibration experiments. A few hundred independent repetitions may be needed to inspect a nominal 5% violation rate; calculate that requirement before running the confirmatory study. Use a finite policy class fixed before calibration, or explicitly account for adaptive generation and multiple looks. The final test pool is opened once for outcome reporting, never to choose thresholds or models. Holdout hashes document integrity, but do not by themselves prove lack of earlier access.

## Publication criteria and kill conditions

The work is ready for a serious submission only if all of these hold:

1. **Novelty:** The final related-work matrix identifies a result that Chen, Wang, generic risk control, and established quantum shot allocation do not already imply. It includes a theorem/algorithmic separation or a genuinely new, independently validated measurement regime. A new acronym or generic safety wrapper fails this gate.
2. **Rigor:** The guarantee targets the same noisy finite-shot policy that is deployed, with explicit iid/stationarity assumptions, shot/label access, action selection, and fallback. The proof handles the actual reuse and dependence in measurements. Simulation verifies the estimator against known truth, and independent calibration experiments check practical coverage.
3. **Utility:** At matched safety and decision power, the proposed method needs a material, prespecified resource or risk gain over the **strongest** applicable baseline. An illustrative engineering target is at least a twofold reduction in certification shots on two different task mechanisms, with a third held-out check of frozen settings; this is a proposed go/no-go bar, not a universal publication threshold. A strong theorem with a matching lower bound could instead justify a smaller empirical gain.
4. **Impact:** The demonstrated difference changes a plausible experimental choice at realistic copy/shot budgets. It survives a physically meaningful approximate-symmetry setting and an independent task mechanism. Results must include when raw or full averaging wins; always selecting fallback is a valid certificate but a failed utility result.
5. **Reproducibility:** Every result maps to a frozen code version, state-instance split, calibration and deployment budgets, noise model or device session, statistical unit, and analysis record. No selection metric reads final-test outcomes. Costs include all methods' calibration and inference work.

Stop the method claim if the closest prior paper already proves it, the certificate has no power at feasible resources, the advantage disappears at equal total shots, the best evidence is another synthetic ring-label perturbation, or the only result is failure to reject a null. A negative result can be publishable if a substantive lower bound explains an important impossibility region; a local underpowered null is not enough.

## Archiving the current work

Before the new protocol begins, create an immutable tag or snapshot of the existing manuscript, rebuttals, reviews, raw run logs, result JSONs, split-consumption ledger, and a hash manifest. Add a short README identifying exploratory and superseded analyses and the final fifth-round decision. Start the new study in a fresh package and dataset namespace. Reuse simulator primitives only after independent tests against a second implementation; do not carry over the old calibration or analysis assumptions. This proposal does not modify the historical record or silently recast its findings as confirmatory.

The first deliverable should be the **novelty and theorem feasibility memo**. If that memo finds a defensible measurement-allocation result and a pilot shows a nonvacuous certificate at feasible cost, the proposed experiment can proceed. If it fails either test, redirect early while the cost is still small.
