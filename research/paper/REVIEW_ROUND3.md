# Third-round referee report

**Submission:** Executable Verification and Analytic Repair in LLM-Guided Quantum Circuit Search  
**Response reviewed:** `REBUTTAL_ROUND2.md`, dated 12 November 2026  
**Recommendation:** Reject under the stated requirement that the work be novel, rigorous, and impactful.

Dear authors,

The new experiments resolve several concrete second-round concerns. In particular, the deployed predictor is now evaluated, subgroup hypotheses are no longer inherently classified as invalid, matched-row baselines expose a previously misleading comparison, and the primary repair uncertainty has a defensible fixed-direction estimand. These are substantive improvements.

The most important new finding, however, changes the interpretation of the entire verification study: the implemented gate tests unrelated target columns and uses exact equality for floating-point labels. Its failure on the invariant ring task is consequently a failure of this implementation to test its intended proposition. Demonstrating that an incorrect gate rejects useful repairs does not yet establish a novel limitation of verification or a competitive repair decision method. A corrected verifier is now an indispensable comparator.

My recommendation remains reject. The surviving evidence supports a useful, candid technical report about this particular implementation. It does not yet meet the requested joint standard for a research contribution. This judgment does not require a positive LLM result or quantum advantage: a rigorous and consequential negative result could qualify. The present negative result is entangled with known implementation defects, while the proposed new contributions are either elementary diagnostics, ordinary statistical procedures, or insufficiently validated engineering tools.

## Scope of this review

I read the second-round rebuttal and the relevant revised LaTeX sections, inspected the new decision-rule, verifier-semantics, deployed-holdout, paired-inference, and manuscript-number-checking implementations, and consulted the artifact manifest. I ran the manuscript number checker: it reports **863 generated numeric tokens, 414 manuscript tokens, OK** for the current files. I did not rerun expensive training, call the model, or open sealed arrays. This review evaluates the submitted record and code; it is not an exhaustive independent reproduction or a new systematic literature search.

## Acceptance assessment

| Criterion | Assessment |
|---|---|
| Novelty | Insufficient. The newly proposed diagnostic needs a correct probabilistic definition; repair accounting is useful but not itself a new method; crossed resampling and numerical consistency checks are not established here as research advances. |
| Rigor | Improved substantially, but not complete. The corrected verifier is absent from the main decision and search comparisons, sampling assumptions for several intervals are unjustified, and the manuscript retains withdrawn claims. |
| Impact | Not demonstrated beyond the current small implementation. The most striking new effect is explained by two local bugs; no independent task-family evidence establishes a general decision principle or practically superior method. |

## Concerns now substantially resolved

- **Deployed endpoint:** `holdout_deployed.py` actually averages using the development-frozen hypothesis when repair fired. This resolves the omission in the earlier held-out evaluator. Candidate, deployed, and supplied-group endpoints are distinct.
- **Test-baseline alignment:** baselines now use the same evaluation rows as the search candidates. The reversal of the edge-count baseline claim is an important correction, not a reason to suppress the result.
- **Subgroup semantics:** proper subgroups can now be correctly classified as sound. This resolves the prior false-accept definition error, subject to the finite-probe limitations you acknowledge.
- **Repair replication:** the E-A seed-vector bootstrap correctly targets optimizer variability conditional on the frozen direction set. It is a substantial improvement over treating all cells as independent.
- **Data reuse disclosure:** the graphs deployed analysis is explicitly a second, post hoc read, while the ring inputs are fresh. Exhaustion of unused graph isomorphism classes explains the constraint. It does not turn the graphs result into confirmatory fresh evidence, and I credit the explicit distinction.

These issues should not be reopened as though no progress had been made. The following concerns arise from the revised evidence itself.

## Required substantive changes

### 1. Compare against the corrected verifier before drawing conclusions about verification

The fixed-panel results identify two implementation defects: checking all target columns instead of the scored target, and requiring zero numerical discrepancy for continuous labels. The corrected target-specific, nonzero-tolerance screen accepts all six sound panel entries, whereas the implemented screen accepts one.

Yet the decision-rule comparison retains the defective gate as R1/R2 and contrasts it with unconditional averaging and a predictor-defect rule. The central claim that the gate forfeits 100% of ring repair benefit therefore describes a known incorrect implementation. The most relevant baseline is missing: the same label gate with the scored target and a justified numerical tolerance, followed by the same repair operation.

**Required:** Add corrected-label and corrected-label-plus-channel rules to the frozen-candidate comparison. Evaluate them on both valid and genuinely invalid supplied groups, using a tolerance justified by numerical error and target scale. Freeze their settings before independent evaluation. For claims about feedback changing LLM search, conduct new matched runs with the corrected feedback: post-processing old candidates cannot recover the search trajectories that correct feedback would have produced.

The discovery may motivate a general study of verifier specification errors. Without such a study, the current result is an implementation audit. It should not be framed as evidence that a correctly specified verification policy is a recall bottleneck.

### 2. The proposed group-size diagnostic does not predict gate behavior as claimed

The ratio |L_t|/|S_n| is the acceptance probability for a **uniformly sampled individual permutation**, assuming an exact target-specific membership test and a known true label-symmetry group. Your proposals are structured generator lists and their closures, sampled nonuniformly by a search process. Their relevant probability is

`Pr_{H drawn from Q}[H is a subgroup of L_t]`,

where Q is the actual proposal distribution. For k independent uniform generators, the ideal acceptance probability would be `( |L_t| / |S_n| )^k`, not the single-permutation ratio. Neither model describes arbitrary LLM proposals without further evidence.

A small ratio also does not imply useful information: Q might be supported entirely on valid subgroups, or entirely on invalid hypotheses, yielding constant decisions. Conversely, the full-group case establishes vacuity only within the specified permutation hypothesis domain. The ring failure is not predicted by 12/720: you have attributed it to checking the wrong labels and using zero tolerance.

**Required:** State the diagnostic's assumptions and limited conclusion precisely. Distinguish algebraically proven symmetry groups from finite-probe estimates, and explain the cost of obtaining L_t before calling it a practical pre-run diagnostic. Enumerating n! permutations does not scale, and already knowing the full valid set may solve much of the proposed discovery problem. Validate any stronger predictive claim across differing proposal distributions and corrected gates. As it stands, the boundary observation that an always-accepting predicate cannot discriminate is correct but not a sufficient novel contribution.

### 3. The predictor-defect rule has not demonstrated efficiency, safety, or generalization

In `decision_rules.py`, the statistic for R3 is `mean((raw - avg)**2)`, and `avg` is computed using the same group averaging whose application the rule is meant to decide. Thus estimating the statistic already incurs the averaging work on the sampled rows. The rule may still be useful for amortized deployment decisions, but the present accounting does not establish that it saves computation.

The q1 threshold selects roughly 75% of the current candidates by construction and retains about 79% of the observed ring benefit. All candidates benefit under the valid group in this sample, so 45/45 precision offers little evidence that R3 can distinguish helpful from harmful repairs. Unconditional averaging retains 100% of the benefit. A low-defect candidate can still warrant repair depending on deployment cost and the user's loss objective.

**Required:** Evaluate a clear decision objective, such as expected risk plus inference cost over a stated deployment horizon. Charge the defect-estimation cost, threshold calibration, and verification cost consistently. Freeze thresholds and assess them on independent tasks or candidates, including invalid groups and approximately symmetric targets. Compare with a random 75% selection rule and with the corrected label gate. Until then, describe 79% as a descriptive retention fraction, not evidence of a better repair policy. “Verifier-free” should also be qualified: R3 itself measures predictive symmetry, even though it omits label verification.

### 4. The mismatched-group control does not evaluate the decision rule it names

`decision_rules.py` describes R4 as “R2's decision, but averaging over a mismatched group.” Its summary actually averages `delta_mismatch` over every candidate with a defined mismatch and does not apply R2's firing mask. On ring, R2 fires zero times, while R4 is reported as applying to all 60 candidates.

The +0.00399 result is a useful unconditional mismatch stress test. It is not the realized risk of R2 under a mismatched group, and it does not show that any proposed gate prevents the harm.

**Required:** Rename the current control accurately, and evaluate each gate using the same mismatched group and target that its repair would use. Report which harmful interventions are rejected, which beneficial interventions are missed, and the resulting paired risk and cost. Avoid attributing a safety role to verification without testing that role.

### 5. Several confidence intervals have no justified sampling interpretation

The fixed panel is implemented as **nine generator-set entries**. The 20 random permutations form one joint generator list, and the 15 transpositions another; they are not 35 separate negative-control trials. Their closures may duplicate the full symmetric group. The manuscript partly discloses “panel members,” but its textual list suggests broader independent coverage than the implementation provides.

Wilson intervals over six deliberately chosen, overlapping sound groups and three invalid generator sets do not automatically have binomial coverage for any population of transformations. The same problem applies to proposal-level rates from adaptively related search proposals, and to pooled decision precision across five arms sharing 12 paired seeds.

**Required:** Report fixed-panel counts as descriptive coverage unless a random sampling population is specified. List each generator set, closure, and unique subgroup. If the intent is to evaluate individual random transformations, test them separately and use a defensible sampling design. For search and decision uncertainty, preserve run/seed dependence, report arm-specific results, and bootstrap the appropriate seed vectors rather than treating all proposals or all 60 candidates as independent Bernoulli trials.

Also remove the claim in `crossed_bootstrap_ci` that its interval is “wider by construction.” The product resampling procedure does not guarantee this ordering for arbitrary data. Present the observed ordering as a sensitivity result, with the assumptions of the procedure.

### 6. Fresh predictions do not constitute an independent replication of frozen gate decisions

The rebuttal and manuscript describe zero firing on fresh ring inputs as an independent reproduction of the zero-firing result. The deployed evaluator deliberately uses the **development-frozen** `repair.repaired` decision. That decision cannot change when fresh prediction inputs are opened. Its persistence is therefore guaranteed by the evaluation design.

**Required:** Say that fresh inputs validate the risks of the frozen policies, not the firing-rate mechanism. Independent replication of gate behavior requires new fitted candidates, new gate/probe samples where relevant, or a new task. This distinction does not diminish the value of fresh-input risk evaluation; it identifies what that evaluation actually tests.

### 7. The manuscript still contains claims the rebuttal explicitly withdraws

The current Discussion states that verification is “a precondition for an analytic repair,” despite the rebuttal saying that sentence is gone. It also says the feedback channel “did not move selected risk,” repeats the classical-baseline superiority claim without its now-essential development restriction, and quotes the legacy eta-one interval `[+0.03134,+0.04087]` with 192 units instead of the newly designated E-A primary inference.

These are not merely obsolete historical quotations: they appear in the manuscript's present-tense interpretation. The paper also says every graphs average is a 24-element Monte Carlo average, whereas the deployed-hypothesis code enumerates a subgroup exactly when its order is at most 24. The declared S6 twirl and the smaller deployed subgroup twirl must be distinguished.

**Required:** Reconcile the abstract, tables, Discussion, limitations, claim ledger, and rebuttal. Replace the Discussion with a coherent interpretation of the final experiments. Remove the conversational history of successive referee corrections from the main scientific narrative, retaining an audit appendix where useful. The reader should be able to identify the current estimand and claim without reconstructing three review rounds.

### 8. The numerical checker is a heuristic, not the claimed validation instrument

I ran `check_numbers.py` successfully. Its implementation collects decimal tokens and accepts a manuscript number if it approximately matches **any** number anywhere in the generated summary, allowing percentage scaling. It does not bind a value to an experiment, endpoint, arm, split, contrast, or table cell. It does not implement the docstring's claimed check of contradictory sentence direction, and its decimal-token pattern does not comprehensively parse integers or scientific notation.

Consequently, copying a valid number into the wrong table can pass. The stale primary interval in the Discussion can pass because it still occurs elsewhere in the generated record. The surviving “precondition” claim is outside the check's capabilities entirely. A green check therefore cannot establish manuscript-record consistency at the claim level.

**Required:** Describe the existing tool as a numeric-token lint check. If claiming a reusable audit instrument as a research contribution, bind each reported value to a structured result key and provenance, generate manuscript table cells from those keys, and test deliberate mutations of signs, arms, splits, exponents, and endpoint labels. Evaluate detection and false alarms on artifacts beyond this manuscript. Ordinary software utility alone should not be presented as demonstrated scientific novelty.

## Novelty and impact after the new experiments

The four contributions proposed in the rebuttal do not yet clear the acceptance threshold:

| Proposed contribution | What is supported | What remains missing |
|---|---|---|
| Group-size diagnostic | A correct vacuity boundary for an ideal predicate over a restricted permutation domain | A distribution-aware result, scalable computation, and evidence that it predicts behavior beyond obvious boundary cases |
| Repair decision accounting | Useful descriptive loss and coverage accounting for this implementation | A corrected-verifier comparison and independently validated risk/cost or safety advantage |
| Four-estimand analysis | Improved statistical practice for this experiment | A new statistical result; unchanged balanced-design means under alternative resampling are expected |
| Number checker | A helpful token-level lint script | Claim-level validation, external evaluation, and a demonstrated advance over ordinary generated reporting |

The strongest prospective scientific question is now more specific: **when does a correctly specified, numerically robust verifier improve the risk–cost tradeoff of repair under uncertain or approximate symmetry?** The present study does not answer it. It answers how a particular buggy gate behaved and how known averaging operations affect a small set of predictors.

Impact does not require a large benchmark collection for its own sake. One carefully chosen independent task could be more informative than many closely related runs if it distinguishes competing mechanisms. Here, the missing evidence should distinguish implementation defects from a fundamental gate limitation, and a real decision advantage from retaining a selected fraction of universally beneficial repairs.

## Minimum evidence needed for reconsideration

1. **Correct the manuscript and immediate analysis inconsistencies** above, including the R4 definition, panel units, numerical-checker scope, frozen-decision replication claim, and stale Discussion.
2. **Compare defective, corrected, and alternative gates on identical frozen predictors and valid/invalid groups**, with consistent costs and paired inference. This establishes whether the headline effect survives fixing the implementation.
3. **Rerun search with the corrected verifier if retaining behavioral conclusions about LLM feedback.** Use a clearly frozen protocol and a practically meaningful effect threshold.
4. **Choose one substantive novelty claim and validate it independently:** a distribution-aware diagnostic, an effective repair decision method, or a reusable externally evaluated audit procedure. A suite of corrections to the original submission is not a substitute.
5. **Demonstrate consequence beyond this particular configuration**, through an unseen task, a theoretically justified generalization, or external systems where the proposed method changes decisions or conclusions.

The authors themselves now characterize the work as a narrow technical report, and I agree that this is an appropriate form for the present evidence. Under the requested standard for acceptance as novel, rigorous, and impactful research, my third-round recommendation remains **reject**. The path forward is a focused new experiment or methodological result built on the corrected system, rather than another expansion of the rebuttal narrative.
