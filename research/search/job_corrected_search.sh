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
#SBATCH --array=0-71%24
#SBATCH --output=logs/wp-corrsearch-%A_%a.out

set -euo pipefail
# Single array over all 72 runs: task id -> (family, arm, seed).
#
# Concurrency note, recorded because an earlier reading of this comment was wrong. Slurm
# reports TotalCPU 00:00:00 for *running* array tasks -- the accounting is flushed at
# completion -- so "TotalCPU 0 after ten minutes" is not evidence of network stalls, and the
# gateway was in fact answering in ~2.4 s (median latency recorded in the frozen runs). The
# real cost is the per-candidate fit under node contention: a 32-candidate run takes tens of
# minutes on a shared 1-CPU task. Concurrency is therefore set by how many nodes are free,
# capped at 24 to stay well clear of the 72-client submission that was cancelled here.
# Usage: sbatch --array=0-71%24 research/search/job_corrected_search.sh
FAMILIES=(ring_n6 graphs_n6)
ARMS=(llm-fitness llm-verify llm-verify-repair)
TID=${SLURM_ARRAY_TASK_ID:-0}
FAMILY="${FAMILIES[$(( TID / 36 ))]}"
SUB=$(( TID % 36 ))
ARM="${ARMS[$(( SUB / 12 ))]}"
BASE_SEED=20261110
OUT=logs/runs_corrected
MODEL=ycrc-local
# Matched to the frozen confirmatory study, which records budget=12, steps=120,
# max_train=256, reasoning_effort=none in all 120 run JSONs. A6.7 requires the same budget
# and seeds, so these are read from that record rather than from the template defaults in
# job_search.sh (whose 32/200 defaults are for a different, larger study and produced three
# cancelled A6.7 submissions before this was checked against the run JSONs).
BUDGET=12
STEPS=120
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
