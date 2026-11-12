#!/bin/bash
#SBATCH --job-name=wp-decide2
#SBATCH --partition=day
#SBATCH --cpus-per-task=24
#SBATCH --mem=32G
#SBATCH --time=03:00:00
set -uo pipefail
module reset >/dev/null 2>&1
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a >/dev/null 2>&1
export LD_LIBRARY_PATH=/apps/software/2024a/software/Python/3.12.3-GCCcore-13.3.0/lib:${LD_LIBRARY_PATH:-}
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "${SLURM_SUBMIT_DIR:-$PWD}"
python3 -m research.search.decision_rules2 --workers "${WORKERS:-24}" \
  --out research/search/decision_rules2.json
