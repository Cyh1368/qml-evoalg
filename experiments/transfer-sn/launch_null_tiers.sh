#!/usr/bin/env bash
# Null-symmetry control, weak and mid tiers. Companion to launch_null.sh.
#
# launch_null.sh ran the frontier ensemble on the null task and got 0/3 on the
# across-run motif count (criterion 5) against 3/3 on the real task. That test
# cannot be repeated at these tiers: the real-task motif rates are already near
# the floor (mid 1/5, weak 2/10), so even a perfect 0/n null gives Fisher
# p=1.000 (mid) and p=0.474 (weak). Criterion 5 is not the readout here.
#
# Pre-registered readout: criterion 6, the WITHIN-run motif rate, which is
# continuous and therefore far better powered (perfect separation at n=5 vs 5
# gives two-sided Mann-Whitney p=0.0079). Real-task within-run rates are
# mid 29.4% and weak 33.3%; the frontier null came in at 9.5%.
#
#   null rate falls near the frontier null's ~10%  -> criterion discriminates at
#       this tier too, and is not frontier-only.
#   null rate stays near the arm's real-task rate  -> that arm's motif rate is
#       baseline parameter-tying noise carrying no information about the task,
#       and the criterion has a minimum model tier.
#
# 20 generations, matching the real e1 arms, so the within-run rate is computed
# over a comparable proposal count. (The frontier null used 15, which was
# justified for a presence/absence readout but not for a rate denominator.)
#
# Measured cost at 20 generations: weak $0.61/run, mid $1.16/run => ~$9 total.
# max_api_costs set well above that so the cap cannot bind and truncate a run.
#
# Usage:  ./launch_null_tiers.sh          (run ON the Bouchet login node)
set -euo pipefail

TASKDIR="$HOME/project/transfer_sn_null"
SRCDIR="$HOME/project/transfer_sn"
GENERATIONS=20
NRUNS=5

[ -r "$HOME/.openrouter_key" ] || { echo "missing $HOME/.openrouter_key (mode 600)" >&2; exit 1; }
[ -f "$TASKDIR/dataset.npz" ] || { echo "missing $TASKDIR/dataset.npz" >&2; exit 1; }
[ -f "$TASKDIR/activate_eval_cluster.sh" ] || {
    echo "missing $TASKDIR/activate_eval_cluster.sh -- eval jobs will die at 'import numpy'" >&2; exit 1; }

# The evolution loop must never see the labelling rule.
if ls "$TASKDIR"/answer_key* >/dev/null 2>&1; then
    echo "REFUSING: answer key present in $TASKDIR" >&2; exit 1
fi

for tier in weak mid; do
    [ -f "$SRCDIR/shinka_config_or_${tier}_r1.json" ] || {
        echo "missing $SRCDIR/shinka_config_or_${tier}_r1.json" >&2; exit 1; }
    for i in $(seq 1 $NRUNS); do
        [ -d "$TASKDIR/results_null_${tier}_r$i" ] && {
            echo "refusing to overwrite $TASKDIR/results_null_${tier}_r$i" >&2; exit 1; }
    done
done

for tier in weak mid; do
    case "$tier" in
        weak) CAP=4.0 ;;
        mid)  CAP=6.0 ;;
    esac

    # One config per tier, written once, then copied verbatim.
    python3 - "$SRCDIR/shinka_config_or_${tier}_r1.json" \
              "$TASKDIR/shinka_config_null_${tier}_r1.json" \
              "$GENERATIONS" "$CAP" <<'PY'
import json, sys
src, dst, gens, cap = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
c = json.load(open(src))
c["evo"]["num_generations"] = gens
c["evo"]["max_api_costs"] = cap
assert c["evo"]["llm_dynamic_selection_kwargs"]["seed"] == 1, "bandit seed must be 1"
json.dump(c, open(dst, "w"), indent=4)
PY

    for i in $(seq 2 $NRUNS); do
        cp "$TASKDIR/shinka_config_null_${tier}_r1.json" \
           "$TASKDIR/shinka_config_null_${tier}_r$i.json"
    done

    echo "$tier config md5 (must be a single value):"
    md5sum "$TASKDIR"/shinka_config_null_${tier}_r*.json | awk '{print $1}' | sort -u

    for i in $(seq 1 $NRUNS); do
        JOB="null_${tier}_r$i"
        sbatch --job-name="$JOB" \
               --chdir="$TASKDIR" \
               --output="$HOME/project/orch_${JOB}_%j.out" \
               "$HOME/project/orch_zc.sbatch" \
               "shinka_config_null_${tier}_r$i.json" "results_null_${tier}_r$i" "$GENERATIONS"
    done
done

echo
echo "submitted $((NRUNS*2)) null-control runs (weak x$NRUNS, mid x$NRUNS) at $GENERATIONS generations"
squeue -u "$USER" -o "%.10i %.24j %.8T %.10M"
