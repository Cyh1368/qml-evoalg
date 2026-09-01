#!/usr/bin/env bash
# Pull the three OpenRouter ensemble runs down from Bouchet and rebuild both
# viewers, so the results are visible in the browser.
#
# Run LOCALLY (not on the cluster). Needs the bouchet ControlMaster socket to be
# live; if it is not, open it first with the expect/Duo flow, otherwise every
# rsync will prompt for MFA.
#
#   ./sync_or_runs.sh
#
# What it does:
#   1. rsync results_or_{weak,mid,frontier}_r1/ into qml-ea/transfer-sn/
#   2. rebuild viz/data (the full run explorer: tree, diffs, metrics)
#   3. rebuild viz/circuits (the ansatz gallery)
#
# Safe to re-run while the runs are still going: rsync just picks up whatever
# has been written so far, and both builders read the sqlite files read-only.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE="bouchet:\$HOME/project/transfer_sn"
ARMS=(weak mid frontier)

if ! ssh -O check bouchet 2>/dev/null; then
    echo "WARNING: no live bouchet ControlMaster socket; rsync may prompt for Duo." >&2
fi

echo "=== 1/3  pulling run databases ==="
for ARM in "${ARMS[@]}"; do
    SRC="results_or_${ARM}_r1"
    # -L so the sqlite files come through as real files, not dangling symlinks.
    # --partial because these databases get large and the link is a VPN hop.
    rsync -avL --partial \
        --include='programs.sqlite' --include='*/' \
        --exclude='gen_*/' --exclude='*.out' --exclude='__pycache__/' \
        "bouchet:project/transfer_sn/${SRC}/" \
        "$REPO/transfer-sn/${SRC}/" || echo "  (skipped ${SRC}: not present yet)"
done

echo
echo "=== 2/3  rebuilding viz/data (run explorer) ==="
python3 "$REPO/viz/build_data.py" --repo-root "$REPO" --out "$REPO/viz/data"

echo
echo "=== 3/3  rebuilding viz/circuits (ansatz gallery) ==="
# The gallery needs numpy to read dataset.npz; .venv_render has it.
PY="$REPO/viz/.venv_render/bin/python"
[ -x "$PY" ] || PY=python3
"$PY" "$REPO/viz/circuits/build_circuits.py" \
    --repo-root "$REPO" --out "$REPO/viz/circuits/circuits_data.js"

echo
echo "done. View with:"
echo "  cd $REPO/viz          && python3 -m http.server 8080   # run explorer"
echo "  cd $REPO/viz/circuits && python3 -m http.server 8081   # ansatz gallery"
