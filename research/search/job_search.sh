#!/bin/bash
# WP-SEARCH sbatch template: one search run per (array) task.
#
# Usage:
#   sbatch research/search/job_search.sh ARM FAMILY MODEL BASE_SEED BUDGET LOGDIR
#   sbatch --array=0-35%6 research/search/job_search.sh llm-verify graphs_n6 \
#          ycrc-local 20261110 32 /path/to/logs/runs_pilot
#
# Array task id is added to BASE_SEED, so one array covers paired seeds.
# Override the array range on the sbatch command line if needed.
#SBATCH --job-name=wp-search
#SBATCH --partition=day
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --array=0-11%4
#SBATCH --output=%x-%A_%a.out

set -euo pipefail
ARM="${1:?arm: random|mutation-ea|llm-fitness|llm-verify|llm-verify-repair}"
FAMILY="${2:?family, e.g. graphs_n6}"
MODEL="${3:?model: ycrc-local|ycrc-local-think (ignored by non-LLM arms)}"
BASE_SEED="${4:?base seed}"
BUDGET="${5:?evaluated-candidate budget}"
LOGDIR="${6:?per-run log directory}"

SEED=$(( BASE_SEED + ${SLURM_ARRAY_TASK_ID:-0} ))

# Optional compute-control / treatment overrides (protocol defaults otherwise).
STEPS="${STEPS:-200}"
MAX_TRAIN="${MAX_TRAIN:-}"
EFFORT="${EFFORT:-none}"

module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
case "$ARM" in
  llm-*) module load ycrc-llm/1.0 ;;
esac
export OPENBLAS_NUM_THREADS=1

# Resolve the repo root robustly: $0 is unreliable inside a Slurm batch script,
# but $SLURM_SUBMIT_DIR is the directory sbatch was run from.
REPO="${REPO:-$SLURM_SUBMIT_DIR}"
if [ -z "$REPO" ] || [ ! -d "$REPO/research" ]; then
  REPO="$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd)"
fi
cd "$REPO"
mkdir -p "$LOGDIR"
EXTRA=()
if [ -n "$MAX_TRAIN" ]; then EXTRA+=(--max-train "$MAX_TRAIN"); fi
python3 -m research.search.harness run \
  --arm "$ARM" --family "$FAMILY" --model "$MODEL" \
  --reasoning-effort "$EFFORT" \
  --seed "$SEED" --budget "$BUDGET" --steps "$STEPS" "${EXTRA[@]}" --out "$LOGDIR"
