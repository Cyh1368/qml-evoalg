#!/bin/bash
# E-R4' SELF-CHECK (no sealed read): refit every WP-REPAIR-2 unit and require that the
# corrected evaluator reproduces the experiment's own logged dev risk to 1e-9.  Only after
# this passes may job_holdout_v3.sh consume the fresh v3 holdout.
#SBATCH --job-name=wp-scheck
#SBATCH --partition=day
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.out
set -euo pipefail
module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
export OPENBLAS_NUM_THREADS=1
cd "${REPO:-$SLURM_SUBMIT_DIR}"
python3 research/holdout_oneshot.py --dry-run --splits dev --skip-search \
  --selfcheck research/experiments/repair/repair2_results.json --workers 16
