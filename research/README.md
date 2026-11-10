# Research continuation

The strongest prospective contribution is **verified symmetry hypotheses and causal repair in LLM-guided quantum circuit search**. Novelty remains a hypothesis pending matched search experiments and transfer. Established symmetry residuals provide the mathematical foundation; they are not themselves a new discovery.

## Findings already reproduced

- Historical selection consumed test information. The prospective public evaluator is patched and its invariance to test-derived metrics is regression-tested. A genuinely inaccessible fresh holdout remains required.
- The hand-designed baseline's one-direction CRZ layer is not generally permutation equivariant. At a documented parameter setting its mean adjacent-generator channel defect is 0.05970837; bidirectional half-angle repair reduces it to numerical precision. This refutes an architecture-wide claim, not necessarily prediction invariance at every trained parameter setting.
- Complete directed gate coverage does not ensure symmetry: noncommuting CRX layers furnish a tested counterexample.
- A training-fitted edge-count threshold achieves 83% validation accuracy on the historical task. Density shortcuts deserve explicit controls.
- A nine-circuit exploratory pilot replaces binary motifs with operator residuals. Some early frontier circuits have numerical-zero defects; later examples do not. Three parameter draws are neither an architecture certificate nor independent search replications.

## Reading order

1. [Audit](audit.md): validity failures, fix boundaries, and computed diagnostics.
2. [Mathematics](mathematics.md): definitions, assumptions, proofs and counterexamples.
3. [Literature](literature.md): primary sources and overlap with existing work.
4. [Experiment protocol](experiment_plan.md): prospective estimands, controls, replication and publication criteria.
5. [Metric pilot](metrics/pilot.json): measured continuous defects, with scope recorded in the artifact.
6. [Structured verifier](verifier/README.md): executable transformation hypotheses, verification and repair interfaces.
7. [Dataset manifest](datasets/manifest.json): exact orbit-disjoint S6 graphs and D6 ring regression with continuous task-symmetry breaking.

## Additional executed experiments

The [paired training pilot](metrics/TRAINING_RESULTS.md) optimizes three-parameter circuits with identical random-search budgets and disjoint input orbits. Repair improves development loss in 6/8 invariant-target seeds, but the sham has a larger mean gain. This is insufficient evidence for a symmetry-specific performance benefit and motivates stronger optimization controls.

The predictive-risk pilot evaluates 160 configurations across eight paired parameter seeds, five circuit-breaking strengths and four target-mismatch strengths. It verifies the squared-risk projection identity on a complete finite input distribution. Its negative control shows that averaging can worsen risk when the target breaks symmetry. This is an exact controlled demonstration, without training or LLM calls; it does not establish search superiority.

The graph benchmark enumerates all 32,768 six-node graphs and partitions 156 exact isomorphism classes across splits. The ring benchmark contains 1,200 inputs with five target-mismatch levels. Independent validation checks graph labels, orbit separation and the quadratic mismatch-defect law. The holdout directory is organizational separation, not an enforced security boundary; future search must receive only development artifacts.

## Execution priorities

First validate measurements and prepare orbit-disjoint tasks. Then compare original, symmetry-repaired and equally sized control interventions using paired retraining. Finally randomize verifier feedback in matched-budget LLM search, reserving an unseen task family. Use independent search runs as the replication unit. Model identities are categorical treatments; symmetry-breaking amplitude, task mismatch and proposal budget supply defensible continuous axes.

Do not force a monotone weak/mid/frontier relationship or infer internal understanding from patch notes. Require structured transformation hypotheses and executable verification. Known-group repair and unknown-group discovery must be reported separately.

All cluster jobs must use `gpu_devel`. The completed audits and matrix pilots use only small local computations. Historical results and datasets remain exploratory; passing software tests does not establish a publishable empirical claim.

## Reproduction

```sh
python3 research/audit.py
OPENBLAS_NUM_THREADS=1 python3 research/metrics/validate.py
OPENBLAS_NUM_THREADS=1 python3 research/metrics/baseline_check.py
OPENBLAS_NUM_THREADS=1 python3 research/metrics/pilot.py
OPENBLAS_NUM_THREADS=1 python3 research/metrics/risk_pilot.py
python3 -m unittest discover -s research/verifier -p 'test_*.py'
python3 research/datasets/validate.py
```

NumPy is sufficient for these checks. Original historical baseline code is retained as evidence; its repaired operator is built explicitly by the counterexample script.
