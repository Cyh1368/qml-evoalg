# Agent memory

> Agents: when you learn durable facts about this repo (a fix for a recurring problem, a preference stated by the maintainer, a constraint discovered the hard way), append a date-stamped entry under 3 sentences. Never rewrite prior entries.

- 2026-07-08 — The quick eval preset mis-ranks candidates; all reported/final numbers must come from the converged protocol (cluster path). README's headline run (`20260605_124906`, score 0.5984) predates this correction.
- 2026-07-08 — `shinka_cli_task/activate_eval_env.sh` embeds a fallback OPENROUTER_API_KEY that is committed to git history; maintainer should rotate it. Until then, treat the file as sensitive.
- 2026-07-08 — Long-lived background processes (evolution runs, Flask dashboard) are commonly running; check `*.pid` files and `ps` before starting new runs or touching `results/`.
