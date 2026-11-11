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

## 7. What is *not* changed by this protocol

The audit findings (`research/audit.md`), the mathematical preliminaries, and the refusal
to claim quantum advantage are unchanged. The confirmatory 120-run search record is
reanalysed, not re-run: its arms, budgets, prompts and seeds are frozen and untouched.
