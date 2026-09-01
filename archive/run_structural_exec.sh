#!/usr/bin/env bash
source /etc/profile >/dev/null 2>&1 || true
module load miniconda >/dev/null 2>&1 || true
source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null || true
conda activate qml-ea
set -eu
python -u "$HOME/project/structural_exec.py" "$@"
