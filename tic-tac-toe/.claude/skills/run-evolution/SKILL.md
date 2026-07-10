---
name: run-evolution
description: Use this skill when the user asks to launch, resume, or monitor a local ShinkaEvolve ansatz-search run (e.g. "start an evolution run", "run N generations", "kick off a quick/cheap run").
---

Scope: may touch `run_shinkaevolve_monitored.py`, the notebook, and read `shinka_cli_task/`. Never edit `shinka_cli_task/initial.py`/`evaluate.py` directly (regenerated from the notebook) or anything under `results/`, `logs/`.

1. Check for a live run first: `cat *.pid 2>/dev/null` and `ps aux | grep shinka` — don't double-launch; the driver kills stale runs itself.
2. `source shinka_cli_task/activate_eval_env.sh`.
3. Launch in background: `python3 run_shinkaevolve_monitored.py --num-generations N --eval-preset quick` (add cheap LLM preset for smoke tests; `full` eval only when the user asks — it's slow). Note the new `results/ttt_qml_cli_<timestamp>/` dir.
4. Monitor by tailing `results/<run>/evolution_run.log` (tail, never full read). Progress = generations advancing, scores logged, no repeated evaluator tracebacks.
5. Report: run dir, generations completed, best score so far, LLM cost if logged.

Verification: `bash scripts/verify.sh` after any code change; otherwise a completed generation with a score in `programs.sqlite` is the success signal.

Stop and report (don't improvise) if: the venv fails to activate, the OpenRouter API errors persist (key/cost cap), or the evaluator crashes on the unmodified seed program.
