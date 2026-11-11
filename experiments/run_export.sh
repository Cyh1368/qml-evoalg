#!/usr/bin/env bash
# Regenerate the T2 result CSVs from the run databases.
source /etc/profile >/dev/null 2>&1 || true
module load miniconda >/dev/null 2>&1 || true
source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null || true
conda activate qml-ea
set -eu
python -u "$HOME/project/export_results.py" --out-dir "$HOME/project/t2_results"
