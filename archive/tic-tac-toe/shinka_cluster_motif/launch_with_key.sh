#!/usr/bin/env bash
# Reads OPENROUTER_API_KEY from STDIN (first line) so the secret never appears
# in process args or any on-disk file. Then launches the motif-discovery Shinka
# orchestrator detached (setsid) so it survives the ssh session closing.
set -e
IFS= read -r OPENROUTER_API_KEY
export OPENROUTER_API_KEY
cd "$HOME/project/motif_discovery"
source /etc/profile >/dev/null 2>&1 || true
module load miniconda >/dev/null 2>&1 || true
source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null || true
conda activate qml-ea
setsid python launch_shinka_cluster.py --generations 100 --max-eval-jobs 8 --max-proposal-jobs 4 > orchestrator.log 2>&1 < /dev/null &
disown || true
sleep 1
echo "launched motif orchestrator"
