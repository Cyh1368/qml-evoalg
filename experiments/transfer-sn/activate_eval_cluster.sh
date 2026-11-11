#!/usr/bin/env bash
# Activation wrapper sourced by each Shinka SLURM eval job on Bouchet.
# Activates the qml-ea conda env and exports the CONVERGED eval protocol
# (full-data + validation-loss early stopping + restore-best-weights) so every
# candidate is ranked the same way as the cemoid paper-replication analyses.
set -e
module load miniconda 2>/dev/null || true
conda activate qml-ea

# NOTE: eval jobs only TRAIN candidates — they never call OpenRouter, so no API
# key is needed or stored here. The orchestrator (login node) gets the key from
# its own environment at launch time.

# Single-thread the linear algebra; each eval gets its own SLURM cpus.
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-8}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-8}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-8}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib-shinka-ttt}"
export PYTHONUNBUFFERED=1
export PYTHONIOENCODING=utf-8

# --- Converged eval protocol (the corrected stopping criterion) ---
export NUM_RUNS="${NUM_RUNS:-1}"
export SAMPLE_WITH_REPLACEMENT="${SAMPLE_WITH_REPLACEMENT:-1}"
export USE_TEST_IN_SCORE="${USE_TEST_IN_SCORE:-0}"
export TTT_LOG_DIR="${TTT_LOG_DIR:-$HOME/project/transfer_sn/logs/training/${SLURM_JOB_ID:-$$}}"
mkdir -p "$TTT_LOG_DIR" 2>/dev/null || true
export DATA_SEED="${DATA_SEED:-2027}"
export TRAIN_SIZE="${TRAIN_SIZE:-450}"
export VALIDATION_SIZE="${VALIDATION_SIZE:-300}"
export TEST_SIZE="${TEST_SIZE:-600}"
export STEPS_PER_EPOCH="${STEPS_PER_EPOCH:-30}"
export BATCH_SIZE="${BATCH_SIZE:-15}"
export LEARNING_RATE="${LEARNING_RATE:-0.03}"
export N_EPOCHS="${N_EPOCHS:-1000}"      # hard cap (max_epochs); early stopping ends sooner
export EARLY_STOPPING="${EARLY_STOPPING:-1}"
export PATIENCE="${PATIENCE:-75}"
export MIN_DELTA="${MIN_DELTA:-1e-4}"
export CONVERGENCE_THRESHOLD="${CONVERGENCE_THRESHOLD:-0.90}"
export EVAL_EVERY_EPOCHS="${EVAL_EVERY_EPOCHS:-1}"
export VERBOSE_TRAINING="${VERBOSE_TRAINING:-0}"
export TASK_DATA="$HOME/project/transfer_sn/dataset.npz"
