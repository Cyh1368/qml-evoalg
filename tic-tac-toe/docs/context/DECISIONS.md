# Decision log

Append-only. Format: date — decision — why — status.

- 2026-06-04 — Freeze circuit skeleton (9 qubits, RX(2π/3·cell) feature map, l=3 re-uploading, p=2 block repeats); evolve only `ANSATZ_SPEC`. — Isolates the search space to the ansatz block, matching the reference paper's setup. — Active.
- 2026-06-04 — Restrict two-qubit gates to the 12-edge 3×3 grid adjacency; cap params at 768 (seed EfficientSU2-style block = 162 params). — Paper-inspired hardware-locality constraint; keeps circuits trainable. — Active.
- 2026-06-05 — Use ShinkaEvolve with UCB1 dynamic LLM selection and per-run API cost cap (`max_api_costs: 5.0`); cheap vs expensive LLM presets. — Cost control for LLM-driven mutation. — Active.
- 2026-06-05 — Designate `results/ttt_qml_cli_20260605_124906` as the main reported run (best gen 10, score 0.5984). — First full monitored run. — Superseded in part by later converged re-runs (see MEMORY).
- 2026-06-18 — Adopt the "corrected converged" eval protocol (full data, validation-loss early stopping, restore-best-weights) for cluster runs; earlier quick-protocol scores deemed unreliable for final claims. — The quick preset under-trains candidates and mis-ranks them. — Active; quick preset retained for cheap local smoke runs only.
- 2026-06-20 — Run heavy evaluation on clusters (Yale Bouchet via SLURM `slurm_conda`, plus cemoid) rather than locally. — Converged protocol is too slow for WSL. — Active.
- 2026-07-08 — Add agent-context infrastructure (this docs/context/ folder, lean CLAUDE.md, `.claude/skills/`, `scripts/verify.sh`); place it in `tic-tac-toe/` (the primary working dir) rather than the qml-ea repo root, since sibling dirs are inactive. — Token-efficient cold starts for future agent sessions. — Active.
- 2026-07-08 — Keep `results/` and `logs/` git-tracked as the research record despite churn from live runs. — Reproducibility of reported numbers. — Active; revisit if repo size becomes a problem.
