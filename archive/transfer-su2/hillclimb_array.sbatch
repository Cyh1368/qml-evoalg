#!/usr/bin/env bash
#SBATCH --job-name=su2v3hill
#SBATCH --partition=day
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --output=/home/ch2499/project/su2_v3_tools/slurm/hill_%A_%a.out
set -euo pipefail

module load miniconda 2>/dev/null || true
source activate qml-ea

TOOLS="$HOME/project/su2_v3_tools"
cd "$TOOLS"

export SU2_TASK_DIR="$HOME/project/zc_su2_v3"
export SU2_VALIDATE_OUT="$TOOLS/v3_validation"
export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
export MKL_NUM_THREADS=4
export PYTHONDONTWRITEBYTECODE=1
# Training logs disabled: concurrent tasks share a seed-named log path.

STARTS=(v2_sonnet_winner v2_gpt_winner seed trivial_1p)
START=${STARTS[$SLURM_ARRAY_TASK_ID]}
echo "=== hillclimb from $START ==="
export PYTHONUNBUFFERED=1
python -u su2_v3_validate.py --hillclimb "$START" --steps "${SU2_HILL_STEPS:-40}"
