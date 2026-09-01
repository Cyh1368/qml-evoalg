#!/usr/bin/env bash
# Generic detached orchestrator launcher. Args: <remote_dir> <config_file> <results_subdir> ; key on stdin.
set -e
IFS= read -r OPENROUTER_API_KEY
export OPENROUTER_API_KEY
cd "$HOME/project/$1"
source /etc/profile >/dev/null 2>&1 || true
module load miniconda >/dev/null 2>&1 || true
source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null || true
conda activate qml-ea
setsid python launch_shinka_cluster.py --generations 100 --max-eval-jobs 5 --max-proposal-jobs 3 \
  --config "$2" --results-dir "$3" > "orchestrator_$3.log" 2>&1 < /dev/null &
disown || true
sleep 1
echo "launched $1 / $2 -> $3"
