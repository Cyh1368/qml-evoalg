#!/bin/bash
#SBATCH --job-name=quotient
#SBATCH --partition=day
#SBATCH --array=0-109%110
#SBATCH --cpus-per-task=8
#SBATCH --mem=12G
#SBATCH --time=24:00:00
#SBATCH --output=slurm_logs/quotient_%A_%a.out
#SBATCH --error=slurm_logs/quotient_%A_%a.out

# Quotient-ansatz experiment: degeneracy-guided parameter tying, trained from
# scratch under the converged protocol.
# 6 variants (full x10 seeds, 5 tied variants x20 seeds) = 110 tasks (index 0..109).
# See quotient_ansatz.py docstring for the variant definitions.
set -euo pipefail

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

# Same convergence protocol as the other converged experiments.
export MAX_EPOCHS=1000
export PATIENCE=75
export MIN_DELTA=1e-4
export WALL_BUDGET_SECONDS=84000

module purge
module load miniconda
conda activate qml-ea

cd "$SLURM_SUBMIT_DIR"
mkdir -p slurm_logs quotient_results

echo "host=$(hostname) index=${SLURM_ARRAY_TASK_ID} cpus=${SLURM_CPUS_PER_TASK}"
python quotient_ansatz.py --index "${SLURM_ARRAY_TASK_ID}"
