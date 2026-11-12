#!/bin/bash
# A5.5: deployed-endpoint evaluation. Submit with DRY_RUN=1 first (opens nothing sealed);
# the real one-shot run happens only after the dry run's self-check passes.
#SBATCH --job-name=wp-deploy
#SBATCH --partition=day
#SBATCH --cpus-per-task=24
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x-%j.out
set -euo pipefail
module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
export OPENBLAS_NUM_THREADS=1
export LD_LIBRARY_PATH=/apps/software/2024a/software/Python/3.12.3-GCCcore-13.3.0/lib:${LD_LIBRARY_PATH:-}
cd "${REPO:-$SLURM_SUBMIT_DIR}"
if [ "${DRY_RUN:-0}" = "1" ]; then
  mkdir -p build/deployed
  python3 -m research.holdout_deployed --dry-run --workers "${WORKERS:-24}" \
    --out build/deployed/dry.json --access-log build/deployed/dry_access.json
else
  python3 -m research.holdout_deployed --workers "${WORKERS:-24}" \
    --out "${OUT:-research/HOLDOUT_DEPLOYED.json}" \
    --access-log "${ACCESS:-research/HOLDOUT_DEPLOYED_ACCESS.json}" \
    --allow-reread graphs_v1 \
    --reread-reason "no fresh class-disjoint graphs_n6 inputs exist: generate_holdout_v5
enumerated all 2^15 labeled 6-vertex graphs and found 0 isomorphism classes unused by
development plus holdouts v1-v4, so a first-and-only graphs read is impossible; this second
read is labelled post hoc in the paper, the manifest and the rebuttal"
fi
