# Referee report

**Manuscript:** Verified Symmetry Hypotheses and Causal Repair in LLM-Guided Quantum Circuit Search  
**Review date:** 11 November 2026  
**Recommendation:** Reject in its present form; invite substantial revision and renewed evaluation.

Dear authors,

The research question is interesting: can executable feedback help an LLM translate symmetry hypotheses into useful quantum predictors? The audit, explicit distinction between operator and predictive symmetry, and willingness to report unsuccessful interventions are valuable. However, the current manuscript is not sufficiently rigorous for publication as a full research paper. Its strongest causal claims exceed the design, one principal analysis uses duplicated experimental units, and the reported search endpoint does not measure the repaired predictor. Novelty is plausible at the level of an integrated empirical study, but is not established by the present evidence. These are substantive issues rather than presentation edits.

This review covers the current `main.tex`, `research/results_summary.md`, claim ledger, research overview and literature assessment, repair implementation and saved repair results, search analysis and relevant harness code, and the separate Qwen run report. I checked primary bibliographic records for two references. I did not rerun expensive training or LLM searches, independently reproduce every historical audit finding, or conduct an exhaustive priority search. Numerical statements below distinguish recorded results from conclusions that remain to be demonstrated.

## Overall assessment

| Criterion | Assessment |
|---|---|
| Rigor | Insufficient: duplicated repair observations, development-selection optimism, an endpoint/intervention mismatch, and unsupported causal attribution need correction. |
| Novelty | Unestablished: the mathematics and symmetry constructions are acknowledged prior art; the empirical contribution needs a clearly demonstrated new finding. |
| Interest | Promising: executable verification failures and limits of LLM-guided search could interest QML and automated-science audiences. |
| Publication readiness | Not ready for a full archival paper. A narrower audit or workshop submission may become viable after correcting the analyses and claims. |

## Required substantive revisions

### 1. Correct the repair experiment's replication unit and recompute uncertainty

The paper reports 24 paired draws from three teachers and eight optimizer seeds. At eta = 0, however, the target is h regardless of teacher seed. `build_targets` changes only the breaking direction; `fit_block` receives the same input, target, optimizer seed, and budget for each teacher. Inspection of `repair_results.json` confirms that each arm contains 24 eta-zero rows but only eight distinct `(opt_seed, dev_risk)` pairs. These are three copies of eight experiments, not 24 independent replications.

The current bootstrap resamples all 24 differences independently, thereby overstating precision for the central positive result. Collapse exact repeats and recompute the eta-zero interval from eight pairs. Publish all eight differences and explicitly state whether the revised interval supports the claim. For nonzero eta, account for shared teachers and reused optimizer seeds; report teacher-specific results and use an analysis appropriate to the crossed design. Three breaking directions cannot support a strong population-level claim about arbitrary target mismatches. Increase genuinely independent replication if that generality is important.

This issue is especially consequential because the paper criticizes pseudoreplication in the historical study while introducing it in its headline repair experiment.

### 2. Evaluate the repaired predictor: the current search contrast does not do so

In `research/search/harness.py`, Reynolds-averaged risk is saved as `dev_risk_repaired_diagnostic`, but the official endpoint remains `best_risk = best['dev_risk']`. `research/search/analyze.py` then loads that unaveraged endpoint. Thus the reported verify-repair versus verify contrast does not establish whether inference-time averaging helps or fails to help. It compares the selected underlying predictors across runs while omitting the direct repair effect from the endpoint.

Define the estimands explicitly. Report the paired before/after averaging effect on the same frozen candidate, and separately compare the complete deployed search-and-repair pipelines on fresh evaluation data. Report eligibility, attempted repairs, successful repairs, group sizes, and coverage of the intervention. Correct the statement that an averaging benefit failed to survive confirmation unless an analysis of actual averaged predictions supports it. A protocol may legitimately designate averaging as diagnostic, but the manuscript must then describe it as diagnostic rather than as a tested performance treatment.

### 3. Replace held-out generalization claims with accurately labeled development results

The results summary explicitly states that the locked holdout was never read. The search harness uses validation risk for candidate selection and feedback, and the tables report development-selected risk. Nonetheless, the abstract and conclusions repeatedly describe improvements in held-out risk.

A split held out from parameter fitting is not an independent test set after adaptive search has used it. Label every current endpoint as development risk, explain how many adaptive decisions use that split, and remove confirmatory generalization language. Freeze the revised method, endpoint, and analysis before evaluating an untouched test set. If the holdout has influenced any decisions outside the search process, use a fresh one. Document actual access controls and evaluation provenance rather than relying on directory names.

### 4. Withdraw the claim that equal gate counts isolate symmetry from capacity

The repaired and control circuits have equal gate and parameter counts, but different parameter-to-function maps, reachable functions, and optimization geometry. Equal counts do not establish equal expressivity. Further, the repeated-direction control represents the original interaction at angle 2b. Identical numerical initializations and Adam settings therefore do not match initial operators or optimization trajectories.

The experiment can estimate the effect of these particular circuit interventions under the specified training procedure. It does not isolate an abstract symmetry-only effect. Replace “confound-free,” “differ only in symmetry,” and “attributable to symmetry rather than capacity” with this narrower estimand. Add operator-matched original/control initializations, optimizer-budget sensitivity, and multiple asymmetric controls if retaining a mechanistic attribution. For a direct function-space intervention, evaluate f and its exact Reynolds projection on the same complete-orbit distribution; explain that this answers a different question from retraining different circuit families.

### 5. Remove the unsupported if-and-only-if claim

“Repair helps iff the target is invariant” is not proved by three mismatch levels on one task and one circuit family. An invariant target does not guarantee that a separately trained repaired circuit outperforms an asymmetric one. Conversely, approximate symmetry can yield a beneficial bias–variance tradeoff even with a nonzero breaking component.

State instead that the observed mean differences have opposite signs at the tested mismatch settings, subject to corrected uncertainty. Distinguish the exact squared-risk projection identity for a fixed predictor from empirical comparisons of separately optimized architectures. Do not use the former as a theorem about the latter.

### 6. Correct the interpretation of the invariant-risk floor

The population bound requires a group-invariant input measure. The code checks the agreement between eta-squared times the empirical mean of b-squared and the residual from subtracting an orbit-averaged target, evaluated at the sampled development representatives. That agreement is algebraic; it does not establish a universal empirical lower bound on the singleton development sample. A sample containing one representative per orbit can admit invariant interpolants of those labels.

Specify the probability measure for the theorem, prove its invariance for the benchmark, and separate population bounds, Monte Carlo estimates, and exact finite complete-orbit bounds. If claiming an empirical floor, evaluate an explicitly orbit-completed distribution with declared weights. Report excess risk above that floor with uncertainty. At eta = 1, the reported repaired risk 0.9711 exceeds the quoted floor 0.866 by about 0.1051, which is larger than the repaired/control difference 0.04523. “Pinned near the floor” requires quantitative justification and an approximation/optimization error analysis.

### 7. Repair the inference procedure and null-result language

The search analysis computes a purported two-sided p-value by counting which side of zero ordinary bootstrap means occupy. This is not automatically a calibrated null-hypothesis test. Holm correction cannot repair uncalibrated input p-values. Use a justified paired test or null-centered bootstrap, state assumptions, and include an appropriate small-sample sensitivity analysis. A sign-flip test is useful only with its own exchangeability or symmetry assumptions made explicit.

Define the multiplicity families, including the two primary task-specific tests and the repair contrasts. Never report simulated p-values as literal zero. More importantly, confidence intervals spanning zero establish failure to detect a difference, not equivalence or absence of benefit. Replace “clean null,” “unchanged,” and “does not improve” with appropriately scoped language. If practical equivalence is the desired result, prespecify a meaningful margin and show that the interval lies within it.

### 8. Resolve contradictions between the prose and tables

The repair findings say the control tracks the original at every eta with an interval containing zero. At eta = 0, the table instead reports control minus original = -0.00107 with interval [-0.00203, -0.00017], excluding zero under the current analysis. Correct both the analysis and the accompanying interpretation. Lack of significance at other eta values would not establish equivalence either.

The search findings attribute the null to an “implementation-reliability result,” but the main results do not provide a corresponding paired reliability endpoint. Add hypothesis correctness, executable validity, channel and predictive defects, nonconstant-output checks, and repair success statistics, or remove the claim of demonstrated reliability improvement.

### 9. Establish a contribution beyond known symmetry effects

The acknowledged projection mathematics and known equivariant constructions are useful foundations, but not the new result. The potential contribution is evidence about how verification changes LLM behavior and resulting models. The current paper gives little direct measurement of the propose–implement–perform gap that motivates it.

Provide a contribution-to-evidence table. Compare against direct constructive equivariant architectures, simple classical task-aware baselines, and non-LLM search with access to the same verifier/repair tools. Include incorrect-group hypotheses and symmetry-breaking tasks to test verifier selectivity. If claiming transfer or discovery, evaluate a genuinely unseen task family and distinguish supplied-group construction from inferred-group discovery. More tasks, budgets, and model treatments are needed for broad claims; alternatively narrow the title and conclusions to the current small benchmark study.

The absence of a significant LLM advantage on graphs does not show that a density shortcut caused its disappearance. That explanation needs an intervention, such as density-matched graph evaluation or a controlled shortcut-strength sweep.

### 10. Correct and verify the bibliography

Two checked entries contain material bibliographic errors:

- The cited ICML 2021 paper is **Bryn Elesedy and Sheheryar Zaidi, “Provably Strict Generalisation Benefit for Equivariant Models.”** It is not “Provably depth-efficient quantum neural networks via symmetric architecture,” and the listed author initials are incorrect. See the [official PMLR record](https://proceedings.mlr.press/v139/elesedy21a.html).
- The ShinkaEvolve record lists **Robert Tjarko Lange, Yuki Imajuku, and Edoardo Cetin**, with title **“ShinkaEvolve: Towards Open-Ended and Sample-Efficient Program Evolution.”** The manuscript's title and authors differ. Verify the final venue metadata against the version actually cited; see the [primary arXiv record](https://arxiv.org/abs/2509.19349).

Audit every remaining entry against its primary source, including title, authors, identifier, publication status, and the claim it supports. These two verified errors do not prove that all remaining references are wrong, but they make a complete audit necessary. Extend the novelty comparison beyond a list of adjacent topics and avoid claiming priority until the closest empirical and methodological predecessors have been compared directly.

### 11. Make the experimental record independently reproducible

Replace `ycrc-local` with a precise model/checkpoint identifier and immutable revision, plus serving configuration, decoding settings, reasoning configuration, prompt templates, token limits, and failure/retry policies. Report both evaluator-call budgets and actual compute/inference costs; Reynolds averaging adds group-dependent inference cost. Check matching of parameter-training budgets as well as candidate counts.

Release raw paired run records, split identifiers, dataset generation seeds, code revisions, and the exact analysis command for each table. Explain which plans were committed before which results were inspected, and clearly distinguish pilots from subsequent confirmations. Blanket assertions that every result was prospective require dated evidence.

The separate Qwen report is explicitly one incomplete run, with context-length failures, nonrandom missing generations, and a historical score using train–test information. Keep it exploratory and separate from the 120-run prospective study; do not use it to establish model rankings or clean generalization. Resolve stale documentation: the repair module's opening description still describes ansatz-generated teachers, whereas the active implementation uses the invariant oracle plus a linear breaking direction.

## Presentation and scope

Identify the audited prior study precisely, with a stable citation or archived artifact and reproducible evidence for each criticism. If it is an earlier version of this project, say so. State the encoding and state-preparation conditions required to lift block equivariance to predictor invariance, in addition to the readout condition. Give the analytic argument for the repaired family rather than presenting numerical zero as proof. Report eta = 0.5 risks as well as contrasts, and distinguish raw confidence intervals from multiplicity-adjusted tests.

The mathematical definitions of strict and channel residuals and the qualified projection identity are reasonable foundations. The refusal to claim quantum advantage is appropriate. Those strengths should remain, with the assumptions and scope made explicit.

## Minimum path to a publishable revision

1. Recompute the repair statistics using genuine experimental units and correct the search repair endpoint.
2. Rewrite every causal, generalization, equivalence, and floor claim to match the actual estimand and assumptions.
3. Freeze a corrected protocol and evaluate the selected predictors on untouched data.
4. Demonstrate the proposed behavioral contribution with direct verification/reliability measurements and appropriate baselines, or reposition the work as a focused audit.
5. Correct all bibliography metadata and provide reproducible provenance for the experiments and preregistration claims.

My recommendation is based on identifiable validity problems, not on the fact that the primary performance hypothesis was unsuccessful. A well-powered and well-measured negative result could be publishable. The present evidence does not yet support the manuscript's stronger claims, and fixing only the prose will not resolve the duplicated observations or the omitted repair endpoint.
