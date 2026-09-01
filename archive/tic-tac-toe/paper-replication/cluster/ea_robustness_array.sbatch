#!/bin/bash
#SBATCH --job-name=ea_robustness
#SBATCH --partition=day
#SBATCH --array=0-149
#SBATCH --cpus-per-task=8
#SBATCH --mem=12G
#SBATCH --time=04:00:00
#SBATCH --output=slurm_logs/ea_rob_%A_%a.out
#SBATCH --error=slurm_logs/ea_rob_%A_%a.out

set -euo pipefail

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

module purge
module load miniconda
conda activate qml-ea

cd "$SLURM_SUBMIT_DIR"
mkdir -p slurm_logs ea_robustness_histories ea_programs

echo "host=$(hostname) index=${SLURM_ARRAY_TASK_ID}"
python ea_seed_robustness.py --index "${SLURM_ARRAY_TASK_ID}"
