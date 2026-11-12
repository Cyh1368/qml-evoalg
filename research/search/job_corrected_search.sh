#!/bin/bash
# A6.7 matched corrected-feedback search study.
#
# Three arms (llm-fitness as the contemporaneous paired comparator, llm-verify,
# llm-verify-repair) under the A6.1 corrected label semantics, on the same families,
# seeds, budget, steps and max_train as the frozen 120-run confirmatory study. Runs are
# written to a separate log directory and carry label_mode="corrected" in the run JSON,
# so they can never be pooled with the frozen defective-feedback runs by accident.
#
# Usage: sbatch --array=0-11 research/search/job_corrected_search.sh ARM FAMILY
#SBATCH --job-name=wp-corrsearch
#SBATCH --partition=day
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --array=0-71%6
#SBATCH --output=logs/wp-corrsearch-%A_%a.out

set -euo pipefail
# Single throttled array: task id -> (family, arm, seed). The confirmatory study used
# --array=0-11%4; 72 simultaneous LLM clients sit idle on network waits (TotalCPU 0:00 after
# ten minutes), which is the gateway throttling a single account, so concurrency is capped
# here rather than spread across six uncoordinated arrays.
# Usage: sbatch --array=0-71%6 research/search/job_corrected_search.sh
FAMILIES=(ring_n6 graphs_n6)
ARMS=(llm-fitness llm-verify llm-verify-repair)
TID=${SLURM_ARRAY_TASK_ID:-0}
FAMILY="${FAMILIES[$(( TID / 36 ))]}"
SUB=$(( TID % 36 ))
ARM="${ARMS[$(( SUB / 12 ))]}"
BASE_SEED=20261110
OUT=logs/runs_corrected
MODEL=ycrc-local
BUDGET=32
STEPS=200
MAX_TRAIN=256

module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a ycrc-llm/1.0
export LD_LIBRARY_PATH=/apps/software/2024a/software/Python/3.12.3-GCCcore-13.3.0/lib:${LD_LIBRARY_PATH:-}
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p "$OUT"
SEED=$(( BASE_SEED + (SUB % 12) ))
cd "${SLURM_SUBMIT_DIR:-.}"
sleep $(( (TID * 7) % 60 ))   # desynchronise the 6 concurrent clients
python3 -m research.search.harness run \
  --arm "$ARM" --family "$FAMILY" --model "$MODEL" --seed "$SEED" \
  --budget "$BUDGET" --steps "$STEPS" --max-train "$MAX_TRAIN" \
  --reasoning-effort none --label-mode corrected --out "$OUT"
