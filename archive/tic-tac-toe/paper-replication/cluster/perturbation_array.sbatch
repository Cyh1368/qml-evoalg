#!/bin/bash
#SBATCH --job-name=pert
#SBATCH --partition=day
#SBATCH --array=0-209%140
#SBATCH --cpus-per-task=8
#SBATCH --mem=12G
#SBATCH --time=24:00:00
#SBATCH --output=slurm_logs/pert_%A_%a.out
#SBATCH --error=slurm_logs/pert_%A_%a.out

# Experiment C: perturbation / stability-region test around converged base optima.
# 3 variants (random_gate, nearzero_gate, delta_weight) x 7 r values x 10 base
# optima = 210 tasks (index 0..209).
# Requires base_optima/ to already exist (built by gate_insertion_frozen.py --build-base).
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
mkdir -p slurm_logs perturbation_results

echo "host=$(hostname) index=${SLURM_ARRAY_TASK_ID} cpus=${SLURM_CPUS_PER_TASK}"
python perturbation_stability.py --index "${SLURM_ARRAY_TASK_ID}"
