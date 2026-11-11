#!/usr/bin/env bash
# Compute the three cheap corner extremes in parallel with multithreading.
# (l5p5 is handled by the still-running original worker.)
set -u
cd "$(dirname "$0")"
PY=../.venv-shinka-ttt/bin/python
mkdir -p logs histories

run_pair() {
  local l=$1 p=$2
  OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 \
  "$PY" - "$l" "$p" > "logs/extreme_l${l}_p${p}.log" 2>&1 <<'PYEOF'
import sys, json, time
import sweep
l, p = int(sys.argv[1]), int(sys.argv[2])
path = sweep.history_path(l, p)
if path.exists():
    print(f"l={l} p={p}: cached"); sys.exit(0)
t0 = time.time()
print(f"l={l} p={p}: training ({l*p*sweep.N_CEMOID_PARAMS} params)...", flush=True)
res = sweep.train_model(l, p)
path.write_text(json.dumps(res, indent=2))
print(f"l={l} p={p}: done in {time.time()-t0:.1f}s  final={res['final_test_accuracy']:.3f}")
PYEOF
}

run_pair 1 1 &
run_pair 1 5 &
run_pair 5 1 &
wait
echo "EXTREMES DONE"
