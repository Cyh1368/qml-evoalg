#!/bin/bash
#SBATCH --job-name=cemoid_lp_ext
#SBATCH --partition=day
#SBATCH --array=0-50
#SBATCH --cpus-per-task=8
#SBATCH --mem=12G
#SBATCH --time=24:00:00
#SBATCH --output=slurm_logs/sweep_ext_%A_%a.out
#SBATCH --error=slurm_logs/sweep_ext_%A_%a.out

# Extended L/P sweep: probe whether converged accuracy keeps climbing toward 1.0
# or saturates past the original 7x7 frontier (the accuracy-ceiling question,
# builds on SWEEP_LP_REPORT.md).  One array task per NEW frontier (l,p) pair
# (l>7 or p>7), 51 pairs (indices 0..50), ordered heaviest-first so the long-pole
# deep circuits (up to L=10,P=10 = 900 params) start in the first scheduling wave.
# Cached 7x7 histories are skipped; results land in histories/history_l{l}_p{p}.json.
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
# Soft walltime cap (~23.3h of the 24h limit): the heaviest cells may not fully
# converge, so write a partial result (stop_reason="walltime", best-so-far test
# acc) instead of being SIGKILLed mid-epoch and losing the job.
export WALL_BUDGET_SECONDS=84000

module purge
module load miniconda
conda activate qml-ea

cd "$SLURM_SUBMIT_DIR"
mkdir -p slurm_logs histories

echo "host=$(hostname) ext_index=${SLURM_ARRAY_TASK_ID} cpus=${SLURM_CPUS_PER_TASK}"
python sweep.py --ext-index "${SLURM_ARRAY_TASK_ID}"
