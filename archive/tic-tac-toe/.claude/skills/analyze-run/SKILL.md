---
name: analyze-run
description: Use this skill when the user asks to analyze, summarize, or report on an evolution run's results (e.g. "what's the best ansatz", "make a report for run X", "compare generations").
---

Scope: read-only on `results/` and `logs/`; may write reports/figures to the repo (outside `results/`) and run `make_ansatz_report.py`, `display_circuit.py`, `evolution_server.py`.

1. Identify the run dir (`ls -dt results/ttt_qml_cli_*/ | head`); default to the newest unless the user names one. The README's canonical run is `20260605_124906`.
2. Query, never read raw: `sqlite3 results/<run>/programs.sqlite '.tables'`, then e.g. best score per generation, top programs. Sample `evolution_run.log` with tail only.
3. For a shareable artifact: `python3 make_ansatz_report.py --results-dir results/<run>` (standalone HTML). For live browsing: `evolution_server.py` on port 5050.
4. **Always state which eval protocol produced the scores** (quick vs converged) — mixing them is the repo's #1 footgun (see docs/context/GOTCHAS.md).
5. Report: best score + generation, ansatz structure summary (gates/params vs the 162-param SU2 seed), and any anomalies.

Verification: the HTML report opens/renders (check file exists and is >10 KB); sqlite queries return rows.

Stop and report if: `programs.sqlite` is missing/locked by a live run (check pid files), or the schema doesn't match expected tables.
