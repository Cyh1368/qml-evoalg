#!/usr/bin/env bash
#SBATCH --partition=day
#SBATCH --time=23:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=%x_%j.out
# One Azure-routed orchestrator arm.
# Usage: sbatch --job-name=<name> --chdir=$HOME/project/transfer_sn \
#          $HOME/project/orch_azure.sbatch <config.json> <results_dir> <generations>

CONFIG="${1:?config json required}"
RESULTS="${2:?results dir required}"
GENERATIONS="${3:-80}"

# Environment first: /etc/profile and lmod reference unset variables, so `set -u`
# here would kill the job before it starts.
source /etc/profile >/dev/null 2>&1 || true
module load miniconda >/dev/null 2>&1 || true
source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null || true
conda activate qml-ea

set -eu

# Credentials from a mode-600 file so they never appear in job args or scontrol.
set -a
. "$HOME/.azure_key"
set +a

echo "host=$(hostname) dir=$(pwd) config=$CONFIG results=$RESULTS gens=$GENERATIONS"
echo "start=$(date)"

# Fail loudly here rather than 20 retries deep in a proposal call.
python - <<'PY'
import os
import shinka.llm.client as c
from shinka.llm.providers.pricing import is_reasoning_model, get_model_prices
assert "PATCHED: AzureOpenAI appends" in open(c.__file__).read(), \
    "azure client fix missing -- run patch_azure_client.py"
assert os.getenv("AZURE_API_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"), \
    "azure credentials not in environment"
# Only gpt-5.6-sol may carry reasoning.effort on this resource.
for m, want in (("gpt-5.6-sol", True), ("DeepSeek-V4-Pro", False),
                ("Mistral-Large-3", False)):
    got = is_reasoning_model(m)
    assert got == want, f"{m} is_reasoning={got}, expected {want}"
    get_model_prices(m)  # raises if the pricing row is missing -> cost cap dead
print("preflight OK: azure client patched, creds present, pricing+flags sane")
PY

python launch_shinka_cluster.py \
    --generations "$GENERATIONS" \
    --max-eval-jobs 5 \
    --max-proposal-jobs 3 \
    --config "$(pwd)/$CONFIG" \
    --results-dir "$(pwd)/$RESULTS"

echo "finished=$(date)"
