#!/usr/bin/env bash
# RESUME the Azure ensemble arms in place, past their first stopping points.
#
# ShinkaEvolve resumes automatically when --results-dir already holds a
# programs.sqlite with last_iteration > 0: it reloads the bandit state, the
# completed-generation count, and crucially the API cost already spent
# (async_runner: `self.total_api_cost = existing_costs`).
#
# Two consequences that decide what the arguments mean:
#   max_api_costs is a LIFETIME total, not an increment. $50 leaves mid ~$35 and
#     frontier ~$33 of headroom; weak has spent almost nothing.
#   num_generations is a TARGET total, not an increment
#     (_get_remaining_generation_slots = num_generations - next_to_submit).
#
# Where each arm stopped, and why:
#   az_weak_r1      gen 78, $1.30 of $6    -- finished its 80, plateaued at gen 64
#   az_mid_r1       gen 72, $15.17 of $15  -- TRUNCATED on the cap, still improving
#   az_frontier_r1  gen 79, $17.03 of $30  -- finished its 80, best came at gen 77
#
# Measured burn: weak $0.017/gen, mid $0.211/gen, frontier $0.216/gen. Reaching
# generation 200 therefore costs about $42 for mid and $43 for frontier, so the
# $50 cap and the 200-generation target bind at roughly the same place and
# whichever arrives first stops the run.
#
# Usage:  ./resume_azure_ens.sh [target_generations]   (on the Bouchet login node)
set -euo pipefail

GENERATIONS="${1:-200}"
TASKDIR="$HOME/project/transfer_sn"

if [ ! -r "$HOME/.azure_key" ]; then
    echo "missing $HOME/.azure_key (mode 600)" >&2
    exit 1
fi

for ARM in weak mid frontier; do
    CONFIG="shinka_config_az_${ARM}_r1.json"
    RESULTS="results_az_${ARM}_r1"
    DB="$TASKDIR/$RESULTS/programs.sqlite"

    # A missing database would silently start a FRESH run and overwrite nothing,
    # but it would also throw away the point of resuming. Refuse instead.
    if [ ! -f "$DB" ]; then
        echo "refusing: $DB does not exist, nothing to resume" >&2
        exit 1
    fi
    if [ ! -f "$TASKDIR/$CONFIG" ]; then
        echo "missing $TASKDIR/$CONFIG" >&2
        exit 1
    fi

    JOB="az_${ARM}_r1_cont"
    sbatch --job-name="$JOB" \
           --chdir="$TASKDIR" \
           --output="$HOME/project/orch_${JOB}_%j.out" \
           "$HOME/project/orch_azure.sbatch" "$CONFIG" "$RESULTS" "$GENERATIONS"
done

echo
echo "resumed 3 Azure arms toward generation $GENERATIONS, \$50 lifetime cap each"
squeue -u "$USER" -o "%.10i %.22j %.8T %.10M"
