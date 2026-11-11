#!/bin/bash
# WP-REPAIR-2: corrected causal-repair experiment (research/REVISED_PROTOCOL.md 1-3).
#SBATCH --job-name=wp-rep2
#SBATCH --partition=day
#SBATCH --cpus-per-task=48
#SBATCH --mem=48G
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x-%j.out
set -euo pipefail
module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
export OPENBLAS_NUM_THREADS=1
REPO="${REPO:-$SLURM_SUBMIT_DIR}"
cd "$REPO"
python3 -m research.experiments.repair.repair_experiment2 \
  --n-opt-seeds "${NOPT:-24}" \
  --steps-main "${STEPS_MAIN:-200}" \
  --sens-steps "${SENS_STEPS:-600,1800}" \
  --sens-directions "${SENS_DIRS:-2}" \
  --sens-opt-seeds "${SENS_NOPT:-6}" \
  --workers "${WORKERS:-48}" \
  --out "${OUT:-research/experiments/repair/repair2_results.json}"
