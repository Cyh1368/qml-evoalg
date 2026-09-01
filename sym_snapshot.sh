#!/usr/bin/env bash
# Run the S_8 structural analysis against a SNAPSHOT of a live run's database.
# The runs are still writing, and sqlite in WAL mode on this NFS mount refuses
# even read-only URI opens from another host ("locking protocol"), so copy the
# db + -wal + -shm to local scratch first and analyse the copy.
# Environment first: /etc/profile and lmod reference unset variables, so `set -u`
# above this point kills the script before it starts.
source /etc/profile >/dev/null 2>&1 || true
module load miniconda >/dev/null 2>&1 || true
source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null || true
conda activate qml-ea

set -eu

for R in "$@"; do
  SRC="$HOME/project/transfer_sn/$R"
  TMP=$(mktemp -d)
  mkdir -p "$TMP/$R"
  cp "$SRC"/programs.sqlite* "$TMP/$R/" 2>/dev/null || true
  echo "############ $R ############"
  python "$HOME/project/sn_tools/symmetry_analysis.py" --results-dir "$TMP/$R" 2>&1 | tail -24
  rm -rf "$TMP"
done
