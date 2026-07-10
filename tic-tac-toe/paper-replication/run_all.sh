#!/usr/bin/env bash
# Launch the full (l,p) sweep across NSHARDS parallel single-threaded workers,
# then draw the 5x5 grid plot once every worker has finished.
set -u
cd "$(dirname "$0")"
PY=../.venv-shinka-ttt/bin/python
NSHARDS=${NSHARDS:-8}
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

mkdir -p logs
pids=()
for ((k=0; k<NSHARDS; k++)); do
  "$PY" sweep.py --shard "$k" --nshards "$NSHARDS" --no-plot \
      > "logs/shard_${k}.log" 2>&1 &
  pids+=($!)
done
echo "launched $NSHARDS workers: ${pids[*]}"

fail=0
for pid in "${pids[@]}"; do
  wait "$pid" || fail=1
done

echo "all workers finished (fail=$fail); drawing plot"
"$PY" sweep.py --plot-only
echo "DONE"
