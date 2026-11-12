# HANDOFF — verified symmetry hypotheses and causal repair (round 2 complete)

Updated 2026-11-12 02:15 UTC. Session model: see `PI_*`. Repo
`/home/cpsc4710_ch2499/qml-evoalg`. Last commits carry the whole second-round revision.

## Where the work stands

Second-round referee report (`research/paper/REVIEW_ROUND2.md`, decision "reject in current
form") raised six code-level blockers plus a novelty judgment. **All six were verified in the
source before answering, all six were correct, and all six are fixed.** Response:
`research/paper/REBUTTAL_ROUND2.md`. Protocol Addendum **A5** was committed (22:32Z) before any
new analysis ran.

Status of the manuscript: `main.tex` compiles clean as an article-class preview (21 pages, no
errors, no undefined refs), and `python3 -m research.paper.check_numbers` reports
**863 generated numbers / 414 manuscript numbers, OK** — every manuscript number of ≥4 digits
matches a generated value.

## Headline numbers (all from `research/results_summary2.md`)

| result | number |
|---|---|
| η=1 cost of enforced invariance, primary estimand E-A (seeds) | +0.03605 [+0.02998,+0.04210]; E-B [+0.02610,+0.04597]; E-C crossed [+0.02366,+0.04828]; E-D legacy [+0.03134,+0.04087] |
| η=0 symmetry-specific benefit vs gate-matched duplicate | −0.00060 [−0.00135,+0.00019], Holm 0.246 — **not established** |
| Graphs target label-symmetry group | **720 = the whole hypothesis space** → label gate vacuous by construction |
| Ring scored target / implemented conjunction | 12/720 vs 2/720 (gate is 6× stricter than the scored target) |
| Fixed-panel sensitivity, implemented → corrected | 1/6 → **6/6**, false accepts 0/3 in every variant |
| Search hypotheses | graphs 10 exact + 289 valid proper subgroups + 0 invalid; ring 0 exact + 120 valid + 72 invalid; 0 false accepts; 95/95 rejected ring hypotheses were sound [0.961,1.0] |
| Decision rules, ring | R0 always −0.00345; **R1/R2 gate fires 0/60, realised 0.00000**; R3 defect gate −0.00274, precision 45/45; R4 mismatched group **+0.00399 harm** |
| Decision rules, graphs | every rule −0.08705 (gate fires 60/60); R3 −0.07544 (45/60) |
| Gate cost vs repair cost | graphs 0.45 s vs 12.5 s; ring 0.013 s vs 0.18 s; channel condition satisfied by 60/60 candidates (no discrimination) |
| Deployed endpoint, graphs repair | candidate 0.52913 → deployed **0.50067**, −0.02846 [−0.04704,−0.01190], 7/12 fired |
| Deployed endpoint, ring (fresh v5 inputs) | gate fires **0/12** → deployed = candidate for every arm (replicates 0/60) |
| Declared-group twirl on held-out rows | helps every arm: graphs −0.070…−0.096, ring −0.0034…−0.0046; `random`+twirl 0.40915 beats all five deployed arms |
| Constructive equivariant on **fresh** ring inputs | **0.00026** vs best arm candidate 0.00648 |
| Edge-count rule, matched rows | development 0.351 (beats arms) → sealed **0.57812** (does **not** beat arms 0.50067–0.54472) |

## Corrections made to our own previous text this round

1. **Edge-count rule "beats every arm"** — true on development validation, false on matched
   held-out rows. Abstract, §baselines and the new §deployed now scope it. (This is the
   referee's point 7 producing a real reversal, not a rewording.)
2. **"289 wrong-group proposals passed the gate"** — they are *valid* proper-subgroup
   hypotheses; 0 invalid; and on graphs the gate cannot fail at all.
3. **Meyer et al. citation** — our round-1 audit claim was wrong; primary-text quotes now in
   `REFERENCES_AUDIT.md`, novelty claim narrowed to the decision-level measurement.
4. **E-S7** relabelled candidate endpoint; cross-endpoint/cross-split comparisons removed.
5. MC twirl disclosed: every graphs average is 24-of-720, so exact-projector guarantees do
   not transfer.

## Defects found and recorded (not silently fixed)

* `paired.verdict()` direction reversed for risk metrics (test only exercised one side).
* `dev_analysis` equality-based "wrong group" metric conflated sound-incomplete with false accept.
* `holdout_oneshot._search_run` never computed the deployed endpoint (`None`).
* Cell-level bootstrap at η>0 resampled 192 quantities reusing both directions and seeds.
* `%.3f` Holm printing (`0.000`) + identity-column mislabelling.
* `fresh_v3` in the reproduction path (stale).
* `hashlib.sha256(Path)` crash — aborted job 33042529 **before** any sealed read.
* `check_numbers` en-dash false positive (`0.5--0.6` parsed as a negative number).
* Projection-identity sign error (round 1, Addendum A3) — verified to 3.7e-16 over 2340 fits.

## Jobs

| job | what |
|---|---|
| 33039560 | A5.4 decision-rule ablation → `research/search/decision_rules.json` |
| 33039574 / 33040509 / 33041014 / 33041668 | A5.5 dry runs (gate 120/120 exact, max 1.73e-18); final artifact `build/deployed/dry.json` |
| 33042529 | A5.5 attempt aborted by the digest bug **before any sealed read** |
| 33044945 | A5.5 one-shot → `research/HOLDOUT_DEPLOYED.json`, digests unchanged, graphs second read authorised and logged |
| 33045959 | preview PDF (21 pages, clean) |

## Split ledger (one read each; evaluator refuses consumed splits)

v1 consumed (E-S7 + defective E-R4 + **authorised** A5.5 graphs second read) · v2 consumed ·
v3 consumed by an aborted run (inputs-only, no label exposed) · v4 consumed by E-R4' ·
v5 ring consumed by A5.5; **v5 graphs does not exist** — exhaustive enumeration of all 2^15
labeled 6-vertex graphs leaves 0 unseen isomorphism classes, so a first-and-only graphs read
is impossible on this benchmark.

## Next useful work

1. **Drop in the official `neurips_2024.sty`** and compile for real (`research/paper/README.md`
   step 1). The preview is article-class only.
2. `tictactoe_n9` is still sealed and unclaimed; dense n=9 is ~30× the ring cost. If attempted,
   it needs its own protocol amendment and a fresh split, not a reuse of these.
3. If a third round asks for task-family variation: the honest blocker is that both families
   are 6-qubit and one is shortcut-dominated; a new family needs a protocol amendment *before*
   any pilot, and the `|L_t|/|S_n|` diagnostic computed first (it predicts whether a label gate
   can carry information before any model runs).
4. R3 (verifier-free defect gate) is a measured comparison on this benchmark, not a validated
   method — promoting it to a method claim needs a second dataset per family and a threshold
   sensitivity sweep.
5. Do not re-read any consumed split. `research/HOLDOUT_ACCESS.json` is the ledger;
   `holdout_deployed.py` refuses consumed splits unless `--allow-reread` is passed with a
   reason, and that flag writes to the ledger.

## Environment (non-persistent shells — set up in the same command)

```bash
module reset && module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
export LD_LIBRARY_PATH=/apps/software/2024a/software/Python/3.12.3-GCCcore-13.3.0/lib:$LD_LIBRARY_PATH
export OPENBLAS_NUM_THREADS=1
python3 -m research.compile_results2 --out research/results_summary2.md
python3 -m research.paper.check_numbers
python3 -m research.build_manifest --out research/MANIFEST.md
```
Tests: `python3 -m unittest discover -s research/core -p 'test_*.py'` (also
`research/search`, `research/experiments/repair`) — all green.
