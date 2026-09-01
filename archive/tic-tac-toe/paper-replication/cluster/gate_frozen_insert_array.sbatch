#!/bin/bash
#SBATCH --job-name=cemoid_frozins
#SBATCH --partition=day
#SBATCH --array=0-139%140
#SBATCH --cpus-per-task=8
#SBATCH --mem=12G
#SBATCH --time=24:00:00
#SBATCH --output=slurm_logs/frozins_%A_%a.out
#SBATCH --error=slurm_logs/frozins_%A_%a.out

# Stage B: gate insertion with frozen vs joint conditions.
# 2 conditions x 7 gate-counts x 10 base optima = 140 tasks (index 0..139).
# Submit with --dependency=afterok:<stageA_jobid> so base_optima/ exist first.
set -euo pipefail

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

# Same convergence protocol.
export MAX_EPOCHS=1000
export PATIENCE=75
export MIN_DELTA=1e-4
export WALL_BUDGET_SECONDS=84000

module purge
module load miniconda
conda activate qml-ea

cd "$SLURM_SUBMIT_DIR"
mkdir -p slurm_logs gate_insertion_frozen_results

echo "host=$(hostname) index=${SLURM_ARRAY_TASK_ID} cpus=${SLURM_CPUS_PER_TASK}"
python gate_insertion_frozen.py --index "${SLURM_ARRAY_TASK_ID}"
