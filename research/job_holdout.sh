#!/bin/bash
# ONE-SHOT sealed/fresh holdout evaluation (REVISED_PROTOCOL section 5).
#SBATCH --job-name=wp-hold
#SBATCH --partition=day
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x-%j.out
set -euo pipefail
module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
export OPENBLAS_NUM_THREADS=1
cd "${REPO:-$SLURM_SUBMIT_DIR}"
python3 -m research.holdout_oneshot --workers "${WORKERS:-16}" \
  --out research/HOLDOUT_RESULTS.json \
  --access-log research/HOLDOUT_ACCESS.json
