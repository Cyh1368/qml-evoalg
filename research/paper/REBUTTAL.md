# Author rebuttal to the referee report (11 November 2026)

**Manuscript:** *Verified Symmetry Hypotheses and Causal Repair in LLM-Guided Quantum
Circuit Search* → revised as *Executable Verification and Analytic Repair in LLM-Guided
Quantum Circuit Search: What a Controlled Benchmark Does, and Does Not, Show*
(`research/paper/main.tex`).

We thank the referee. Every substantive point was checked against the code, the stored
run records, and primary bibliographic sources **before** we responded, and the referee was
right on all of them: the duplicated units are real, the omitted endpoint is real, the
bibliography errors are real, and two further provenance defects that the report did not
name turned up while we were checking it. Nothing below is a prose-only fix; each item
names the artefact, the command, and where the corrected number now appears. Where a fix
changed the conclusion, the conclusion changed.

Two conventions used throughout:

* **Frozen protocol.** `research/REVISED_PROTOCOL.md`, committed at
  `ecd1be7246f6ee74e8605b38ddaafa654dd7c6b7`, 2026-11-11 **16:20:02Z**, before the revised
  experiments were submitted (17:10Z, 17:21Z, 17:37Z). It defines endpoint vocabulary,
  replication units, estimands E-R1…E-R4 / E-S1…E-S7, the inference procedure, prespecified
  equivalence margins, and the one-shot holdout policy.
* **Auto-compiled numbers.** `python3 -m research.compile_results2` regenerates
  `research/results_summary2.md` from the result JSONs; no number in the revised manuscript
  is hand-typed from a different source.

---

## 1. Repair experiment: replication unit and uncertainty — **accepted; the headline claim did not survive**

**Verified first-hand.** `build_targets` changes only the breaking direction and, at
`eta = 0`, the target is `h` for every teacher. Recomputing from the stored record: each
arm contains 24 `eta = 0` rows but **8** distinct `(opt_seed, dev_risk)` pairs — three
copies of eight experiments.

**What we did.**
1. New inference module `research/core/paired.py` with `collapse_units()`, which drops exact
   repeats of a unit and *raises* if a unit key ever appears with different values. All
   repair inference goes through it, and every table now prints `rows` **and** `units`.
2. Recomputed the existing record (`research/experiments/repair/repair_v1_reanalysis.json`,
   command in the appendix):

   | contrast (η=0) | rows | units | mean diff | 95% CI | p (shifted boot) | p (sign-flip) |
   |---|---|---|---|---|---|---|
   | repaired − control | 24 | **8** | −0.00093 | [−0.00217, −0.00002] | 0.083 | 0.125 |
   | repaired − original | 24 | **8** | −0.00201 | [−0.00394, −0.00021] | 0.034 | 0.125 |
   | control − original | 24 | **8** | −0.00107 | [−0.00277, +0.00041] | 0.191 | 0.320 |

   All eight differences are published in the JSON. **The revised conclusion is that this
   record does not support the η=0 benefit**: the interval is on the edge of excluding zero
   and neither calibrated p-value is small. We say so in the abstract.
3. New experiment WP-REPAIR-2 (`research/experiments/repair/repair_experiment2.py`, job
   `32982225`) with the unit definition enforced by design: **8** breaking directions ×
   **24** optimiser seeds, so η=0 has 24 genuine units and η>0 has 192; η=0 is emitted once
   (direction-free) rather than three times. For η>0 we report every direction separately
   and add a cluster bootstrap over directions with the caveat that 8 clusters support only
   a within-benchmark statement.
4. The paper's language now distinguishes "not detected" from "no effect" everywhere
   (`paired.verdict()` returns only sanctioned wordings).

The referee's observation that we criticised pseudoreplication in the prior study while
introducing it here is fair, and we now say that explicitly in §5 of the revision.

## 2. The search contrast did not evaluate the repaired predictor — **accepted; this reversed one of our findings**

**Verified first-hand.** In `harness.py`, the averaged risk was stored as
`dev_risk_repaired_diagnostic` while the official endpoint was `best_risk = best['dev_risk']`,
and `analyze.py` read only the latter. The referee is right that the reported contrast could
not speak to the repair.

**What we did.** `research/search/analyze2.py` defines the estimands separately:
* **E-S1** — paired before/after averaging on the *same frozen candidate*:
  **−0.04862, CI [−0.07083, −0.02839], shifted-bootstrap p < 10⁻⁴, sign-flip p = 0.0156,
  7 of 12 runs** on `graphs_n6`; on `ring_n6` **4 repairs attempted, 0 fired → no data**,
  which the first version did not report either.
* **E-S2** — deployed-pipeline endpoint: `verify-repair − verify` moves from **+0.0009**
  (candidate endpoint, as first reported) to **−0.02744, CI [−0.05401, +0.00519]** (deployed).
* **Coverage** is printed next to both (eligible / attempted / fired), and E-S1 is labelled
  coverage-conditional, not intention-to-treat.

Consequently the sentence "an averaging benefit did not survive confirmation" is **removed**:
the benefit was never measured. We also added **E-S5b**: applying the same declared-group
averaging to *every* arm's selected predictor helps all arms (graphs −0.0639 to −0.1114;
ring −0.0031 to −0.0039; all CIs exclude 0), so the gain belongs to the analytic tool, not
to the LLM. That is now the paper's central, honestly-scoped finding.

## 3. Held-out language for development results — **accepted; wording removed, one-shot evaluation added**

We agree that a split used by candidate selection, by the feedback loop and by the verifier
is not an independent test set. The revision (a) labels every endpoint
**development / sealed test / fresh holdout** (§6 and Table captions), (b) states that the
development split drives all adaptive decisions, and (c) removes every confirmatory use of
"held-out", "test" and "generalisation" for development numbers.

We then ran the frozen one-shot evaluation (`research/holdout_oneshot.py`, job `32984980`),
which records sha256 of each sealed file before and after and writes an access log
(`research/HOLDOUT_ACCESS.json`): E-R4 (repair arms on untouched ring data, both the v1
sealed split and a **fresh** holdout) and E-S7 (all 120 dev-selected candidates refitted
deterministically and scored on the sealed split). Results are in §7.4 of the revision.
Access controls are documented as an access contract, not a directory name: `research/search`
refuses any argument containing "locked" (`LOCKED_FORBIDDEN_IN`), and the one-shot script is
outside that package by design.

## 4. "Equal gate counts isolate symmetry from capacity" — **accepted; claim withdrawn and instrumented**

The referee is correct on both mechanisms. We verified numerically that
`control_dup` = `CRZ_ij(b)²` = `CRZ_ij(2b)` (agreement to 10⁻¹⁴), i.e. the control is the
*original* interaction at double angle, and that with identical numerical initialisations
its initial **operator** differs from the original's (initial-operator distance 1.37).

Changes: (i) the phrases "confound-free", "differ only in symmetry" and "attributable to
symmetry rather than capacity" are gone, replaced by "the effect of these particular circuit
interventions under this training procedure"; (ii) we added **`control_matched`**, whose
initial `b` is halved so its initial operator is *identical* to the original's (verified to
10⁻¹², unit-tested), and **`control_rand`**, a second asymmetric gate-count-matched rule;
(iii) optimiser-budget sensitivity at 200/600/1800 steps; (iv) the function-space estimand
**E-R1** evaluates `f` and its exact Reynolds projection on the orbit-completed distribution
with declared uniform weights, and we state that this answers a different question from
retraining different families. Appendix A gives the CRZ algebra as the analytic argument for
the repaired family (the measured residual is a check, not the proof).

## 5. "Repair helps iff the target is invariant" — **accepted; withdrawn**

The revised statement is: *the mean differences have opposite signs at the tested mismatch
levels* — a robust cost at η=1 (+0.045, CI [+0.032, +0.058]) and a benefit at η=0 that our
units do not establish (§1 above). We also separate Proposition 1 (an exact identity for a
fixed predictor under an invariant input measure) from the empirical comparison of separately
optimised architectures, and we no longer use the former as a theorem about the latter.

## 6. Invariant-risk floor — **accepted; three quantities separated, and one of the referee's numbers traced to our own presentation error**

We now (i) state the measure: μ = Unif[−1,1]⁶ with the site-permutation action, a product of
identical marginals, hence invariant, and prove the invariance we use; (ii) give the
decomposition `R(f) = R(Pf) + E[(f−Pf)²] + 2E[(f−Pf)(y−ȳ)]`, whose cross term vanishes only
for an invariant target — measured per arm, and reported; (iii) separate the **population**
floor, its **Monte-Carlo** estimate on representatives, and the **exact finite-orbit** floor
on the orbit-completed set (uniform weights, declared), and we agree that one representative
per orbit admits invariant interpolants, so no non-vacuous empirical floor exists on
representatives alone.

On the specific arithmetic: the 0.866 the referee used is a *per-direction* floor (the first
teacher's). Recomputed per unit, the floor ranges 0.866–1.059 across directions (mean 0.948),
and the repaired arm's excess above the floor is **+0.0228** (range −0.010 to +0.052), while
the asymmetric arms sit **below** the floor (−0.020, −0.022) because the floor constrains
only invariant predictors. "Pinned near the floor" is therefore replaced by these numbers
plus the approximation/optimisation error (excess risk with intervals, and the budget-
sensitivity runs). The root cause — quoting one direction's floor as *the* floor — was our
error and is listed as such in the revision's Table 3.

## 7. Inference procedure and null language — **accepted; procedures replaced**

* Side-counting bootstrap p-values are gone. Every contrast now carries a **null-centred
  (shifted) bootstrap** p and an **exact sign-flip** p for n ≤ 12 (randomised, 2×10⁵ flips,
  otherwise), with the exchangeability/symmetry assumption stated wherever used.
* Simulated p-values are never 0: `paired.py` returns `(count+1)/(n+1)` and a `p_floor`, and
  tables print "at the resolution floor" instead of 0.000.
* Multiplicity families are declared in the protocol (A: the two primaries; B/C: repair
  contrasts at η=0/η=1; D: secondary search contrasts per family **and per endpoint**; E: the
  new breaking-target study) and Holm is applied within a family only. Raw CIs are labelled
  unadjusted.
* Every primary carries a leave-one-unit-out range.
* "Clean null", "unchanged" and "does not improve" are removed; CIs containing 0 are reported
  as "difference not detected". We do **not** claim equivalence: the prespecified margin is
  δ = 0.05·Var_dev(y) (graphs 0.03274, ring 0.00097) and neither primary interval lies inside
  it.

## 8. Prose/table contradictions — **accepted; both sides corrected**

The η=0 control-minus-original interval did exclude zero in the old table; with correct units
it is [−0.00277, +0.00041], and the accompanying text now says "not detected", not
"equivalent". For the reliability claim, the revision adds paired reliability endpoints
computed from the frozen record rather than asserted: per-arm invalid-proposal rates
(0.55% overall: 8 of 1448 proposals), hypothesis-present rates, verifier false-accept rates
against the true group (§9 below), and a nonconstant-output check on all 120 deployed
predictors (all nonconstant; minimum prediction std 0.089). The unsupported sentence
"implementation-reliability result" is replaced by these measurements, and where the
measurements do not show an improvement, we say so.

## 9. Contribution beyond known symmetry effects — **accepted; contribution table and the requested controls added**

The revision opens with a **contribution-to-evidence table** (Claim / Evidence / Does not
show). New evidence added:
* **Non-LLM pipeline with the same tool (E-S5b):** the declared-group twirl helps every arm,
  including `random` and `mutation-ea` — so we no longer attribute the gain to the LLM.
* **Constructive equivariant architecture at matched budget (E-S6):** development risk
  0.00055 on the ring; every search arm is worse (+0.0060 to +0.0097, p < 10⁻⁴). On graphs the
  same construction is worse than every arm (0.667 vs 0.538–0.566), which we report as the
  two-sided lesson.
* **Classical task-aware baseline:** edge-count threshold fitted on training rows only
  (k = 6) reaches development risk 0.351 / accuracy 0.912 on graphs, beating every arm; best
  constant predictor 0.657; invariant oracle on the ring 0 by construction.
* **Incorrect-group hypotheses (E-S4c), measured:** on graphs, 299 proposals carried a
  hypothesis, **10** carried the task group, and **289 wrong-group proposals passed the
  label-preservation gate**; on ring, 192 carried a hypothesis, **0** carried D6, 7 passed.
  We now explain why this is inevitable — every subgroup of a label symmetry passes — and
  reclassify the gate as a soundness filter rather than an identification test.
* **Symmetry-breaking task (protocol Addendum A1, declared before running):** all five arms on
  `ring_n6` with target `alpha_1`, where the declared group is *not* a label symmetry, 12
  fresh paired seeds, its own Holm family, with the prediction stated in advance.
* **Density shortcut:** we no longer assert causation. We report the stratified risks
  (E-S5: band 0–5 mean risk 1.39 vs 0.14 in band 8–9) and the classical rule's band profile,
  and describe the task as shortcut-dominated; the intervention that would license a causal
  claim (density-matched arm ordering, or a shortcut-strength sweep) is named as required
  future work rather than claimed.
* **Novelty:** the title, abstract and conclusions are narrowed to this benchmark; no priority
  claim is made anywhere; the related-work section compares against the closest empirical and
  methodological predecessors rather than listing topics.

## 10. Bibliography — **accepted; all eight entries were wrong; the two named are confirmed**

Each entry was checked against a primary record (arXiv Atom API, Crossref, PMLR). Full table
with reproducible commands: `research/paper/REFERENCES_AUDIT.md`. Highlights:
* **Confirmed:** `elesedy2021` is *Provably Strict Generalisation Benefit for Equivariant
  Models*, Bryn Elesedy and Sheheryar Zaidi (PMLR 139); our title and both initials were wrong.
* **Confirmed:** ShinkaEvolve is *Towards Open-Ended and Sample-Efficient Program Evolution*,
  Robert Tjarko Lange, Yuki Imajuku, Edoardo Cetin (arXiv:2509.19349, 2025); our authors,
  title and "ICLR 2026" venue were wrong, and "bandit ensemble selection" is not from that
  paper at all — it is our prior study's own harness modification, now attributed there.
* **Six more errors found:** `nguyen2024`'s cited article number PRX Quantum **5:020330**
  belongs to an unrelated Hamiltonian-simulation paper (correct: 5:020328, *Theory for
  Equivariant Quantum Neural Networks*, Nguyen, Schatzki, Braccia, Ragone, Coles, Sauvage,
  Larocca, Cerezo); `meyer2023`'s title is *Exploiting Symmetry in Variational Quantum Machine
  Learning* (Meyer, Mularski, Gil-Fuster, Mele, Arzani, Wilms, Eisert) — the title we printed
  does not exist for that DOI; `mansky2025`, `baumann2026`, `otto2023` and `chen2026` all had
  wrong titles and/or authors, and `otto2023`'s now-published JMLR version was uncited.
* **Claim-level check:** where a verified source does not support the claim we attached to it
  (e.g. "invariant re-uploading" for Meyer et al.), the claim is removed rather than re-cited.
* The audited prior study is now cited as an archived artefact with a commit hash, and we state
  that it is our own earlier work.

## 11. Independent reproducibility — **accepted; model pinned, budgets reported, and two defects we found in our own record**

* **Model identity.** The alias `ycrc-local` resolves to **Qwen3.8-Flash-Next**, root
  `/apps/software/openwebui_models/Qwen3.8-Flash-Next-FP8`, served by vLLM,
  `max_model_len = 262144`, module `ycrc-llm/1.0`. Requests send only `model` and
  `reasoning_effort="none"` (no temperature/top_p/max_tokens), 180 s timeout, up to 8 retries.
  **Disclosed limitation:** the gateway publishes no immutable checkpoint revision, so the pin
  is alias + root path + module version + date; we do not claim bit-level reproducibility of
  the LLM component.
* **Budgets.** 584 calls; 1,294,840 tokens (829,452 prompt / 465,388 completion); 1448
  proposals, 8 invalid and retained; 18.1 core-hours; parameter-training budgets identical
  across arms (Adam, 120 steps, 256 rows). The Reynolds average's inference cost is charged to
  the arm that uses it and reported with its effect.
* **Provenance defects we found while checking this point** (both recorded in
  `research/PROVENANCE.md`, not silently fixed): (1) every run JSON records
  `git_commit = a37fc2d6`, but that commit **does not contain** the code that ran — it was
  uncommitted at run time; (2) the plan document that asserts it was frozen before any outcome
  was seen first appears in git (14:04Z) **after** the pilot (02:23–05:38Z) and confirmatory
  (06:09–10:48Z) runs. Consequence: the 120-run study is described as *protocol-consistent, not
  verifiably pre-registered*, and the "all results are prospective and pre-declared" sentence is
  removed. The new chain (protocol 16:20:02Z → jobs 17:10Z/17:21Z/17:37Z) **is** verifiably
  pre-registered.
* **Artefacts.** Raw paired run records, dataset manifests and seeds, all result JSONs, the
  frozen protocol, the bibliography audit, the one-shot access log and one exact command per
  table ship with the paper (appendix).
* **The Qwen material.** The legacy single-run reports under `experiments/transfer-sn/` are the
  audited prior study's exploratory material; they are excluded from every claim in this
  manuscript, and the revision says so. The stale docstring in the repair module is fixed: the
  active implementation uses the invariant oracle plus a frozen linear breaking direction, and
  the module now says exactly that.

## Presentation and scope — **accepted**

The audited prior study is identified precisely (author, date, file, commit hash, artefact
paths) and named as our own earlier work. §3.1 states the encoding-equivariance,
invariant-preparation, block-equivariance and invariant-readout conditions under which block
equivariance lifts to predictor invariance, and — because a block residual is not a predictor
certificate — we now measure predictor invariance directly on all group images
(`E[(f−Pf)²]`, reported per arm). Appendix A gives the analytic argument for the repaired
family instead of presenting a numerical zero as proof. η = 0.5 risks are reported alongside
contrasts (Table 3), raw CIs are labelled unadjusted, and multiplicity-adjusted tests are
distinguished from them. The strengths the referee kept — the residual definitions, the
qualified projection identity, the refusal to claim quantum advantage — are retained with
their assumptions made explicit.

## Minimum path to a publishable revision — status

| Referee's minimum step | Status |
|---|---|
| 1. Recompute repair statistics on genuine units; correct the search repair endpoint | **Done.** §1 (units, all differences published) and §2 (E-S1/E-S2 + coverage). The η=0 claim did not survive. |
| 2. Rewrite causal, generalisation, equivalence and floor claims to match estimands/assumptions | **Done.** Endpoint vocabulary enforced; "iff", "confound-free", "held-out", "clean null", "pinned near the floor" removed; floors separated into population / MC / exact-orbit with per-unit values. |
| 3. Freeze a corrected protocol and evaluate on untouched data | **Done.** Protocol frozen at `ecd1be72` before submission; one-shot sealed + fresh-holdout evaluation with digests and an access log; a fresh ring holdout was generated after the freeze because our metadata-only access of the v1 split is on the record. |
| 4. Demonstrate the behavioural contribution with direct measurements and baselines, or reposition | **Done, and the paper was repositioned.** Direct measurements: verifier group-identification failure (10/299, 0/192, 289 false accepts, with the subgroup explanation), reliability endpoints, the tool-vs-LLM contrast, constructive and classical baselines, breaking-target selectivity study. The claim is now that verification's value here is as a precondition for analytic repair, not as a teacher. |
| 5. Correct all bibliography metadata and provide reproducible provenance | **Done.** All eight entries corrected against primary records; provenance defects in our own earlier records disclosed. |

## What we did *not* fix, and why

* **Larger model/treatment coverage and bigger search budgets.** The 120-run record is frozen
  and reanalysed, not re-run; a multi-model, larger-budget study is a new paper, and we would
  rather report a well-measured negative than a thinly extended one.
* **`tictactoe_n9` transfer.** Left sealed and unclaimed: dense n = 9 simulation is ~30× the
  ring cost and does not fit this revision's compute window.
* **Verifier identification of the group.** We measured that our gate cannot do it (and why),
  but we did not build the instrument that could (counterexample search or a symmetry-breaking
  probe distribution). The revision states this as the main open gap.
* **Bit-level model reproducibility.** Not available from the serving stack; disclosed as a
  limitation instead of being glossed over.

We believe the revised manuscript is now a narrower paper whose claims fit its evidence: a
self-audit, a corrected causal repair experiment, and a measurement of where executable
verification helps (analytic repair, uniformly) and where it cannot (group identification),
against baselines that beat the LLM pipeline on both tasks.
