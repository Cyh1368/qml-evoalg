# Revised protocol (frozen 2026-11-11, before any new outcome was inspected)

Frozen at 2026-11-11T16:45Z by `cpsc4710_ch2499` in response to the referee report
(`research/paper/REVIEW.md`). Nothing in this file was written after inspecting a new
outcome; the git commit that adds this file predates the submission of jobs `WP-REPAIR-2`,
`WP-DEV-ANALYSIS` and `WP-HOLDOUT-ONESHOT` (see `research/PROVENANCE.md` for the dated
chain). This file supersedes the analysis sections of `extension_plan.md` for everything
listed below. Where the old protocol and this one disagree, this one governs and the old
result is reported as exploratory.

## 0. Endpoint vocabulary (mandatory wording)

* **development risk** — risk on the `validation` split of the *development* artifact.
  This split is used by candidate selection, by the search feedback loop, and by the
  verifier. It is **not** held out in any confirmatory sense.
* **sealed test risk** — risk on the sealed `test` split, read exactly once per frozen
  evaluation, after this protocol and all analysis code are committed.
* **fresh holdout risk (ring only)** — risk on `locked_holdout_v2`, generated after this
  freeze from orbits disjoint from every development and v1-test orbit.
* No sentence in the manuscript may use "held out", "generalisation", "test" or
  "confirmatory" for a development-risk number.

## 1. WP-REPAIR-2 — replication units

Target family `ring_n6`, group `D6` (order 12, explicit closure), targets
`y_eta = h + eta * b` where `h = alpha_0` (the dataset's ground-truth invariant oracle)
and `b` is the group-centred, train-variance-normalised remainder of a frozen random
linear direction `v` (`teacher_seed`). `eta in {0, 0.5, 1}`.

**Unit definition (this is the fix for the pseudoreplication in the first run).**
* `eta = 0`: `b` does not enter the target, so the target is identical for every
  direction. The replication unit is the **optimiser seed**; direction/teacher is a
  nuisance index with exactly one distinct level. `n_units = n_opt_seeds`.
* `eta > 0`: the unit is the **(direction, optimiser seed) pair**, with direction a
  blocking factor. Primary inference resamples optimiser seeds *within* direction and
  reports every direction separately; a direction-level (cluster) bootstrap over the 8
  directions is reported for the "population of breaking directions" reading, with the
  explicit caveat that 8 directions support only a within-benchmark statement.
* Duplicate detection is automatic: any arm whose distinct
  (`unit covariates`, `dev_risk`) count is smaller than its row count is reported with
  `n_rows` **and** `n_units`, and all inference uses `n_units`.

**Design.** 5 arms (below), `n_opt_seeds = 24`, 8 directions
(`teacher_seed` 101,202,303,404,505,606,708,909), `steps = 200`, `max_train = 256`,
common random numbers, fixed symmetric readout, selection on the training split only.
Budget sensitivity: the same arms at `steps in {600, 1800}` on a declared subset
(2 directions x 6 optimiser seeds), reported as sensitivity only.

**Arms** (all: 3 trainable block parameters `a,b,c`, 30 CRZ gates unless stated, fixed
D6-invariant readout `w = mean_i Z_i`):

| arm | CRZ layer | gates | symmetry | role |
|---|---|---|---|---|
| `original` | `CRZ(i,j;b)` for the 15 ordered pairs `i<j` | 15 | asymmetric | reference |
| `repaired` | `CRZ(i,j;b)` and `CRZ(j,i;b)` per pair | 30 | exactly equivariant | treatment |
| `control_dup` | `CRZ(i,j;b)` twice per pair | 30 | asymmetric | gate-count-matched |
| `control_rand` | per-pair direction from a fixed seeded rule, each pair twice | 30 | asymmetric | second asymmetric control |
| `control_matched` | as `control_dup`, initial `b` halved | 30 | asymmetric | **operator-matched** to `original` (identical initial operator) |

`control_dup` is the original interaction at angle `2b`; it therefore matches gate count
and reachable function family with `repaired` but **not** optimisation geometry. The
manuscript must say that, and `control_matched` exists to remove the initial-operator
mismatch (it is a re-parameterisation of `original`, which is stated as such).

## 2. Estimands (WP-REPAIR-2)

* **E-R1 (function space, deterministic).** For each fitted predictor `f`, the paired
  difference `R_orb(f) - R_orb(P_G f)` on the **orbit-completed** development
  distribution (every development representative replaced by its 12 group images,
  uniform weights). Under the orbit-completed (group-invariant) measure this is exactly
  `E[(f - P_G f)^2] >= 0` by the projection identity; it is reported as an algebraic
  identity check, not as evidence about retrained architectures.
* **E-R2 (architecture, primary).** Paired development-risk difference
  `repaired - control_dup` at each `eta`, units as in section 1. Secondary: `repaired -
  control_rand`, `repaired - original`, `control_dup - original`, `control_matched -
  original`.
* **E-R3 (floor accounting).** Excess risk above the floor,
  `dev_risk - floor`, per arm, with uncertainty; plus the exact-orbit floor on the
  orbit-completed set and the oracle invariant predictor risk (`f = h`, which attains the
  floor exactly). "Pinned near the floor" is banned unless
  `excess < |repaired - control_dup|` with non-overlapping intervals.
* **E-R4 (sealed test).** E-R2 restricted to `original`, `repaired`, `control_dup` on the
  sealed/fresh test rows, one shot (section 5).

## 3. Estimands (WP-SEARCH, reanalysed from the frozen 120-run record)

* **E-S1 (averaging effect on the frozen candidate).** For every run of
  `llm-verify-repair` whose repair fired, the paired difference
  `risk(P_G f_best) - risk(f_best)` on the same development rows and the same fitted
  predictor. This is the endpoint the first analysis omitted. Coverage (eligible /
  attempted / fired, per family) is reported next to it; the estimate is
  coverage-conditional and cannot be read as an intention-to-treat effect.
* **E-S2 (deployed pipeline).** `llm-verify-repair - llm-verify` on the *deployed*
  predictor: the averaged predictor where repair fired, the candidate otherwise.
* **E-S3 (primary, unchanged).** `llm-verify - llm-fitness` development-selected risk.
* **E-S4 (reliability, paired).** Per run: invalid-proposal rate, hypothesis-present
  rate, verifier false-accept rate (a hypothesis group that is not the task group but
  passes label preservation on 64 training rows), mean/max channel residual of accepted
  candidates, nonconstant-output rate (`std(predictions) < 1e-8`), repair fired rate.
* **E-S5 (shortcut intervention).** Per run, development risk restricted to
  edge-count-matched bands of `graphs_n6` (bands of the 15-bit edge count), plus a
  density-matched classical baseline. The claim "a density shortcut caused the graphs
  null" requires the arm ordering to change under this conditioning.
* **E-S6 (tool baselines).** Same-budget constructive equivariant architecture and
  task-aware classical baselines (edge-count threshold for graphs, invariant oracle for
  ring) scored on the same development rows.

## 4. Inference (applies to every contrast)

1. **Interval**: percentile bootstrap of the mean paired difference, 20 000 resamples,
   resampling the *units* of section 1 (cluster bootstrap where a blocking factor is
   part of the population statement).
2. **p-value**: null-centred ("shifted") bootstrap — resample `d - mean(d)`, compare the
   shifted statistic to 0 — reported together with an exact sign-flip test when
   `n_units <= 12`, otherwise `2 x 10^4` random sign flips. The sign-flip test assumes the
   null distribution of the paired differences is symmetric about 0; that assumption is
   stated wherever the test is used. A small-sample sensitivity (leave-one-unit-out
   range of the mean) accompanies every primary contrast.
3. Simulated p-values are never reported as 0: report `p < 1/(2 n_flip)` style floors.
4. **Multiplicity**: family A = the two primary task-specific E-S3 tests (one per family);
   family B = the three E-R2 contrasts at `eta = 0`; family C = the three E-R2 contrasts
   at `eta = 1`; family D = E-S1/E-S2/E-S5/E-S6 secondary contrasts. Holm within family,
   never across families. Raw CIs are reported unadjusted and labelled as such.
5. **Equivalence**: a CI containing 0 is "not detected", never "no effect" or "clean
   null". Prespecified equivalence margin `delta = 0.05 * Var_target` (target variance of
   the relevant `y_eta` on the development split, reported numerically); equivalence is
   claimed only if the whole CI lies inside `[-delta, +delta]`.
6. Three breaking directions cannot support a population claim about arbitrary target
   mismatches; the "iff" statement is withdrawn and replaced by a statement about the
   tested mismatch levels.

## 5. Sealed / fresh holdout policy (one shot)

* The v1 sealed splits `research/datasets/locked_holdout/*.npz` were opened **once**, on
  2026-11-11, for a metadata-only inspection (`npz` keys and row counts) that occurred
  before this freeze; the event and its (empty) influence are recorded in
  `research/PROVENANCE.md`. No label value from that inspection entered any design or
  analysis decision, and the split is still evaluated exactly once for outcomes.
* Because that access is recorded, a **fresh** ring holdout
  (`research/datasets/locked_holdout_v2/ring_n6.npz`, new seed 20261112, orbits disjoint
  from every development and v1-test orbit, sha256 recorded at generation) is evaluated
  in the same one-shot run and reported as the primary untouched result for WP-REPAIR-2.
* The one-shot run is `research/search/holdout_eval.py` + `research/experiments/repair/
  holdout_repair.py`; both print the LOCKED banner, both write an access record with the
  sha256 of the sealed file before and after.
* `tictactoe_n9` stays sealed: at `n = 9` the dense simulator makes it ~30x the ring
  cost and it is out of this revision's compute budget. It is not claimed either way.

## 6. Provenance requirements for the manuscript

Every reported number names: the run-record path, the git commit recorded in that
record, the analysis command that produced the table, the endpoint (development / sealed
test / fresh holdout), and the unit count. Model identity is reported as the served
model name plus the serving configuration actually used (see `PROVENANCE.md`), never as a
bare alias.

## 6b. Addendum A1 (added 2026-11-11 **17:37:14Z**, commit `e32e0f9a`; job submitted 17:37:16Z — i.e. before any of its results existed)

Referee point 9 asks for a symmetry-breaking task to test verifier **selectivity**.
This is a **new prospective comparison**, declared here before submission and kept out
of every frozen family above:

* family `ring_n6`, target `alpha_1` = `h + 1.0 * (x_0 - mean x)`, i.e. the declared
  group `D6` is **not** a label symmetry of the target;
* all five arms, budget `B = 12`, `steps = 120`, `max_train = 256`, 12 paired seeds
  `20261110..20261121` (a fresh seed block, so no reuse of inspected outcomes);
* endpoint: development-selected risk on the `alpha_1` target, paired by seed,
  inference as in section 4, its own Holm family (E);
* prediction stated in advance: if the verifier's effect is to push the search toward
  invariance, `llm-verify` must be **worse** than `llm-fitness` here; if the verifier is
  selective, the two should not differ materially. Whichever happens is reported.

## 6c. Addendum A2 (2026-11-11 17:45Z, committed before its analysis runs): density-matched arm comparison

The referee asked for "density-matched arm comparisons or explicit shortcut-strength sweeps"
before any causal role may be asserted for the density shortcut. Because all arms share seeds
and therefore datasets, restricting a paired arm contrast to the rows inside one edge-count
band **is** a density-matched comparison by construction. New estimand **E-S5c**: for each
band, the paired mean difference between arms over the rows in that band (same units and
inference as the D-family contrasts, Holm within the family "band contrasts per family");
still development risk. Interpretation fixed in advance: if within-band arm differences are
small and of mixed sign while the between-band risk profile is steep, the shortcut explains
the level of risk but not the ordering of arms; if within-band ordering reproduces the
marginal ordering, the shortcut does not explain the null. No quantum-advantage or
task-generality claim is made either way.

## 6d. Addendum A3 (2026-11-11 18:05Z): algebraic correction to the E-R1 description

E-R1 above stated that on the orbit-completed measure
`R_orb(f) - R_orb(P_G f)` "is exactly `E[(f - P_G f)^2] >= 0` by the projection identity".
That is true **only for an invariant target**. The correct identity for an arbitrary target
is

```
R(f) - R(Pf) = E[(f-Pf)^2] - 2 E[(f-Pf)(y - P y)],
```

so with a symmetry-breaking target the difference can be negative. WP-REPAIR-2 measures
exactly that (`-0.013` to `-0.018` at `eta=0.5`, `-0.033` to `-0.047` at `eta=1` for the
asymmetric arms), and the corrected identity holds to `3.7e-16` over all 2340 fits
(`5.5e-18` at `eta=0`). This amendment changes a **stated algebraic fact and its
interpretation only**: no estimand, replication unit, contrast, multiplicity family,
decision rule or threshold is altered, and it was written after the WP-REPAIR-2 runs
completed (which is why it is an amendment and not a silent edit).

## 6e. Addendum A4 (2026-11-11 18:15Z): one-shot E-R4 defect, corrected evaluator, and a third holdout

**What happened.** The one-shot run `32984980` (completed 18:01:38Z) evaluated E-R4
correctly for `eta = 0` but **invalidly for `eta > 0`**: `holdout_oneshot.py` built one label
array per split (`y_alpha_0_test`, the invariant target) and scored every arm against it,
regardless of the `eta` the arm was trained on. Two independent mismatches were involved:
(i) the single-`alpha_0` label, and (ii) the sealed files' own `alpha_*` labels use a
*different* breaking function (`x[:,0] - mean(x)`, unnormalised) from WP-REPAIR-2's
frozen-direction, train-normalised `b`. The symptom was unmistakable in hindsight: risks of
$0.015$--$0.03$ at `eta = 1`, where any invariant predictor's risk is at least
$\eta^2\mathbb{E}[b^2] \approx 1$ --- impossible against the real target, and the reason the
`eta > 0` contrasts came out with the opposite sign to development.

**Policy consequence.** Section 5 says the sealed splits are evaluated exactly once. The v1
and v2 ring splits *were* read in that run, so they stay consumed: the defective `eta > 0`
numbers are **not** reported as results, and the splits are **not** re-read. The evaluator now
refuses them (`--splits sealed_v1|fresh_v2` raises).

**Remedy, declared before the corrected run exists.**
1. The evaluator now rebuilds the target from the *same trusted* `TargetFn` that trained each
   arm, so an untouched-input holdout supplies new `x` and the label is the generative
   function there. A third holdout (`research/datasets/locked_holdout_v3/ring_n6_x.npz`,
   seed 20261203, **inputs only**, 4000 rows, zero dihedral-orbit overlap with development,
   v1 and v2, sha256 `a82280545dd6741c7650cfb83eee7a4cf326606dac266be46bd9aa2161781bc4`,
   mode 0444) is the only untouched input the corrected run may read, once.
2. **Self-check gate** (`--selfcheck`, job `32989281`, no sealed read): the corrected
   evaluator refits every WP-REPAIR-2 unit and must reproduce the experiment's own logged
   development risk to `1e-9`. The v3 evaluation runs only if this passes.
3. E-S7 (search arms on the v1 sealed test split) is unaffected by the defect --- its target
   handling was correct --- and is reported from the original run; it is not re-run.

This amendment changes no estimand, unit, contrast or decision rule. It records a defect,
the policy consequence of having consumed two splits, and the pre-declared remedy.

## 7. What is *not* changed by this protocol

The audit findings (`research/audit.md`), the mathematical preliminaries, and the refusal
to claim quantum advantage are unchanged. The confirmatory 120-run search record is
reanalysed, not re-run: its arms, budgets, prompts and seeds are frozen and untouched.

## Addendum A5 (2026-11-11T22:32Z) --- second-round blockers, declared before new analysis

Written after reading `research/paper/REVIEW_ROUND2.md` and **after verifying each of its
code-level claims in the source** (all six were confirmed: the `verdict()` direction, the
equality-based group-correctness metric, the missing deployed endpoint in
`holdout_oneshot._search_run`, the cell-level headline inference at `eta > 0`, the
`%.3f` Holm printing plus the mislabelled identity column, and the `fresh_v3` default in the
reproduction path). Nothing below was run before this section was committed.

### A5.1 Estimand-appropriate inference for `eta > 0` (replaces the cell-level headline)

The `eta > 0` design crosses 8 breaking directions with 24 optimiser seeds, so a cell-level
bootstrap resamples 192 quantities that reuse both directions and seeds. Three estimands,
each with its own procedure, all reported:

* **E-A (primary):** *average over the frozen direction set, generalise over optimiser
  randomness.* For each (arm, seed) average the 8 direction cells into one vector, then
  cluster-bootstrap the **24 seed vectors** and sign-flip them. Units = seeds.
* **E-B (sensitivity):** *generalise over directions, condition on seeds.* Cluster-bootstrap
  the 8 direction vectors. Units = directions.
* **E-C (sensitivity, two-way):** resample **both** clusters (seed vectors outside, directions
  inside) to expose the joint dependence; report as a wider interval, never as the headline.
* **E-D (legacy, retained for traceability only):** the previous cell-level interval.

All four condition on **one** dataset and **one** task family: no interval here quantifies
variation over newly sampled training datasets or task families, and no table may imply it.
The same rule is applied to the four-direction / eight-seed fresh-input analysis (units = 8
seeds for E-A).

### A5.2 Hypothesis status: soundness is not maximal-group recovery

The previous `wrong_group_but_label_preserving` counter conflated two different failures.
Every accepted hypothesis closure `H` is now classified against the declared task group `G`
and the **empirically measured label-symmetry group** `L_probe` of the scored target (all
`n!` site permutations tested on an independent probe panel, seed distinct from the gate's
rows):

| status | definition | reading |
|---|---|---|
| `exact_declared` | `H = G` | maximal-group recovery |
| `valid_proper_subgroup` | `H < G` | sound but incomplete: a genuine symmetry, weaker than declared |
| `valid_supergroup` | `G < H <= L_probe` | sound, stronger than declared, still label-preserving |
| `invalid` | some `h in H` violates labels on the probe | a false accept of the gate |

**False acceptance is reported only for `invalid`.** Exact recovery is reported separately and
is *not* the task the implemented gate was built for; the proposal prompt asks for a symmetry
under which labels are preserved, not for the maximal one, and the manuscript must say which
objective it is scoring. A finite-sample label test is reported as a *screen*, never as a
universal soundness certificate.

### A5.3 Fixed-panel selectivity test (no LLM, no sealed data)

The graphs-versus-breaking-ring comparison changes input domain, target, proposal
distribution and search trajectory at once, so it cannot isolate the verifier. The replacement
holds the inputs fixed and varies only the target:

* inputs: the ring `n = 6` development rows, one fixed probe panel of 512 rows drawn with
  seed 777 (never used by the gate, which reads training rows);
* targets: `alpha_0` (declared-group invariant) and `alpha_2` (deliberately not
  `D6`-invariant), same inputs;
* panel of transformations, fixed in advance: identity; the `D6` rotation; the `D6`
  reflection; the `C3` and `C2` subgroups; the full `S6`; 20 random permutations; 20
  single transpositions; and the measured `L_probe` for each target;
* metrics: sensitivity (fraction of true label symmetries accepted) and false-accept rate
  (fraction of label-violating panel members accepted), each with its own denominator and a
  Wilson 95% interval; `|L_probe|` reported per target.

Recovering `D6` on a target that is not `D6`-invariant would be the wrong answer; the panel
reports this as `exact_declared` versus `invalid` rather than as success or failure.

### A5.4 Verification as a decision rule (new estimand; the only way to test "precondition")

That declared-group averaging helps non-LLM pipelines does **not** show a verifier is
necessary. The testable question is whether the gate is a *good decision rule* about when to
repair. On development data only, for every candidate and every rule, the same Reynolds
averaging is applied and the same dev endpoint is scored:

| rule | fires when |
|---|---|
| `R0_supplied_group` | always (unconditional supplied-group averaging) |
| `R1_label_gate` | label preservation holds on the gate's rows |
| `R2_label_channel` | `R1` **and** channel residual below threshold (the implemented gate) |
| `R3_predictor_defect` | measured predictor non-invariance on dev rows exceeds threshold |
| `R4_invalid_group` | `R1` but averaging over a mismatched group (negative control) |

Primary metric: **mean risk change over all candidates** (intention-to-treat at the decision
level). Secondary: precision (share of fired repairs that helped), recall (share of
beneficial repairs fired), mean harm among fired, mean missed gain among unfired. Thresholds
come from development records only. No claim of optimality; the finding is the measured
calibration failure of `R2`, whatever it turns out to be.

### A5.5 Deployed endpoint on newly reserved inputs (one-shot, second fresh holdout)

`holdout_oneshot._search_run` scored the candidate endpoint and left
`test_risk_averaged_diagnostic = None`, so E-S7 validates candidates, not the deployed
repaired pipeline. The replacement (`research/holdout_deployed.py`) evaluates, on **newly
reserved** inputs (seed 20261205; the original sealed split stays consumed and is not
re-read):

* `test_risk_candidate` and `test_risk_deployed`, the latter applying the
  **development-frozen** repair eligibility and group to the held-out inputs;
* the same-tool non-LLM comparators on the same rows: declared-group twirl applied to the
  `random` and `mutation-ea` candidates;
* matched test-split baselines: the edge-count rule (threshold fitted on training rows only,
  scored on these rows) and the constructive equivariant block (fit at the search protocol's
  per-fit budget, scored on these rows);
* the target-defining oracle, labelled a **reference value**, not a learned baseline.

Equal *per-fit* budgets are reported as such; total search budget is reported separately and
the two are never conflated.

### A5.6 Reporting policy (enforced in code, not in prose)

* `paired.verdict` takes the metric direction and the adjusted test: a wholly positive
  a-minus-b risk interval reads **"a worse"**; a raw-CI direction may not be printed as a
  protocol verdict when the multiplicity-adjusted `p > alpha`.
* p-values below their resampling resolution print as bounds (`< 5e-05 (floor 5e-05)`), never
  as `0.000`.
* the two identity residuals are printed under their own names: `no-cross-term gap` and
  `full A3 gap`.
* "buys nothing", "equally", "did not move", "no effect" are banned; failure to detect is
  written as failure to detect, and equivalence requires the prespecified margin test.

---

## Addendum A6 — corrected verifier as comparator, costed decision objective,
## distribution-aware diagnostic (added 2026-11-12, after the third-round report,
## **before** any of the analyses below were run)

Third-round review verified in source: `verifier_bridge.label_preservation` defaults to
`tolerance=0.0` and calls `task.label_oracle(rows)` with **no** `target=`, so the deployed
label test demands that a hypothesis preserve *every* target column at exact floating-point
equality. Both defects are real. Therefore no conclusion about *verification* may be drawn
from the defective gate alone; the corrected gate is added as a first-class comparator, and
the mismatched-group control is re-specified so that each rule is scored under its own
decision.

### A6.1 Corrected label test (settings frozen here, before evaluation)

`label_preservation_corrected(task, hypothesis, n_rows, target, tol_rule)` differs from the
implemented test in exactly two ways, both named in A6: it scores **the scored target
column** (`task.label_oracle(rows, target=target)`), and it treats a `(row, permutation)`
entry as violated iff

    |y_t(g x) - y_t(x)| > tol,   tol = ATOL_ABS + ATOL_REL * |y_t(x)|
    ATOL_ABS = 1e-12, ATOL_REL = 1e-9            # frozen here

`ATOL_REL = 1e-9` is the probe tolerance already used for truth determination, so the gate
cannot be more demanding than the instrument that defines soundness; `ATOL_ABS = 1e-12` is
two orders above the largest roundoff discrepancy observed for an exact symmetry in this
codebase. Accept iff `violated_fraction == 0`. Row count is the harness value
(`LABEL_ROWS = 64`), so gate cost is comparable to the implemented gate.

Because a single frozen tolerance could itself be load-bearing, every corrected-gate result
is reported over the **tolerance sweep** `{0, 1e-15, 1e-12, 1e-9, 1e-6, 1e-3}` with the
frozen point marked, and the sensitivity of each conclusion to the sweep is stated.

### A6.2 Rule set, scored under each rule's own decision

All rules are applied to the **same frozen predictors, same rows, same averaging operation**.
Each rule is evaluated in four supplied-group regimes, and in every regime the rule's **own**
firing mask selects which candidates are averaged (this is the correction to the previous
`R4`, which averaged the mismatched-group delta over all candidates while being described as
"R2's decision"):

| rule | decision |
|---|---|
| `R0_always` | average unconditionally |
| `R1_defective` | implemented label test (all columns, tol 0) |
| `R2_defective` | implemented label test AND channel residual > `REPAIR_RESIDUAL_FLOOR` |
| `R1_corrected` | corrected label test (A6.1) |
| `R2_corrected` | corrected label test AND channel residual > floor |
| `R3_defect` | predictor non-invariance statistic below the frozen `q1` threshold |
| `R_rand75` | random selection at the same firing count as `R3_defect` (seeded) |

Regimes: `declared` (the task's group, valid), `subgroup` (a valid proper subgroup),
`mismatched` (a group that is not a label symmetry of the scored target), `approximate`
(a group that is a symmetry of a perturbed target, A6.4). Reported per rule per regime:
fired, realised mean risk change, risk change if always applied, **harmful interventions
rejected**, **beneficial interventions missed**, paired intervals, and cost.

### A6.3 Cost model and decision objective (replaces "saves computation" talk)

Costs are **measured**, not assumed, in seconds per candidate on the evaluation hardware:
label test, channel test, defect statistic, and averaging. The defect statistic is charged
for what it actually costs: it needs the averaged predictions on its own sample, so
`cost(R3) = cost(averaging on m rows)`, and this is deducted in the objective.

Objective (frozen): for a deployment horizon of `H` predictions and a cost weight `w`,

    J(rule) = mean risk after the rule + w * (gate cost + one-off averaging + H * per-prediction averaging overhead)

reported for `H in {1, 10, 100, 1000}` and `w` spanning the measured cost/risk exchange rate.
A rule is reported as **dominated** if another rule is at least as good in risk and cost for
all `(H, w)` considered. No rule may be described as efficient without this table.

### A6.4 Approximate-symmetry regime (separates implementation defect from gate limitation)

Ring labels are perturbed, `y_eps = alpha_0 + eps * xi` with `xi` fixed by seed `20261207`, for
`eps in {0, 1e-12, 1e-9, 1e-6, 1e-3, 1e-2}`. The declared group is an exact symmetry only at
`eps = 0`. This regime is where a zero-tolerance test and a tolerance-aware test must differ;
if the corrected gate behaves like the defective one here too, the finding is about gates,
not about our bug.

### A6.5 Diagnostic restated as a distribution-aware, estimable quantity

The A5 statement `|L_t| / |S_n|` is **retracted as a predictor of gate behaviour** and
replaced by an explicitly distribution-aware quantity:

    accept(Q, t) = Pr_{H ~ Q}[ H is a label symmetry of t ]

for a stated proposal distribution `Q`. It is estimated by Monte Carlo under three declared
`Q`s: (i) one uniform permutation; (ii) closures of `k` independent uniform permutations,
`k in {1,2,3}`; (iii) the **empirical** proposal distribution of the 491 recorded search
hypotheses. Enumeration cost is reported (`n!` grows as 720 at `n=6`, 362880 at `n=9`), and
`n = 9` is computed by sampling only. Predictions are validated against observed gate
decisions per family, and the boundary cases are stated as boundary cases: `accept = 1` means
the predicate cannot discriminate, `accept = 0` means it always rejects; neither is an
information claim, and a small `accept` is useless if `Q` is concentrated.

### A6.6 Panel units, intervals, and what may be called replication

* The fixed panel is **nine generator-set entries**, and three of them (`full_symmetric`,
  `random_permutations`, `single_transpositions`) generate the **same** subgroup of order 720.
  Panel results are therefore **descriptive coverage over a hand-chosen panel**: report the
  unique subgroups, and do not attach binomial/Wilson interpretation to panel counts.
* Proposal-level and decision-level rates keep their dependence structure: report counts, and
  for any interval use the seed-vector bootstrap over the 12 paired seeds; Wilson intervals
  are reserved for genuinely independent Bernoulli trials, of which this design has few.
* `crossed_bootstrap_ci` may **not** be described as wider by construction; the observed
  ordering is a sensitivity result.
* Fresh prediction inputs with a **development-frozen** decision validate the *risks* of the
  frozen policies. They cannot replicate a *firing rate*, which is fixed by construction. Any
  firing-rate replication needs new fitted candidates.

### A6.7 Corrected-feedback search rerun (needed for any behavioural claim about feedback)

Post-processing frozen candidates cannot recover the trajectories that corrected feedback
would have produced, so behavioural claims require new matched runs: same initial population,
same budget, same seeds, same prompt structure, arms
`llm-fitness`, `llm-verify-defective`, `llm-verify-corrected`, both families, 12 paired seeds.
Primary contrast `llm-verify-corrected - llm-fitness` on development-selected risk, Holm within
the family, with a **prespecified practically meaningful threshold** frozen here at
`0.002` absolute risk (the ring invariant floor gap between arms and the constructive block is
`0.006`; half of it is the smallest effect this study is designed to care about). If the
corrected feedback does not clear it, the feedback conclusion stays "difference not detected".

### A6.8 Numeric checker: scope, and what would make it a claim-level instrument

`research/paper/check_numbers.py` is a **numeric-token lint**: it confirms that a decimal
token appearing in the manuscript also appears somewhere in the generated summary. It does
not bind values to endpoints, arms, splits or table cells, so a valid number in the wrong
place passes. It may be described only as such. To support a claim-level statement it must
(i) bind each manuscript value to a structured result key, (ii) generate table cells from
those keys, and (iii) pass a **mutation test** (sign flips, arm swaps, split swaps, exponent
changes, endpoint relabels) with reported detection and false-alarm rates.

---

## Addendum A7 — decision model, subgroup-sampling fix, exact Q, gate parity, calibrated screen

Written **before** any A7 analysis or recomputation. Motivated by the fourth-round review, whose
four code-level claims were each verified in source before being accepted: the `ClosureTooLarge`
fallback in `corrected_gate.label_test` samples arbitrary permutations of $S_n$ rather than words
in the proposed subgroup; `_empirical_hypotheses` filters neither arm nor family and appends each
selected best hypothesis a second time, while the filtered `emp_here` is computed and then ignored
in favour of the unfiltered pool; `decision_rules2.evaluate_candidate` passes `gens_declared` to
the defective label test in every regime and computes the channel residual once with
`group="true"` outside the regime loop; `_masks` recomputes its thresholds inside each regime. The
manuscript contradictions it lists were also verified. Nothing here is disputed.

### A7.1 Subgroup sampling, and a three-level certification vocabulary

`label_test` must test the hypothesis that was actually proposed: **the subgroup generated by the
proposed generators**. When `closure` exceeds the cap, the fallback draws **words in that subgroup**
(products of the proposed generators and their inverses, BFS from the identity, capped), never
arbitrary elements of $S_n$: a violation at a permutation outside the hypothesized subgroup refutes
nothing. If the subgroup cannot be enumerated and word sampling is used, the result is reported with
`scope="inconclusive"`; a violation found is still conclusive evidence against the hypothesis, an
absence is not.

Certification language is fixed at three levels, and no result may use a stronger one than its
level:

| level | meaning | permitted wording |
|---|---|---|
| `proof` | analytic derivation over all inputs | "proved" |
| `exhaustive_subgroup_on_probe_set` | every element of the hypothesized subgroup tested, on a fixed finite row set | "exhaustive over the hypothesized subgroup, on the probe set" |
| `inconclusive` | sampled words, or subgroup not enumerable | "not refuted on the probe set" |

Finite probing over rows is never called a proof of the population label-symmetry group. Where an
exact group is claimed by exhaustive checking over a *finite input domain* (all $2^n$ bitstrings),
that is stated as exhaustive over the domain, which is a proof for that domain and not for
continuous inputs. Zero acceptances in $k$ draws from a named $Q$ is reported as
$0/k$ with a one-sided Clopper--Pearson upper bound at 95% ($3.69/k$ for $k{=}400$), never as zero
probability.

### A7.2 The proposal distribution $Q$, defined before measuring it

$Q$ is **the hypothesis-proposal distribution of the arm under study, on the family under study**.
The pool is therefore filtered to (i) LLM arms only, (ii) the family's own runs, and (iii) one entry
per proposal, with the selected-best duplicate removed. Each variant is named in the record:
`Q=llm_ring` (ring, LLM arms, deduplicated), `Q=llm_graphs`, `Q=uniform_single`,
`Q=uniform_pair`, `Q=declared_group`. Because the empirical pool is finite and fully stored, its
acceptance rate is computed by **exact enumeration over the pool**, not Monte Carlo; the Monte Carlo
layer is retained only for the analytic uniform models, where the support is $n!$. The record states
that the pool rate's uncertainty is Monte-Carlo-free but **conditional on the stored pool**: it
carries no uncertainty about the adaptive LLM process or future runs, and run-level uncertainty is
reported separately as the between-run spread of the per-run acceptance fraction. Headline ratios
are recomputed from the corrected pools.

### A7.3 Gate parity in the multi-rule comparison

Every gate in every regime receives **that regime's own group** and that regime's own target, so the
only thing that varies across regimes is the treatment. The channel condition is recomputed per
regime with the regime's group. Two threshold designs are reported side by side and named
differently: `q1_frozen`, a numeric threshold computed once on the declared-group regime and applied
unchanged to every regime (fixed-threshold transfer), and `q1_within`, recomputed inside each regime
(**within-regime quantile selection**, which preserves a selection fraction by construction and is
not threshold transfer). A `never_repair` rule with zero gate and zero repair cost is added as an
explicit baseline. Averaged-inference time is **measured** (timed call over the twirl elements), not
raw time multiplied by group order; every timing is tagged `measured` or `extrapolated`, and
timings are repeated (median of 3) with spread reported before any "strictly cheaper" claim.

### A7.4 Costed objective, with the decision maker's information stated

The decision maker chooses a **policy**, which is a function of the candidate and the supplied group
only; the regime (whether the supplied group is a label symmetry of the target, and the perturbation
strength) is **not** observed at decision time. Risk is deployed risk: candidate risk when the policy
does not fire, group-averaged risk when it does (this is the deployed predictor the protocol already
defines, and it is computable from stored diagnostics — non-firing runs contribute their candidate
risk, so no additional holdout read is needed or permitted). The objective is
$R(\pi) = \mathbb{E}_{\text{regime}\sim\pi}[\text{deployed risk}] + w\,c$, with the mixture
$\pi$ over regimes predeclared at $\{0, 0.25, 0.5, 0.75, 1\}$ and $w$ swept. Cost is
per-deployment: gate time plus fired-repair time plus horizon-scaled inference overhead at a stated
horizon $H{=}10^3$ predictions, and the record states that gate cost is paid per candidate screened
during search while repair/inference overhead is paid per deployed prediction, so the two are never
added in the same units without the horizon factor.

### A7.5 The one contribution: a calibrated screen against simple policies under approximate symmetry

The referee's stated open question is adopted as the experiment: *can a calibrated, statistically
justified screen choose beneficial repairs under approximate symmetry better than the simple
policies?* Predeclared:

* **Approximate-symmetry continuum.** The ring development target perturbed as
  $y_\varepsilon = y_0 + \varepsilon\,(x\cdot v)$ with a fixed unit $v$ (seeded), on a frozen grid
  $\varepsilon \in \{0, 0.05, 0.1, 0.2, 0.4\}$ scaled by the target's own spread, plus the
  mismatched-group regime. Scope is stated as synthetic: this is a controlled continuum, not an
  independently validated task-relevant approximately symmetric application.
* **Calibration rule.** Tolerance is not hand-picked. Given a null panel of exactly symmetric
  targets, $t^\star$ is the largest tolerance in the frozen grid whose false-accept rate on the null
  panel has a one-sided 95% upper bound at most $\alpha = 0.05$. This is computed by the same code
  path as the tests it calibrates, and the calibration data are recorded.
* **Policies compared.** `never`, `always`, `corrected@t` for the frozen tolerance grid,
  `calibrated` (the rule above), `defect@q1_frozen`, and the constructive equivariant block as a
  non-LLM baseline predictor under `always`.
* **Verdict categories, fixed in advance.** If `calibrated` is not strictly best at any mixture
  weight, the result is reported as a **scoped negative**: a calibrated exactness screen does not
  beat always/never on this continuum. If it is best only in an interval of $\pi$, that interval and
  its width are the reported finding. Neither outcome may be re-described post hoc as the other.
* **Inference.** Seed-vector bootstrap over candidates, paired across policies; Holm within each
  family of comparisons; no claim transfers to new datasets or families.

### A7.6 Feedback endpoint: multiplicity before verdicts, and equivalence wording

`analyze_corrected` applies Holm **before** assigning verdicts, and the verdict vocabulary is split:
`bounded within prespecified band` (whole CI inside $\pm0.002$, descriptive), and, additionally
reported, a multiplicity-controlled equivalence statement only if the Holm-adjusted TOST rejection
holds at the prespecified margin. The two are never conflated, and band containment is never called
"no effect". The threshold's meaning is justified on the risk scale (the ring invariant-floor gap
between arms and the constructive block is $0.006$; $0.002$ is a third of it) and related to the
repair-side margins. Candidate-endpoint and deployed-endpoint contrasts are reported as separate
rows; the coverage-conditional three-run estimate is labelled as conditional on firing. The
contemporaneous corrected-vs-corrected comparison carries the causal reading; corrected-vs-old-gate
comparisons are labelled as differing in run time and possibly serving state.

### A7.7 Manuscript coherence, and the checker's status

One statement of each final claim. The superseded A5 defect-gate comparison, the 79% recovery figure
and the review-response narrative move to the audit appendix with their provenance, and are not
cited as present-tense conclusions in the abstract, results or Discussion. `\texttt{tictactoe_n9}` is
described accurately: its label-symmetry structure has been measured (that needs no circuit
simulation), while it remains unrun as a search/repair benchmark. `claim_bind.py` and
`check_numbers.py` are described as internal supporting software for this manuscript — self-checks on
documents produced by this project — and are not offered as external validation or as a novelty
contribution.

### A7.5a Amendment to the calibration rule (written before any A7 result exists)

As first written, A7.5 says the tolerance is calibrated so that the "false-accept rate on a null
panel of exactly symmetric targets" stays below $\alpha$. That is incoherent: on a panel where the
supplied group *is* a label symmetry, accepting is correct at every tolerance, so the rate it
constrains is identically zero and the rule selects nothing. The error being controlled must be
stated, and two rules are therefore pre-declared and reported side by side. Both use the one-sided
95% Clopper--Pearson upper bound on the accept-error rate over the named panel, and both choose the
**largest** tolerance on the frozen grid whose bound is at most $\alpha = 0.05$; if none qualifies,
the rule returns "no admissible tolerance" rather than the smallest one.

| rule | panel (entries where...) | error controlled |
|---|---|---|
| `calib_exact` | the supplied group is **not** a label symmetry of the target on the probe set | accepting a group that is not a symmetry |
| `calib_harm` | the realized change in risk is **positive** ($\Delta > 0$, repair hurt) | accepting a repair that actually harms this predictor |

The two answer different questions and their gap is itself a reported result: `calib_exact` is the
literal exactness screen, and it is the rule that approximate symmetry defeats; `calib_harm` is the
decision-relevant calibration, which tolerates inexactness exactly when it is harmless. The
tolerance grid is scale-free, $\{0, 10^{-9}, 10^{-6}, 10^{-4}, 10^{-3}, 3{\times}10^{-3},
10^{-2}, 3{\times}10^{-2}\}$ multiplied by the target's own standard deviation, so the grid does not
encode a preference for one dataset's units. Calibration data are recorded with the choice they
produced.
