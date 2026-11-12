#!/bin/bash
#SBATCH --job-name=cemoid_optbench
#SBATCH --partition=day
#SBATCH --array=0-349%150
#SBATCH --cpus-per-task=8
#SBATCH --mem=12G
#SBATCH --time=24:00:00
#SBATCH --output=slurm_logs/optbench_%A_%a.out
#SBATCH --error=slurm_logs/optbench_%A_%a.out

# 7 optimizers x 50 seeds = 350 tasks (index 0..349), cemoid L=3,P=2.
# Same convergence protocol as the robustness run.
set -euo pipefail

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

# Convergence protocol: validation-loss early stopping (restore best weights).
export MAX_EPOCHS=1000
export PATIENCE=75
export MIN_DELTA=1e-4
export WALL_BUDGET_SECONDS=84000

module purge
module load miniconda
conda activate qml-ea

cd "$SLURM_SUBMIT_DIR"
mkdir -p slurm_logs optimizer_histories

echo "host=$(hostname) index=${SLURM_ARRAY_TASK_ID} cpus=${SLURM_CPUS_PER_TASK}"
python optimizer_benchmark.py --index "${SLURM_ARRAY_TASK_ID}"
