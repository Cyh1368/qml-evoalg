#!/bin/bash
# WP-REPAIR decisive causal-repair experiment (CPU batch, ring_n6).
#SBATCH --job-name=wp-repair
#SBATCH --partition=day
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=06:00:00
#SBATCH --output=%x-%j.out
set -euo pipefail
module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
export OPENBLAS_NUM_THREADS=1
REPO="${REPO:-$SLURM_SUBMIT_DIR}"
if [ -z "$REPO" ] || [ ! -d "$REPO/research" ]; then REPO="$(cd "$(dirname "$0")/../.." && pwd)"; fi
cd "$REPO"
TEACHERS="${TEACHERS:-101,202,303}"
ETAS="${ETAS:-0,0.5,1}"
NOPT="${NOPT:-8}"
BUDGETS="${BUDGETS:-200}"
MAXTRAIN="${MAXTRAIN:-256}"
OUT="${OUT:-research/experiments/repair/repair_results.json}"
python3 -m research.experiments.repair.repair_experiment \
  --teacher-seeds "$TEACHERS" --n-opt-seeds "$NOPT" --budgets "$BUDGETS" \
  --max-train "$MAXTRAIN" --out "$OUT"
