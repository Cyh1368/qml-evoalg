# HANDOFF — round-3 revision (third referee report)

## Round 4 status (Addendum A7 / A7.5a) — complete

`REBUTTAL_ROUND4.md` answers all seven fourth-round blockers. Nothing is pending.

| item | state |
|---|---|
| A7 protocol (A7.1–A7.7) + A7.5a amendment | committed `73a95d77` **before** any A7 analysis |
| A7.1 subgroup-word fallback, three-level certification | `corrected_gate.closure_capped`, `scope`, `cp_upper_95`; 25 tests |
| A7.2 defined $Q$ pools, exact enumeration | `empirical_pool`, `accept_pool_exact`; ring **0.6250** (120/192) replaces 0.47 |
| A7.3/A7.4 gate parity, never-repair, mixture, measured timings | `decision_rules3.py` (job 33073899), `analyze_decision3.py` |
| A7.5 calibrated screen | pre-declared **scoped negative** in both families |
| A7 decision model + counterexample | `decision_model.py`, 11 tests, `decision_model.json` |
| A7.6 Holm-before-verdict, deployed endpoint | `analyze_corrected.py`; deployed graphs −0.07269 (flip 0.0176, Holm 0.158) |
| A7.7 manuscript coherence | abstract 79% removed, A5 material to appendix, Discussion contradiction fixed, checker scope paragraph |

Checkers: manuscript 22/22 bound (86/87 mutations), CLAIMS 21/21 (82/83), rebuttal 3 18/18 (71/71),
**rebuttal 4 11/11 (44/44)**. `check_numbers` OK. Tests: search 59, core 51, repair 13.

New traps found this round (details in `research/PROVENANCE.md`):
- **A source patch must be verified by re-reading the target.** A heredoc died on quote escaping
  before writing, and the resulting record looked complete but still held the old row.
- **Never let `min()` over names break an exact tie.** It reported a calibrated policy as optimal
  when it fired nothing and equalled never-repair. Use strict improvement + simplicity tie-break.
- **`claim_bind` paths into a dict-of-lists must name the key first**: `accept.alpha_0.[Q=...]`,
  not `accept.[Q=...]`; the dict branch treats the whole selector as a literal key.
- **Parity changes our own numbers downward.** With regime-specific groups the defect rule rejects
  only 4/58 harmful repairs; the 79% recovery figure is superseded, not merely re-labelled.

Working directory: `/home/cpsc4710_ch2499/qml-evoalg`
Last commit at the time of writing: see `git log --oneline -1`.

## What this session was for

Read `research/paper/REVIEW_ROUND3.md`, address it with new experiments and corrections, and
write `research/paper/REBUTTAL_ROUND3.md`. The referee's central demand was that **a corrected
verifier is the indispensable comparator**; acting on it reversed one of our headline claims.

## Status

| deliverable | state |
|---|---|
| Addendum A6 pre-declared in `research/REVISED_PROTOCOL.md` (commit `4ab15f81`, before any A6 analysis) | done |
| A6.2/A6.3 corrected-gate decision comparison, 7 rules × 5 regimes on the 120 frozen candidates | done — `research/search/decision_rules2.json` (job 33050023) |
| A6.5/A6.6 accept-probability, exact label groups, panel units, tolerance sweep, n=9 case | done — `research/search/corrected_gate.json` (job 33053412; 33050360 cancelled, 33051692 superseded) |
| A6.8 claim binding with mutation testing | done — `research/paper/claim_bind.py`, report `claim_binding_report.md` |
| Manuscript: new `sec:corrected`, accept table, de-Wilsoned panel table, rewritten Discussion, review narrative moved to `app:audit` | done, preview clean (25 pp, job 33054054) |
| `REBUTTAL_ROUND3.md` | written and complete — the A6.7 block is filled with generated numbers (18/18 claims bound, 71/71 mutations detected) |
| A6.7 matched corrected-feedback search runs | **done** — job array `33058123`, 72 runs, 12/12 seeds in all six cells, `research/search/corrected_search.json`. Earlier arrays 33053054-9, 33054417, 33058032 were cancelled — two on a misdiagnosis of Slurm CPU accounting, one because it carried the wrong budget — and none wrote a run log |
| CLAIMS / PROVENANCE / MANIFEST / README reconciliation | done |

## The one unfinished thing, and exactly how to finish it

Job `33054417` writes `logs/runs_corrected/*.json` (72 runs, each carrying
`label_mode="corrected"`). When it is done:

```bash
module reset && module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a ycrc-llm/1.0
export LD_LIBRARY_PATH=/apps/software/2024a/software/Python/3.12.3-GCCcore-13.3.0/lib:$LD_LIBRARY_PATH
export OPENBLAS_NUM_THREADS=1
python3 -m research.search.analyze_corrected --out research/search/corrected_search.json
python3 -m research.compile_results2 --out research/results_summary2.md
```

Then replace the `<!--A67-->` marker in `research/paper/REBUTTAL_ROUND3.md` with the contrast
table (copy the numbers from `research/results_summary2.md`, section "Corrected-feedback search
runs (A6.7)" — do not retype them from the JSON), and mirror any behavioural sentence in the
manuscript's Discussion. The decision rule is already frozen inside `analyze_corrected.py`:
a contrast counts as *detected at the prespecified threshold* only if the seed-pair bootstrap CI
excludes 0 **and** `|mean| >= 0.002`. If it does not clear that, the sentence stays "difference
not detected", which is not "no effect".

Check afterwards, in this order:

```bash
python3 -m research.paper.check_numbers        # numeric-token lint
python3 -m research.paper.claim_bind           # claim-level binding + mutation battery
sbatch research/paper/job_preview.sh           # PDF build; check the .out for errors
```

`check_numbers` will fail until any new number quoted in the manuscript also appears in
`results_summary2.md`; that is the intended direction of the dependency.

## Results you need to know to continue the science

1. **The corrected gate reverses our round-2 claim.** On the same 60 frozen ring candidates: the
   implemented screen fires 0/60 and realises 0.00000; the corrected screen fires 60/60 and
   realises the full −0.00345 for 0.0017 s of gate time. "Verification is a recall bottleneck"
   is withdrawn.
2. **The gate's safety role is now measured**: under a mismatched group averaging harms 58/60
   candidates and the corrected screen rejects all 58 at 0.0005 s, while the defect rule rejects
   15 and random 75% selection 14.
3. **The tolerance is the policy** under approximate symmetry: the corrected gate accepts at
   ε=1e-12 and rejects at 1e-9 and above, while averaging still helps at all of them.
4. **The group-size ratio is the wrong functional**: uniform models are confirmed
   (0.0179 single, 0.00025 for two generators, matching `|L|/|S_n|` and its square) but the
   empirical LLM proposal distribution accepts at 0.47 — 21× the single-permutation rate.
5. **`graphs_n6` gate is vacuous** (`|L| = |S_6| = 720`, exact enumeration) and **`tictactoe_n9`
   is vacuous in the opposite direction** (`|L|/|S_9| = 2.2e-5`, algebraic anchor, never
   enumerated).
6. **Panel units**: 9 generator sets → 7 distinct subgroups at n=6; counts are descriptive
   coverage, no Wilson intervals.

## Traps and conventions that bit us

- **Do not re-implement shared structures.** `corrected_gate.py` had a local copy of the A5.3
  panel that had silently drifted while claiming to be canonical; it changed the headline
  distinct-subgroup count. Import from `verify_semantics`, and `TestCanonicalPanel` now pins it.
- **Never enumerate closures at n=9**: `|S_9| = 362880`. `closure()` has a 2000-element cap and
  raises `ClosureTooLarge`; sampling can refute a symmetry but never certify one.
- **`TotalCPU 00:00:00` on a RUNNING array task means nothing**: Slurm flushes CPU accounting
  at completion. It is not evidence of a network stall (the gateway answers in ~2.4 s median).
  A 32-candidate run genuinely takes tens of minutes on a contended 1-CPU task; judge progress by
  files appearing in the output directory, not by `sacct` CPU.
- **Module version is `ycrc-llm/1.0`**, not `1.0.0` (that typo failed 72 tasks in 4 s).
- **Repair state is at `best.repair`, not top-level `repair`.** The top-level key is `None` in
  every run log; counting it gives a false "0 attempted, 0 fired" everywhere. `best.repair` reproduces
  the known 7/12 on frozen graphs, so it is the correct location.
- **Take matched settings from the record you are extending.** The A6.7 script inherited budget 32 /
  steps 200 from a template while the frozen study it extends is budget 12 / steps 120; three
  arrays went out wrong before the run JSONs were checked.
- `sound_on_probe`/`panel_reanalysis` take a **probe index array** (`probe_indices(...)`), not rows.
- Shell calls are isolated: `module reset` + loads + command must be in one invocation.
- `module reset`, never `module purge`.

## Files touched this round

`research/search/corrected_gate.py` (+ tests), `research/search/decision_rules2.py`,
`research/search/analyze_corrected.py`, `research/search/harness.py` (`label_mode`),
`research/search/job_corrected_search.sh`, `research/paper/claim_bind.py`,
`research/paper/main.tex`, `research/paper/REBUTTAL_ROUND3.md`, `research/CLAIMS.md`,
`research/PROVENANCE.md`, `research/MANIFEST.md`, `research/build_manifest.py`,
`research/compile_results2.py`, `research/REVISED_PROTOCOL.md` (A6).

## If a fourth round arrives

The referee's remaining structural demand is *consequence beyond this configuration*: a task
family whose target is only **approximately** symmetric is the single most informative new
experiment, because that is the regime where the tolerance rather than the verifier decides.
`tictactoe_n9` is still sealed and unclaimed for the risk side (dense n=9 simulation is ~30× the
ring cost) and needs its own protocol amendment and a fresh split. Do not re-read any consumed
split: `research/HOLDOUT_ACCESS.json` is the ledger and `holdout_deployed.py` refuses them.

## ShotCert round-3 repair (A6) — current state

Third review (`shotcert/REVIEW_3.md`): reject, but "continue the research direction, with a new central
result and a corrected experiment." All six of its technical claims were verified in source before being
accepted; the principal one was confirmed to five decimal places.

| item | status |
|---|---|
| A6.0 estimand defect confirmed | offset −0.05258 measured vs predicted σ₀²/(2s) = −0.05258; 32.8× the effect |
| A6.1 common-estimand record | `shotcert/record.py`; raw baseline gets S identity shots, cost S(2−1/G) = 3s |
| A6.2 estimand audit (stop gate (a)) | **passes**, max disagreement 5.6e-17 vs independent enumeration; pinned in `test_record.py` |
| A6.3 equal-total-budget frontiers | **mixed**: group arm wins 10/18 cells, group-free 8/18; "cheaper on 6 of 7" **withdrawn** |
| A6.4 mechanism counting | cluster_even ≡ cluster_raw (verified identical); reported as one mechanism |
| A6.5 variance-profile boundary | recoverable cost = Var_g(σ); 0 for measure-preserving orbits, +0.000058 measured vs 0.000058 predicted on the non-preserving counterpart |
| A6.6 stop gate | (a) passes; (b)/(c) reported in the frontier run |
| A6.7 presentation | duplicate labels renamed `*_hist`; test count now generated (35) |

**New central result (A5 + A6.5).** `w*(S) = (Δ_ideal + A)/(2A) − V/(2AS)` is the unique optimum of the
verified risk functional over the whole class of allocations splitting S between raw and orbit; symmetry is
a luxury good when V > 0, worthless below `S_on = V/(Δ_ideal + A)`, full only above
`S_full = V/(Δ_ideal − A)`. Neyman orbit allocation recovers exactly `Var_g(σ)`, which is zero for any
measure-preserving group action — so the cost is irreducible on every orbit in this study.

**Traps added this round.**
- A coefficient estimated from a finite input sample moves with the sample: `Δ_ideal` was −0.00213 on 120
  instances and −0.001635 on the frozen 300. Quote the artifact, not the ad-hoc check.
- The estimand audit caught a missing enumerator branch for a new estimator; without it the audit would
  have silently compared against a different estimator and passed.
- A generated table header with an unbalanced `$` swallows the row terminator and fails as
  "Misplaced \noalign", not as a math error.
- Giving shrinkage to only one arm is the same unfairness class as a shot mismatch.
