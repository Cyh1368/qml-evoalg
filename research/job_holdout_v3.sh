#!/bin/bash
# E-R4' ONE-SHOT evaluation on the inputs-only v3 holdout (protocol Addendum A4).
# Gate: the same command with --dry-run --splits dev must reproduce WP-REPAIR-2's own
# development risk exactly (job 32989301: 216/216 compared, max |diff| = 0.0).
#SBATCH --job-name=wp-hold3
#SBATCH --partition=day
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x-%j.out
set -euo pipefail
module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
export OPENBLAS_NUM_THREADS=1
cd "${REPO:-$SLURM_SUBMIT_DIR}"
python3 -m research.holdout_oneshot --splits fresh_v3 --skip-search \
  --selfcheck research/experiments/repair/repair2_results.json \
  --out research/HOLDOUT_RESULTS_v3.json \
  --access-log research/HOLDOUT_ACCESS_v3.json --workers 16
