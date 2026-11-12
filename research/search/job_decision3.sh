#!/bin/bash
# A7.3/A7.4/A7.5: gate-parity decision comparison with never-repair, frozen vs within-regime
# thresholds, measured timings, mixture objective and the calibrated tolerance rules, on the
# frozen 120 development runs. Supersedes decision_rules2 for the multi-rule comparison; the A6
# record is retained unchanged as the audited artifact of what was run.
#SBATCH --job-name=dr3-parity
#SBATCH --partition=day
#SBATCH --cpus-per-task=24
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --output=logs/%x-%j.out
set -euo pipefail
module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
export OPENBLAS_NUM_THREADS=1
export LD_LIBRARY_PATH=/apps/software/2024a/software/Python/3.12.3-GCCcore-13.3.0/lib:${LD_LIBRARY_PATH:-}
cd "${REPO:-$SLURM_SUBMIT_DIR}"
python3 -m research.search.decision_rules3 \
  --runs "${RUNDIR:-logs/runs_confirm}" \
  --workers "${WORKERS:-24}" \
  --out "${OUT:-research/search/decision_rules3.json}"
