"""Local comparison: seed ansatz (initial_program.py) vs. hand-designed
S_8-equivariant baseline ansatz (baseline_program.py), on the transfer-sn
graph-connectedness task. Reuses the exact scoring formulas from evaluate.py
(duplicated here to avoid depending on the shinka package, which isn't
installed in this local venv) so the numbers are directly comparable to the
ShinkaEvolve cluster runs.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import initial_program
import baseline_program

HERE = Path(__file__).resolve().parent

SCORE_ANCHOR_SEED = 0.8545656310200919
SCORE_ANCHOR_BEST = 0.9483080295061955
N_EPOCHS, STEPS_PER_EPOCH = 1000, 30
SEED_TOTAL_PARAMS = 146
BASE_SEED = 1000


def rescale_score(raw: float) -> float:
    span = SCORE_ANCHOR_BEST - SCORE_ANCHOR_SEED
    return (raw - SCORE_ANCHOR_SEED) / span


def score_result(result: dict, use_test: bool = False) -> dict:
    primary_acc = result["test_accuracy"] if use_test else result["validation_accuracy"]
    primary_loss = result["test_loss"] if use_test else result["validation_loss"]
    train_accuracy = result["train_accuracy"]
    test_accuracy = result["test_accuracy"]
    gap = abs(train_accuracy - test_accuracy)
    n_params = max(float(result["n_params"]), 1.0)
    max_steps = max(float(result.get("max_steps") or (N_EPOCHS * STEPS_PER_EPOCH)), 1.0)
    convergence_step = result.get("convergence_step")

    gap_score = max(0.0, 1.0 - min(gap / 0.35, 1.0))
    loss_score = 1.0 / (1.0 + max(primary_loss, 0.0))
    parameter_efficiency_score = min(1.0, primary_acc * SEED_TOTAL_PARAMS / n_params)
    convergence_score = 0.0
    if convergence_step is not None:
        convergence_score = max(0.0, 1.0 - min(float(convergence_step) / max_steps, 1.0))

    combined = (
        0.50 * primary_acc + 0.10 * train_accuracy + 0.15 * gap_score
        + 0.15 * loss_score + 0.05 * parameter_efficiency_score + 0.05 * convergence_score
    )
    return dict(
        combined_score_raw=combined,
        combined_score_rescaled=rescale_score(combined),
        primary_accuracy=primary_acc,
        gap_score=gap_score,
        loss_score=loss_score,
        parameter_efficiency_score=parameter_efficiency_score,
        convergence_score=convergence_score,
    )


def run_one(module, label: str) -> dict:
    print(f"--- running {label} (seed={BASE_SEED}) ---", flush=True)
    t0 = time.time()
    result = module.run_experiment(seed=BASE_SEED, verbose=False)
    elapsed = time.time() - t0
    print(f"{label}: done in {elapsed:.1f}s, test_accuracy={result['test_accuracy']:.4f}", flush=True)
    scored = score_result(result)
    return {"raw": result, "scored": scored, "elapsed_seconds": elapsed}


def main() -> None:
    out = {
        "seed": run_one(initial_program, "seed (initial_program.py)"),
        "baseline": run_one(baseline_program, "baseline (S_8-equivariant, baseline_program.py)"),
    }
    out_path = HERE / "seed_vs_baseline_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
