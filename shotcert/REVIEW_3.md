# Third referee report: *Symmetry Spending Under a Quantum Shot Budget*

**Decision: Reject the present manuscript. Continue the research direction, with a new central result and a corrected experiment.**

## Overall assessment

The response to round two is unusually direct. The authors now distinguish a finite-sample Maurer–Pontil certificate from Studentised and plug-in selectors; count single-copy preparations per shot; share deterministic measurement records; and acknowledge that the earlier claimed resource advantage reverses in their revised sweep. The small-budget outcome enumeration and the explicit physical-action check remain useful contributions to the technical record. I appreciate that the frozen A2.7 stop gate is reported as failed rather than rewritten after seeing the result.

The paper still does not support its new headline negative. The symmetry arm's calibration contrast is measured against a raw predictor with **half the shots** of the raw predictor used to define its reported risk difference. This makes even the corrected finite-sample bound target the wrong quantity. The “matched-resource” table also compares risk differences against different baselines and gives the two arms different deployment shot counts. Its observed factor-of-two cost is largely built into the arm definitions. These issues make the conclusion that symmetry spending loses to the group-free alternative unproven. Even after repairing them, the present paper offers no novel method or theorem and no independently established operational result at the standard of this journal.

This decision does **not** mean the research topic should be abandoned. Choosing and certifying a *deployed finite-shot* predictor under a joint task-instance and state-copy budget is a valid, experimentally relevant question. The present work has clarified why generic calibration and naive orbit averaging are insufficient. A publishable next paper would need a sharper structural result or an equal-access resource advantage that survives correct shot accounting and independent physical tests.

## Principal technical problem: the calibration and scored predictors differ

In [`exp_matched.py`](experiments/exp_matched.py), the symmetry arm sets `S = s * G` and creates `Policy("a0", "raw", S=S)` and a full stratified policy. For its two-element group, the scored risk difference is therefore

$$
\Delta_{2s}=R_{2s}(\mathrm{strat})-R_{2s}(\mathrm{raw}).
$$

But [`shared_record()`](experiments/exp_matched.py) measures only **$s$ identity-circuit shots** and $s$ transformed-circuit shots, and [`losses_from_record()`](experiments/exp_matched.py) uses the $s$-shot identity mean as the raw baseline. The actual calibration contrast has expectation

$$
\mathbb E[D_{\rm cal}]=R_{2s}(\mathrm{strat})-R_s(\mathrm{raw})
=\Delta_{2s}-\frac{\mathbb E[\sigma_0^2(X)]}{2s},
$$

for the manuscript's unbiased $\pm1$ shot estimator. The last term is generally positive. At $s=8$ on the Heisenberg task, its scale is about $0.83/16\approx0.052$, much larger than the reported group gain of roughly $0.0085$. The calibration record therefore makes the group policy appear substantially better than the matched-$2s$ risk difference used as “truth.” A simultaneous Maurer–Pontil bound can be perfectly valid **for $\mathbb E[D_{\rm cal}]$** and still fail to certify $\Delta_{2s}$.

The group-free arm does not have this particular mismatch: its raw and shrinkage policies both use $s$ shots, and its calibration record has $s$ identity shots. This asymmetry contaminates the group-versus-group-free selection and the claim that the valid rule reaches high power in any row. The risk calculation, calibration evaluator, and ledger must be tied to one explicit stochastic predictor per policy; a test should verify their conditional means, variances, and expected loss contrasts for each arm at several small budgets.

There are several legitimate repairs. For example, keep the $2s$-shot raw baseline and collect **another $s$ identity shots** for calibration, reusing the first $s$ identity outcomes as appropriate and accounting for the resulting within-instance dependence; the group record then costs at least $3s$ per calibration instance. Alternatively, define both candidates at a common total $S$ and allocate $S/2$ to each group circuit while the raw policy receives $S$ identity shots. Either choice needs a new shot ledger and a rerun. Changing the estimand to compare unequal deployment budgets is possible, but it would answer a different question and should be labeled as such.

## The reported negative is not yet a matched-budget comparison

The new [`tabs_matched.tex`](paper/tabs_matched.tex) quotes each arm's best risk difference at a common **shots per circuit** $s=8$. At that point the group policy deploys $2s=16$ shots, while the group-free policy deploys $s=8$. The deltas are measured relative to raw baselines with different shot variances. A larger negative delta in the group-free column does not establish a lower **absolute deployed risk** at an equal per-prediction shot budget. The table's costs of 17,600 versus 8,800 shots likewise show the stipulated two-circuit versus one-circuit price at the same $n,s$; they are not outcomes of optimizing both arms under the same total budget.

The generated verdict finds the cheapest grid point crossing 0.9 plug-in power. The grid begins at $n=100,s=8$, so both arms often cross at their first possible point, mechanically producing a factor of two. A fair frontier would fix a total calibration-plus-deployment budget and inference horizon, allow each arm to optimize its $n$, per-circuit shots, and admissible policies under that budget, and compare **absolute realized risk, useful-selection probability, violation probability, and fallback**. It should show uncertainty around threshold crossing. A $0.9$ power threshold alone is especially weak when the group-free arm's oracle candidate may have a different risk and the selector is the non-guaranteed plug-in rule.

The manuscript's abstract says the group-free arm is cheaper on six of seven tasks, including both physical mechanisms. That is a fair description of the current grid calculation, but it is not a general or even fully matched operational negative. A2.7 may properly prohibit an *advantage* claim; its failure does not by itself establish the stronger proposition that spending shots on symmetry is dominated. The present negative should remain provisional until the estimand and common-budget comparison are repaired.

## The revised submission still lacks a top-tier contribution

The authors now correctly identify the risk expression as conditional bias–variance bookkeeping, the calibration split as the law of total variance, and the Maurer–Pontil radius as an application of a known inequality. The $5{,}000$–$20{,}000$ labeled-instance figure characterizes a conservative bound, not a lower bound for the underlying decision problem. The per-switch optimum charges an interleaved schedule that the predictor need not use. These clarifications are rigorous and welcome, but they leave no new theorem or algorithmic separation.

The paper also does not yet provide a strong empirical negative. All matched-arm evidence comes from a simulator with exact response functions and binomial shot sampling. The cluster variants have nearly identical even- and raw-target behavior, so they are not independent evidence for the claimed odd-content mechanism. The Heisenberg input flip is a useful control transformation, but the authors correctly show it is not a symmetry of the full preparation-and-readout experiment. Its performance should therefore be framed as a particular paired-control denoising example, not as a general symmetry decision. These limitations need not doom the research direction; they make this particular submission a control study rather than a journal-level result.

The [Chen symmetry-release work](https://arxiv.org/abs/2609.11470) already includes finite-measurement decisions and independent validation, while [Catak's allocation paper](https://arxiv.org/abs/2608.24891) treats a different shot/sample estimand. The remaining opportunity is **not** another finite-menu bound. It is a result that uses the structure of symmetry-related measurements to change attainable risk or certification cost under identical access. The [Maurer–Pontil inequality](https://arxiv.org/abs/0907.3740) is a baseline tool for that comparison, not the novel part.

## Specific route to a publishable next paper

1. **Freeze one physical access and deployment model.** Specify the prepared state, transformed circuit or input, observable, label, group action, device-noise stationarity assumption, and exact measurement record. For every policy, state its total deployment shots $S$, circuit settings, switching schedule, and stochastic output. Write the calibration estimator so that its expected contrast equals that policy's deployed-risk difference. Audit this equality analytically and by independent small-system enumeration before any power study.

2. **Ask a sharper structural question.** One promising target is whether a *shared* orbit measurement record, paired conditional variance estimator, or adaptive allocation across orbit points can reduce the **total copies needed for a valid decision** relative to generic paired calibration on the **same candidate policies**. Quantify both between-instance uncertainty and within-instance shot/group randomness. A theorem giving an instance-dependent advantage, a matching lower bound in a restricted access model, or a sharp condition under which all such advantages vanish would be a real contribution. It must account for all copies and labels, and explain why the result does not follow from standard stratified allocation plus generic risk control.

3. **Compare optimized frontiers at equal resources.** Include raw, full average, random group sampling, partial averaging, standard stratified or variance-adaptive allocation, generic paired calibration on the identical menu, and a group-free predictor with well-tuned shrinkage or direct-observable features. Permit physically valid measurement reuse for every arm. Fix a deployment horizon and compare the best admissible policy at the same *total* calibration and deployment copies, reporting absolute MSE and decision power at the declared risk threshold. Reserve oracle risks for interpretation, not for selection or a free comparator.

4. **Test a mechanism where the group could plausibly pay for itself.** Choose a task with a demonstrated group action on the full preparation, channel, observable, and target, plus a separately controlled approximate-symmetry or non-covariant-noise perturbation. Use two independent mechanisms whose odd components and shot variances differ materially; a nearly even cluster variant does not test transfer of the decision boundary. A device run would strengthen impact, but careful simulated noise and independently prepared task instances could support a strong theorem.

5. **Set an early stop gate.** Before a large confirmatory run, require (a) exact agreement between calibrated and deployed estimands, (b) a nonvacuous finite-sample-valid decision at feasible costs, and (c) a material matched-budget gain or a substantive lower-bound explanation for why such a gain is impossible. If these fail, stop developing this selector and archive the result. Do not submit a fourth version whose only new finding is another rearrangement of the same variance identity or a different loose confidence bound.

A negative result could also be publishable if it establishes a **general boundary**, rather than the current local null: for example, a lower bound showing that with scalar single-copy access and a specified symmetry defect, no orbit-based policy can repay its extra circuit/copy cost below a calculable signal-to-noise threshold, with a matching method above that threshold. The present experiments suggest this question but do not answer it.

## Presentation and verification points

The historical appendix is commendably labeled, but it duplicates old section labels such as `sec:certify` and `sec:ledger`, and the reproducibility paragraph still describes the old 16-test, pre-A2 result set. I recommend moving superseded analyses to a linked repository archive rather than carrying their full text inside the submission. The number checker only verifies that a literal appears *somewhere* in generated tables or JSON; it cannot establish that a value belongs to the claimed task, budget, or statistic. The new estimator mismatch demonstrates why semantic tests are needed in addition to a number-presence check.

I reviewed the response, revised LaTeX, generated tables and claims, protocol addenda, matched experiment code, and result JSON. The main objections above follow from the declared policy parameters and evaluator, independent of the outcome of a software test run.

## Final recommendation and judgment on the direction

**Reject this submission. Continue the research question, but stop presenting the current fixed-menu selector and control sweep as a method paper.** The problem of certifying the risk of a finite-shot deployed quantum predictor is worthwhile because the deployment policy changes the risk itself, and the allocation of copies, independent instances, and transformed circuits can matter in practice. This manuscript has not yet found a novel or robust advantage. A new submission should be built around a verified common estimand and either a meaningful structure-dependent theorem or an equal-access resource result that survives strong baselines on distinct physical tasks.
