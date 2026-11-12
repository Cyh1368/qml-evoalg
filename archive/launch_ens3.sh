#!/usr/bin/env bash
# Launch the multi-provider ensemble arms for transfer-sn (T2, contextualized).
#
# Baseline being compared against: results_gpt56sol_r2, a SOLO openai/gpt-5.6-sol
# arm that found `permutation_equivariant_ansatz` at generation 33 (combined
# score 0.8713 -> 0.9372) and was stopped by its $10 cap at generation 63.
#
# Question these arms answer: does an ensemble of three SMALL models drawn from
# three different pretraining pipelines reach the equivariant solution, and does
# it get there in fewer generations than one large model did?
#
# Two replicates, because one run cannot separate "the ensemble finds it" from
# "this run got lucky". They differ only in the bandit seed.
#
# Usage:  ./launch_ens3.sh [generations]     (run ON the Bouchet login node)
set -euo pipefail

GENERATIONS="${1:-80}"
TASKDIR="$HOME/project/transfer_sn"

if [ ! -r "$HOME/.openrouter_key" ]; then
    echo "missing $HOME/.openrouter_key (mode 600)" >&2
    exit 1
fi

for REP in r1 r2; do
    CONFIG="shinka_config_ens3_${REP}.json"
    RESULTS="results_ens3_${REP}"
    if [ ! -f "$TASKDIR/$CONFIG" ]; then
        echo "missing $TASKDIR/$CONFIG" >&2
        exit 1
    fi
    if [ -d "$TASKDIR/$RESULTS" ]; then
        echo "refusing to overwrite existing $TASKDIR/$RESULTS" >&2
        exit 1
    fi
    JOB="ens3_${REP}"
    sbatch --job-name="$JOB" \
           --chdir="$TASKDIR" \
           --output="$HOME/project/orch_${JOB}_%j.out" \
           "$HOME/project/orch_zc.sbatch" "$CONFIG" "$RESULTS" "$GENERATIONS"
done

echo
echo "submitted 2 ensemble arms at $GENERATIONS generations"
squeue -u "$USER" -o "%.10i %.22j %.8T %.10M"
