#!/bin/bash
#SBATCH --job-name=su2_robustness
#SBATCH --partition=day
#SBATCH --array=0-499%200
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=24:00:00
#SBATCH --output=slurm_logs/su2_rob_%A_%a.out
#SBATCH --error=slurm_logs/su2_rob_%A_%a.out

# 500-seed parameter-init robustness for the evolved SU2-like L=3,P=2 model.
# One array task per seed; results -> robustness_histories_ea/seed_{NNN}.json.
set -euo pipefail

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

export MAX_EPOCHS=1000
export PATIENCE=75
export MIN_DELTA=1e-4
export WALL_BUDGET_SECONDS=84000

module purge
module load miniconda
conda activate qml-ea

cd "$SLURM_SUBMIT_DIR"
mkdir -p slurm_logs robustness_histories_ea

echo "host=$(hostname) seed=${SLURM_ARRAY_TASK_ID} cpus=${SLURM_CPUS_PER_TASK}"
python seed_robustness_ea.py --seed "${SLURM_ARRAY_TASK_ID}"
