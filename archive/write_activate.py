"""Write the eval activation script for each zero-context task.

Two things differ from the originals: PYTHONPATH must include the task dir so the
hidden `_backend` module resolves from inside a generation directory, and the
SU(2) task trains on very few examples so that generalisation, not raw accuracy,
does the discriminating.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REMOTE = "$HOME/project"

COMMON = """#!/usr/bin/env bash
# Sourced by each Shinka SLURM eval job. Activates the env and exports the
# evaluation protocol. Eval jobs only train candidates; they never call any API.
set -e
module load miniconda 2>/dev/null || true
conda activate qml-ea

# The task backend lives beside the seed and is imported, not shown to the
# proposer; generation dirs are elsewhere, so put the task dir on the path.
export PYTHONPATH="{remote}/{name}:$PYTHONPATH"
export TASK_DATA="{remote}/{name}/{data}"

export OMP_NUM_THREADS="${{OMP_NUM_THREADS:-8}}"
export OPENBLAS_NUM_THREADS="${{OPENBLAS_NUM_THREADS:-8}}"
export MKL_NUM_THREADS="${{MKL_NUM_THREADS:-8}}"
export NUMEXPR_NUM_THREADS="${{NUMEXPR_NUM_THREADS:-8}}"
export MPLCONFIGDIR="${{MPLCONFIGDIR:-/tmp/matplotlib-shinka-zc}}"
export PYTHONUNBUFFERED=1
export PYTHONIOENCODING=utf-8
# Concurrent eval jobs all import _backend from this shared NFS dir; racing
# to write __pycache__ produces intermittent [Errno 116] Stale file handle.
export PYTHONDONTWRITEBYTECODE=1

export NUM_RUNS="${{NUM_RUNS:-1}}"
export SAMPLE_WITH_REPLACEMENT="${{SAMPLE_WITH_REPLACEMENT:-1}}"
export USE_TEST_IN_SCORE="${{USE_TEST_IN_SCORE:-0}}"
# Absolute, and created here: eval jobs run from a generation directory, so a
# relative log path silently resolves to somewhere that does not exist.
#
# Per SLURM job, NOT shared. The backend names the training log after the
# TRAINING seed, which is the same constant for every candidate, so a shared
# directory means every concurrent eval job in every arm unlinks and rewrites
# one path on NFS. That produced [Errno 116] Stale file handle and a failed
# generation-0 evaluation on the first v3 launch attempt. Same root cause as
# the v2 __pycache__ race, different file.
export TTT_LOG_DIR="${{TTT_LOG_DIR:-{remote}/{name}/logs/training/${{SLURM_JOB_ID:-$$}}}}"
mkdir -p "$TTT_LOG_DIR" 2>/dev/null || true
export DATA_SEED="${{DATA_SEED:-2027}}"
export TRAIN_SIZE="${{TRAIN_SIZE:-{train}}}"
export VALIDATION_SIZE="${{VALIDATION_SIZE:-300}}"
export TEST_SIZE="${{TEST_SIZE:-600}}"
export STEPS_PER_EPOCH="${{STEPS_PER_EPOCH:-30}}"
export BATCH_SIZE="${{BATCH_SIZE:-{batch}}}"
export LEARNING_RATE="${{LEARNING_RATE:-0.03}}"
export N_EPOCHS="${{N_EPOCHS:-1000}}"
export EARLY_STOPPING="${{EARLY_STOPPING:-1}}"
export PATIENCE="${{PATIENCE:-75}}"
export MIN_DELTA="${{MIN_DELTA:-1e-4}}"
export CONVERGENCE_THRESHOLD="${{CONVERGENCE_THRESHOLD:-0.90}}"
export EVAL_EVERY_EPOCHS="${{EVAL_EVERY_EPOCHS:-1}}"
export VERBOSE_TRAINING="${{VERBOSE_TRAINING:-0}}"
"""

TASKS = {
    "zc-ttt": {"data": "data_splits.npz", "train": 450, "batch": 15},
    "zc-sn": {"data": "dataset.npz", "train": 450, "batch": 15},
    # Few-shot: correct structure is what still generalises from 16 examples.
    # Each scoring redesign deploys to a fresh remote dir; older results stay put.
    "zc-su2": {"data": "dataset.npz", "train": 16, "batch": 8,
               "remote": "zc_su2_v3"},
    # The contextualized arm of the same task. It runs the IDENTICAL evaluation
    # protocol as zc-su2 (same data, train size, batch size, stopping rule) so
    # the only difference between the two arms is how much the proposer is told.
    # v1 ran this at train=450/batch=15, which confounded context with training
    # budget and is not comparable to the zero-context arm.
    "transfer-su2": {"data": "dataset.npz", "train": 16, "batch": 8,
                     "remote": "transfer_su2_v3"},
}

for name, cfg in TASKS.items():
    remote_name = cfg.get("remote", name.replace("-", "_"))
    text = COMMON.format(remote=REMOTE, name=remote_name, data=cfg["data"],
                         train=cfg["train"], batch=cfg["batch"])
    p = ROOT / name / "activate_eval_cluster.sh"
    p.write_text(text)
    p.chmod(0o755)
    print(f"wrote {p.relative_to(ROOT)}  (remote dir {remote_name}, train={cfg['train']})")
