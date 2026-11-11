#!/bin/bash
# WP-DEV-ANALYSIS: refit-based development analyses (E-S4b/c, E-S5, E-S6).
#SBATCH --job-name=wp-dev
#SBATCH --partition=day
#SBATCH --cpus-per-task=24
#SBATCH --mem=24G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x-%j.out
set -euo pipefail
module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
export OPENBLAS_NUM_THREADS=1
cd "${REPO:-$SLURM_SUBMIT_DIR}"
python3 -m research.search.dev_analysis \
  --dir "${RUNDIR:-logs/runs_confirm}" \
  --workers "${WORKERS:-24}" \
  --baseline-steps "${BSTEPS:-120}" \
  --out "${OUT:-research/search/dev_analysis.json}"
