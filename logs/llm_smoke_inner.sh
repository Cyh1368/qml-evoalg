#!/bin/bash
#SBATCH --job-name=llmsmoke
#SBATCH --partition=devel
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
set -euo pipefail
module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
module load ycrc-llm/1.0
export OPENBLAS_NUM_THREADS=1
cd /home/cpsc4710_ch2499/qml-evoalg
echo "OPENAI_BASE_URL=${OPENAI_BASE_URL:-UNSET}"
.venv/bin/python - <<'PY'
import os
from research.search.llmclient import chat_completion
r=chat_completion([{"role":"user","content":"Reply with exactly: {\"ok\": true}"}], model="ycrc-local", reasoning_effort="none")
print("MODEL",r["model"],"tokens",r["total_tokens"],"latency %.1fs"%r["latency"])
print("CONTENT",repr(r["content"][:200]))
PY
