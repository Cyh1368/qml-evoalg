# Experiment and provenance record (2026-11-11)

Written for referee requirement 11 ("make the experimental record independently
reproducible"). Every statement below is checkable with the commands at the end.

## 1. Model identity (replaces the bare alias `ycrc-local`)

| field | value |
|---|---|
| alias used in code | `ycrc-local` (and `ycrc-local-think`, unused in the 120-run study) |
| served model behind the alias | **`Qwen3.8-Flash-Next`**, root `/apps/software/openwebui_models/Qwen3.8-Flash-Next-FP8` (FP8 weights) |
| server | vLLM, OpenAI-compatible, endpoint `http://a1127u31n01.mghpcc.ycrc.yale.edu:8008/v1`, `max_model_len = 262144` |
| module that sets endpoint + key | `ycrc-llm/1.0` (EasyBuild module; no software installed) |
| decoding settings actually sent | `model=ycrc-local`, `reasoning_effort="none"`, **no** `temperature`, **no** `max_tokens`, **no** `top_p` (server defaults apply) |
| client | stdlib `urllib` (`research/search/llmclient.py`), timeout 180 s, max 8 retries with exponential backoff (base 1 s) on timeout/connection/429/5xx |
| retries observed | **0**: all 584 calls in the 120-run study succeeded on attempt 1 (mean latency 2.75 s) |
| prompt templates | frozen in `research/search/prompts.py` (recorded in each run log's `proposals[*].summary` and prompt token counts) |

**Disclosed limitation.** The gateway exposes no immutable checkpoint revision or weight
hash (`/v1/models` reports only the alias, root path and a `created` field that tracks
the query time, not the deployment). The strongest available pin is therefore
*alias + root path + FP8 + module version + run date*, and that is what the paper
reports. A rerun is reproducible only against the same deployment; we do not claim
bit-level reproducibility of the model.

## 2. Compute and inference budget (not just candidate counts)

From the 120 confirmatory run logs (`logs/runs_confirm/run_*.json`):

| quantity | value |
|---|---|
| LLM calls | 584 |
| tokens | 1,294,840 total = 829,452 prompt + 465,388 completion |
| proposals | 1,448 total, 1,440 valid, **8 invalid (0.55 %)** — invalid retained in the denominator |
| evaluated candidates per run | 12 (budget `B = 12`), 120 runs |
| parameter-training budget per candidate | identical across arms: Adam, `steps = 120`, `max_train = 256`, batch 32, lr 0.05 |
| wall time | 18.1 core-hours total (random 15,776 s, mutation-ea 16,952 s, llm-fitness 16,555 s, llm-verify 7,714 s, llm-verify-repair 8,079 s) |
| inference-time Reynolds averaging | adds `|G|` predictor evaluations per deployed prediction (12 for `ring_n6`; the graphs repairs used the proposal's own subgroup, order 6). The cost is **not** hidden: it is charged to the arm that uses it and reported with the E-S1/E-S2 effect. |

Monetary cost is zero (internal serving), so tokens and wall time are the reported
budgets.

## 3. Dated chain: what was committed before which result

| UTC | event | evidence |
|---|---|---|
| 2026-11-10 19:36 | datasets + sealed splits generated (seed 20261110) | `research/datasets/manifest.json`, file mtimes |
| 2026-11-11 02:23–05:38 | **pilot** search runs (48) | run-log `timestamp` fields, Slurm `32867567..71` |
| 2026-11-11 02:53–06:03 | **WP-REPAIR v1** (exploratory, 216 fits) | Slurm `32873697`, `repair_results.json` |
| 2026-11-11 06:09–10:48 | **confirmatory** search runs (120) | run-log `timestamp` fields, Slurm `32906227..31` |
| 2026-11-11 14:04 | first git commit that contains `extension_plan.md`, `train.py`, `harness.py`, `analyze.py` | `git log --diff-filter=A` → `e983f2d5` |
| 2026-11-11 16:19 | **locked-holdout metadata-only inspection** (see §5) | this file |
| 2026-11-11 16:20 | **revised protocol frozen** | commit `ecd1be7246f6ee74e8605b38ddaafa654dd7c6b7` |
| 2026-11-11 17:10 | WP-REPAIR-2 code committed, then job submitted | commit `1b7aafde`, Slurm `32982225` |
| 2026-11-11 17:21 | corrected search analyses committed, then job submitted | commit `7d7b4202`, Slurm `32983298` |
| after the above | one-shot holdout evaluation | Slurm job recorded in `research/HOLDOUT_ACCESS.json` |

**Two provenance defects found in the old record, stated plainly:**

1. Every run/result JSON records `metadata.git_commit = a37fc2d6`, but `a37fc2d6`
   **does not contain** `research/core/train.py`, `research/search/harness.py`,
   `research/search/analyze.py` or `research/experiments/repair/*` — the code was
   uncommitted when the jobs ran, so `git rev-parse HEAD` named an ancestor commit.
   The recorded commit therefore identifies the repository state, not the code that
   produced the numbers. Fix: all code is now committed, and the new jobs record
   commits that do contain their code (`1b7aafde`, `7d7b4202`); the old pilot/confirm
   records are labelled "commit field unreliable; code first committed at `e983f2d5`".
2. `extension_plan.md` says "All choices here were frozen before any new outcome was
   seen", but its first **dated** appearance in git (`e983f2d5`, 2026-11-11 14:04 UTC)
   is *after* the pilot (02:23–05:38) and confirmatory (06:09–10:48) runs. Its file
   mtime (2026-11-10 19:49) is consistent with earlier authorship but is not evidence:
   mtimes are trivially mutable. **Consequence:** the 120-run search study is reported
   as *protocol-consistent but not verifiably pre-registered*, and the manuscript's
   blanket "all results are prospective and pre-declared" sentence is removed. The
   WP-REPAIR-2 / dev-analysis / one-shot-holdout chain **is** verifiably pre-registered:
   the protocol commit `ecd1be72` (16:20:02Z) precedes the job submissions
   (17:10Z, 17:21Z) and every result of that chain.
3. **`git_commit` in `repair2_results.json` (`c62a3e26`, committed 17:50:42Z) postdates the
   run** (submitted 17:10:06Z, started 17:30:45Z, finished ~18:00Z), because the job runs from
   the working tree and stamps metadata when it *finishes*. The field therefore names HEAD at
   completion, not the code at start. What rescues the claim is a file-level check:
   `research/experiments/repair/repair_experiment2.py` was last modified at `1b7aafde`
   (17:10:06Z) and not touched again until 18:05Z, so the code that ran is exactly
   `1b7aafde`'s version; the same holds for `research/core/*` used by it. **Fix going
   forward:** stamp `git rev-parse HEAD` at submit time in the job wrapper and record
   `sha256` of the experiment module, so code identity does not depend on completion order.
4. **The first one-shot E-R4 evaluation was invalid for `eta > 0`** (job `32984980`, finished
   18:01:38Z): the evaluator scored every arm against a single `alpha_0` label per split, and
   the sealed files' `alpha_*` labels use a different breaking function from the experiment's.
   Detected because `eta = 1` risks came out at $0.019$ where the invariant floor is $\approx
   1.0$. Consequences, policy and remedy are recorded in `REVISED_PROTOCOL.md` Addendum A4:
   the v1/v2 ring splits stay consumed, the defective numbers are not reported, the evaluator
   now refuses those splits, a third inputs-only holdout (seed 20261203, sha256
   `a82280545dd6741c7650cfb83eee7a4cf326606dac266be46bd9aa2161781bc4`) is evaluated once, and a
   self-check must reproduce the experiment's own development risk to `1e-9` first.

## 4. Artefacts released with the analysis

* raw per-run records: `logs/runs_confirm/run_*.json` (120), `logs/runs_pilot/run_*.json` (48)
  — each contains every proposal (valid and invalid), validation errors, verifier
  reports, token/latency/attempt logs, the selected candidate and the fit protocol;
* dataset generation seeds and split masks: `research/datasets/manifest.json`
  (seed 20261110, orbit-disjoint splits), `research/datasets/locked_holdout_v2/manifest.json`
  (seed 20261112, sha256, zero orbit overlap);
* result records: `research/experiments/repair/repair_results.json` (v1, exploratory),
  `research/experiments/repair/repair2_results.json` (corrected),
  `research/search/confirm_analysis.json` (v1 statistics, superseded),
  `research/search/confirm_analysis2.json` (corrected),
  `research/search/dev_analysis.json`, `research/HOLDOUT_RESULTS.json`;
* one exact command per table: `research/paper/main.tex` appendix and
  `research/compile_results.py`.

## 5. Locked-holdout access record

* `research/datasets/locked_holdout/{ring_n6,graphs_n6}.npz` and
  `research/datasets/tictactoe/locked_holdout/*` were created 2026-11-10 19:36/19:55 UTC
  and are read by no code path under `research/search/` (enforced by
  `check_locked_path`, `LOCKED_FORBIDDEN_IN`).
* **Incident (2026-11-11 ~16:19 UTC, before the protocol freeze commit at 16:20 UTC):**
  while sizing the one-shot evaluation, `research.core.tasks.load_family(...,
  locked=True)` was called for `ring_n6` and `graphs_n6` to inspect **keys and row
  counts**. The LOCKED banner printed; the call is reproducible from the shell history of
  that session. No label value was printed, and no design choice in
  `REVISED_PROTOCOL.md` depends on the inspected quantities (the design fixes arms,
  seeds, splits and estimands, none of which are derived from test data).
* **Remedy, rather than argument:** a second holdout was generated *after* the freeze
  (`research/datasets/locked_holdout_v2/ring_n6.npz`, seed 20261112, 4000 rows, zero
  canonical-orbit overlap with any development or v1-test row, sha256
  `2f813e71962354d0ddf42026a7fb27a83743b676127e2eeb76022db667a7f9c7`, file mode 0444).
  The WP-REPAIR-2 test evaluation is reported on **both** splits, and the fresh one is
  the primary untouched result. The v1 splits are still evaluated exactly once for
  outcomes, with sha256 recorded before and after
  (`research/HOLDOUT_ACCESS.json`).
* `tictactoe_n9` remains sealed and unclaimed (dense `n = 9` simulation is ~30x the ring
  cost and is outside this revision's compute budget).
* **Split ledger after the second review round** (machine-readable in
  `research/HOLDOUT_ACCESS.json`, human-readable in `research/MANIFEST.md`):
  v1 consumed (search E-S7 + the defective first E-R4 + the A5.5 graphs second read);
  v2 consumed; v3 consumed by an aborted run, inputs-only so no label was exposed;
  v4 consumed by the corrected E-R4'; v5 ring consumed once by the A5.5 deployed-endpoint
  run, and its graphs half **does not exist** because exhaustive enumeration leaves 0
  unseen isomorphism classes.
* **Authorised second read (2026-11-12 02:03 UTC, job 33044945).** `graphs_v1` was read a
  second time for the A5.5 deployed endpoint. This is not a silent exception: the run
  command passes `--allow-reread graphs_v1` with the reason written into the command
  itself, the module refuses any consumed split without that flag (verified by running it:
  `REFUSING to read consumed split(s): graphs_v1`), the reason and digests are appended to
  the shared ledger, and every table containing those numbers labels them *second read,
  post hoc*. The justification is structural, not convenient: a first-and-only graphs read
  is impossible on this benchmark.
* **Aborted attempt, recorded (job 33042529, 2026-11-12 01:50 UTC).** The A5.5 module crashed
  in its own digest helper (`hashlib.sha256` handed a `pathlib.Path` because
  `hasattr(path, "read_bytes")` is true for `Path`). The crash occurred at the digest step,
  *before* the first sealed `np.load`, so no held-out value was read; the fix and its lesson
  are in the helper's docstring and in `research/core/test_paired.py`'s sibling audit notes.
  We record it because an aborted one-shot attempt is exactly the kind of event a clean
  provenance table tends to lose.

## 6. Reproduce / verify

```bash
# dated chain
git log --format="%h %ad %s" --date=iso -8
git log --diff-filter=A --format="%h %ad" --date=iso -- research/extension_plan.md
git ls-tree -r --name-only a37fc2d6 | grep -c "research/core/train.py"   # 0 -> defect 1
# budgets
python3 -m research.search.analyze2 --dir logs/runs_confirm --out /tmp/a.json
# sealed integrity (does not read labels)
sha256sum research/datasets/locked_holdout/*.npz research/datasets/locked_holdout_v2/*.npz
# model identity (inside a Slurm job, module loaded)
module load ycrc-llm && curl -sS -H "Authorization: Bearer $(id -un).api" \
  "$OPENAI_BASE_URL/models" | python3 -m json.tool | head -20
# jobs actually used
sacct -j 32982225,32983298 --format=jobid,jobname,state,start,end,ncpus,TotalCPU,Elapsed
```
