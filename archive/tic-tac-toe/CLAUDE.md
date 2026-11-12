# tic-tac-toe — ShinkaEvolve QML ansatz search

Evolutionary (LLM-driven, ShinkaEvolve) search over quantum ansatz "evolve blocks" for a 9-qubit PennyLane tic-tac-toe classifier. Only the `ANSATZ_SPEC` evolve block is searched; the surrounding circuit (feature map, data re-uploading l=3, p=2 repeats, 12-edge grid connectivity) is frozen by design.

## Start every session

Read `docs/context/MEMORY.md` and `docs/context/DECISIONS.md` before starting. Append to them when you learn durable facts or make architectural choices.

## Environment & commands

- Env: `source shinka_cli_task/activate_eval_env.sh` (activates `.venv-shinka-ttt`, sets training hyperparameter env vars). No conda; no requirements.txt — the venv is the environment.
- Run local evolution: `python3 run_shinkaevolve_monitored.py --num-generations N --eval-preset quick|full`
- Dashboard: `python3 evolution_server.py` (port 5050)
- Report: `python3 make_ansatz_report.py --results-dir results/<run>`
- Verify changes: `bash scripts/verify.sh` (compile-checks scripts, validates config JSON, smoke-imports the evaluator). There is no test suite or linter.

## Hard boundaries

- Never modify: `results/`, `logs/`, `*.sqlite*`, `*.pkl`, `.venv-shinka-ttt/`, `reference-*/`.
- `shinka_cli_task/{initial.py,evaluate.py}` are **generated** from the notebook by `run_shinkaevolve_monitored.py` — edit the notebook, not the extracts.
- Never open large files wholesale: run logs (MB-scale), `programs.sqlite`, notebooks — sample with head/tail/queries.
- `shinka_cli_task/activate_eval_env.sh` contains a live API key — never print, copy, or commit it elsewhere.

## Conventions

- Python, no enforced formatter/linter. Match existing style (plain scripts, argparse, env-var-driven config).
- Two-qubit gates only on the 12-edge grid adjacency; param cap `MAX_PARAMS = 768`. Constraints are enforced by `evaluate.py`.
- Local "quick" eval and cluster "converged" eval protocols differ deliberately — never compare scores across them (see GOTCHAS).

## Pointer index

- Architecture & data flow → `docs/context/ARCHITECTURE.md`
- Common task recipes (launch run, analyze, cluster) → `docs/context/TASKS.md`
- Footguns → `docs/context/GOTCHAS.md`
- Coding patterns → `docs/context/CONVENTIONS.md`
- Decision log → `docs/context/DECISIONS.md`
- Durable facts / agent memory → `docs/context/MEMORY.md`
- Skill: `run-evolution` — launch/monitor a local ShinkaEvolve run
- Skill: `analyze-run` — inspect a results dir, query programs.sqlite, build reports
- Skill: `cluster-run` — SLURM runs on Yale Bouchet via `shinka_cluster/`
- `paper-replication/` is a separate experimental track with its own reports; see ARCHITECTURE.md pointer.
