# Architecture

```
tic_tac_toe_shinkaevolve_ansatz_search.ipynb   # SOURCE OF TRUTH for task code
        │ (cells extracted by run_shinkaevolve_monitored.py)
        ▼
shinka_cli_task/            # generated: initial.py (ANSATZ_SPEC evolve block),
                            # evaluate.py (trainer/scorer), shinka_config.json,
                            # activate_eval_env.sh (env + hyperparams + API key)
        │
        ▼
ShinkaEvolve (installed in .venv-shinka-ttt; shinka.core/.database/.launch)
  LLM proposes ANSATZ_SPEC mutations → evaluate.py trains/scores → programs.sqlite
        │
        ├── results/ttt_qml_cli_<timestamp>/   # per-run: programs.sqlite, gen_N/,
        │                                      # bandit_state.pkl, evolution_run.log
        ├── logs/ttt_training/                 # per-candidate training JSONL
        ▼
evolution_server.py (Flask dashboard :5050)  |  make_ansatz_report.py (static HTML)
```

## Components

- **Task spec**: 9-qubit PennyLane circuit; feature map `RX(2π/3·cell)`, data re-uploading l=3, evolve block repeated p=2. Only `ANSATZ_SPEC` (a gate-list schema) evolves. Constraints (12-edge grid connectivity, MAX_PARAMS=768) validated in `evaluate.py`.
- **Local driver**: `run_shinkaevolve_monitored.py` — extracts notebook, launches monitored ShinkaEvolve run; LLM presets `cheap`/`expensive` (UCB1 model selection, `max_api_costs` cap), eval presets `quick`/`full`.
- **Cluster driver**: `shinka_cluster/launch_shinka_cluster.py` — SLURM on Yale Bouchet (`job_type="slurm_conda"`); uses the *corrected converged* eval protocol (full data, val-loss early stopping, restore-best-weights).
- **Visualization**: `evolution_server.py` (live tree/PCA/score timeline from programs.sqlite), `activate_shinkaevolve_visualization.py` (stock viz picker), `display_circuit.py`.
- **Reporting**: `make_ansatz_report.py` → standalone HTML report per results dir.
- **paper-replication/**: independent sub-project (gate insertion, seed robustness, L/P sweeps, optimizer benchmarks, SU2 analyses) with its own `cluster/`, `run_all.sh`, and `*_REPORT.md` files. Does not share code with the ShinkaEvolve pipeline.

## Key data

- Canonical reported run: `results/ttt_qml_cli_20260605_124906` (see README; best gen 10, score 0.5984). Later run dirs exist and may supersede it — check DECISIONS/MEMORY.
- `programs.sqlite` schema: query with sqlite3, never read raw.
