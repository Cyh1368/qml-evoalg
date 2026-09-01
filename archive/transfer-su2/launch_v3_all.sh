#!/usr/bin/env bash
# Launch all six v3 arms: two task variants x three proposer models.
#
#   zc_su2_v3        zero-context   -- proposer sees a 56-line stub and is told
#                                      nothing about the data
#   transfer_su2_v3  contextualized -- proposer sees the full seed source and is
#                                      told the inputs are quantum states with a
#                                      dataset-supplied correlator readout
#
# Both run the IDENTICAL evaluation protocol (same dataset, TRAIN_SIZE=16,
# BATCH_SIZE=8, same stopping rule and scorer), so the only variable across the
# two variants is how much the proposer is told. v1 confounded this by training
# the contextualized arm on 450 samples and the zero-context arm on 16.
#
# Usage:  ./launch_v3_all.sh [generations]     (run ON the Bouchet login node)
set -euo pipefail

GENERATIONS="${1:-80}"
PROJECT="$HOME/project"

if [ ! -r "$HOME/.openrouter_key" ]; then
    echo "missing $HOME/.openrouter_key (mode 600)" >&2
    exit 1
fi

for VARIANT in zc_su2_v3 transfer_su2_v3; do
    for MODEL in haiku sonnet gpt56sol; do
        CONFIG="shinka_config_${MODEL}.json"
        RESULTS="results_${MODEL}"
        if [ ! -f "$PROJECT/$VARIANT/$CONFIG" ]; then
            echo "missing $PROJECT/$VARIANT/$CONFIG" >&2
            exit 1
        fi
        JOB="${VARIANT}_${MODEL}"
        sbatch --job-name="$JOB" \
               --chdir="$PROJECT/$VARIANT" \
               --output="$PROJECT/orch_${JOB}_%j.out" \
               "$PROJECT/orch_zc.sbatch" "$CONFIG" "$RESULTS" "$GENERATIONS"
    done
done

echo
echo "submitted 6 arms at $GENERATIONS generations"
squeue -u "$USER" -o "%.10i %.28j %.8T %.10M"
