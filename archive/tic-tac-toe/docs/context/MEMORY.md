# Agent memory

> Agents: when you learn durable facts about this repo (a fix for a recurring problem, a preference stated by the maintainer, a constraint discovered the hard way), append a date-stamped entry under 3 sentences. Never rewrite prior entries.

- 2026-07-08 — The quick eval preset mis-ranks candidates; all reported/final numbers must come from the converged protocol (cluster path). README's headline run (`20260605_124906`, score 0.5984) predates this correction.
- 2026-07-08 — `shinka_cli_task/activate_eval_env.sh` embeds a fallback OPENROUTER_API_KEY that is committed to git history; maintainer should rotate it. Until then, treat the file as sensitive.
- 2026-07-08 — Long-lived background processes (evolution runs, Flask dashboard) are commonly running; check `*.pid` files and `ps` before starting new runs or touching `results/`.
- 2026-07-18 — The committed API key was already removed from the working tree (`activate_eval_env.sh` now errors if OPENROUTER_API_KEY unset; the real key lives in `tic-tac-toe/.env`), but it remains in git history — rotation still pending.
- 2026-07-18 — Bouchet launch pattern for orchestrators: `launch_with_key.sh` reads the key from stdin (`cut -d= -f2- .env | ssh bouchet 'bash .../launch_with_key.sh'`); do NOT strip the trailing newline or `read` fails under `set -e`. Duo: pexpect pty answering "2", user approves push.
- 2026-07-18 — Three cluster workloads launched: quotient array 18732390 (110 tasks), train-size array 18732954 (240 tasks), motif-discovery orchestrator on login node (`~/project/motif_discovery`, results dir `results/`, first eval job 18732710). Fetch targets: `deploy_and_run.sh quotient-fetch | trainsize-fetch`; motif results need rsync + `motif_analysis.py`.
