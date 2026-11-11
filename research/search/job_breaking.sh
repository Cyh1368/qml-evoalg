#!/bin/bash
# WP-SEARCH-BREAKING: verifier selectivity on a symmetry-BREAKING target.
# Declared in research/REVISED_PROTOCOL.md addendum A1 (2026-11-11) BEFORE running.
# ring_n6 with target alpha_1 (= invariant oracle + 1.0 * breaking component):
# the declared group is NOT a label symmetry here, so a verifier that pushes the
# search toward invariance must hurt. This is the selectivity test the referee asked
# for; it is a new prospective comparison, not a reanalysis of the frozen 120 runs.
#SBATCH --job-name=wp-brk
#SBATCH --partition=day
#SBATCH --cpus-per-task=36
#SBATCH --mem=36G
#SBATCH --time=03:00:00
#SBATCH --output=logs/%x-%j.out
set -euo pipefail
module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a ycrc-llm/1.0
export OPENBLAS_NUM_THREADS=1
cd "${REPO:-$SLURM_SUBMIT_DIR}"
OUT="${OUT:-logs/runs_breaking}"
mkdir -p "$OUT"
: > "$OUT/jobs.txt"
for arm in llm-fitness llm-verify llm-verify-repair; do
  for seed in 20261110 20261111 20261112 20261113 20261114 20261115 \
              20261116 20261117 20261118 20261119 20261120 20261121; do
    echo "--arm $arm --family ring_n6 --target alpha_1 --seed $seed --budget 12 \
--steps 120 --max-train 256 --out $OUT" >> "$OUT/jobs.txt"
  done
done
# also the two non-LLM baselines, for a matched-budget reference on the same target
for arm in random mutation-ea; do
  for seed in 20261110 20261111 20261112 20261113 20261114 20261115 \
              20261116 20261117 20261118 20261119 20261120 20261121; do
    echo "--arm $arm --family ring_n6 --target alpha_1 --seed $seed --budget 12 \
--steps 120 --max-train 256 --out $OUT" >> "$OUT/jobs.txt"
  done
done
wc -l "$OUT/jobs.txt"
xargs -a "$OUT/jobs.txt" -d '\n' -r -P "${WORKERS:-36}" -I{} \
  python3 -m research.search.harness run {}
echo "runs written to $OUT: $(ls "$OUT"/run_*.json 2>/dev/null | wc -l)"
