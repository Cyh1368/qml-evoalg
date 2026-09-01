#!/bin/bash
#SBATCH --job-name=cemoid_lp_sweep
#SBATCH --partition=day
#SBATCH --array=0-48
#SBATCH --cpus-per-task=8
#SBATCH --mem=12G
#SBATCH --time=24:00:00
#SBATCH --output=slurm_logs/sweep_%A_%a.out
#SBATCH --error=slurm_logs/sweep_%A_%a.out

# One SLURM array task per (l,p) pair (49 pairs, indices 0..48), ordered
# heaviest-first so the long-pole deep circuits start in the first wave.
# Each task trains one model to convergence and writes
# histories/history_l{l}_p{p}.json.
set -euo pipefail

# Keep each task's linear algebra to its allotted cores (no oversubscription).
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

# Convergence protocol: validation-loss early stopping (restore best weights).
export MAX_EPOCHS=1000
export PATIENCE=75
export MIN_DELTA=1e-4
# Soft walltime cap (~23.3h of the 24h limit): write a partial result instead of
# being SIGKILLed mid-epoch.  Partial results carry stop_reason="walltime".
export WALL_BUDGET_SECONDS=84000

module purge
module load miniconda
conda activate qml-ea

cd "$SLURM_SUBMIT_DIR"
mkdir -p slurm_logs histories

echo "host=$(hostname) task=${SLURM_ARRAY_TASK_ID} cpus=${SLURM_CPUS_PER_TASK}"
python sweep.py --index "${SLURM_ARRAY_TASK_ID}"
