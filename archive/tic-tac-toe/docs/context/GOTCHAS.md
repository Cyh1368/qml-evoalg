# Gotchas

- **Quick vs converged eval protocols are not comparable.** Local `--eval-preset quick` uses small subsets/few epochs; the cluster protocol is the "CORRECTED converged" one (full data, validation-loss early stopping, restore-best-weights). Scores from the two must never be compared or mixed in reports. The converged protocol is the trusted one.
- **`shinka_cli_task/initial.py` and `evaluate.py` are generated.** `run_shinkaevolve_monitored.py` re-extracts them from the notebook (see `notebook_extract_manifest.json`). Edits made directly to the extracts are silently overwritten on the next launch — edit the notebook.
- **Live API key** in `shinka_cli_task/activate_eval_env.sh` (OPENROUTER_API_KEY fallback). It is git-tracked and in history. Do not print or replicate it; treat the file as sensitive.
- **Huge files everywhere.** `evolution_cheap_seed2000.log` ~2 MB, run dirs up to ~70 MB, notebook 72 KB, `.venv-shinka-ttt/` 1.2 GB. Sample with head/tail or sqlite queries; never read wholesale.
- **`results/` and `logs/` are git-tracked** (deliberate — they're the research record). Long-running evolution processes write to them continuously, so `git status` is often noisy with modified sqlite/log files; don't "clean up" or commit them mid-run.
- **Background processes may be live.** `*.pid` files (`evolution_server.pid`, etc.) may point to running evolution/dashboard processes. Check `ps` before assuming stale; `run_shinkaevolve_monitored.py` has its own stale-run killer.
- **Bouchet SSH requires Duo 2FA** — non-interactive SSH needs the askpass workaround already allowlisted in root `.claude/settings.local.json`. Fresh sessions may need the user to authenticate.
- **No tests, no linter.** `scripts/verify.sh` is the only automated check (compile + config + import smoke). Real verification is empirical: run a short evolution and inspect scores.
- **`**/.venv/` in root .gitignore does NOT match `.venv-shinka-ttt/`** — it stays untracked only because nobody `git add`ed it. Never `git add -A` in this repo.
- **Python 3.14 venv.** System python may differ; always activate the venv first.
