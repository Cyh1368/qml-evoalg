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
- **Tree**: x = generation, node color = combined score, ring = patch type.
  Hover a node for score/metrics; click it to load the detail panels.
- **Patch notes** panel: the LLM's own name + description for each change,
  with evaluator feedback below it.
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

## Alternative: ShinkaEvolve's stock WebUI

The original `programs.sqlite` files are committed, so ShinkaEvolve's own
interactive viewer works directly on them (needs the `shinka_evolve` package
installed and internet access for its CDN assets):

```bash
shinka_visualize . --port 8888 --open
```

It adds embedding/MAP-Elites views but has no circuit rendering and needs a
live server; this static page is the recommended entry point.
