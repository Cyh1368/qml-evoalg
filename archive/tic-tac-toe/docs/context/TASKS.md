# Task recipes

## Launch a local evolution run
1. `source shinka_cli_task/activate_eval_env.sh`
2. `python3 run_shinkaevolve_monitored.py --num-generations N --eval-preset quick` (`--eval-preset full` for converged-style local eval; use `cheap` LLM preset for smoke tests).
3. Output lands in `results/ttt_qml_cli_<timestamp>/`; tail `evolution_run.log` there for progress.
4. Verify: run completes, `programs.sqlite` has rows per generation, no repeated evaluator tracebacks in the log.

## Modify the seed ansatz / evaluator
1. Edit the notebook `tic_tac_toe_shinkaevolve_ansatz_search.ipynb` (NOT `shinka_cli_task/*.py` — they're regenerated).
2. Relaunch via `run_shinkaevolve_monitored.py`, which re-extracts.
3. Verify: `bash scripts/verify.sh`, then a 1–2 generation quick run.

## Analyze a completed run
1. `sqlite3 results/<run>/programs.sqlite '.tables'` then query (e.g., best scores per generation) — never read the DB or logs raw.
2. `python3 make_ansatz_report.py --results-dir results/<run>` → standalone HTML.
3. Live browsing: `python3 evolution_server.py` → http://localhost:5050.
4. Circuit diagram: `python3 display_circuit.py`.

## Cluster run (Yale Bouchet, SLURM)
1. SSH to bouchet (Duo 2FA; askpass workaround allowlisted in root `.claude/settings.local.json`; see memory file `bouchet-cluster-access`).
2. On the login node: `nohup python shinka_cluster/launch_shinka_cluster.py --generations N ... &` (uses `slurm_conda` job type and the converged eval protocol).
3. Monitor with `squeue`; fetch results back with the deploy/sync scripts noted in memory.
4. Verify: SLURM jobs complete, results dir synced locally, scores use the converged protocol.

## paper-replication experiments
Separate track: `cd paper-replication/`, use its `run_all.sh` / `analyze_results.py` / `make_report_figures.py`; each experiment produces a `*_REPORT.md` + figures. Read its existing reports before adding new ones.
