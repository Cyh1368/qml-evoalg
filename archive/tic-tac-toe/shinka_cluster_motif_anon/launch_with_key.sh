#!/usr/bin/env bash
# Reads OPENROUTER_API_KEY from STDIN (first line) so the secret never appears in
# process args or on disk. Launches ONE anonymized motif-discovery orchestrator,
# detached (setsid), in the run directory given as $1.
#   usage:  <key on stdin> | bash launch_with_key.sh <run_dir>
set -e
RUN_DIR="$1"
if [ -z "$RUN_DIR" ]; then echo "usage: launch_with_key.sh <run_dir>" >&2; exit 2; fi
IFS= read -r OPENROUTER_API_KEY
export OPENROUTER_API_KEY
cd "$RUN_DIR"
source /etc/profile >/dev/null 2>&1 || true
module load miniconda >/dev/null 2>&1 || true
source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null || true
conda activate qml-ea
setsid python launch_shinka_cluster.py --generations 100 --max-eval-jobs 6 --max-proposal-jobs 3 \
    > orchestrator.log 2>&1 < /dev/null &
disown || true
sleep 1
echo "launched anon orchestrator in $RUN_DIR"
