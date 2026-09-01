#!/usr/bin/env bash
# Pull the null-control ShinkaEvolve runs off Bouchet and rebuild the viewer data.
#
# The null arm trains on transfer_sn_null/dataset.npz, a DIFFERENT dataset from
# the main S_n transfer task, so it is landed under its own `null/` variant dir
# rather than alongside the real-task runs. See viz/README.md for why the
# scores are not comparable across the two conditions.
#
# Remote dirs are named results_null_<tier>_<run>; locally they land as
# results_<tier>_<run>, which is what build_data.py turns into the run slug
# sn-transfer-null-<tier>_<run>.
#
# Usage:
#   viz/sync_null_runs.sh                      # every null run present remotely
#   viz/sync_null_runs.sh weak_r1 mid_r3       # just these
#   viz/sync_null_runs.sh r1 r2                # bare rN means frontier (legacy)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_BASE="\$HOME/project/transfer_sn_null"
DEST_BASE="$REPO/experiments/transfer-sn/null"
RUNS=("$@")

# Default: discover every completed run directory on the cluster.
if [ ${#RUNS[@]} -eq 0 ]; then
  # (bash 3.2 on macOS has no mapfile)
  RUNS=()
  while IFS= read -r line; do
    [ -n "$line" ] && RUNS+=("$line")
  done < <(ssh bouchet "ls -d $REMOTE_BASE/results_null_* 2>/dev/null" \
           | sed 's#.*/results_null_##')
  [ ${#RUNS[@]} -eq 0 ] && { echo "no results_null_* dirs found remotely" >&2; exit 1; }
  echo "discovered ${#RUNS[@]} remote run(s): ${RUNS[*]}"
fi

mkdir -p "$DEST_BASE"
synced=0

for r in "${RUNS[@]}"; do
  # bare "r1" is shorthand for the original frontier arm
  case "$r" in r[0-9]*) name="frontier_$r" ;; *) name="$r" ;; esac

  remote="$REMOTE_BASE/results_null_$name"
  dest="$DEST_BASE/results_$name"

  # Refuse to sync a run whose orchestrator is still running: the sqlite is
  # WAL-locked and would land half-written.
  if ssh bouchet "squeue -u \$USER -h -o %j | grep -qx null_$name"; then
    echo "SKIP $name: orchestrator still RUNNING"
    continue
  fi
  if ! ssh bouchet "test -f $remote/programs.sqlite"; then
    echo "SKIP $name: no programs.sqlite at $remote"
    continue
  fi

  # Fold the WAL into the main db remotely so we copy one consistent file.
  ssh bouchet "~/.conda/envs/qml-ea/bin/python -c \"
import sqlite3
c=sqlite3.connect('$remote/programs.sqlite')
c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
c.close()\"" >/dev/null

  echo "SYNC $name -> ${dest#$REPO/}"
  mkdir -p "$dest"
  rsync -az --delete \
    --exclude 'gen_*/results/job_log.*' \
    "bouchet:$remote/" "$dest/"
  synced=$((synced + 1))
done

echo "=== synced $synced run(s); rebuilding viewer data ==="
python3 "$REPO/viz/build_data.py" --repo-root "$REPO" --scan-root "$REPO/experiments" --out "$REPO/viz/data"
