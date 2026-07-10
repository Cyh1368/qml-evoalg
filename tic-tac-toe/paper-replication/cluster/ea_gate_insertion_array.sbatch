#!/bin/bash
#SBATCH --job-name=ea_gate_ins
#SBATCH --partition=day
#SBATCH --array=0-209
#SBATCH --cpus-per-task=8
#SBATCH --mem=12G
#SBATCH --time=04:00:00
#SBATCH --output=slurm_logs/ea_gi_%A_%a.out
#SBATCH --error=slurm_logs/ea_gi_%A_%a.out

set -euo pipefail

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

module purge
module load miniconda
conda activate qml-ea

cd "$SLURM_SUBMIT_DIR"
mkdir -p slurm_logs ea_gate_insertion_results ea_programs

echo "host=$(hostname) index=${SLURM_ARRAY_TASK_ID}"
python ea_gate_insertion.py --index "${SLURM_ARRAY_TASK_ID}"
