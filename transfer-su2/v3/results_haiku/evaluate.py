"""Evaluator for ShinkaEvolve 8-qubit state-classification ansatz search."""

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
SEED_TOTAL_PARAMS = 26  # generic seed: 24 distinct names + gain/bias
EXPECTED_REPEATS = 3
USE_TEST_IN_SCORE = bool(int(os.environ.get("USE_TEST_IN_SCORE", "0")))
# Economy decay scale, in distinct trainable parameter names. exp(-names/6) is
# strictly decreasing everywhere: fewer names ALWAYS scores higher, with no
# saturation point at any count (both prior designs died on a saturation
# plateau: divisor 4 went flat below ~36 params, divisor 36 targeted a count
# that the repeat-multiplied bookkeeping made unreachable).
ECONOMY_SCALE = 6.0


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
    if result.get("n_repeats") != EXPECTED_REPEATS:
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


def worst_group_margin(result: dict) -> float:
    """Mean clipped signed margin of the WORST difficulty group on validation.

    Per-sample margins arrive from the backend; the dataset ships an integer
    group id per validation sample (quartiles of hidden difficulty). Scoring
    the minimum over groups keeps the term discriminative even when the mean
    margin saturates: a candidate cannot coast on the easy samples.
    Falls back to the overall mean margin, then to accuracy mapped to [-1, 1].
    """
    margins = result.get("validation_margins")
    if not margins:
        return 2.0 * float(result["validation_accuracy"]) - 1.0
    m = np.asarray(margins, dtype=float)
    groups = result.get("validation_groups")
    if not groups:
        return float(m.mean())
    g = np.asarray(groups, dtype=int)
    return float(min(m[g == gid].mean() for gid in np.unique(g)))


def score_result(result: dict) -> dict:
    primary_acc_key = "test_accuracy" if USE_TEST_IN_SCORE else "validation_accuracy"
    primary_loss_key = "test_loss" if USE_TEST_IN_SCORE else "validation_loss"
    primary_accuracy = float(result[primary_acc_key])
    primary_loss = float(result[primary_loss_key])
    train_accuracy = float(result["train_accuracy"])
    test_accuracy = float(result["test_accuracy"])
    gap = abs(train_accuracy - test_accuracy)
    n_names = max(int(result.get("n_params_per_block") or 0), 0)
    max_steps = max(float(result.get("max_steps") or (N_EPOCHS * STEPS_PER_EPOCH)), 1.0)
    convergence_step = result.get("convergence_step")

    # Continuous primary signal: worst-group margin mapped from [-1, 1] to [0, 1].
    # Stays informative after accuracy pins at 1.0, so selection keeps a
    # gradient instead of plateauing (v1 failure: every term was at ceiling
    # from generation 0 and the population random-walked on ties).
    margin_score = 0.5 * (worst_group_margin(result) + 1.0)

    # Strictly monotone economy: fewer distinct names always scores higher, no
    # saturation at any count. Multiplied by accuracy so an inaccurate tiny
    # circuit cannot harvest economy points; at fixed accuracy the count
    # ordering is strict.
    economy_score = math.exp(-n_names / ECONOMY_SCALE) * primary_accuracy

    # Gap term likewise gated by accuracy: a uniformly bad circuit has zero
    # gap and must not collect the full reward for it.
    gap_score = max(0.0, 1.0 - min(gap / 0.35, 1.0)) * primary_accuracy
    loss_score = 1.0 / (1.0 + max(primary_loss, 0.0))
    # Log-scaled convergence: linear scaling gave 0.999 to everything that
    # converged in the first epoch and had no resolution.
    convergence_score = 0.0
    if convergence_step is not None:
        convergence_score = max(
            0.0, 1.0 - math.log1p(float(convergence_step)) / math.log1p(max_steps)
        )

    combined_score = (
        0.45 * margin_score
        + 0.20 * economy_score
        + 0.15 * gap_score
        + 0.10 * loss_score
        + 0.10 * convergence_score
    )
    return {
        "combined_score": float(combined_score),
        "primary_accuracy": primary_accuracy,
        "margin_score": margin_score,
        "worst_group_margin": worst_group_margin(result),
        "economy_score": economy_score,
        "n_distinct_params": n_names,
        "gap_score": gap_score,
        "loss_score": loss_score,
        "convergence_score": convergence_score,
    }


def _mean(results: list[dict], key: str) -> float:
    return float(np.mean([float(result[key]) for result in results]))


def _std(results: list[dict], key: str) -> float:
    return float(np.std([float(result[key]) for result in results]))


def aggregate_metrics(results: list[dict], results_dir: str) -> dict:
    scored = [score_result(result) for result in results]
    combined_score = float(np.mean([item["combined_score"] for item in scored]))

    public = {
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
        "validation_margin_mean": round(_mean(results, "validation_margin"), 4),
        "worst_group_margin_mean": round(
            float(np.mean([item["worst_group_margin"] for item in scored])), 4),
        "n_params": int(results[0]["n_params"]),
        "n_distinct_params": int(results[0].get("n_params_per_block") or 0),
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
        f"Validation accuracy mean: {public['validation_accuracy_mean']:.4f}",
        f"Test accuracy mean: {public['test_accuracy_mean']:.4f}",
        f"Validation margin mean: {public['validation_margin_mean']:.4f}",
        f"Worst-group validation margin: {public['worst_group_margin_mean']:.4f}",
        f"Train-test generalization gap mean: {public['generalization_gap_mean']:.4f}",
        f"Validation L2 loss mean: {public['validation_loss_mean']:.4f}",
        f"Distinct trainable parameters: {public['n_distinct_params']}, "
        f"depth mean: {public['depth_mean']}, gate count mean: {public['gate_count_mean']}",
    ]
    if not USE_TEST_IN_SCORE:
        lines.append("Fitness uses validation metrics; test metrics are reported as holdout diagnostics.")
    if public["validation_accuracy_mean"] < 0.55:
        lines.append("Accuracy is near chance; explore different entanglement placement, rotation structure, or parameter sharing.")
    if public["generalization_gap_mean"] > 0.15:
        lines.append("Large train-test gap; consider fewer parameters or repeated structural motifs.")
    lines.append(
        "Scoring rewards, in order of weight: the mean margin of the WORST "
        "validation group (samples are grouped by hidden difficulty, so robust "
        "separation on the hardest group is what counts), parameter economy "
        "(fewer distinct parameter names ALWAYS scores higher, at every count), "
        "a small train-test gap, low loss, and early convergence.")
    lines.append(f"Economy score: {round(float(np.mean([s['economy_score'] for s in scored])), 4)}")
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
