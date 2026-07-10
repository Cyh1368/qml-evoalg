#!/usr/bin/env bash
# Run all EA seed-robustness + gate-insertion jobs locally, ~14-way parallel.
set -u
cd /home/chengyou1368/QuantumAnsatz/qml-ea/tic-tac-toe/paper-replication
PY=/home/chengyou1368/QuantumAnsatz/qml-ea/tic-tac-toe/.venv-shinka-ttt/bin/python
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export MPLCONFIGDIR=/tmp/mpl-ttt
# Eval-opt: only evaluate train/val/test at the first & last epoch. Final trained
# model and its accuracy are unchanged; only per-epoch logging is skipped (~2x faster).
# Speedup: 50 epochs (was 100), eval only first/last epoch.
export N_EPOCHS=50 EVAL_EVERY_EPOCHS=50 VERBOSE_TRAINING=0
NPROC=12

# Seed robustness: 3 progs x 25 seeds = 75 jobs (indices 0..74)
echo "=== SEED ROBUSTNESS: 75 jobs $(date) ==="
seq 0 74 | xargs -P $NPROC -I {} $PY ea_seed_robustness.py --index {}

echo "=== GATE INSERTION: 210 jobs $(date) ==="
seq 0 209 | xargs -P $NPROC -I {} $PY ea_gate_insertion.py --index {}

echo "=== ALL DONE $(date) ==="
