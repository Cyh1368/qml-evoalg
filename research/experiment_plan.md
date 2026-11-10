# Confirmatory continuation protocol

This protocol is prospective. Existing data are an exploratory discovery set; do not relabel reused validation/test results as confirmation. All cluster submissions must explicitly request `gpu_devel`; no other partition is permitted.

## Research questions and estimands

1. Does verifier feedback improve final held-out predictive risk at a fixed number of evaluated candidates? Primary estimand: paired run-level difference between the same search configuration with and without verification feedback.
2. Does analytical repair of a proposed symmetry improve prediction? Primary estimand: paired risk change after retraining original and repaired candidates with matched initializations and training budgets. This is an intervention on the implemented architecture, not proof of the LLM's reasoning.
3. Does verified symmetry discovery transfer across group actions and task families? Hold out at least one family from method development.

Do not force weak/mid/frontier into a continuous capability scale. Use individual models as categorical treatments and fixed proposal allocation. Continuous axes are evaluated-candidate budget, measured equivariance residual, controlled symmetry-breaking amplitude and task symmetry mismatch. Model cost is an accounting variable, not an intrinsic capability score.

## Phase 1: establish measurement validity

Use explicit finite group actions and channel/predictor residuals defined in mathematics.md. Validate on identity, exact symmetric layers, untied rotations, noncommuting ordered controlled rotations, and global-phase-equivalent unitaries. Report parameter-prior residual separately from trained-parameter residual. A random-parameter check is empirical evidence, not an all-parameter proof.

Always report predictive variance and held-out loss beside output invariance: constant predictions are perfectly invariant. Test equivalence of gate reorderings only when gates commute. Define random group sampling and fixed random seeds before inspecting comparisons. Generator residuals and uniform-group residuals are distinct quantities.

## Phase 2: clean task suite

| Family | Action | Label and counterfactual |
|---|---|---|
| Graphs, n=6 then n=8 | S_n vertex relabeling | Connectedness; separate bipartiteness transfer. Counterfactual: label depending on designated vertex. |
| Legal tic-tac-toe boards | D4 board transformations | Terminal/winner classification with a documented convention. Counterfactual: designated-cell label. |
| Spin configurations on a ring | C_n translations, optional reflection | Regression of translation-invariant local correlations. Counterfactual: site-specific field contribution. |

Split by group orbit before assigning training, development and test sets. Graph orbit splitting requires exact canonicalization/isomorphism checks, not a heuristic hash alone. Freeze evaluation data and prevent candidate code from accessing it. Stratify by class without duplicating orbit members across splits. Use fresh test sets for confirmation. Include a simple classical task solver or feature baseline to expose shortcuts and task difficulty; no quantum advantage claim follows from these small tasks.

## Phase 3: continuous controlled interventions

Construct H_epsilon = T_G(H) + epsilon [H - T_G(H)] for Hermitian H, with fixed norm conventions and epsilon in {0, .05, .1, .2, .4, .7, 1}. Exponentiate the full generator for small systems; a finite ordered product of orbit-related noncommuting gates is not guaranteed equivariant. Measure actual residual rather than assuming epsilon equals it. Keep trainable dimension, initialization distribution and optimization budget documented; use a second perturbation that stays within the invariant subspace to control for generic parameter disturbance.

For a separate regression benchmark set y_eta = y_inv + eta y_break with orthogonal invariant and breaking components under a group-invariant input measure. This gives a known continuously varying task mismatch. Do not expect accuracy on a binary task to vary continuously; prefer squared loss and calibrated probabilities. Group-average risk decompositions rely on the stated measure and label assumptions.

## Phase 4: search comparison

Primary arms: random valid-circuit search; mutation-only evolutionary search; fixed-model LLM search with scalar fitness; same LLM search with verifier feedback; same with verified compiler/repair. Include hand-designed equivariant and generic parameter-matched circuits as reference endpoints. Separate the benefit of known-group compilation from unknown-group discovery. If transformations are supplied, call the task symmetry implementation or hypothesis selection.

Use identical initial populations, task splits, proposal count and candidate training budgets. Report wall time, tokens, evaluator calls, failed proposals and monetary cost separately. Secondary budgets can be cost-matched. Compare fixed allocation with UCB only as a separate harness experiment. Preserve invalid attempts in denominators. Require structured group-generator hypotheses and evaluate their validity using independent probes; retain natural-language notes only as qualitative evidence.

Pilot with 3 paired search seeds to estimate variance and runtime; do not use that pilot for significance claims. Set confirmatory replication using a minimum scientifically meaningful risk difference and pilot run-level variance, then freeze the sample size. A suggested initial planning range is 12–20 independent paired search runs per primary contrast, subject to power analysis. Retraining seeds nested inside a search run do not create independent search replicates.

## Analysis and stopping

Primary endpoint: test risk of the candidate selected using development data only at the fixed search budget. Secondary endpoints: area under best-development-risk trajectory, time to a predeclared verified hypothesis, transformation validity, executable residual, and cross-family transfer. Give paired confidence intervals at the search-run level; bootstrap whole runs or use a hierarchical model. Test one primary contrast first and correct secondary families for multiplicity. Report all task failures and all seeds.

Go/no-go: if verifier feedback changes residual but not predictive risk, report implementation reliability rather than performance improvement. If repair helps only with a supplied group, do not claim unknown symmetry discovery. If results disappear after orbit splitting or budget matching, revise the central claim. If all methods recover the same obvious all-pairs template, require an additional held-out family before asserting general discovery ability.

## Deliverables required for a publishable submission

Versioned dataset/orbit manifests and split hashes; a sandboxed evaluator contract; tested metrics; complete run logs; predeclared analysis; mathematical assumptions and counterexamples; a reproducible audit of old results; and a manuscript distinguishing established theory, new method and empirical findings. This plan establishes rigor criteria, not evidence that the criteria have already been met.
