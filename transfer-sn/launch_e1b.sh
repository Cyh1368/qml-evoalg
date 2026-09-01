#!/usr/bin/env bash
# Experiment 1b: is the noise floor a property of the weak roster, or of the
# instrument?
#
# Exp1 measured the weak arm: 10 byte-identical runs spanned 0.000-0.754,
# sd 0.2386 (EXP1_RESULTS.md). This repeats that measurement on the two other
# arms of BENCHMARK_PLAN.md Gate 1+2.
#
#   mid       gpt-5.4-mini / gemini-3-flash / haiku-4.5      medium   n=5
#   frontier  gpt-5.6-sol / opus-4.6 / gemini-3.1-pro        xhigh    n=2
#
# Protocol matches exp1 exactly except the roster: 20 generations, bandit seed
# fixed at 1, byte-identical configs within an arm (single md5), nothing else
# free to vary. Configs are derived from the *_r1 originals by changing only
# num_generations and max_api_costs.
#
# mid n=5 rather than the planned 10: exp1 showed the bandit seed contributes
# no measurable variance, so the existing mid_r1..r3 pool in as extra draws
# from the same distribution, giving effective n=8.
#
# frontier n=2 gives a range, not an sd. Reported as such.
#
# Cost, from stored trajectories at generation 20: mid $1.01/run, frontier
# $7.72/run => $5.05 + $15.44 = ~$20.5 expected. max_api_costs is set to 3x
# the measured spend per arm so the cap never binds and silently truncates a
# run: mid 3.0, frontier 24.0. Worst case $63, expected $20.5.
#
# Usage:  ./launch_e1b.sh          (run ON the Bouchet login node)
set -euo pipefail

TASKDIR="$HOME/project/transfer_sn"
GENERATIONS=20

[ -r "$HOME/.openrouter_key" ] || { echo "missing $HOME/.openrouter_key (mode 600)" >&2; exit 1; }

# arm:nruns:cap
ARMS=("mid:5:3.0" "frontier:2:24.0")

# Refuse before submitting anything if ANY run would clobber existing results,
# so we never end up with a half-submitted set.
for SPEC in "${ARMS[@]}"; do
    IFS=: read -r ARM N CAP <<<"$SPEC"
    [ -f "$TASKDIR/shinka_config_or_${ARM}_r1.json" ] || {
        echo "missing $TASKDIR/shinka_config_or_${ARM}_r1.json" >&2; exit 1; }
    for i in $(seq 1 "$N"); do
        [ -d "$TASKDIR/results_or_${ARM}_e1_r$i" ] && {
            echo "refusing to overwrite $TASKDIR/results_or_${ARM}_e1_r$i" >&2; exit 1; }
    done
done

for SPEC in "${ARMS[@]}"; do
    IFS=: read -r ARM N CAP <<<"$SPEC"

    # Write one config, then copy it verbatim: byte-identical by construction.
    python3 - "$TASKDIR/shinka_config_or_${ARM}_r1.json" \
              "$TASKDIR/shinka_config_or_${ARM}_e1_r1.json" \
              "$GENERATIONS" "$CAP" <<'PY'
import json, sys
src, dst, gens, cap = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
c = json.load(open(src))
c["evo"]["num_generations"] = gens
c["evo"]["max_api_costs"] = cap
assert c["evo"]["llm_dynamic_selection_kwargs"]["seed"] == 1, "bandit seed must be 1"
json.dump(c, open(dst, "w"), indent=4)
PY

    for i in $(seq 2 "$N"); do
        cp "$TASKDIR/shinka_config_or_${ARM}_e1_r1.json" \
           "$TASKDIR/shinka_config_or_${ARM}_e1_r$i.json"
    done

    echo "$ARM config md5 (must be a single value):"
    md5sum "$TASKDIR"/shinka_config_or_${ARM}_e1_r*.json | awk '{print $1}' | sort -u

    for i in $(seq 1 "$N"); do
        JOB="or_${ARM}_e1_r$i"
        sbatch --job-name="$JOB" \
               --chdir="$TASKDIR" \
               --output="$HOME/project/orch_${JOB}_%j.out" \
               "$HOME/project/orch_zc.sbatch" \
               "shinka_config_or_${ARM}_e1_r$i.json" "results_or_${ARM}_e1_r$i" "$GENERATIONS"
    done
    echo
done

echo "submitted mid x5 + frontier x2 at $GENERATIONS generations"
squeue -u "$USER" -o "%.10i %.24j %.8T %.10M"
