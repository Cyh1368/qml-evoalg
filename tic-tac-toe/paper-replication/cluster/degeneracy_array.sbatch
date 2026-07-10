#!/bin/bash
#SBATCH --job-name=degen
#SBATCH --partition=day
#SBATCH --array=0-499%140
#SBATCH --cpus-per-task=8
#SBATCH --mem=12G
#SBATCH --time=24:00:00
#SBATCH --output=slurm_logs/degen_%A_%a.out
#SBATCH --error=slurm_logs/degen_%A_%a.out

# Experiment D: degeneracy / latent-space Monte-Carlo joint-perturbation test
# around converged base optima.
# 10 base optima x 50 MC samples = 500 tasks (index 0..499).
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
mkdir -p slurm_logs degeneracy_results

echo "host=$(hostname) index=${SLURM_ARRAY_TASK_ID} cpus=${SLURM_CPUS_PER_TASK}"
python degeneracy_pca.py --index "${SLURM_ARRAY_TASK_ID}"
