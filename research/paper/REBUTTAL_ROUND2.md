# Second-round rebuttal

**Manuscript:** Executed Verification and Analytic Repair in LLM-Guided Quantum Circuit
Search: What a Controlled Benchmark Does, and Does Not, Show
**Response to:** `research/paper/REVIEW_ROUND2.md` (decision: reject in current form)
**Date:** 2026-11-12
**Authored by:** the authors listed on the manuscript

---

## 0. Position

We accept the framing that correcting the previous manuscript does not by itself create a
new contribution, and we accept that the strongest surviving positive finding — group
averaging improves predictions on invariant tasks, for non-LLM methods too — is confirmation
of established machinery. We have acted on that rather than argued with it:

1. **Every code-level finding in this review was verified in the source before we answered,
   and all six were correct**: the reversed `verdict()` wording, the equality-based
   group-correctness metric, the missing deployed endpoint in `holdout_oneshot._search_run`,
   the cell-level headline inference at `eta > 0`, the `%.3f` Holm printing plus the
   mislabelled identity column, and the `fresh_v3` reproduction path. Nothing here is
   disputed.
2. **One of our own round-1 corrections was wrong and we have retracted it.** The referee
   was right that Meyer et al. discuss invariant re-uploading; we had recorded the opposite.
   Primary-text quotations are now in `research/paper/REFERENCES_AUDIT.md`, and the paper's
   novelty claim shrank accordingly (§9 below).
3. **We added three experiments** (fixed-panel verifier selectivity; a decision-rule
   ablation for repair; a deployed-endpoint holdout on newly reserved inputs), **one
   inference layer** (four estimands for the crossed design), **one new instrument**
   (a manuscript-versus-record number checker), and **one artifact manifest**. All are
   pre-declared in `research/REVISED_PROTOCOL.md` Addendum A5 (committed at 22:32Z, before
   any of the new analyses ran).

The result changes the paper's claim. The claim we now defend is not "verification helps"
and not "verification is a precondition for repair" (that claim is withdrawn, §4). It is a
measured statement about a decision problem the prior literature does not address: given a
symmetry tool you already know how to build, **how much of its benefit does a
label-preservation gate actually let through, and can you predict that before running
anything?** On our benchmark the answers are "none of it, on one family" and "yes — from the
size of the target's label-symmetry group", and we can now quantify both, including where the
gate is provably vacuous and where a verifier-free rule does strictly better.

We agree with the referee that this may still not clear a bar requiring novelty, rigor and
impact together; §9 states what we believe it does establish and what it does not.

---

## 1. Held-out search evaluation did not evaluate the repaired pipeline — **accepted; new one-shot evaluation added**

**Confirmed in source.** `holdout_oneshot._search_run` computed `test_risk` from
`_train.risk(fit, ...)`, recorded `repair_fired`, and set
`test_risk_averaged_diagnostic = None` unconditionally. E-S7 therefore validated the selected
*candidates*, including for the arm named `llm-verify-repair`, and the sealed graph number
0.50674 could not validate the deployed pipeline. The abstract's emphasis on deployed
averaging made this the most consequential gap in the paper.

**What we did.**

* E-S7 is relabelled everywhere as a **candidate endpoint**, including in the table caption,
  and the paper now says in the generated summary that the deployed predictor is measured
  elsewhere.
* A new module, `research/holdout_deployed.py` (Addendum A5.5), measures per frozen run:
  `test_risk_candidate`, `test_risk_deployed` (the candidate averaged over the group its
  **development-frozen** repair decision selected — `best.repair.repaired` plus the
  candidate's hypothesis generators), and `test_risk_declared_twirl` (the same tool with the
  declared group, applied to **every** arm, including `random` and `mutation-ea`).
* All endpoints are scored on one fixed, paired row subsample (1024 rows, seed 5150, recorded
  per family) so the paired comparisons are on identical rows.
* **The development self-check runs before any held-out array is opened** (the Addendum A4
  lesson): all 120 refits must reproduce their logged development risk, or the module aborts
  without reading. Dry-run gate: **120/120 exact, max |dev diff| 1.73e-18**.
* Baselines are fitted on development **training** rows and scored on **the same rows as the
  arms**: edge-count rule (threshold fitted on train only), constructive equivariant block
  (search protocol's per-fit budget, with the per-fit/total distinction stated), best
  constant, and the oracle — labelled a **reference value, not a learned baseline**, because
  it is the function the synthetic target is.

**A constraint we discovered and did not paper over.** A fresh graphs holdout is
*impossible* on this benchmark: `research/datasets/generate_holdout_v5.py` enumerated all
2^15 labeled 6-vertex graphs and found **0 isomorphism classes** not already used by
development plus holdouts v1/v2. So:

* `ring_n6` — genuinely fresh inputs (v5, seed 20261205, dihedral-orbit disjoint from
  development and v1–v4), first read, digests recorded before/after.
* `graphs_n6` — the v1 sealed split, **second read, labelled post hoc in the output JSON, the
  manifest and the paper**, because the alternative was to claim a fresh comparison that the
  benchmark cannot supply. The exhausted-isomorphism-class fact is itself reported as a
  benchmark-design limitation.

**Result** (gate first: 120/120 refits exact, max |dev diff| 1.73e-18; sealed digests
unchanged; access record `research/HOLDOUT_DEPLOYED_ACCESS.json`):

| family | arm | candidate | deployed | declared-group twirl | repair fired |
|---|---|---|---|---|---|
| graphs | random | 0.50548 | 0.50548 | **0.40915** | 0/12 |
| graphs | mutation-ea | 0.50895 | 0.50895 | 0.42886 | 0/12 |
| graphs | llm-fitness | 0.54472 | 0.54472 | 0.47449 | 0/12 |
| graphs | llm-verify | 0.50941 | 0.50941 | 0.43511 | 0/12 |
| graphs | llm-verify-repair | 0.52913 | **0.50067** | 0.44353 | 7/12 |
| ring | random | 0.01036 | 0.01036 | **0.00578** | 0/12 |
| ring | mutation-ea | 0.01052 | 0.01052 | 0.00592 | 0/12 |
| ring | llm-fitness | 0.00648 | 0.00648 | **0.00311** | 0/12 |
| ring | llm-verify | 0.00712 | 0.00712 | 0.00348 | 0/12 |
| ring | llm-verify-repair | 0.00676 | 0.00676 | 0.00319 | 0/12 |

* The repair step on the endpoint the paper emphasises: **−0.02846, CI [−0.04704, −0.01190]**,
  7/12 runs (graphs). Everywhere else deployed equals candidate exactly.
* On the **fresh** ring inputs the deployed gate fires on **0/12** runs, so deployed and
  candidate coincide for every arm there — an independent replication of the 0/60 firing rate
  of §4, on data no pipeline stage had seen.
* The declared-group twirl helps every arm on both families (graphs −0.070 to −0.096, ring
  −0.0034 to −0.0046, all CIs excluding 0), and `random` + twirl (0.40915) beats every arm's
  deployed risk (0.50067–0.54472).
* Matched-row baselines: on fresh ring inputs the constructive equivariant block reaches
  **0.00026**, 25× below the best arm's candidate and 12× below the best arm's own twirl.

**And one of our own claims fell out of it.** The edge-count rule reaches development risk
0.351 against the arms' 0.538–0.566, and the previous manuscript said it "beats every arm".
On matched held-out rows it reaches 0.57812 against the arms' 0.50067–0.54472 — it does not.
The best-constant reference moves from 0.65667 (development validation) to 0.58968 (sealed),
so the two splits differ in label composition and their risk levels were never comparable.
The referee's point 7 is not merely a wording issue: fixing it reversed a headline baseline
claim of ours, and the paper now states the split-scoped version.

---

## 2. Valid subgroup hypotheses are not false accepts — **accepted; metric replaced, numbers re-reported**

**Confirmed.** `dev_analysis.py` incremented `wrong_group_but_label_preserving` for every
accepted hypothesis whose closure was not *equal* to the declared group. On an
S6-invariant target a proper subgroup is a correct answer for a soundness test.

**Replacement taxonomy (A5.2), with the label-symmetry group measured rather than assumed.**
For each target we tested all `n! = 720` permutations on an independent probe panel (512
development rows excluding the 64 the gate reads, seed 777) to obtain `L_t`, then classified
each hypothesis as `exact_declared`, `valid_proper_subgroup`, `valid_supergroup`,
`sound_noncomparable` (a fifth case our first implementation got wrong and which a unit test
now pins), or `invalid`. False acceptance is reported **only** for `invalid`.

| family / target | exact declared | valid proper subgroup | invalid | gate accepted | false accepts among accepted |
|---|---|---|---|---|---|
| graphs / connected | 10 | 289 | **0** | 144 | **0** (CI [0.000, 0.026]) |
| ring / alpha_0 | 0 | 120 | 72 | 7 | **0** (CI [0.000, 0.354]) |

The measured quantity that makes this interpretable is `|L_t| / |S_n|`, which is computable
**before any model runs**:

| family | target | `|L_t|` | `|L_t|/|S_n|` | equals full symmetric |
|---|---|---|---|---|
| graphs | connected | 720 | 1.0000 | **yes** |
| ring | alpha_0 | 12 | 0.0167 | no |
| ring | alpha_0.5 | 2 | 0.0028 | no |
| ring | *conjunction the implemented gate checks* | 2 | 0.0028 | no |

On graphs the label gate is **vacuous by construction** — connectedness is invariant under
every vertex relabelling, so no permutation hypothesis can fail it, and the 144/144
acceptances carry no information about proposal quality. The abstract no longer calls those
289 hypotheses "wrong-group proposals"; it states the corrected reading, including the
vacuity.

**On the objective question the referee asked:** the proposal prompt asks for a symmetry under
which labels are preserved, *not* for the maximal one. We now say which objective each number
scores, and we report maximal-group recovery separately (10/299 on graphs, 0/192 on ring) as
a property of the *proposals*, never as a verifier error rate. We also state that a
finite-sample label test is a screen, not a universal soundness certificate.

---

## 3. The selectivity comparison confounded target with task and proposal distribution — **accepted; replaced by a fixed-panel test**

The referee is right that comparing 299/299 (graphs) with 8/348 (breaking ring) changes input
domain, target, proposal distribution and search trajectory simultaneously. The replacement
(A5.3) holds inputs fixed and varies only the target, on a panel fixed in advance: identity,
rotation, reflection, the declared dihedral group, its `C3` and `C2` subgroups, the full
symmetric group, 20 random permutations, all 15 single transpositions; truth is determined by
recomputing labels for every closure element on the probe.

| target | gate variant | sensitivity | false-accept |
|---|---|---|---|
| alpha_0 | implemented (all target columns, tolerance 0) | 1/6 = 0.167 [0.030, 0.564] | 0/3 [0.000, 0.561] |
| alpha_0 | scored target only, tolerance 0 | 1/6 = 0.167 [0.030, 0.564] | 0/3 [0.000, 0.561] |
| alpha_0 | scored target only, tolerance 1e-9 | **6/6 = 1.000** [0.610, 1.000] | 0/3 [0.000, 0.561] |
| alpha_1 | implemented | 1/2 = 0.500 [0.095, 0.905] | 0/7 [0.000, 0.354] |
| connected | implemented | 9/9 = 1.000 [0.701, 1.000] | **0/0 — no violator exists** |

This isolates **two separable causes** of the sensitivity loss, neither of which is group
theory: (i) the implemented gate tests *every* target column in the dataset, so on the ring it
demands symmetry of targets that are deliberately not symmetric — its acceptance set is 2/720
where the scored target admits 12/720; and (ii) a tolerance of exactly 0 applied to a
continuous target — the declared rotation has worst violated fraction 0.0 at 1e-9 yet records
a violated fraction of 0.53125 (34 of 64 gate rows) at tolerance 0 and is rejected. Fixing
both takes panel sensitivity from 1/6 to 6/6 with no false accepts.

Search-generated hypotheses are analysed separately as a behavioural outcome (§2 table):
0 false accepts, and **95 of 95** rejected ring hypotheses were sound for the scored target
(CI [0.961, 1.000]).

**We also accept the referee's last sentence and have removed the framing.** Absence of D6
recovery on a target that is not D6-invariant is not a failure; recovering D6 there would be
the wrong scientific answer. The breaking-target experiment now reports statuses against the
measured `L_t` and states that its pre-declared prediction was neither confirmed nor refuted
at n = 12.

---

## 4. "Verification is a precondition for repair" was unsupported — **accepted; claim withdrawn and replaced by a measurement**

The sentence is gone. The referee is also right on the mechanism: with a known valid group,
averaging can be applied directly, and channel equivariance of a circuit block does not
imply predictor invariance because a readout can break it.

We did not stop at rewording. A5.4 turns "is a verifier needed?" into a decision problem
scored on identical fitted predictors, and reports five rules: always-average; label gate;
the **deployed** gate (label test *and* channel residual above the harness floor of 1e-6 — we
model the deployed semantics exactly, having read the harness constant); a verifier-free
predictor-defect gate at three development thresholds; and a mismatched-group negative
control.

| family | rule | fired | realised mean risk change | if always applied | precision | missed beneficial |
|---|---|---|---|---|---|---|
| graphs | R0 always | 60/60 | −0.08705 | −0.08705 | 60/60 | 0 |
| graphs | R1 label gate | 60/60 | −0.08705 | −0.08705 | 60/60 | 0 |
| graphs | R2 deployed gate | 60/60 | −0.08705 | −0.08705 | 60/60 | 0 |
| graphs | R3 defect gate (q1) | 45/60 | −0.07544 | −0.08705 | 45/45 | 15 |
| graphs | R4 mismatched group | — | *undefined: no mismatched group exists* | | | |
| ring | R0 always | 60/60 | −0.00345 | −0.00345 | 60/60 | 0 |
| ring | R1 label gate | **0/60** | **0.00000** | −0.00345 | 0/0 | 60 |
| ring | R2 deployed gate | **0/60** | **0.00000** | −0.00345 | 0/0 | 60 |
| ring | R3 defect gate (q1) | 45/60 | −0.00274 | −0.00345 | 45/45 | 15 |
| ring | R4 mismatched group | 60 | **+0.00399** | — | — | — |

Four findings, none of which we had before:

1. Averaging over the supplied group **never harmed a single one of the 120 candidates**, so
   on these targets unconditional averaging dominates and the verifier is not a precondition.
2. The implemented gate **forfeits 100% of the available repair benefit on the ring**
   (realised 0.00000 against −0.00345). That is the operational price of the sensitivity loss
   in §3, and it is the kind of number a practitioner can use.
3. A **verifier-free** gate on the predictor's own measured non-invariance recovers 79% of
   the benefit (−0.00274) at precision 45/45 with zero candidates harmed.
4. The **negative control locates where verification would matter**: averaging over a
   mismatched group costs +0.00399, so a fire-at-blind rule is unsafe precisely on targets
   whose symmetry differs from the supplied group — the regime our own breaking-target
   experiment creates.

Two mechanical facts add design value: the channel condition is satisfied by 60/60 candidates
in both families, so it contributes **no discrimination at all**; and on graphs the label test
costs 0.45 s while the averaging it gates costs 12.5 s, so the filter is 3.6% of the work it
is meant to ration and it filters nothing.

We do **not** claim R3 is optimal, nor that it generalises: it is one statistic, one dataset
per family, one budget. We claim that on this benchmark the gate is a recall bottleneck rather
than a safety device, and that this is measurable.

---

## 5. Crossed dependence in the headline repair inference — **accepted; estimand-appropriate analysis promoted**

The referee is right that resampling 192 cells that reuse both directions and seeds is not a
justified interval, and that a direction-only cluster bootstrap does not fix it either.
A5.1 now reports four procedures for every `eta > 0` contrast, with E-A as the headline:

| estimand | procedure | repaired − control_dup at eta = 1 |
|---|---|---|
| **E-A (primary)** | average the 8 frozen directions within each seed, cluster-bootstrap the 24 seed vectors | **+0.03605 [+0.02998, +0.04210]** |
| E-B | cluster-bootstrap the 8 direction vectors | +0.03605 [+0.02610, +0.04597] |
| E-C | resample both clusters (seeds outside, directions inside) | +0.03605 [+0.02366, +0.04828] |
| E-D (legacy) | cell-level resampling of 192 cells | +0.03605 [+0.03134, +0.04087] |

The mean is identical across procedures because the design is balanced (each seed has all 8
directions), which is worth stating because it means the correction changes *uncertainty*, not
effect size. The widest, most conservative interval (E-C) still excludes 0, so the eta = 1
cost survives every procedure we can justify; the referee's expectation that "the large
eta-one mean effect may survive" is borne out. Direction-specific effects are now printed
(eta = 1: +0.016 to +0.054 across the eight directions), because the spread is itself
informative and pooling hid it.

The same treatment is applied to the four-direction / eight-seed fresh-input analysis (units =
8 seeds for E-A). And the paper now states, in the generated summary and in the limitations,
that **all of these intervals condition on one dataset and one task family**: they do not
quantify variation over newly sampled training datasets or task families. We removed wording
that implied otherwise.

---

## 6. Automated reporting produced incorrect or contradictory conclusions — **accepted; five bugs fixed, and a new instrument found two more gaps**

All five items were real:

* **Direction bug.** `verdict()` returned "b worse" for a wholly positive a-minus-b interval.
  For risk, positive means **a is worse**. Fixed; the old unit test only exercised the
  negative side, which is how it survived. New tests pin both directions, the
  `lower_is_better` flip, and the adjusted-p downgrade.
* **Verdicts now enforce the inferential policy.** `verdict()` takes the adjusted p-value and
  the metric direction: a raw CI that excludes 0 with an adjusted p above alpha prints as
  "difference not detected after multiplicity adjustment (raw CI excludes 0 but is not a
  protocol verdict)". Equivalence wording is emitted only from the prespecified margin test.
  The v1 eta-zero rows can no longer print "a better" while the adjusted test says otherwise.
* **p floors.** `%.3f` → `%.3g`, so Holm values print as 2.5e-04 rather than 0.000. The
  remaining `0.000` entries in the summary are invalid-*rate* columns, where zero is a real
  measurement.
* **Identity columns separated.** The table previously labelled the invariant-only residual
  `identity_gap_max` as "identity gap". Both are now printed under their own names:
  `no-cross-term gap` (≈ 2·|cross|, nonzero by construction for eta > 0) and
  `full A3 gap` (the corrected identity, at roundoff: max 3.7e-16 over all 2340 fits). The
  rebuttal's roundoff claim refers to the latter, and the tables now say so.
* **Equality wording removed.** "buys nothing", "helps equally" and "did not move" are gone
  from the abstract, the baseline section and the fresh-input discussion; each site now
  states the estimate, the interval, and that failure to detect is not equality.

**The referee's closing line — "Automated compilation alone is not validation" — was the most
useful sentence in the report.** We built the missing check (`research/paper/check_numbers.py`)
that requires every manuscript number of ≥4 significant digits to match a generated value at
its own precision, and it immediately found two more gaps of exactly this class:

* the E-S7 arm-versus-random contrasts in the paper had **no generated counterpart at all**
  (the record contained 4 contrasts per family, only one of which involved `random`). We
  regenerated the full matrix from the stored per-run risks
  (`research/holdout_search_contrasts.py`, no new sealed read). The numbers turned out to be
  correct, but they had been uncheckable;
* the floor-excess column was being computed by hand in the manuscript; it is now produced by
  the analysis.

The checker currently reports: *generated numbers 801, manuscript numbers 381, **OK***. It
runs as part of the reproduction list, so a future stale number fails the build.

---

## 7. Baseline conclusions mixed splits and overstated what optimisation establishes — **accepted**

* **Matched test-split baselines.** The A5.5 evaluation scores the edge-count rule, the
  constructive equivariant block, the best constant and the oracle on the same rows as the
  arms, each fitted on training rows only. The E-S7 caption no longer compares sealed-test arm
  risk with a development-split baseline risk; the development number stays in the development
  section, labelled as such. This change reversed one of our own claims (see the end of §1): the
  edge-count rule's advantage exists on development validation and not on the sealed split.
* **Expressivity claim removed.** "Cannot express connectedness" is replaced with the
  empirical statement: at the search protocol's per-fit budget this exactly equivariant
  three-parameter block did not reach the arms' risk (0.667 vs 0.538–0.566), and no proof or
  exhaustive representational argument is offered.
* **Per-fit versus total budget** is stated explicitly wherever the constructive baseline is
  compared with a search arm: the arms also spend proposals, and we do not claim total-budget
  equality.
* **Oracle demoted.** It is reported as a reference value with the reason, not as a baseline a
  learned model should beat.
* **Monte-Carlo twirling is now disclosed where it is used, with its cost.** The declared
  group of `graphs_n6` is S6 (720 elements), so **every** graphs twirl in this paper is a
  24-element Monte-Carlo average: MC share 1.00 on graphs, 0.00 on the ring (|D6| = 12,
  enumerated exactly). The paper states that exact-projector guarantees (equivariance of the
  averaged predictor, the projection identity) do not transfer to the 24-element average, and
  reports the measured cost, 12.5 s per candidate on graphs against 0.18 s on the ring.

---

## 8. Provenance and reproduction need one consistent final manifest — **accepted; manifest generated**

`research/MANIFEST.md` is generated by `research/build_manifest.py` and maps each manuscript
table to: analysis code with the last commit that touched it, result file with a truncated
sha256 and size, endpoint, split/seed, protocol amendment, and status — including explicit
**invalid** and **superseded** statuses (the first E-R4 table is marked `INVALID for eta>0`;
E-S7 is marked `candidate endpoint only`; the v1 repair table is marked `superseded`). A split
consumption ledger lists v1–v5 and what each was used for.

* **The reproduction path is now consistent.** The manuscript's command block named
  `fresh_v3`; it now names `fresh_v4` for E-R4′ and the A5.5 job for the deployed endpoint,
  and every one-shot command refuses a split recorded as consumed, so copying the block cannot
  cause a second look.
* **The limits of the safeguards are stated, not oversold.** The paper now has a paragraph
  saying that a digest recorded before and after a read shows the bytes did not change, does
  **not** show the file was never opened before, and that `0444` permissions plus a path check
  are procedural guards against our own drift rather than access isolation. Git is described
  as a documented chronology, explicitly not a certified preregistration service.
* We keep the model-checkpoint limitation as disclosed, and agree that bit-level LLM replay is
  not a publication prerequisite given that raw outputs and transformations are reproducible.

---

## 9. Novelty: what we now claim, and what we do not

We are not going to argue the novelty judgment; we will state precisely what the evidence now
supports, including where it shrank.

**Removed by our own re-check.** The referee asked us to revisit Meyer et al. against the
primary text. We had written in our round-1 audit that the "invariant re-uploading"
attribution was unsupported by that source. **That was wrong**, and reading the accepted
manuscript (APS open full text, doi:10.1103/PRXQuantum.4.010328) shows it plainly: the paper
constructs "variational quantum data re-uploading models that make invariant predictions",
defines equivariant embeddings `U(V_s[x]) = U_s U(x) U_s†`, and gives the twirling formula
`T_U[X] = |S|^{-1} Σ_s U_s X U_s†` as a projector onto the commutant, applied to gates and
whole ansätze. Our inference-time average is the output-side specialisation of their
Proposition 2; our constructive equivariant baseline is an instance of their blueprint. Those
are not contributions of ours and the related-work section now says so, with the quotations
recorded in the audit file. The failure mode is worth naming: we verified the bibliographic
*record* and then reasoned about the *content* from memory.

**Also not ours, and now stated as prior art:** the projection identity; the general fact that
a validity test cannot separate a group from its valid subgroups (a structural property of
such tests, not a discovered limitation of LLM reasoning); the averaging benefit for invariant
targets.

**What we believe is new and is measured here:**

1. **A pre-registration diagnostic for verifier design.** `|L_t| / |hypothesis space|` — the
   fraction of the hypothesis space whose labels the target preserves — is computable before
   any model runs and determines whether a label-preservation verifier can carry information.
   On our two families it is 1.0000 (vacuous) and 0.0167 (severely constraining), and both
   predictions were confirmed by the observed gate behaviour. We know of no statement of this
   diagnostic in the symmetry-learning literature we read; if it exists, we will cite it.
2. **A decision-level accounting of repair gating** (§4): realised risk change, precision,
   recall, harm, missed beneficial repairs, and the cost of the gate relative to the repair,
   with a mismatched-group negative control. The headline — a deployed soundness gate that
   forfeits 100% of the available benefit on one family while a verifier-free defect gate
   recovers 79% at zero harm — is a result about *when to repair*, which the literature on
   *how to build* equivariant models does not address.
3. **The four-estimand treatment of a crossed repair design**, with the finding that the
   correction changes uncertainty rather than effect size, and that the most conservative
   crossed interval still excludes zero.
4. **A reproducible audit instrument**: a checker that fails the build when a manuscript
   number has no generated counterpart, which found two such numbers in our own paper.

**What we do not claim:** a new verification method that beats the state of the art (R3 is one
statistic on one dataset per family); any quantum advantage; any LLM advantage over
constructive or classical baselines on these tasks; identification of maximal symmetry groups;
or that the negative results hold beyond these two families, one model, and one short budget.

**On the three paths the referee offered.** Path 2 (a decisive negative study) is not what we
have: exposure is sparse and margins wide, and we say so. Path 3 (a field-level audit with a
reusable remedy) is partially served by the number checker and the `|L_t|` diagnostic, but our
audit is of one in-house study, and we have removed any implication that it indicts an
influential published claim. Path 1 (a new verification/repair decision method) is the one we
advanced, and only as far as a measured decision rule plus the diagnostic and the negative
control — not a validated method across unseen task families, which would need the task-family
variation we do not have.

We therefore agree with the referee's own closing assessment: **the present evidence supports
a narrow technical report, and that is how we have rewritten the paper.** Its contribution
table lists what each result does and does not establish; its abstract states failure to
detect where that is what we measured; and its claims ledger
(`research/CLAIMS.md`) records every claim with the interval and the ceiling on its
interpretation. If the venue's bar requires a positive, generalisable methodological result,
we do not believe this submission meets it, and we would rather say that than inflate it.

---

## 10. New artifacts, tests and jobs

| artifact | what it adds |
|---|---|
| `research/REVISED_PROTOCOL.md` Addendum A5 | pre-declaration (22:32Z) of A5.1 estimands, A5.2 taxonomy, A5.3 panel, A5.4 decision rules, A5.5 deployed endpoint, A5.6 reporting policy |
| `research/core/paired.py` | direction-correct `verdict`, adjusted-p enforcement, `seed_vector_bootstrap_ci`, `crossed_bootstrap_ci`, `wilson_ci` (+ 5 new unit tests) |
| `research/search/verify_semantics.py` (+ 9 unit tests) | label-symmetry groups, taxonomy, fixed panel, gate cross-tabulation |
| `research/search/decision_rules.py` | R0–R4 decision ablation with cost measurement |
| `research/holdout_deployed.py` | candidate / deployed / declared-twirl endpoints, matched baselines, gate-before-read |
| `research/datasets/generate_holdout_v5.py` | fresh ring inputs; documents that graphs has 0 unseen isomorphism classes |
| `research/holdout_search_contrasts.py` | regenerates the E-S7 vs-random matrix from the stored record |
| `research/paper/check_numbers.py` | manuscript-vs-record number check (currently OK: 801 generated, 381 manuscript) |
| `research/build_manifest.py` → `research/MANIFEST.md` | artifact manifest and split-consumption ledger |

Test suites: `research/core` (20), `research/search` (including the two new files),
`research/experiments/repair` — all green. Jobs: `33033493`/`33034704`/`33039560`
(decision rules, final `33039560`), `33039574`/`33040509`/`33041014`/`33041668` (deployed dry
runs, final gate 120/120 exact), `33042529` (aborted at a `Path`-vs-`hashlib` digest bug *before*
any sealed array was opened, recorded in the module docstring), `33044945` (A5.5 one-shot, result
in `research/HOLDOUT_DEPLOYED.json`, access in `research/HOLDOUT_DEPLOYED_ACCESS.json`, and
appended to the shared ledger `research/HOLDOUT_ACCESS.json` with the graphs second read
explicitly authorised and its reason recorded).
