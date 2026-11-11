# HANDOFF — qml-evoalg research continuation

Working dir: `/home/cpsc4710_ch2499/qml-evoalg`. Read `research/README.md`,
`research/extension_plan.md` (the executed protocol), `research/CLAIMS.md`,
`research/experiment_plan.md`, `research/core/INTERFACES.md` before acting.

## Goal
Turn the audited continuation plan into publishable evidence for: **verified
symmetry hypotheses + causal repair in LLM-guided quantum circuit search**.
Rigor bar is already set by the plan (orbit-disjoint splits, matched budgets,
paired run-level CIs, locked holdouts, negative controls). Do not let claims
outrun the paired evidence.

## State
- **WP-CORE** (`research/core/`): COMPLETE and green (36 tests). The previously
  **missing `train.py`** is implemented + unit-tested (6 tests in `test_train.py`).
- **WP-TTT** (`research/datasets/tictactoe/`): generated + validated. Its single
  validation "FAIL" is by-design (center-cell sham control is D4-invariant; the
  corner counterfactual `winner_designated_corner` is the real D4-breaking target,
  violated fraction 0.375). See `validation.json`.
- **WP-REPAIR** (`research/experiments/repair/`): IMPLEMENTED + unit-tested
  (`test_repair.py`, 6 tests). Key design: confound-free targets
  `y_eta = h + eta*b` with `h` = dataset ground-truth invariant `alpha_0` and `b`
  = group-centred random direction (Reynolds projection via the EXPLICIT D6
  closure, NOT the dataset `orbit` labels which are singletons for ring). Three
  matched arms trained with a FIXED symmetric readout (only 3 block params):
  `original` (15 CRZ, asymmetric), `repaired` (30 CRZ, exactly equivariant,
  residual ~1e-15), `control` (30 CRZ, asymmetric, family-equivalent to original).
  `repaired` vs `control` isolates symmetry from gate count. Analytic floor
  `eta^2 E[b^2]` verified == empirical floor. **RUNNING** as job `32873697`
  (ring_n6, 3 teachers x 3 etas x 8 opt seeds x 3 arms, steps=200, max_train=256,
  ~3.6h). Early stdout: at eta=0 repaired dev <= control dev (expected pattern).
- **WP-SEARCH** (`research/search/`): harness works on the cluster (real LLM
  smoke: 12/12 clean `llm-verify` runs). **Pilot RUNNING** as 5 grid jobs
  (`run_grid.py`/`job_grid.sh`, one job per arm): arms random, mutation-ea,
  llm-fitness, llm-verify, llm-verify-repair; families ring_n6, graphs_n6;
  LLM arms x 3 treatments (ycrc-local/none, ycrc-local/medium,
  ycrc-local-think/medium); 3 paired seeds 20261110-12; budget 12, steps 120,
  max_train 256. Output `logs/runs_pilot/` (66 runs expected). Analysis tool
  `research/search/analyze.py` (paired run-level bootstrap CIs, Holm) is READY.
- **WP-PAPER**: `analyze.py` done; `manuscript.md` pending final numbers.

## Files changed this session
- `research/core/train.py` — NEW. `fit`/`Fit.predict`/`risk` per INTERFACES.md;
  Adam+MSE, readout `f=w·<O>(x)+b`, seeded init, bitwise determinism; gradients
  via `simulator.Forward.grad`; vectorized structure-grouped `batched_expectations`
  for fast full-validation risk.
- `research/core/test_train.py` — NEW. batched-vs-reference (3 families),
  gradient-vs-central-diff, determinism, progress.
- `research/core/test_tasks_candidates.py` — fixed infinite loop in `_d4_closure`
  (was re-appending processed elements → hung the whole suite) + 2 target-key /
  split-mask test bugs.
- `research/search/harness.py` — added `--steps` and `--max-train` (protocol
  defaults 200/None preserved); threaded into `run_search`→`train.fit`, logged.
- `research/search/job_search.sh` — passes `STEPS`, `MAX_TRAIN`, `EFFORT` env
  overrides to the harness.
- `logs/` — local test/probe logs (disposable). `.venv/` — local test venv.

## Commands and tests (all PASS)
Run from repo root with the venv (agent node has no numpy on default path):
```
L=/apps/software/2024a/software/Python/3.12.3-GCCcore-13.3.0/lib
env LD_LIBRARY_PATH=$L OPENBLAS_NUM_THREADS=1 PYTHONPATH=$PWD \
  .venv/bin/python -u -m unittest discover -s research/core   -p 'test_*.py'   # 36 OK
env LD_LIBRARY_PATH=$L OPENBLAS_NUM_THREADS=1 PYTHONPATH=$PWD \
  .venv/bin/python -u -m unittest discover -s research/verifier -p 'test_*.py' # 7 OK
env LD_LIBRARY_PATH=$L OPENBLAS_NUM_THREADS=1 PYTHONPATH=$PWD \
  .venv/bin/python -u -m unittest discover -s research/search  -p 'test_*.py'  # 14 OK
```
- Gradient check: max abs err 1.4e-11. Batched predict == per-row reference (1e-10).
- Real LLM endpoint verified in a Slurm job: `ycrc-local` OK (~0.3s, correct JSON).
- Per-`fit` cost (steps=200, batch=32, full train): ring_n6 ≈88s, graphs_n6 ≈88s,
  **tictactoe_n9 (n=9) very slow** → use ring+graphs as the two DEVELOPMENT
  families; reserve tictactoe as the HELD-OUT transfer family (matches plan).
- Dataset sizes: graphs train 19739 / val 6217; ring 720/240; ttt 904/316.
  Full graphs validation risk eval ≈30s/candidate (batched).

## Slurm jobs (as of handoff)
- `32873697` day `wp-repair` — WP-REPAIR decisive experiment (see above).
- `32867567..71` day `wp-grid` — WP-SEARCH pilot, one per arm (random,
  mutation-ea, llm-fitness, llm-verify, llm-verify-repair).
- `32826379` agent — THIS session. `32820860` agent — older session (not mine to
  kill). `32848443` day `cglm-*` — user's parallel work (do NOT touch).
- Per-user CONCURRENT job limit is real; submit grid-style single jobs (loop
  internally) rather than many arrays. Batch output goes to the SHARED repo path
  (`-o logs/...`), never `/tmp` (compute-node `/tmp` is node-local). `job_*.sh`
  scripts now `cd "$SLURM_SUBMIT_DIR"` (the old `$(dirname $0)` cd failed in Slurm).
- When pilot + repair finish: run
  `python3 -m research.search.analyze --dir logs/runs_pilot --out research/search/pilot_analysis.json`
  and read `research/experiments/repair/repair_results.json` (has a `contrasts`
  block). Then write `research/manuscript.md` and update `CLAIMS.md`.

## Results so far (executed)
- **WP-REPAIR (DECISIVE, done):** `research/experiments/repair/repair_results.json`
  (n=24 paired = 3 teachers x 8 seeds, ring_n6, D6). Repaired (exactly equivariant,
  channel residual 0) vs gate-count-matched control (asymmetric): at eta=0 repaired
  better (mean diff -0.00093, CI[-0.0016,-0.0004]); at eta=1 repaired WORSE
  (+0.045, CI[+0.032,+0.058], pinned at invariant floor 0.866). control ~= original
  throughout (validates control). => symmetry enforcement causally helps iff the
  target is invariant. Analysis: `analyze()` in the module / `compile_results.py`.
- **WP-SEARCH (PILOT, done):** `research/search/pilot_analysis.json` (48 runs, n=3).
  Verifier feedback did NOT reduce dev-selected risk (slightly worse all cells);
  verify-repair (inference-time Reynolds averaging) DID reduce risk. Pilot only.
  NOTE: pilot had a filename collision (effort not in filename) collapsing 3
  treatments to 2; FIXED in harness.py/run_grid.py for the confirmatory run.
- `research/results_summary.md` (auto-compiled) and `research/manuscript.md`
  (skeleton + results) are written; `CLAIMS.md` updated to the evidence.

## Confirmatory WP-SEARCH (DONE)
Jobs `32906227..31` COMPLETED (120 runs, 24/arm = 12 seeds x 2 families, 1
treatment ycrc-local/none, budget 12). Results in
`research/search/confirm_analysis.json` + `results_summary.md`. PRIMARY = NULL
(verifier vs fitness: CI includes 0 both families). LLM beats baselines on ring
(Holm p<0.001) not graphs. Manuscript 5.2 and CLAIMS.md updated to this.

## Optional next steps (not yet done)
- One-shot transfer evaluation on the held-out `tictactoe_n9` family (locked
  holdout, evaluate once) to answer the transfer question.
- `git commit` the new code so future run provenance records a commit containing
  `train.py`/repair/analysis (current JSONs record a37fc2d6, pre-code).
- Third model treatment (ycrc-local/medium) in a future confirmatory run.

## Environment
- Batch: `module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a`
  (numpy 1.26.4, scipy 1.13.1). LLM arms additionally `module load ycrc-llm/1.0`.
  Stdlib+numpy+scipy only; `OPENBLAS_NUM_THREADS=1`. Use `module reset` (never purge).
- CPU batch → `partition=day`; short dev → `devel`. `gpu_devel` NOT used (no GPU
  work; idle-GPU policy). See `extension_plan.md` "Cluster note".
- Local agent-node testing: `.venv/bin/python` with
  `LD_LIBRARY_PATH=/apps/software/2024a/software/Python/3.12.3-GCCcore-13.3.0/lib`.

## Next steps
1. **Free a job slot** (user cancels stale agent `32820860`, or confirms it's safe
   to cancel). Then:
2. **WP-SEARCH pilot** via `research/search/job_search.sh` (array, `partition=day`):
   5 arms × {`graphs_n6`,`ring_n6`} × 3 paired seeds; LLM arms × 3 treatments
   (`ycrc-local`/none, `ycrc-local`/medium, `ycrc-local-think`/medium);
   `STEPS=120 MAX_TRAIN=256 BUDGET=12`. Output to `logs/runs_pilot/`. First re-run
   one real `llm-verify ring_n6` cell to measure wall time, then launch full arrays.
3. **WP-REPAIR**: implement `research/experiments/repair/repair_experiment.py`
   per `extension_plan.md` WP-REPAIR + `training_review.md` "next decisive test":
   `y_eta = h + eta*b` (b group-centered, orbit-variance-normalized), analytic
   invariant floor `eta^2 E[b^2]`, continuous circuit breaking `H_eps`, gate-count-
   matched control (repeated half-angle same-direction CRZ), phase-shift sham,
   >=8 paired optimizer seeds, >=3 frozen teacher draws, select on train only,
   locked holdout evaluated exactly ONCE. Run as CPU batch on `day`.
4. **WP-PAPER**: `research/search/analyze.py` (paired run-level bootstrap CIs,
   Holm within secondary families), figures, `research/manuscript.md`, update
   `CLAIMS.md` to only what paired evidence supports.

## Integrity rules (do not violate)
- `datasets/locked_holdout/` and `datasets/tictactoe/locked*` stay sealed until the
  single confirmatory evaluation; `research/search/` must never read locked paths
  (harness `check_locked_path` enforces this).
- Every result JSON records seeds, module versions, git commit, host.
- Report negative/null results as such; don't relabel reused dev/test as confirmation.
