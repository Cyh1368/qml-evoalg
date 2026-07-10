---
name: cluster-run
description: Use this skill when the user asks to launch, check, or fetch results from a SLURM run on the Yale Bouchet cluster (e.g. "launch on bouchet", "check my cluster jobs", "sync results back").
---

Scope: `shinka_cluster/` locally; remote actions over SSH to `bouchet`. Never modify local `results/` except by syncing new run dirs into it.

1. SSH access needs Duo 2FA; use the askpass workaround allowlisted in the root `.claude/settings.local.json` (see agent memory `bouchet-cluster-access` for paths/deploy script). If auth fails, ask the user to authenticate.
2. Launch (on the login node): `nohup python shinka_cluster/launch_shinka_cluster.py --generations N ... &` — this uses `job_type="slurm_conda"` and the corrected **converged** eval protocol (full data, val-loss early stopping, restore-best-weights).
3. Monitor: `squeue -u $USER`, plus the launcher's log. Jobs are long (hours); prefer checking back over polling.
4. Fetch: rsync the remote results dir back under local `results/`, then hand off to the analyze-run skill.
5. Report: job IDs, states, and once fetched, run dir + best converged score.

Verification: SLURM jobs reach COMPLETED, the synced dir contains `programs.sqlite`, and scores are labeled as converged-protocol.

Stop and report if: Duo/SSH auth cannot be completed non-interactively, SLURM rejects the submission, or the remote env/conda setup is missing.
