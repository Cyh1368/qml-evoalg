#!/bin/bash
#SBATCH --job-name=trainsize
#SBATCH --partition=day
#SBATCH --array=0-239%120
#SBATCH --cpus-per-task=8
#SBATCH --mem=12G
#SBATCH --time=24:00:00
#SBATCH --output=slurm_logs/trainsize_%A_%a.out
#SBATCH --error=slurm_logs/trainsize_%A_%a.out

# Training-set-size sweep: {cemoid, ea} x {30,60,120,240,450,600} x 20 seeds
# = 240 tasks (index 0..239). Puts our circuits on the Meyer/Baumann
# accuracy-vs-train-size axes. See train_size_sweep.py docstring.
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
mkdir -p slurm_logs train_size_results

echo "host=$(hostname) index=${SLURM_ARRAY_TASK_ID} cpus=${SLURM_CPUS_PER_TASK}"
python train_size_sweep.py --index "${SLURM_ARRAY_TASK_ID}"
