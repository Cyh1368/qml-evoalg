#!/usr/bin/env bash
# Sourced by each Shinka SLURM eval job. Activates the env and exports the
# evaluation protocol. Eval jobs only train candidates; they never call any API.
set -e
module load miniconda 2>/dev/null || true
conda activate qml-ea

# The task backend lives beside the seed and is imported, not shown to the
# proposer; generation dirs are elsewhere, so put the task dir on the path.
export PYTHONPATH="$HOME/project/transfer_su2_v3:$PYTHONPATH"
export TASK_DATA="$HOME/project/transfer_su2_v3/dataset.npz"

export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-8}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-8}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-8}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib-shinka-zc}"
export PYTHONUNBUFFERED=1
export PYTHONIOENCODING=utf-8
# Concurrent eval jobs all import _backend from this shared NFS dir; racing
# to write __pycache__ produces intermittent [Errno 116] Stale file handle.
export PYTHONDONTWRITEBYTECODE=1

export NUM_RUNS="${NUM_RUNS:-1}"
export SAMPLE_WITH_REPLACEMENT="${SAMPLE_WITH_REPLACEMENT:-1}"
export USE_TEST_IN_SCORE="${USE_TEST_IN_SCORE:-0}"
# Absolute, and created here: eval jobs run from a generation directory, so a
# relative log path silently resolves to somewhere that does not exist.
#
# Per SLURM job, NOT shared. The backend names the training log after the
# TRAINING seed, which is the same constant for every candidate, so a shared
# directory means every concurrent eval job in every arm unlinks and rewrites
# one path on NFS. That produced [Errno 116] Stale file handle and a failed
# generation-0 evaluation on the first v3 launch attempt. Same root cause as
# the v2 __pycache__ race, different file.
export TTT_LOG_DIR="${TTT_LOG_DIR:-$HOME/project/transfer_su2_v3/logs/training/${SLURM_JOB_ID:-$$}}"
mkdir -p "$TTT_LOG_DIR" 2>/dev/null || true
export DATA_SEED="${DATA_SEED:-2027}"
export TRAIN_SIZE="${TRAIN_SIZE:-16}"
export VALIDATION_SIZE="${VALIDATION_SIZE:-300}"
export TEST_SIZE="${TEST_SIZE:-600}"
export STEPS_PER_EPOCH="${STEPS_PER_EPOCH:-30}"
export BATCH_SIZE="${BATCH_SIZE:-8}"
export LEARNING_RATE="${LEARNING_RATE:-0.03}"
export N_EPOCHS="${N_EPOCHS:-1000}"
export EARLY_STOPPING="${EARLY_STOPPING:-1}"
export PATIENCE="${PATIENCE:-75}"
export MIN_DELTA="${MIN_DELTA:-1e-4}"
export CONVERGENCE_THRESHOLD="${CONVERGENCE_THRESHOLD:-0.90}"
export EVAL_EVERY_EPOCHS="${EVAL_EVERY_EPOCHS:-1}"
export VERBOSE_TRAINING="${VERBOSE_TRAINING:-0}"
