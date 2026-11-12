#!/bin/bash
#SBATCH --job-name=su2_lp_sweep
#SBATCH --partition=day
#SBATCH --array=0-99%200
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=24:00:00
#SBATCH --output=slurm_logs/su2_sweep_%A_%a.out
#SBATCH --error=slurm_logs/su2_sweep_%A_%a.out

# L/P sweep for the evolved SU2-like ansatz, (l,p) over the full {1..10}^2 grid
# (100 cells, one array task per pair, heaviest-first). Counterpart to the
# cemoid sweep; results land in histories_ea/history_l{l}_p{p}.json.
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
mkdir -p slurm_logs histories_ea

echo "host=$(hostname) index=${SLURM_ARRAY_TASK_ID} cpus=${SLURM_CPUS_PER_TASK}"
python sweep_ea.py --index "${SLURM_ARRAY_TASK_ID}"
