#!/bin/bash
#SBATCH --job-name=wp-gatefix
#SBATCH --partition=day
#SBATCH --time=01:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
set -uo pipefail
module reset >/dev/null 2>&1
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a >/dev/null 2>&1
export LD_LIBRARY_PATH=/apps/software/2024a/software/Python/3.12.3-GCCcore-13.3.0/lib:${LD_LIBRARY_PATH:-}
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "${SLURM_SUBMIT_DIR:-$PWD}"
python3 -m unittest research.search.test_corrected_gate 2>&1 | tail -3
python3 -m research.search.corrected_gate --out research/search/corrected_gate.json
