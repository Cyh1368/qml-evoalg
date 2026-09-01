#!/usr/bin/env bash
#SBATCH --job-name=su2v3val
#SBATCH --partition=day
#SBATCH --time=03:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --output=/home/ch2499/project/su2_v3_tools/slurm/val_%A_%a.out
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

# One task id per array index, read from the manifest built by --list.
TASK_ID=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "$TOOLS/task_manifest.txt")
if [ -z "$TASK_ID" ]; then
    echo "no task for index $SLURM_ARRAY_TASK_ID"
    exit 0
fi
echo "=== $TASK_ID (array index $SLURM_ARRAY_TASK_ID) ==="
python su2_v3_validate.py --task "$TASK_ID" --seeds "${SU2_SEEDS:-1000}"
