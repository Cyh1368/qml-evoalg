#!/usr/bin/env bash
# Null-symmetry control: frontier ensemble on a task with no S_8 structure.
#
# Tests the criterion in VALIDATION_CRITERIA.md against a negative control.
# Inputs are distributionally identical to the real task (same scrambling, same
# feature_pairs, same density sampling); only the label rule changes, from
# "graph is connected" (S_8 invariant) to "deg(v*) >= 2" (not invariant).
# See make_dataset_null.py.
#
# Pre-registered readout: the fully-tied-parameter-family motif rate across
# runs, compared against 3/3 on the real task.
#   3/3 or 2/3 tied  -> criterion false-positives, hypothesis fails
#   0/3 or 1/3 tied  -> criterion discriminates (Fisher p=0.10 at n=3, so
#                       suggestive rather than significant)
#
# 15 generations: frontier signal saturates by generation 9-14 on the real task.
# Cost $5.50/run measured => ~$16.50 expected. max_api_costs 9.0 per run so the
# cap cannot bind and silently truncate a run.
#
# Usage:  ./launch_null.sh          (run ON the Bouchet login node)
set -euo pipefail

TASKDIR="$HOME/project/transfer_sn_null"
SRCCFG="$HOME/project/transfer_sn/shinka_config_or_frontier_r1.json"
GENERATIONS=15
NRUNS=3

[ -r "$HOME/.openrouter_key" ] || { echo "missing $HOME/.openrouter_key (mode 600)" >&2; exit 1; }
[ -f "$SRCCFG" ] || { echo "missing $SRCCFG" >&2; exit 1; }
[ -f "$TASKDIR/dataset.npz" ] || { echo "missing $TASKDIR/dataset.npz" >&2; exit 1; }

# The evolution loop must never see the labelling rule.
if ls "$TASKDIR"/answer_key* >/dev/null 2>&1; then
    echo "REFUSING: answer key present in $TASKDIR" >&2; exit 1
fi

for i in $(seq 1 $NRUNS); do
    [ -d "$TASKDIR/results_null_frontier_r$i" ] && {
        echo "refusing to overwrite $TASKDIR/results_null_frontier_r$i" >&2; exit 1; }
done

# One config, written once, then copied verbatim: byte-identical by construction.
python3 - "$SRCCFG" "$TASKDIR/shinka_config_null_frontier_r1.json" "$GENERATIONS" <<'PY'
import json, sys
src, dst, gens = sys.argv[1], sys.argv[2], int(sys.argv[3])
c = json.load(open(src))
c["evo"]["num_generations"] = gens
c["evo"]["max_api_costs"] = 9.0
assert c["evo"]["llm_dynamic_selection_kwargs"]["seed"] == 1, "bandit seed must be 1"
json.dump(c, open(dst, "w"), indent=4)
PY

for i in $(seq 2 $NRUNS); do
    cp "$TASKDIR/shinka_config_null_frontier_r1.json" \
       "$TASKDIR/shinka_config_null_frontier_r$i.json"
done

echo "config md5 (must be a single value):"
md5sum "$TASKDIR"/shinka_config_null_frontier_r*.json | awk '{print $1}' | sort -u

for i in $(seq 1 $NRUNS); do
    JOB="null_frontier_r$i"
    sbatch --job-name="$JOB" \
           --chdir="$TASKDIR" \
           --output="$HOME/project/orch_${JOB}_%j.out" \
           "$HOME/project/orch_zc.sbatch" \
           "shinka_config_null_frontier_r$i.json" "results_null_frontier_r$i" "$GENERATIONS"
done

echo
echo "submitted $NRUNS null-control frontier runs at $GENERATIONS generations"
squeue -u "$USER" -o "%.10i %.24j %.8T %.10M"
