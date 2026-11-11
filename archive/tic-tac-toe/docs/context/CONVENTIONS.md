# Conventions

- **Plain-script style**: standalone Python scripts with `argparse` CLIs and module-level constants in CAPS (e.g., `LLM_PRESETS`, `DEFAULT_EVAL_PRESET` in `run_shinkaevolve_monitored.py`). No packages, no `src/` layout, no type-checking.
- **Config via env vars**: training hyperparameters (`N_EPOCHS`, `BATCH_SIZE`, `LEARNING_RATE`, `CONVERGENCE_THRESHOLD`, seeds, thread caps) are exported by `shinka_cli_task/activate_eval_env.sh` and read with `os.environ.get(..., default)` in `evaluate.py`. Add new knobs the same way — env var with a sane default, documented in the activate script.
- **Evolve-block edits**: candidate ansatz changes live only between the `EVOLVE-BLOCK-START/END` markers around `ANSATZ_SPEC` in `initial.py` (source: notebook). Gates limited to the schema in `shinka_config.json`'s `task_sys_msg`; two-qubit gates only on the 12 grid edges; total params ≤ 768.
- **Logging**: long-running drivers write both a `.log` file (tee'd) and per-run artifacts under `results/<run>/`; training emits JSONL to `logs/ttt_training/`. Follow that pattern for new long jobs.
- **Reports**: analysis outputs are standalone artifacts (self-contained HTML via `make_ansatz_report.py`, or markdown `*_REPORT.md` + PNG figures as in `paper-replication/`). One report per experiment, named after the experiment.
- **Naming**: results dirs `ttt_qml_cli_<YYYYMMDD_HHMMSS>`; seed-specific logs `candidate_seed_<seed>.jsonl`.
- **Commits**: short lowercase imperative-ish messages (history is minimal). Commit code and docs; never commit the venv or in-flight run mutations you didn't create.
