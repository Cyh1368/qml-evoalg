# Fourth-round referee report

**Manuscript:** Executable Verification and Analytic Repair in LLM-Guided Quantum Circuit Search  
**Response reviewed:** `REBUTTAL_ROUND3.md`  
**Date:** 12 November 2026  
**Recommendation:** Reject under the requirement that the work be novel, rigorous, and impactful.

Dear authors,

The corrected-verifier comparison and 72 new search runs are substantial additions. They address the central experimental omission in my previous report. The corrected gate captures the benefit of averaging over the valid ring group and avoids the harmful mismatched-group intervention; the contemporaneous search comparison provides useful evidence that corrected feedback has a small effect on development-selected candidate risk in this particular ring experiment. I credit these findings and do not regard the earlier defective gate as the sole basis of the current submission.

Nevertheless, I do not recommend acceptance. The proposed boundary result is not yet a correct general characterization of verifier value; the third-task evidence is overstated; several implementation details undermine the claimed comparison; and the manuscript remains internally inconsistent. More fundamentally, the surviving scientific lesson largely combines familiar properties of validity tests, approximation bias, and decision costs. The work has become a better technical report, but a compelling new, consequential research result is still missing.

This decision does not require positive LLM results, quantum advantage, or a larger benchmark collection for its own sake. A precise negative result or useful general theorem could satisfy the standard. The present record supports narrower conditional observations than the novelty claim demands.

## Scope and acceptance assessment

I read the rebuttal, inspected the revised manuscript and the implementations of corrected-feedback analysis, corrected-gate probing, and decision-rule evaluation. I did not run new model calls, retrain circuits, or open sealed data. My findings concern the supplied results and inspectable code; I have not performed a new exhaustive literature search or independent full reproduction.

| Criterion | Fourth-round assessment |
|---|---|
| Novelty | Insufficient. The proposed two-probability characterization is incomplete, and the supported boundary cases are elementary consequences of the test definition. |
| Rigor | Improved, especially through corrected controls and contemporaneous runs, but not complete. Important claims still exceed sampling, endpoint, and implementation evidence. |
| Impact | Not demonstrated beyond the local setting. There is useful implementation guidance, but no validated general decision rule, consequential external audit, or decisive broad negative result. |

## What is resolved or materially improved

1. **The corrected verifier is now a real comparator.** Its success on the same frozen candidates establishes that the original ring recall failure was caused by the implementation. The withdrawal of the earlier bottleneck interpretation is appropriate.
2. **Corrected feedback has been run inside search.** The new fitness arm is contemporaneous, and the matched budget and training configuration are checked. This addresses my request for new trajectories rather than post-processing alone.
3. **Decision accounting now includes the defect statistic's cost and random selection.** Demoting the defect rule when it does not outperform simple alternatives is appropriate.
4. **The intended primary repair estimand is clearer.** Seed-vector inference conditional on fixed directions is defensible for optimizer variability; the alternative resampling results are useful sensitivity analyses.
5. **Panel counts, frozen-policy evaluation, and numerical lint are more honestly described.** These corrections should remain. They are improvements in rigor, although not independent scientific contributions.

## Remaining acceptance blockers

### 1. The chosen novelty claim omits variables essential to verifier value

The rebuttal proposes that verifier value is a function of the probability that the supplied group is wrong and the probability that the proposal distribution falls inside the target's symmetry group. In general these are insufficient. Value also depends on the magnitude and distribution of repair benefits and harms, the gate's sensitivity and specificity, its numerical and statistical errors, and the cost of checking and repairing.

Let Δ be repair risk minus unrepaired risk, A the gate's binary firing decision, and C the relevant cost. Relative to never repairing, the expected change is

`E[A Δ] + w E[C_gate + A C_repair]`.

Relative to always repairing it is

`E[(A − 1) Δ] + w E[C_gate + (A − 1) C_repair]`.

Knowing only two group-validity probabilities does not determine either expression. Two problems can have identical validity probabilities and opposite optimal policies because their conditional effect magnitudes differ. A valid group need not produce a strictly useful repair for every predictor; an invalid group need not harm every predictor, as your own two beneficial mismatched repairs show. If the “supplied group” is itself sampled from Q and “wrong” means outside the true label-symmetry set, your two probabilities may simply be complements rather than two independent explanatory quantities.

**Required:** Replace the claimed characterization with a correctly specified decision model, including the estimand, distribution, assumptions, losses, and costs. Either prove a substantive result under those assumptions or present the current observation as descriptive accounting. Constant-output predicates being unable to discriminate is correct but does not itself establish novelty.

### 2. The third-task evidence does not prove a non-discriminating verifier

Zero acceptances in 400 sampled proposals does not establish zero acceptance probability. It is consistent with a rare valid subgroup. The rebuttal itself identifies the eight square symmetries as valid; a proposal distribution concentrated on those symmetries would be accepted. Thus the claim that the n=9 verifier is “provably non-discriminating in the opposite direction” is unsupported.

Likewise, checking all permutations on a finite probe set is exhaustive over transformations, not over inputs. It does not by itself prove the population label-symmetry group. The algebraic square-symmetry anchor establishes at least eight valid transformations; equality with the entire label-symmetry group requires ruling out others. The graph invariance can be proved from connectedness itself, and the ring quadratic form can support an analytic characterization; supply those arguments if exact cardinalities matter.

A further code issue affects the n=9 fallback. In `corrected_gate.label_test`, when closure exceeds the cap, the code samples arbitrary permutations from S_n rather than words in the proposed generators. Such a permutation need not belong to the hypothesized subgroup. A violation outside that subgroup does not refute the hypothesis. The output also marks untruncated finite-input tests as `certifies_soundness`, which overstates what finite probing establishes.

**Required:** Sample within the proposed subgroup, or return an explicitly inconclusive result. Report zero sampled acceptances with its finite-sample bound and the specified Q. Distinguish algebraic proof, exhaustive finite-domain checking, and finite-probe evidence throughout. The third task currently extends probing scope, not validated decision-policy transfer.

### 3. The “empirical LLM proposal distribution” is not the distribution named

`corrected_gate._empirical_hypotheses` collects hypotheses from every run in `logs/runs_confirm`, without filtering LLM arms or task family, and appends each selected best hypothesis in addition to its occurrence among proposals. The main loop computes a filtered `emp_here` but calls `accept_probability(..., empirical=emp, ...)` using the unfiltered pool.

Consequently, the reported empirical distribution can mix random/mutation proposals with LLM proposals, mix both six-qubit tasks, and double-weight selected candidates. The 0.47 acceptance estimate should not be called the actual ring LLM proposal distribution without correcting or explicitly defining those weights.

Independent resampling from this fixed pool can justify Monte Carlo uncertainty conditional on that pool. It does not measure uncertainty about the underlying adaptive LLM proposal process or future runs. Exact enumeration of the finite stored pool may also remove the need for this Monte Carlo layer.

**Required:** Define Q precisely, filter by model arm/task/target as intended, remove unintended selection duplicates, and distinguish empirical-pool Monte Carlo error from run-level uncertainty. Recompute the headline ratios. A contrast between uniform permutations and strongly structured prompts is informative, but should not be advertised as a general three-orders-of-magnitude diagnostic failure based on the wrong pool.

### 4. The decision comparison still has mismatched group inputs and recalibrated thresholds

In `decision_rules2.evaluate_candidate`, the corrected label test uses the current regime's group. The defective label test always receives `gens_declared`, and the channel residual is computed once with `group="true"` before the regime loop. In mismatched-group regimes these are not tests of the same proposed repair. This prevents an isolated comparison of defective versus corrected semantics and of the channel condition across regimes.

In `_masks`, q1 and median are recomputed from the defect values within each regime. This is not the rebuttal's claimed procedure of freezing a threshold from the development candidate pool and applying it to invalid groups. A predeclared quantile rule is a valid alternative design, but it maintains a rank-based selection fraction and must be described as recalibration, not fixed-threshold transfer.

**Required:** Pass identical regime-specific groups to all gates, changing only the stated treatment. Either implement a frozen numeric threshold or relabel the analysis as a within-regime quantile selection policy. Recompute the relevant comparison and costs. These issues do not necessarily overturn the corrected label gate's valid-group result; they limit the causal interpretation of the multi-rule experiment.

### 5. Cost-optimality claims need a complete and operational decision problem

A never-repair rule is absent as an explicit zero-cost baseline. In a regime where all corrected decisions reject, never repairing has the same realized prediction loss and no gate cost. Thus a corrected gate cannot be unqualifiedly optimal for positive cost weights in a known mismatched regime. Its value is insurance when the regime is uncertain, which requires a mixture or distribution over supplied groups and a common policy applied before knowing the regime.

The code estimates per-prediction averaging time as raw prediction time multiplied by group size; not every reported cost is directly measured. It also includes both one-off averaging and horizon-dependent overhead, whose operational meaning should be explicit so evaluation work is not charged as deployment work or counted twice.

**Required:** Include never repair, define what the decision maker knows, and evaluate policies under a stated mixture of valid and invalid groups with sensitivity to mixture frequency. State whether risk is mean per prediction or cumulative loss when combining it with horizon-scaled cost. Identify measured versus extrapolated timings and assess timing variability before declaring strict cost winners. A grid of user-chosen weights does not itself demonstrate practical impact.

### 6. The corrected-feedback result is useful, but its interpretation needs precision

The ring verify-minus-fitness interval, `[-0.00016, +0.00093]`, is meaningfully narrower than ±0.002. I accept this as more informative than a nonsignificant p-value alone. It constrains the mean effect on this candidate-risk endpoint under the experiment's conditions.

However, the frozen analyzer describes a superiority rule—CI excludes zero and absolute mean exceeds 0.002—rather than implementing an equivalence test. The rebuttal alternates between “no effect,” an interval bound, and “difference not detected.” The code applies Holm p-values after creating verdict strings without updating those verdicts. The manuscript should distinguish a descriptive interval wholly inside a prespecified practical band from any formal multiplicity-controlled equivalence conclusion. Explain why 0.002 is practically meaningful on this risk scale and how it relates to earlier margins.

The repair arm again uses candidate risk as its official endpoint. This is now openly disclosed, so it is not the hidden error of round one. But coverage-conditional averaging over three ring runs does not replace the full deployed-pipeline contrast. That contrast can be computed from stored diagnostics with zero repair effect for non-firing runs, without another holdout read.

**Required:** Report candidate and deployed contrasts separately, label the three-run conditional estimate appropriately, and restrict the feedback bound to development-selected risk on one dataset/model/budget. Use the contemporaneous comparison for causal interpretation; corrected-versus-old runs also differ in run timing and potentially serving state. Do not equate “trajectory outcome did not move” with a bounded average endpoint difference.

### 7. The submission remains inconsistent about what has been removed or completed

The current abstract still says a “verifier-free” defect gate recovers 79% of benefit. The old A5 decision section still presents the implemented gate's 100% forfeiture and the 79% recovery as present-tense conclusions. Yet the rebuttal says those interpretations have been withdrawn or demoted. Most strikingly, after describing the 72 corrected-feedback runs, the Discussion's “What would change these conclusions” paragraph says corrected-feedback runs were not performed.

These contradictions are material: they leave readers unsure which system supports the paper's central claim. The reported claim-binding mutation tests on this paper, its own claim ledger, and its own rebuttal are useful internal checks, but these are not independent external research artifacts. Context-token binding is plainly not a substitute for semantic reconciliation, as the surviving contradictions demonstrate.

**Required:** Produce one coherent final manuscript. Move obsolete experiments and review history to a clearly marked audit appendix, preserve their provenance, and state the final claims once. Remove claims of external validation for tests on documents produced within this same project. The checker can remain supporting software without a novelty claim.

## Novelty and impact judgment

The corrected results now support a clear local account: a wrongly specified verifier rejected valid repairs; fixing it restores expected acceptance; valid-group averaging helps these predictors; mismatched averaging usually harms them; an exactness screen rejects sufficiently perturbed labels; and corrected feedback has a small mean effect on ring candidate risk at the tested budget.

This is useful, but its general components are expected from the definitions and standard bias–variance and decision reasoning. The tolerance determines a numerical membership test's boundary by construction. The interesting unresolved question is whether a calibrated, statistically justified screen can choose beneficial repairs under approximate symmetry better than existing simple policies. The current tiny perturbation sweep illustrates a failure mode; it does not solve that problem or establish a new transferable law.

I also would not accept the claim that no approximately symmetric target exists in the current set without qualification: adding a non-invariant perturbation already creates an approximately symmetric target. What is missing is independently validated, task-relevant approximate symmetry over a meaningful range, with effects and costs that distinguish competing policies.

## What would justify reconsideration

A revised submission should first fix the concrete sampling, group-input, threshold, endpoint, and manuscript issues above. Beyond correctness, choose one contribution that can meet the research bar:

- A valid decision-theoretic result with nontrivial assumptions and useful consequences, followed by empirical validation; or
- A calibrated repair policy tested on independent approximately symmetric tasks against corrected label screening, always repair, never repair, and fair non-LLM baselines; or
- A sharply scoped negative study whose effect bounds answer an important externally motivated hypothesis across conditions sufficient for the claimed scope.

I am not requiring all three. I am requiring a substantive advance beyond correcting and explaining this implementation. The new controls and runs make the technical report stronger, but the proposed boundary/accounting claim is not yet sufficiently novel, rigorous, or impactful to warrant acceptance. My fourth-round recommendation is therefore **reject**.
