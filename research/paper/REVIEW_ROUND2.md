# Second-round referee report

**Manuscript:** Executable Verification and Analytic Repair in LLM-Guided Quantum Circuit Search: What a Controlled Benchmark Does, and Does Not, Show  
**Materials:** revised LaTeX manuscript, REBUTTAL.md, results_summary2.md, provenance record, corrected analysis and evaluation implementations  
**Decision:** Reject in its current form. Substantial progress on rigor; novelty and impact remain insufficiently demonstrated, and important validity issues remain.

Dear authors,

The rebuttal makes meaningful progress. You acknowledge the original errors, change conclusions when the corrected analyses demand it, introduce stronger controls, and add untouched-input evaluation. I regard this as a substantially improved study. I do not, however, recommend acceptance under a standard requiring novelty, rigor, and impact together. Correcting the previous manuscript is necessary but does not itself create a new scientific contribution. The strongest surviving positive finding is that group averaging improves predictions on invariant tasks, including for non-LLM methods. That is useful experimental confirmation of established machinery. The proposed contribution about what verification teaches or enables remains underidentified.

This assessment is based on reading the rebuttal, revised manuscript and generated results, inspecting the relevant repair statistics, group-identification analysis, averaging implementation and held-out evaluator, and checking primary records for Meyer et al. and Otto et al. I did not rerun training, make new LLM calls, or open sealed datasets. Code-level findings below are directly inspectable; I do not claim an exhaustive independent reproduction or priority search.

## Assessment against the acceptance criteria

| Criterion | Second-round assessment |
|---|---|
| Novelty | Not established at the required level. Known projection behavior, a subgroup-identification limitation apparent from the gate definition, and corrections to an in-house study do not yet constitute a strong new result about automated scientific discovery. |
| Rigor | Much improved, but still incomplete. The held-out repair endpoint is omitted, group correctness is misclassified, crossed replication is not reflected in headline inference, and reporting contradicts the stated safeguards. |
| Impact | Plausible methodological value, but limited demonstrated reach. One model, a short search budget, two small task families, and no convincing verification benefit or equivalence result leave the practical lesson uncertain. |

My decision would remain negative even if the remaining reporting bugs were fixed tomorrow: the contribution still needs a compelling scientific question with evidence that changes what researchers should believe or do.

## What the rebuttal resolves

1. **The eta-zero pseudoreplication is acknowledged and corrected.** The new 24 optimizer seeds are genuine distinct units for the direction-free target. The original repair-versus-control result is appropriately no longer treated as established.
2. **The development repair endpoint is restored.** The distinction between a within-candidate averaging effect and a between-pipeline effect is now explicit. The 7/12 graph coverage and zero fired ring repairs are essential disclosures.
3. **The controls are materially stronger.** Operator-matched and random-direction controls, together with budget sensitivity, clarify that equal gate counts did not establish a symmetry-only explanation.
4. **The floor argument is substantially improved.** Separating the population measure, representative-sample estimate, and orbit-completed empirical measure addresses the original mathematical objection. I accept the correction that the old 0.866 floor was one direction's value rather than the correct mean reference for the pooled risk; my first-round numerical comparison relied on the manuscript's misleading presentation.
5. **The fresh repair-input evaluation is valuable.** Its reported effect directions agree with the corrected development interpretation. The failed earlier evaluation and consumed splits are disclosed rather than concealed.
6. **The baseline and provenance work is useful.** The constructive and classical controls weaken an LLM-performance story but strengthen the credibility of the narrower empirical record. Bibliographic corrections and acknowledgment of uncommitted original code and unverifiable original preregistration are appropriate.

These changes deserve credit. The following issues nevertheless prevent acceptance.

## Major remaining concerns and required revisions

### 1. Held-out search evaluation still does not evaluate the repaired pipeline

The central endpoint error is fixed for development analysis but persists in `research/holdout_oneshot.py`, function `_search_run`. It computes `test_risk` using `_train.risk(fit, ...)`, records `repair_fired`, and unconditionally sets `test_risk_averaged_diagnostic` to `None`. It never applies the selected hypothesis's averaging operation to the held-out inputs.

Consequently, E-S7 evaluates the selected underlying candidates, including for the arm named `llm-verify-repair`. It does not test that arm's deployed repaired predictor. The sealed graph number 0.50674 cannot validate the repaired pipeline's held-out performance. This is particularly important because the revised abstract calls deployed averaging the consistent positive effect.

**Required:** Label current E-S7 results as candidate endpoints. Freeze and evaluate both candidate and deployed predictions for each selected model, applying exactly the development-frozen repair eligibility and group. Include the same-tool non-LLM baselines on the same test distribution. Respect the declared consumed-split policy; a post hoc addition to previously inspected test data must be labeled as such or evaluated on newly reserved data. Do not describe held-out search validation as complete until the actual deployed endpoint is measured.

### 2. Valid subgroup hypotheses are not false accepts

`research/search/dev_analysis.py` defines group correctness by equality between the hypothesis closure and the declared task-group closure. It increments `wrong_group_but_label_preserving` for every accepted hypothesis whose closure is not exactly equal to that declared group. On an S6-invariant graph task, a proper subgroup of S6 is a valid symmetry hypothesis. Accepting it is correct behavior for a soundness test.

The 289 graph proposals therefore establish failure to recover the entire declared group under this equality metric, not 289 false accepts. The revised abstract and rebuttal still call them “wrong-group” proposals and use the numbers as a verifier limitation. A hypothesis can be sound and incomplete. In addition, a finite-sample label test is not a universal soundness certificate without coverage or distributional guarantees.

**Required:** Distinguish invalid transformations, valid proper subgroups, exact declared-group recovery, and potentially larger valid symmetry groups. State whether the proposal task actually asks for the maximal symmetry group. Audit correctness at the transformation level against the oracle or an appropriate independent probe distribution. Report false acceptance only for transformations that genuinely violate label preservation. If maximal-group recovery is the scientific objective, define and test it separately from the existing verifier's intended task.

### 3. The selectivity comparison confounds target symmetry with task and hypothesis distribution

The rebuttal compares 299/299 accepted hypotheses on invariant graphs with 8/348 on the symmetry-breaking ring task. This changes the input domain, target, proposed transformations, and search trajectories together. It does not isolate the verifier's response to symmetry breaking. The manuscript also reports only seven accepted hypotheses among 192 hypotheses on the invariant ring task, making the graphs-versus-breaking-ring comparison especially incomplete.

**Required:** Test a fixed panel of transformations on identical ring inputs under invariant and breaking targets. Include true label symmetries, proper subgroups, identity, and transformations known to violate the target. Report sensitivity and false-accept rates with denominators and uncertainty. Analyze search-generated hypotheses separately as a behavioral outcome. Absence of D6 recovery on a target that is deliberately not D6-invariant is not evidence of failure: recovering D6 there would be the wrong scientific answer.

### 4. The claim that verification is a precondition for repair is unsupported

The same declared-group averaging helps random and mutation-only pipelines. That demonstrates the utility of the averaging operation in these settings. It does not demonstrate that a verifier is necessary for that utility, nor that verification itself produced the improvement. With a known valid group, averaging can be applied directly. Channel non-equivariance is also not necessary for predictive non-invariance: a readout can break predictor invariance even when the circuit block is equivariant.

**Required:** Replace “verification's value is as a precondition for analytic repair” with a descriptive statement about the implemented pipeline unless tested. A convincing ablation compares unconditional supplied-group averaging, label-gated averaging, the current label-plus-channel gate, and a predictor-defect gate, including truly invalid groups. Measure saved cost, prevented harm, and missed beneficial repairs. This could produce a new decision rule or useful empirical finding; current evidence does not identify it.

### 5. Crossed dependence remains in the headline repair inference

For eta greater than zero, `analyze_repair.py` constructs all direction-by-optimizer differences and passes them to an ordinary unit bootstrap and sign-flip test. A direction-cluster bootstrap is added separately. The headline 192-unit intervals and p-values are still based on independent resampling of cells that reuse both directions and optimizer seeds.

The correct analysis depends on the estimand. For a fixed set of directions and random optimizer seeds, average across directions within each seed and resample the seed vectors. For generalization across directions and optimizer randomness, use a justified crossed or hierarchical procedure and make its assumptions explicit. Resampling only directions does not account for all dependence introduced by shared optimizer randomness.

**Required:** Promote the estimand-appropriate analysis to the main tables. Report direction-specific effects and cluster-aware sensitivity results alongside it. Apply the same reasoning to the four-direction/eight-seed fresh-input analysis. The large eta-one mean effect may survive; the present p-values and precision still require justification. Also clarify that seed intervals conditional on one dataset do not quantify variation over newly sampled training datasets or task families.

### 6. Automated reporting still produces incorrect or contradictory conclusions

Several directly observable issues remain:

- In `research/core/paired.py`, `verdict()` returns **“b worse”** for a wholly positive interval. For an a-minus-b risk contrast, positive means **a is worse**. This reverses the textual interpretation of many repair results in `results_summary2.md`.
- The generated v1 eta-zero rows say **“a better”** because the raw percentile interval excludes zero, even though the rebuttal correctly withdraws the benefit and the adjusted tests do not support it. A generic CI-only verdict cannot enforce the stated inferential policy.
- The generated tables still print Holm values as **0.000**, contrary to the claim that resolution floors are consistently displayed.
- The E-R1 table labels a column “identity gap” and prints values around 0.05–0.21 for asymmetric breaking-target fits. Inspection of `analyze_repair.py` shows that this is the invariant-only residual; a separate `full_identity_gap_max` measures the corrected identity. The rebuttal's roundoff claim and the table therefore refer to different quantities. This is a reporting mismatch, not evidence that the corrected algebra is false.
- The manuscript says enforcement “buys nothing” over the matched control, that non-LLM averaging helps “equally,” and that verification “did not move selected risk.” Those claims exceed failure to detect a difference. No equivalence or equality-of-benefit result has been established.

**Required:** Correct the direction bug; define verdicts by the prespecified inferential rule and metric direction; show both raw intervals and adjusted tests without conflating them; print nonzero resolution bounds accurately; label both identity residuals correctly; and remove equality/no-effect wording. Regenerate every table and inspect the generated prose. Automated compilation alone is not validation.

### 7. Baseline conclusions mix splits and overstate what optimization establishes

The E-S7 caption compares sealed-test search performance with the edge-count rule's **development** risk 0.351. That is not a matched test comparison. The manuscript also says the three-parameter equivariant block “cannot express connectedness.” A failed fit at a finite optimization budget does not prove a function-class impossibility.

**Required:** Evaluate each training-fitted baseline on the same test split and loss as the search pipelines. Replace the expressivity impossibility statement with an empirical optimization result unless a proof or exhaustive representational argument is provided. Distinguish equal per-fit budgets from equal total search budgets. An oracle that defines the synthetic target is a reference value, not a learned competitive baseline.

The declared-group averaging analysis also uses a Monte Carlo subset of group elements when the full group exceeds `MC_TWIRL_ELEMENTS`, as `dev_analysis.py` explicitly records. Report that approximation and its inference cost prominently. Do not silently transfer guarantees for exact Reynolds projection to a finite random approximation.

### 8. Provenance and reproduction need one consistent final manifest

The rebuttal reports the inputs-only holdout seed 20261204 and v4 access record, while the manuscript's reproduction command still names `fresh_v3` and v3 output files. `PROVENANCE.md` retains older descriptions of the v2 remedy and v3 evaluation. These histories are useful, but the current reproduction path is ambiguous.

File hashes before and after a read establish immutability, not that data were never previously inspected. Read-only permissions and a path-string guard are useful procedural controls, not strong access isolation. The current limitations should describe that distinction accurately. Git timestamps supply a documented chronology; they should not be represented as an independently certified preregistration service.

**Required:** Add a final artifact manifest mapping each manuscript table to its code revision, result file, endpoint, split ID, seed, digest, protocol/amendment, and status. Mark obsolete and invalid artifacts explicitly. Provide the exact v4 reproduction/analysis commands without inviting another unauthorized holdout access. Preserve the disclosed model-checkpoint limitation; bit-level LLM replay is not a prerequisite for publication if the raw outputs and transformations are reproducible.

## Novelty: what remains after the corrections?

The revised paper has four candidate contributions, none yet sufficient for acceptance on its own.

- **Self-audit:** useful for correcting the record, but its broader importance depends on whether the audited errors affect an influential published claim or recur across independent studies. An in-house correction is not automatically a new research finding.
- **Repair experiment:** better controls show that the originally claimed symmetry-specific benefit is unestablished and that imposing a mismatched invariant restriction has a cost. The latter is expected approximation bias. The former could support a useful methodological result if it reveals a general mechanism for misleading controls across architectures or tasks.
- **Averaging gains:** empirically informative, but theoretically expected for exact averaging with invariant targets and measures. Their presence across LLM and non-LLM pipelines does not establish a new verification mechanism.
- **Group recovery failure:** a label-preservation test cannot distinguish a full valid group from its valid subgroups by testing their validity alone. This is a structural property of the test, not an unexpected discovered limitation of LLM reasoning.

The relevant prior literature already covers symmetry-based model construction and distinguishes enforcing, discovering, and promoting symmetry. See [Meyer et al., PRX Quantum](https://doi.org/10.1103/PRXQuantum.4.010328) and [Otto et al., JMLR](https://jmlr.org/papers/volume26/24-1315/24-1315.pdf). The manuscript needs an explicit account of what its evidence adds beyond these foundations. A targeted check also shows Meyer et al. explicitly discuss invariant reuploading constructions; the rebuttal's blanket assertion that this attribution was unsupported should be revisited against the primary text.

I am not requiring a positive LLM result, a quantum advantage, or a universal theorem. A negative result can be novel and impactful if it tightly constrains an important hypothesis. Here, the uncertainty is broad, the verifier is not designed to identify maximal groups, and the treatment exposure is sparse. Those features make the negative interpretation less decisive.

## What would change my recommendation

Choose a coherent contribution and supply evidence that is decisive for it. The following are alternative paths, not a demand to complete three new papers.

1. **A new verification/repair decision method:** correct the distinction between valid symmetry and maximal-group recovery, introduce a justified way to decide when and how to repair, and show reduced risk or cost on unseen task families against supplied-group averaging, constructive models, and non-LLM search with identical tools. Include wrong-group negative controls.
2. **A decisive negative empirical study:** test a well-defined claim about verification using informative feedback, adequate intervention exposure, prespecified practically meaningful margins, and enough independent task/model/budget variation to establish where benefits are absent or constrained. Explain why this changes a reasonable prior expectation, rather than documenting that one small harness has low power.
3. **A general methodological audit:** demonstrate that the identified statistical, endpoint, or control failures recur in independent published systems, and provide a validated audit procedure or benchmark that others can use. The impact would then come from a documented field-level problem and a reusable remedy.

For any path, the immediate acceptance blockers are the true held-out deployed endpoint, correct subgroup semantics, estimand-appropriate inference, consistent reporting, and fair test baselines. Resolving those is necessary. Demonstrating a substantive new and consequential result is additionally necessary.

The revised study is more credible than the first submission, and its transparent corrections are valuable. My recommendation remains **reject**, because the present manuscript still falls short on all three acceptance criteria taken together. A narrower technical report can accurately preserve these findings now; a publishable full research contribution requires the additional conceptual or empirical advance described above.
