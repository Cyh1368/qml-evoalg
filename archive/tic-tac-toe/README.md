# Tic-Tac-Toe QML Ansatz Evolution

This folder contains a ShinkaEvolve search over quantum machine-learning ansatz blocks for a tic-tac-toe classification task, plus a `paper-replication/` analysis track.

## Main results (converged protocol — the only protocol valid for reported numbers)

- **Evolved winner** (`cemoid_ea_converged`, gen 16, program `b6ba28a0`, 66 params): combined score **0.7393**, test accuracy **0.787** on the winning seed; **0.730 ± 0.041 over 500 seeds** (`paper-replication/SU2_ROBUSTNESS_500SEED_REPORT.md`). The evolution rediscovered board-symmetry weight sharing (corner/edge/center orbit tying + CRZ ring + CRX hub) unaided.
- **Paper-ansatz baseline** (cemoid, 54 params, same geometry): **0.698 ± 0.042 over 500 seeds**.
- Full analysis reports live in `paper-replication/` (L/P sweeps, robustness, gate insertion, perturbation stability, degeneracy PCA); summary: `paper-replication/RESULTS_SUMMARY.md`.

> **Protocol warning:** quick-eval and converged-eval scores are **not comparable**
> (see `docs/context/GOTCHAS.md`). Quick-protocol numbers — including the
> historical headline `0.5984` of run `ttt_qml_cli_20260605_124906` — mis-rank
> candidates and must not be cited as results.

## File Structure

```text
.
├── README.md
├── tic_tac_toe_shinkaevolve_ansatz_search.ipynb
├── initial_program.py
├── evaluate.py
├── run_shinkaevolve_monitored.py
├── make_ansatz_report.py
├── activate_shinkaevolve_visualization.py
├── shinka_cli_task/
├── results/
├── logs/
├── reference-background-knowledge/
├── reference-exploiting-symmetry/
└── reference-qml_unitary_learning/
```

## Important Files

- `tic_tac_toe_shinkaevolve_ansatz_search.ipynb`: source notebook for the tic-tac-toe QML ansatz search.
- `initial_program.py`: seed candidate program. Only the `ANSATZ_SPEC` evolve block is intended to change during evolution.
- `evaluate.py`: ShinkaEvolve evaluator for candidate ansatz programs, including validation rules and scoring.
- `run_shinkaevolve_monitored.py`: extracts task files from the notebook, launches ShinkaEvolve, monitors progress, and stops stale runs.
- `make_ansatz_report.py`: builds the standalone HTML ansatz evolution report from a run directory.
- `activate_shinkaevolve_visualization.py`: launches the ShinkaEvolve web UI against the newest or selected local results database.

## Generated Task Files

- `shinka_cli_task/initial.py`: notebook-extracted seed program used by the CLI run.
- `shinka_cli_task/evaluate.py`: notebook-extracted evaluator used by the CLI run.
- `shinka_cli_task/shinka_config.json`: ShinkaEvolve task configuration.
- `shinka_cli_task/notebook_extract_manifest.json`: manifest recording extracted notebook files.
- `shinka_cli_task/activate_eval_env.sh`: helper for activating the evaluation environment.

## Results

- `results/ttt_qml_cli_20260605_124906/ansatz_report.html`: main standalone results report.
- `results/ttt_qml_cli_20260605_124906/programs.sqlite`: ShinkaEvolve program database for the main reported run.
- `results/ttt_qml_cli_20260605_124906/gen_*/`: per-generation source, patches, logs, and metrics.
- `results/ttt_qml_cli_20260605_124906/best/`: copied best candidate artifacts.
- `results/ttt_qml_cli_20260605_124906/evolution_run.log`: ShinkaEvolve run log.
- `results/ttt_qml_cli_20260605_124906/monitor.log`: monitor progress log.
- `results/ttt_qml_cli_20260605_124906/monitor_report.json`: structured monitor summary.
- `results/ttt_qml_*` and older `results/ttt_qml_cli_*` directories: earlier runs.

The HTML report for `ttt_qml_cli_20260605_124906` (best gen `10`, score `0.5984`) is a **quick-protocol historical artifact** — see the protocol warning above; the converged-protocol results in `paper-replication/` supersede it.

## Logs

- `logs/ttt_training/`: evaluator training logs and JSONL records.

## References

- `reference-background-knowledge/`: paper source, bibliography files, and figures used as background material.
- `reference-exploiting-symmetry/`: related symmetry paper source and figures.
- `reference-qml_unitary_learning/`: reference Shinka/QML unitary learning example.

## Useful Commands

Regenerate the main HTML report:

```bash
python3 make_ansatz_report.py --results-dir results/ttt_qml_cli_20260605_124906
```

Run a monitored ShinkaEvolve search using the default quick evaluator preset:

```bash
python3 run_shinkaevolve_monitored.py --num-generations 20 --eval-preset quick
```

Preview which database the ShinkaEvolve visualization UI would serve:

```bash
python3 activate_shinkaevolve_visualization.py --dry-run
```

## Local Artifacts

The folder also contains local/generated artifacts such as `.venv-shinka-ttt/`, `__pycache__/`, Jupyter/IPython runtime directories, `.pip-cache/`, and `:Zone.Identifier` files. These are environment or platform artifacts, not primary project source.
