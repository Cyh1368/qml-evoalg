#!/usr/bin/env bash
# Pull the null-control ShinkaEvolve runs off Bouchet and rebuild the viewer data.
#
# The null arm trains on transfer_sn_null/dataset.npz, a DIFFERENT dataset from
# the main S_n transfer task, so it is landed under its own `null/` variant dir
# rather than alongside the real-task runs. See viz/README.md for why the
# scores are not comparable across the two conditions.
#
# Usage: viz/sync_null_runs.sh [r1 r2 r3 ...]   (default: all three)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_BASE="\$HOME/project/transfer_sn_null"
DEST_BASE="$REPO/transfer-sn/null"
RUNS=("$@")
[ ${#RUNS[@]} -eq 0 ] && RUNS=(r1 r2 r3)

mkdir -p "$DEST_BASE"

for r in "${RUNS[@]}"; do
  remote="$REMOTE_BASE/results_null_frontier_$r"
  dest="$DEST_BASE/results_frontier_$r"

  # Refuse to sync a run whose orchestrator is still running: the sqlite is
  # WAL-locked and would land half-written.
  if ssh bouchet "squeue -u \$USER -h -o %j | grep -qx null_frontier_$r"; then
    echo "SKIP $r: orchestrator still RUNNING"
    continue
  fi
  if ! ssh bouchet "test -f $remote/programs.sqlite"; then
    echo "SKIP $r: no programs.sqlite at $remote"
    continue
  fi

  # Fold the WAL into the main db remotely so we copy one consistent file.
  ssh bouchet "~/.conda/envs/qml-ea/bin/python -c \"
import sqlite3
c=sqlite3.connect('$remote/programs.sqlite')
c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
c.close()\"" >/dev/null

  echo "SYNC $r -> ${dest#$REPO/}"
  mkdir -p "$dest"
  rsync -az --delete \
    --exclude 'gen_*/results/job_log.*' \
    "bouchet:$remote/" "$dest/"
done

echo "=== rebuilding viewer data ==="
python3 "$REPO/viz/build_data.py" --repo-root "$REPO" --out "$REPO/viz/data"
