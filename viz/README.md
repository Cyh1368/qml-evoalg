# Evolution Run Viewer

Static web page for analyzing ShinkaEvolve runs across all three tasks
(T1 tic-tac-toe, T2 S_n graph, T3 SU(2) Hamiltonian): the evolutionary tree,
per-node patch notes, circuit structure, metrics, and code diffs.

## View the results (no install needed)

```bash
cd viz
python3 -m http.server 8080
# open http://localhost:8080
```

Opening `viz/index.html` directly via `file://` also works.

Usage:
- **Run picker** (top left): switch between runs, grouped by task.
- **Tree**: x = depth in the lineage (not generation, which skips ahead and
  stretched edges across empty columns); the generation range each depth column
  covers is labelled on the axis. Node color = combined score, ring = patch type.
  Hover a node for score/metrics; click it to load the detail panels.
- **Score vs. generation**: the y range is editable — type a min and/or max to
  zoom in on a band of scores, "Auto" restores the data-fitted range.
- **Patch notes** panel: the LLM's own name + description for each change,
  with evaluator feedback below it. The **sources** strip at the top names the
  diff base (`parent_id`, the program the diff applies to) and any inspiration
  programs the model was also shown. For a `cross` patch those inspirations are
  the merge partners, which the diff itself never mentions. Every source is
  clickable, and selecting a node draws dashed arrows from its sources in the
  tree. The **Code diff** card states which program the diff is against.
- **Trace lineage**: highlights the ancestor walk from the selected node back
  to the root and lists each step's patch note and score delta. "Trace best"
  does this for the run's best program. This is the intended way to look for
  signals that build up before a phase transition (e.g. the gen-33 jump in
  `sn-transfer-gpt56sol_r2`).
- **Score chart**: per-program dots + best-so-far line, synced with the tree.

## Rebuild the data

`viz/data/` is generated from every non-empty `programs.sqlite` in the repo
(paths, tasks, and models are derived from directory names; byte-identical
duplicate databases are skipped):

```bash
python3 viz/build_data.py --repo-root . --out viz/data
```

To add newly-extracted scalar fields to an existing `viz/data/` without paying
for a full re-render, `viz/backfill_inspirations.py` rewrites the run files in
place with the `archive_inspiration_ids` / `top_k_inspiration_ids` columns
(matching each run to its database by program-id set, not by name):

```bash
python3 viz/backfill_inspirations.py --repo-root . --data viz/data
```

Circuit SVGs are rendered at build time with PennyLane. The script looks for
an interpreter that can `import pennylane` (`viz/.venv_render`,
`tic-tac-toe/.venv-shinka-ttt`, then the running Python); to create one:

```bash
python3 -m venv viz/.venv_render
viz/.venv_render/bin/pip install pennylane matplotlib numpy "autoray==0.6.11"
```

Without PennyLane the build still works; circuits are just omitted.
Known gap: 16 programs in `su2-transfer-v3-gpt56sol` reference a
dataset-derived `READOUT_PAIRS` constant and cannot be rendered statically.

## Null-control runs (`transfer-sn/null/`, variant `transfer-null`)

Runs under `transfer-sn/null/` are a **null control** trained on
`transfer_sn_null/dataset.npz`, a different dataset from the main S_n transfer
task. Sync them with `viz/sync_null_runs.sh` (it refuses to copy a run whose
orchestrator is still on the cluster, and WAL-checkpoints the sqlite first).

**Their scores are NOT comparable to the real-task runs.** `evaluate.py`
affine-rescales the raw score with anchors hardcoded from the *original* task
(`SCORE_ANCHOR_SEED=0.8546`, `SCORE_ANCHOR_BEST=0.9483`), and those anchors were
not re-measured for the null dataset. The null task is much easier (linearly
separable to 97% vs 87%), so its seed alone scores raw 0.9717 -> **1.249 on the
rescaled axis**, i.e. already above the best solution ever found on the real
task. Read null-arm scores as raw values or re-anchor them; do not put them on
the same axis as `transfer` runs.

## Alternative: ShinkaEvolve's stock WebUI

The original `programs.sqlite` files are committed, so ShinkaEvolve's own
interactive viewer works directly on them (needs the `shinka_evolve` package
installed and internet access for its CDN assets):

```bash
shinka_visualize . --port 8888 --open
```

It adds embedding/MAP-Elites views but has no circuit rendering and needs a
live server; this static page is the recommended entry point.
