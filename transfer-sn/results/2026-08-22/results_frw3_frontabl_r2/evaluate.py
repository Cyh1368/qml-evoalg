"""Evaluator for ShinkaEvolve 8-qubit record-classification ansatz search."""

from __future__ import annotations

import json
import math
import os
from functools import partial
from pathlib import Path

import numpy as np

from shinka.core import run_shinka_eval


NUM_RUNS = int(os.environ.get("NUM_RUNS", "1"))
NUM_WORKERS = int(os.environ.get("NUM_WORKERS", "1"))
BASE_SEED = int(os.environ.get("BASE_SEED", "1000"))

N_EPOCHS = int(os.environ.get("N_EPOCHS", "1000"))
STEPS_PER_EPOCH = int(os.environ.get("STEPS_PER_EPOCH", "30"))

MAX_PARAMS = int(os.environ.get("MAX_PARAMS", "768"))
SEED_TOTAL_PARAMS = 146
EXPECTED_UPLOADS = 3
EXPECTED_REPEATS = 2
USE_TEST_IN_SCORE = bool(int(os.environ.get("USE_TEST_IN_SCORE", "0")))

# --- Score rescaling -------------------------------------------------------
# The raw combined score is compressed into roughly [0.64, 0.95], and every
# interesting difference lives in the third decimal place. The proposer reads
# these numbers as text, so that compression wastes most of the signal: the gap
# between "found the symmetry" and "did not" reads as 0.9483 vs 0.8546.
#
# Map the two reference points onto 0 and 1:
#   SCORE_ANCHOR_SEED  the seed program, measured at 0.8546 and reproduced
#                      bit-identically by every arm launched on this task
#   SCORE_ANCHOR_BEST  the best solution that actually uses the permutation
#                      symmetry: results_gpt56sol_r2 generation 51, 4 unique
#                      parameters with 3 fully-tied single-qubit families
#
# This is affine, so it is invisible to the search machinery: parent selection
# normalises by median and MAD (both scale with the transform, so the sigmoid
# argument is unchanged) and archive selection ranks by percentile (invariant
# under any monotone map). The ONLY thing that changes is the number the
# proposer sees. Scores below the seed go negative by design.
#
# Old runs stay comparable: apply the same map to their stored raw scores.
# Full precision, read back from the runs rather than the rounded display
# values, so the seed lands on exactly 0.0 instead of -0.0004.
SCORE_ANCHOR_SEED = float(os.environ.get("SCORE_ANCHOR_SEED", "0.8545656310200919"))
SCORE_ANCHOR_BEST = float(os.environ.get("SCORE_ANCHOR_BEST", "0.9483080295061955"))
SCORE_RESCALE = bool(int(os.environ.get("SCORE_RESCALE", "1")))


def rescale_score(raw: float) -> float:
    """Affine map sending the seed to 0 and the best symmetric solution to 1."""
    if not SCORE_RESCALE:
        return float(raw)
    span = SCORE_ANCHOR_BEST - SCORE_ANCHOR_SEED
    if span <= 0:
        return float(raw)
    return float((float(raw) - SCORE_ANCHOR_SEED) / span)


def get_experiment_kwargs(run_index: int) -> dict:
    return {
        "seed": BASE_SEED + run_index,
        "verbose": bool(int(os.environ.get("VERBOSE_TRAINING", "0"))),
    }


def _finite_number(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def validate_fn(result) -> tuple[bool, str | None]:
    if not isinstance(result, dict):
        return False, f"Expected dict result, got {type(result).__name__}"
    if not result.get("spec_valid", False):
        return False, result.get("error", "ANSATZ_SPEC is invalid")
    if result.get("n_qubits") != 8:
        return False, f"Expected 8 qubits, got {result.get('n_qubits')}"
    if result.get("n_uploads") != EXPECTED_UPLOADS or result.get("n_repeats") != EXPECTED_REPEATS:
        return False, "The fixed architecture layout must be preserved"
    n_params = result.get("n_params")
    if not isinstance(n_params, int) or n_params <= 0 or n_params > MAX_PARAMS:
        return False, f"Invalid parameter count: {n_params}"

    for key in (
        "train_accuracy", "validation_accuracy", "test_accuracy",
        "train_loss", "validation_loss", "test_loss",
        "generalization_gap", "parameter_efficiency",
    ):
        if not _finite_number(result.get(key)):
            return False, f"{key} is missing or non-finite: {result.get(key)}"
    for key in ("train_accuracy", "validation_accuracy", "test_accuracy"):
        value = float(result[key])
        if not 0.0 <= value <= 1.0:
            return False, f"{key} is outside [0, 1]: {value}"

    for gate_name, wires in result.get("operations", []):
        if len(wires) > 2:
            return False, f"Unsupported operation arity: {gate_name} on wires {wires}"
    return True, None


def score_result(result: dict) -> dict:
    primary_acc_key = "test_accuracy" if USE_TEST_IN_SCORE else "validation_accuracy"
    primary_loss_key = "test_loss" if USE_TEST_IN_SCORE else "validation_loss"
    primary_accuracy = float(result[primary_acc_key])
    primary_loss = float(result[primary_loss_key])
    train_accuracy = float(result["train_accuracy"])
    test_accuracy = float(result["test_accuracy"])
    gap = abs(train_accuracy - test_accuracy)
    n_params = max(float(result["n_params"]), 1.0)
    max_steps = max(float(result.get("max_steps") or (N_EPOCHS * STEPS_PER_EPOCH)), 1.0)
    convergence_step = result.get("convergence_step")

    gap_score = max(0.0, 1.0 - min(gap / 0.35, 1.0))
    loss_score = 1.0 / (1.0 + max(primary_loss, 0.0))
    parameter_efficiency_score = min(1.0, primary_accuracy * SEED_TOTAL_PARAMS / n_params)
    convergence_score = 0.0
    if convergence_step is not None:
        convergence_score = max(0.0, 1.0 - min(float(convergence_step) / max_steps, 1.0))

    combined_score = (
        0.50 * primary_accuracy
        + 0.10 * train_accuracy
        + 0.15 * gap_score
        + 0.15 * loss_score
        + 0.05 * parameter_efficiency_score
        + 0.05 * convergence_score
    )
    return {
        "combined_score": float(combined_score),
        "primary_accuracy": primary_accuracy,
        "gap_score": gap_score,
        "loss_score": loss_score,
        "parameter_efficiency_score": parameter_efficiency_score,
        "convergence_score": convergence_score,
    }


def _mean(results: list[dict], key: str) -> float:
    return float(np.mean([float(result[key]) for result in results]))


def _std(results: list[dict], key: str) -> float:
    return float(np.std([float(result[key]) for result in results]))


def aggregate_metrics(results: list[dict], results_dir: str) -> dict:
    scored = [score_result(result) for result in results]
    combined_score_raw = float(np.mean([item["combined_score"] for item in scored]))
    combined_score = rescale_score(combined_score_raw)

    public = {
        "combined_score_raw": round(combined_score_raw, 4),
        "train_accuracy_mean": round(_mean(results, "train_accuracy"), 4),
        "train_accuracy_std": round(_std(results, "train_accuracy"), 4),
        "validation_accuracy_mean": round(_mean(results, "validation_accuracy"), 4),
        "validation_accuracy_std": round(_std(results, "validation_accuracy"), 4),
        "test_accuracy_mean": round(_mean(results, "test_accuracy"), 4),
        "test_accuracy_std": round(_std(results, "test_accuracy"), 4),
        "generalization_gap_mean": round(_mean(results, "generalization_gap"), 4),
        "validation_loss_mean": round(_mean(results, "validation_loss"), 4),
        "test_loss_mean": round(_mean(results, "test_loss"), 4),
        "parameter_efficiency_mean": round(_mean(results, "parameter_efficiency"), 6),
        "n_params": int(results[0]["n_params"]),
        "depth_mean": round(_mean(results, "depth"), 1),
        "gate_count_mean": round(_mean(results, "gate_count"), 1),
        "score_uses_test": USE_TEST_IN_SCORE,
    }

    convergence_steps = [
        result.get("convergence_step")
        for result in results
        if result.get("convergence_step") is not None
    ]
    public["convergence_step_mean"] = (
        round(float(np.mean(convergence_steps)), 1)
        if convergence_steps
        else None
    )

    results_path = Path(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)
    with (results_path / "per_run_metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    with (results_path / "score_components.json").open("w", encoding="utf-8") as handle:
        json.dump(scored, handle, indent=2)

    lines = [
        f"Combined score: {combined_score:.4f}",
        "Score scale: 0.0 = the seed program, 1.0 = the best solution found so "
        "far on this task. Negative means worse than the seed.",
        f"Validation accuracy mean: {public['validation_accuracy_mean']:.4f}",
        f"Test accuracy mean: {public['test_accuracy_mean']:.4f}",
        f"Train-test generalization gap mean: {public['generalization_gap_mean']:.4f}",
        f"Validation L2 loss mean: {public['validation_loss_mean']:.4f}",
        f"Parameters: {public['n_params']}, depth mean: {public['depth_mean']}, gate count mean: {public['gate_count_mean']}",
    ]
    if not USE_TEST_IN_SCORE:
        lines.append("Fitness uses validation metrics; test metrics are reported as holdout diagnostics.")
    if public["validation_accuracy_mean"] < 0.55:
        lines.append("Accuracy is near chance; explore different entanglement placement, rotation structure, or parameter sharing.")
    if public["generalization_gap_mean"] > 0.15:
        lines.append("Large train-test gap; consider fewer parameters or repeated structural motifs.")
    if public["n_params"] > SEED_TOTAL_PARAMS:
        lines.append("Parameter count exceeds the seed; added accuracy must justify the complexity.")
    if public["convergence_step_mean"] is None:
        lines.append("Did not reach the convergence threshold in these runs.")

    return {
        "combined_score": combined_score,
        "public": public,
        "private": {
            "per_run_scores": scored,
            "per_run_test_accuracies": [float(result["test_accuracy"]) for result in results],
        },
        "text_feedback": "\n".join(lines),
    }


def main(program_path: str, results_dir: str) -> None:
    metrics, correct, error_msg = run_shinka_eval(
        program_path=program_path,
        results_dir=results_dir,
        experiment_fn_name="run_experiment",
        num_runs=NUM_RUNS,
        get_experiment_kwargs=get_experiment_kwargs,
        validate_fn=validate_fn,
        aggregate_metrics_fn=partial(aggregate_metrics, results_dir=results_dir),
        run_workers=NUM_WORKERS,
    )
    print("OK" if correct else f"FAILED: {error_msg}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", default="initial_program.py")
    parser.add_argument("--results_dir", default="results_test")
    args = parser.parse_args()

    os.makedirs(args.results_dir, exist_ok=True)
    main(args.program_path, args.results_dir)
