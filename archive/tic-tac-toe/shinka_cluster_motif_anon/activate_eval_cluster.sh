#!/usr/bin/env bash
# Activation wrapper sourced by each Shinka SLURM eval job on Bouchet (anonymized
# motif-discovery variant). Activates the qml-ea conda env and exports the
# CONVERGED eval protocol. Eval jobs only TRAIN candidates; they never call
# OpenRouter, so no API key is needed here.
set -e
module load miniconda 2>/dev/null || true
conda activate qml-ea

# Absolute path to the precomputed, qubit-permuted dataset that lives next to
# this script — robust to the candidate program being copied to a temp dir.
_ANON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export TASK_DATA_NPZ="${TASK_DATA_NPZ:-$_ANON_DIR/data_splits.npz}"

export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-8}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-8}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-8}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib-shinka-anon}"
export PYTHONUNBUFFERED=1
export PYTHONIOENCODING=utf-8

# --- Converged eval protocol (identical to the leaky run for comparability) ---
export NUM_RUNS="${NUM_RUNS:-1}"
export USE_TEST_IN_SCORE="${USE_TEST_IN_SCORE:-0}"
export TTT_LOG_DIR="${TTT_LOG_DIR:-logs/anon_training}"
export STEPS_PER_EPOCH="${STEPS_PER_EPOCH:-30}"
export BATCH_SIZE="${BATCH_SIZE:-15}"
export LEARNING_RATE="${LEARNING_RATE:-0.03}"
export N_EPOCHS="${N_EPOCHS:-1000}"      # hard cap; validation early stopping ends sooner
export EARLY_STOPPING="${EARLY_STOPPING:-1}"
export PATIENCE="${PATIENCE:-75}"
export MIN_DELTA="${MIN_DELTA:-1e-4}"
export CONVERGENCE_THRESHOLD="${CONVERGENCE_THRESHOLD:-0.90}"
export EVAL_EVERY_EPOCHS="${EVAL_EVERY_EPOCHS:-1}"
export VERBOSE_TRAINING="${VERBOSE_TRAINING:-0}"
