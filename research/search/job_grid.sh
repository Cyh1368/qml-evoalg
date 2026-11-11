#!/bin/bash
# WP-SEARCH grid job: runs one arm's full (family x treatment x seed) grid inside
# a single Slurm job (one slot; resumable). Usage:
#   sbatch research/search/job_grid.sh ARM
# Grid parameters come from env (with pilot defaults below).
#SBATCH --job-name=wp-grid
#SBATCH --partition=day
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=06:00:00
#SBATCH --output=%x-%j.out

set -euo pipefail
ARM="${1:?arm: random|mutation-ea|llm-fitness|llm-verify|llm-verify-repair}"

FAMILIES="${FAMILIES:-ring_n6,graphs_n6}"
TREATMENTS="${TREATMENTS:-ycrc-local:none,ycrc-local:medium,ycrc-local-think:medium}"
SEEDS="${SEEDS:-20261110,20261111,20261112}"
BUDGET="${BUDGET:-12}"
STEPS="${STEPS:-120}"
MAX_TRAIN="${MAX_TRAIN:-256}"
OUT="${OUT:-logs/runs_pilot}"

module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
case "$ARM" in
  llm-*) module load ycrc-llm/1.0 ;;
esac
export OPENBLAS_NUM_THREADS=1

REPO="${REPO:-$SLURM_SUBMIT_DIR}"
if [ -z "$REPO" ] || [ ! -d "$REPO/research" ]; then
  REPO="$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd)"
fi
cd "$REPO"

EXTRA=()
if [ -n "$MAX_TRAIN" ]; then EXTRA+=(--max-train "$MAX_TRAIN"); fi
python3 -m research.search.run_grid --arm "$ARM" \
  --families "$FAMILIES" --treatments "$TREATMENTS" --seeds "$SEEDS" \
  --budget "$BUDGET" --steps "$STEPS" "${EXTRA[@]}" --out "$OUT"
