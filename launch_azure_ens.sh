#!/usr/bin/env bash
# Launch the two Azure-routed ensemble arms on transfer-sn (T2, WITH context,
# which is the variant the gpt-5.6-sol baseline used, so the comparison holds).
#
# One replicate each, as requested:
#   az_weak_r1      gpt-5-mini + grok-code-fast-1 + Phi-4          cap $6
#   az_frontier_r1  gpt-5.6-sol@xhigh + DeepSeek-V4-Pro + Mistral  cap $30
#
# Scores are on the RESCALED axis: 0.0 = seed, 1.0 = the best symmetric solution
# (gpt-5.6-sol gen 51). Baseline landmarks translate as:
#   gen 27 plateau 0.8713 -> 0.178 | gen 33 jump 0.9372 -> 0.882 | gen 51 -> 1.000
#
# Usage:  ./launch_azure_ens.sh [generations]     (run ON the Bouchet login node)
set -euo pipefail

GENERATIONS="${1:-80}"
TASKDIR="$HOME/project/transfer_sn"

if [ ! -r "$HOME/.azure_key" ]; then
    echo "missing $HOME/.azure_key (mode 600)" >&2
    exit 1
fi

for ARM in weak frontier; do
    CONFIG="shinka_config_az_${ARM}_r1.json"
    RESULTS="results_az_${ARM}_r1"
    if [ ! -f "$TASKDIR/$CONFIG" ]; then
        echo "missing $TASKDIR/$CONFIG" >&2
        exit 1
    fi
    if [ -d "$TASKDIR/$RESULTS" ]; then
        echo "refusing to overwrite existing $TASKDIR/$RESULTS" >&2
        exit 1
    fi
    JOB="az_${ARM}_r1"
    sbatch --job-name="$JOB" \
           --chdir="$TASKDIR" \
           --output="$HOME/project/orch_${JOB}_%j.out" \
           "$HOME/project/orch_azure.sbatch" "$CONFIG" "$RESULTS" "$GENERATIONS"
done

echo
echo "submitted 2 Azure ensemble arms at $GENERATIONS generations"
squeue -u "$USER" -o "%.10i %.22j %.8T %.10M"
