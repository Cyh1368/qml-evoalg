#!/bin/bash
# Analysis of the Addendum A1 breaking-target runs (60 runs in logs/runs_breaking).
#SBATCH --job-name=wp-brkan
#SBATCH --partition=devel
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.out
set -euo pipefail
module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
export OPENBLAS_NUM_THREADS=1
cd "${REPO:-$SLURM_SUBMIT_DIR}"
python3 -m research.search.analyze_breaking --dir logs/runs_breaking \
  --out research/search/breaking_target.json
