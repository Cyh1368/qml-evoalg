# Response to the third-round referee report

**Submission:** Executable Verification and Analytic Repair in LLM-Guided Quantum Circuit Search
**Response to:** `REVIEW_ROUND3.md`
**Date:** 12 November 2026

The referee's central sentence is the one we accept without qualification: *"A corrected
verifier is now an indispensable comparator."* It was correct, it was checkable against our own
code, and acting on it changed our conclusions. We had reported that a label gate is a recall
bottleneck for repair; with the gate specified as declared, on the same frozen candidates, it
captures the entire available benefit. The bottleneck was our implementation. That claim is
withdrawn, and the corrected comparator is now the primary one in the manuscript.

We also agree with the recommendation as a statement about the present evidence. What we
report below is a narrow technical report with one boundary result we believe is worth
communicating, and we no longer frame it as a method.

Every change below is traceable to an artifact named in the text. Addendum A6 was committed to
the frozen protocol (`research/REVISED_PROTOCOL.md`, commit `4ab15f81`) **before** any of the new
analyses were run; the analysis of the new search runs
(`research/search/analyze_corrected.py`) was committed **before** those runs finished, with its
decision rule and the 0.002 threshold already in the file.

---

## 1. The corrected verifier is now the primary comparator

**What we did.** `research/search/corrected_gate.py` implements the corrected screen exactly as
A6.1 declares it: the scored target only, and a violation means
$|y_t(gx)-y_t(x)| > 10^{-12} + 10^{-9}|y_t(x)|$ — the probe's own numerical tolerance, so the
gate cannot be stricter than the instrument that defines soundness. `research/search/decision_rules2.py`
re-runs the whole decision comparison on the **same 120 frozen predictors**, now with seven
rules (always, defective label, defective label+channel, corrected label, corrected
label+channel, measured-defect, size-matched random) in five regimes (declared group, valid
proper subgroup, mismatched group, and the declared group under label perturbations
$\epsilon \in \{10^{-12},10^{-9},10^{-6},10^{-3}\}$), with **each rule scored under its own
firing mask** and with all costs measured, including the defect statistic's own averaging cost.
Settings (tolerances, thresholds, probe and gate row counts, horizons, cost weights) were
frozen in A6 before evaluation; the settings are echoed in the output record.

The defect is visible on a real frozen hypothesis, which we think is the clearest way to show
what changed. The ring's true symmetry generator (the 6-cycle), proposed by the model in run
`seed 20261112`:

| screen | violated fraction | max discrepancy | decision |
|---|---|---|---|
| as implemented (all target columns, exact equality) | 0.7458 | 1.95 | rejects the true group |
| as declared (scored target, frozen tolerance) | 0.0000 | 1.11e-16 | accepts |

**Results on identical frozen candidates** (60 ring candidates; `risk after − risk before`,
negative helps; "realised" counts a non-firing candidate as 0; gate seconds per candidate):

| regime | rule | fired | realised | harmful rejected | beneficial missed | gate s |
|---|---|---|---|---|---|---|
| valid ($D_6$) | always | 60/60 | −0.00345 | 0/0 | 0/60 | 0.0000 |
| | defective label | 0/60 | 0.00000 | 0/0 | 60/60 | 0.0015 |
| | **corrected label** | **60/60** | **−0.00345** | 0/0 | 0/60 | **0.0017** |
| | measured defect ($q_1$) | 45/60 | −0.00275 | 0/0 | 15/60 | 0.0755 |
| | random 75% | 45/60 | −0.00254 | 0/0 | 15/60 | 0.0000 |
| mismatched | always | 60/60 | **+0.00266** | 0/58 | 0/2 | 0.0000 |
| | defective label | 0/60 | 0.00000 | 58/58 | 2/2 | 0.0015 |
| | **corrected label** | 0/60 | **0.00000** | **58/58** | 2/2 | **0.0005** |
| | measured defect ($q_1$) | 45/60 | +0.00209 | 15/58 | 0/2 | 0.0189 |
| | random 75% | 45/60 | +0.00208 | 14/58 | 1/2 | 0.0000 |
| $\epsilon=10^{-12}$ | corrected label | 60/60 | −0.00345 | 0/0 | 0/60 | 0.0017 |
| $\epsilon\ge 10^{-9}$ | corrected label | 0/60 | 0.00000 | 0/0 | 60/60 | 0.0017 |

Four things follow, and the first two are reversals of what we wrote before.

1. **The recall bottleneck on a valid group was the bug, not the gate.** The corrected screen
   accepts all 60 candidates and captures all of the available benefit for 0.0017 s. "A
   correctly specified verification policy is a recall bottleneck" is withdrawn.
2. **The safety role the referee asked us to test now exists as a measurement.** Under a
   mismatched group, averaging harms 58 of 60 candidates; the corrected screen rejects all 58 at
   a cost of 0.0005 s, the defect rule rejects 15 and a size-matched random rule 14. Under the
   objective of A6.3 ($J = $ risk $+ w\cdot$(gate $+$ one-off averaging $+$ $H$ per-prediction
   overhead)), the corrected label gate is the best rule in the mismatched regime at every
   $(H,w)$ we examined ($J = 0.000000$ at $H{=}100$, $w{=}10^{-3}$, against $+0.002737$ for
   always-average, $+0.002164$ for the defect rule, $+0.002137$ for random), and is itself
   dominated by unconditional averaging in the valid regime ($-0.003103$ vs $-0.003105$). That
   is the honest shape of the answer to "is a verifier worth it": its value is entirely the
   value of insurance against a wrong supplied group, and on these two families that hazard has
   frequency 0 (graphs: no mismatched group exists) and 1 (ring mismatched).
3. **A strict label gate forfeits benefit under approximate symmetry, and the tolerance is the
   policy.** The corrected gate accepts at $\epsilon=10^{-12}$ and rejects at every larger
   perturbation, while averaging still helps by −0.00345 at all of them. The crossover sits at
   the tolerance, so the tolerance is the decision boundary, not an implementation detail. This
   is a limitation of any exact label test, not of our code, and we now report a tolerance sweep
   over $\{0,10^{-15},10^{-12},10^{-9},10^{-6},10^{-3}\}$ rather than one frozen value.
4. **On `graphs_n6` the corrected gate changes nothing**, because the scored target's
   label-symmetry group is the entire permutation group: every rule fires on every candidate in
   every regime that exists there.

**Corrected-feedback search runs (the second half of the requirement).** We agree that
post-processing frozen candidates cannot recover the trajectories corrected feedback would have
produced. We ran the matched study the referee asked for: `llm-fitness`, `llm-verify` and
`llm-verify-repair` under corrected semantics, both families, 12 paired seeds, budget 32, 200
steps, `max_train` 256 — 72 new runs in `logs/runs_corrected/`, each carrying
`label_mode="corrected"` so they cannot be pooled with the frozen runs by accident. The
`llm-fitness` arm was re-run contemporaneously so the paired comparator is from the same model
state rather than from a month earlier.

<!--A67-->

---

## 2. The diagnostic restated, and measured under the actual proposal distribution

The referee is right that $|L_t|/|S_n|$ is the acceptance probability of a **uniformly sampled
single permutation** under an exact membership test, and that our proposals are generator lists
drawn non-uniformly. We now state the diagnostic as the quantity the referee wrote,
$\Pr_{H\sim Q}[H \le L_t]$, and we estimate it — including for the empirical distribution of our
own LLM proposals — with independent Monte-Carlo draws (400 draws, 256-row probe disjoint from
the gate's rows, so the Wilson interval is defensible here in a way it was not for the fixed
panel).

| $Q$ | ring $\alpha_0$ accept | 95% CI | uniform model | graphs accept | tictactoe $n=9$ accept |
|---|---|---|---|---|---|
| one uniform permutation | 0.0225 | [0.0119, 0.0422] | 0.01667 (exact) | 1.0000 | 0.0000 |
| 2 independent uniform generators | 0.0025 | [0.0004, 0.0140] | 2.78e-4 | 1.0000 | 0.0000 |
| 3 independent uniform generators | 0.0000 | [0.0000, 0.0095] | 4.6e-6 | 1.0000 | 0.0000 |
| **empirical LLM hypotheses** (819) | **0.4700** | [0.4216, 0.5190] | — | 1.0000 | — |

Three points, stated with the limits the referee asked for.

- **The uniform models are not wrong; they are irrelevant to these proposals.** An independent
  check (4000 draws) gives single-generator soundness 0.0179 and two-generator 0.00025, matching
  $|L_t|/|S_n|$ and $(|L_t|/|S_n|)^k$. But the actual proposal distribution accepts at 0.47 —
  21× the uniform single-permutation rate and about 1700× the two-generator model. A diagnostic
  that ignores $Q$ is off by three orders of magnitude on the only $Q$ this paper studies. That
  is now the claim: not "the ratio predicts gate behaviour" but "the ratio is the wrong
  functional, and the right one has to be estimated from the proposals".
- **Cost of obtaining $L_t$, stated instead of assumed.** Exact enumeration costs 0.22 s at
  $n=6$ for the ring (all 720 permutations) and 2.65 s for graphs, and is what lets us *prove*
  $|L_{\alpha_0}| = 12$ and $|L_{\text{connected}}| = 720$. It does not scale: at $n=9$,
  $|S_9| = 362880$, and we do not enumerate. We added a hard enumeration cap (2000 elements) and
  a sampler fallback, and we record the asymmetry it implies — sampling group elements can
  *refute* a symmetry (one violating element suffices) but can never certify one. For the
  $n=9$ board task we use the algebraic anchor instead: the eight symmetries of the $3\times3$
  square, all sound on the probe, giving $|L|/|S_9| = 2.2\times10^{-5}$.
- **The two degenerate ends are both measured, not asserted.** Graphs: accept 1.0 under every
  $Q$, so within the permutation hypothesis domain no predicate of this kind can discriminate.
  Tic-tac-toe $n=9$: accept 0.0 under every $Q$, so the same predicate rejects everything. A
  useful gate needs $Q$ to put mass on both sides of $L_t$; that is the whole content of the
  boundary statement, and we say so rather than presenting it as a contribution.

We also state the assumption the referee named: knowing $L_t$ exactly already solves much of the
discovery problem, which is precisely why we now describe verification's value here as a safety
property of a supplied group rather than as a route to finding one.

---

## 3. The predictor-defect rule: costed, objectivised, and demoted

- **Cost charged properly.** The statistic needs averaged predictions on its own sample, so we
  measure it: 0.0755 s per candidate on the ring against 0.0017 s for the corrected label test
  (44×) and 3.66 s against 1.39 s on graphs. This is in the objective, not in a footnote.
- **A stated decision objective.** $J = $ risk $+ w\cdot$(gate $+$ one-off averaging $+$ $H$
  per-prediction overhead) over $H \in \{1,10,100,1000\}$ and
  $w \in \{0, 10^{-4}, 10^{-3}, 10^{-2}, 10^{-1}, 1\}$, with a domination analysis. The defect
  rule is never the best rule in any regime we examined: in the valid regime always-average and
  both corrected gates dominate it; in the mismatched regime the corrected gates dominate it and
  it is statistically indistinguishable from random 75% selection.
- **Compared with random 75%.** −0.00275 vs −0.00254 in the valid regime — a difference of
  0.00021, which we do not present as a method. In the mismatched regime, +0.00209 vs +0.00208.
- **Threshold frozen, and assessed where it can fail.** $q_1$ is fixed from the development
  candidate pool and then evaluated on invalid groups and approximately symmetric targets, not
  only on the pool that defines it.
- **Wording corrected as instructed.** 79% is now "a descriptive retention fraction". "
  Verifier-free" is gone: the rule measures predictive symmetry and simply omits the label test,
  which we now say in the rule's name.

---

## 4. The mismatched-group control now evaluates the rules it names

The referee is correct that the old R4 row averaged `delta_mismatch` over every candidate with a
defined mismatch and did not apply R2's mask, while R2 fires zero times on the ring. Two fixes:

- that control is renamed **"unconditional mismatch stress test (no mask)"** in the table and
  caption, and is described as what it is — a stress test, not the realised risk of a gated
  rule;
- in `decision_rules2.py` every rule is scored under **its own** firing mask in the mismatched
  regime, and we report per rule: harmful rejected (of 58), beneficial missed (of 2), realised
  paired risk, and cost. The corrected label gate rejects 58/58 and realises 0.00000; the defect
  rule rejects 15/58 and realises +0.00209.

So the safety role of verification is now attributed only where it is measured, and the
frequency at which that role pays for itself is reported as a regime property rather than a
method property.

---

## 5. Sampling units: panel counts are descriptive, and decision inference bootstraps seeds

- **Panel.** Reported as **9 generator sets, of which 6 generate distinct subgroups** on the
  ring and on graphs (5 distinct at $n=9$, where three entries exceed the enumeration cap). Each
  entry, its closure order and its closure digest are listed in
  `research/search/corrected_gate.json`; the duplicate groups are explicit
  (`full_symmetric`, `random_permutations` and `single_transpositions` all generate $S_6$).
  Wilson intervals over panel entries are removed; the counts are descriptive coverage.
- **A defect we found in ourselves while writing this.** `corrected_gate.py` carried its *own*
  copy of the panel whose docstring claimed it was the A5.3 panel. It was not: the reflection
  was `-1-i` instead of `-i`, `rotation_subgroup_c2` was $\rho^4$ (order 3, the same subgroup as
  `rotation_subgroup_c3`) instead of $\rho^3$ (order 2), and `full_symmetric` used different
  generators. The drift changed the number of distinct subgroups — the very quantity this
  section is about. The copy is deleted, the canonical panel is imported, and two tests pin the
  two mappings so they cannot drift again
  (`research/search/test_corrected_gate.py::TestCanonicalPanel`).
- **Decision-rule uncertainty** now bootstraps the **12 paired seeds** (E-A) and reports per-arm
  results; candidate-level counts are no longer treated as independent Bernoulli trials. For the
  ring valid-regime corrected gate the seed-vector interval is [−0.00376, −0.00316].
- **"Wider by construction" is removed** from `crossed_bootstrap_ci`. The observed ordering
  (E-A [0.02998, 0.04210], E-B [0.02610, 0.04597], E-C [0.02366, 0.04828], E-D [0.03134,
  0.04087]) is presented as a sensitivity result with its assumptions, and we note that
  identical means under all four procedures are *expected* in a balanced design, not a finding.

---

## 6. Fresh inputs validate frozen policies, not the firing mechanism

Adopted verbatim in substance. The manuscript and the claim ledger now say that fresh inputs
validate **the risks of the development-frozen policies**, and explicitly that the ring's 0/12
firing "does not replicate the firing-rate mechanism (the deployed evaluator reuses the
development-frozen decision, so it cannot change)". Independent replication of gate behaviour
would need new fitted candidates or a new task, and we say that.

---

## 7. Manuscript reconciliation

- The Discussion is **rewritten**, present-tense, organised around the five things the final
  experiments support. "Precondition" survives only as an explicit negation ("it is not a
  precondition for the repair benefit"); "did not move selected risk" is gone; the
  classical-baseline claim carries its development restriction in the sentence that makes it,
  together with the fact that the same rule fails on matched held-out rows.
- The primary $\eta{=}1$ interval is now **E-A: +0.03605, CI [+0.02998, +0.04210]** in the
  abstract and Discussion, with E-B/E-C/E-D reported as sensitivity.
- **Monte-Carlo versus exact twirling is distinguished**: the deployed-hypothesis groups on
  graphs have 2–12 elements and are averaged exactly; only the declared $S_6$ comparison is a
  24-of-720 Monte-Carlo average, and the exact-projector caveats attach to that one.
- The review-round narrative is **moved to an appendix** (`app:audit`, with a table of what
  changed per round and what was withdrawn, and the artifact that documents each). The main text
  is written once, in the present tense, so the current estimand and claim are identifiable
  without reconstructing the review history.
- `research/CLAIMS.md` is updated to match, including the two rows the referee quoted.

---

## 8. The checker is described as a lint, and a claim-level instrument now exists with measured error rates

- `check_numbers.py` is now documented, in its docstring and in the paper, as a
  **numeric-token lint**: it confirms each manuscript token appears in the generated record at
  its own precision, and it cannot establish claim-level consistency. We no longer describe it
  as validation.
- `research/paper/claim_bind.py` adds the layer the referee specified: each headline value is
  **recomputed from a structured result key** and must appear in the manuscript within a context
  window containing that claim's arm/endpoint/split/contrast tokens; table cells are generated
  from the same records by `compile_results2.py`.
- **The instrument is tested against deliberate mutations** (sign flip, arm swap, split swap,
  order-of-magnitude, endpoint relabel) and reports its own error rates:

| artifact | bindings resolved | testable mutations | detected | rate |
|---|---|---|---|---|
| `research/paper/main.tex` | 22/22 | 87 | 86 | 0.989 |
| `research/CLAIMS.md` (external artifact) | 7/7 | 28 | 27 | 0.964 |

  23 mutations are excluded as **degenerate** — a sign flip or 10× change of an exact zero, which
  leaves the printed token unchanged and is undetectable by any token-based instrument; the
  exclusion is stated in the report rather than folded into the rate. The single escaping
  mutation on the manuscript is an order-of-magnitude change to an integer-valued binding (12 →
  120) where the mutated token legitimately occurs nearby; it is listed by name in
  `research/paper/claim_binding_report.md`.
- The mutation battery also found a real weakness in the instrument itself, which we fixed:
  substring token matching let `12` bind inside `10^{-12}` and `120`. Matching is now
  whole-token with LaTeX scale factors stripped.
- **What it still cannot do**, stated in the paper: it binds values, not prose. A sentence that
  states a correct number with an incorrect direction, or a claim with no number, is outside its
  reach; nor does it cover values absent from its spec. We agree that ordinary software utility
  is not scientific novelty, and the checker is not offered as a contribution.

---

## Novelty: we choose one claim, and state what is missing from it

The referee asked for one substantive novelty claim, independently validated. We choose:

> **A label-preservation verifier's value for analytic repair is a function of two measurable
> quantities — the probability that the supplied group is wrong, and the probability that the
> proposal distribution lands inside the target's label-symmetry group — and not of the
> presence of verification.** Where the first is zero the verifier is pure overhead; where the
> second is 0 or 1 the verifier cannot discriminate at all; and the numerical tolerance, not
> the verifier, decides the outcome under approximate symmetry.

What validates it beyond the original configuration: the same measurement on a second family
where the gate is *provably* vacuous (graphs, $|L| = |S_6| = 720$, exact enumeration); a third
task at $n = 9$ where it is provably non-discriminating in the opposite direction
($|L|/|S_9| = 2.2\times10^{-5}$, algebraic anchor, no enumeration); the corrected-versus-defective
comparison on identical frozen predictors; and matched cost measurements that put the corrected
gate 44× cheaper than the alternative rule it is compared to.

What is **not** established, and we do not claim it:

- a validated repair-decision *method* (the defect rule is a measured comparison on one
  benchmark, indistinguishable from random selection at matched size);
- a predictive diagnostic for unseen task families (we predict $Q$-acceptance only for $Q$'s we
  sampled);
- that the boundary result transfers to task families whose target is only approximately
  symmetric — we have no such family, and this is the experiment we would run next;
- any behavioural benefit of verifier feedback beyond what the new matched runs support.

---

## Status against the five minimum-evidence items

| # | requirement | status | artifact |
|---|---|---|---|
| 1 | fix R4 definition, panel units, checker scope, replication claim, stale Discussion | **done** | `decision_rules2.py`, `corrected_gate.json`, `claim_bind.py`, `CLAIMS.md`, rewritten Discussion + `app:audit` |
| 2 | defective vs corrected vs alternative gates, identical frozen predictors, valid/invalid groups, consistent costs, paired inference | **done** | `research/search/decision_rules2.json` (7 rules × 5 regimes × 120 candidates, seed-vector CIs) |
| 3 | rerun search with corrected verifier, frozen protocol, meaningful threshold | **done** | A6.7 committed before analysis; 72 runs in `logs/runs_corrected/`; `research/search/corrected_search.json` |
| 4 | one substantive novelty claim, validated independently | **narrowed and stated**, with the gap named rather than papered over | §"Novelty" above; `verify_semantics.json`, `corrected_gate.json` |
| 5 | consequence beyond this configuration | **partly**: two further task families bound the gate's discriminating power in opposite directions; no approximately-symmetric family exists in our set | `corrected_gate.json` (`tictactoe_n9`) |

---

## Where we agree with the referee

The present evidence supports a narrow technical report, and we now say so in the paper rather
than in the rebuttal. If the corrected-feedback runs do not clear the prespecified 0.002
threshold, the behavioural conclusion stays "difference not detected", and the paper's
contribution is the boundary/accounting result above plus the audit. We do not think a fourth
rebuttal would change the assessment; the next thing that would change it is a task family with
approximately symmetric targets, which is a new experiment, not more analysis.
