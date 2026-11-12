#!/usr/bin/env bash
# Deploy the anonymized motif-discovery experiment to Bouchet: one run dir per
# proposer model. Does NOT launch (launch is a separate keyed step). Run locally.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE_BASE="project"   # under $HOME on Bouchet

# shared files copied into every run dir (config is added per-tag below)
FILES=(initial_program.py evaluate.py motif_analysis.py activate_eval_cluster.sh
       launch_shinka_cluster.py launch_with_key.sh data_splits.npz permutation_meta.json)

declare -A TAGS=(
  [haiku]="motif_anon_haiku"
  [sonnet]="motif_anon_sonnet"
  [gpt56sol]="motif_anon_gpt56sol"
)

for tag in "${!TAGS[@]}"; do
  dir="${TAGS[$tag]}"
  echo "=== deploying $tag -> ~/$REMOTE_BASE/$dir ==="
  ssh bouchet "mkdir -p ~/$REMOTE_BASE/$dir"
  rsync -a "${FILES[@]/#/$HERE/}" "bouchet:$REMOTE_BASE/$dir/"
  # place the per-model config as the canonical shinka_config.json
  rsync -a "$HERE/shinka_config.$tag.json" "bouchet:$REMOTE_BASE/$dir/shinka_config.json"
done
echo "deploy complete"
