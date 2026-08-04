"""Generate one anonymized shinka_config.<tag>.json per proposer model.

All three configs are byte-identical except for the single `llm_models` entry,
so the only variable across the three cluster runs is the proposer model. The
helper roles (meta recommendations, novelty check, embeddings) are held fixed.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

TASK_SYS_MSG = """
You are an expert in quantum machine learning and variational quantum circuits.

Goal:
Evolve the ANSATZ_SPEC for a 9-qubit, 3-class classifier.  The fixed code will
train each candidate with Adam in a simulated PennyLane circuit and report
accuracy, loss, and generalization metrics.

Fixed architecture:
- 9 qubits, indexed 0..8.
- Feature map: RX(2*pi/3 * x_i) on qubit i, for an input vector x in {-1,0,+1}^9.
- Data re-uploading l=3.
- The candidate ansatz block is applied p=2 times after each re-uploading.
- The block receives independent parameter copies for each upload/repetition.
- The three class scores are fixed linear readouts of the final per-qubit
  Pauli-Z expectations.

Only edit the EVOLVE-BLOCK, especially ANSATZ_SPEC.  Do not change the fixed
training loop, data, readout, l, p, or feature map.

Formal ANSATZ_SPEC schema:
- Single-qubit parametrized gates:
  {"gate": "RX"|"RY"|"RZ", "wire": int 0..8, "param": "name"}
- Fixed two-qubit gates:
  {"gate": "CNOT"|"CZ", "wires": [first, second]}
- Parametrized controlled rotations:
  {"gate": "CRX"|"CRY"|"CRZ", "wires": [control, target], "param": "name"}
- Parametrized three-qubit interactions (any three distinct qubits 0..8):
  {"gate": "ZZZ", "wires": [a, b, c], "param": "name"}   # collective exp(-i*theta/2 * Z@Z@Z)
  {"gate": "CCRZ", "wires": [control_1, control_2, target], "param": "name"}   # doubly-controlled RZ

Connectivity constraint:
Two-qubit gates are allowed only on these hardware-native qubit pairs:
(0,2), (0,3), (0,7), (0,8), (1,3), (1,8),
(2,4), (2,6), (3,5), (4,8), (5,7), (6,7).
Three-qubit gates have no connectivity restriction: any 3 distinct qubits.

Parameter sharing:
Reusing the same param string shares that parameter within one ansatz block.
Use sharing deliberately for parameter efficiency.

Starting point:
The seed is an EfficientSU2-style block: independent RY rotations on every
qubit, independent pre-entanglement RZ rotations, CZ gates on each
hardware-native pair, and independent post-entanglement RZ rotations.

Candidate quality:
Improve validation/test accuracy, reduce the train-test gap, reduce L2 loss,
use parameters efficiently, and reach high accuracy in fewer Adam steps.

Invalid candidates will be rejected if they use unsupported gates, bad wires,
non-native two-qubit operations, non-finite metrics, or too many parameters.
"""

MODELS = {
    "haiku": "openrouter/anthropic/claude-haiku-4.5",
    "sonnet": "openrouter/anthropic/claude-sonnet-5",
    "gpt56sol": "openrouter/openai/gpt-5.6-sol",
}


def base_config(model: str) -> dict:
    return {
        "evo": {
            "task_sys_msg": TASK_SYS_MSG,
            "patch_types": ["diff", "full", "cross"],
            "patch_type_probs": [0.65, 0.25, 0.1],
            "max_patch_resamples": 3,
            "max_patch_attempts": 2,
            "llm_models": [model],
            "llm_kwargs": {"temperatures": [0.0, 0.5, 1.0], "max_tokens": 16384},
            "llm_dynamic_selection": "ucb1",
            "llm_dynamic_selection_kwargs": {"exploration_coef": 1.0, "cost_aware_coef": 0.7},
            "meta_rec_interval": 5,
            "meta_llm_models": ["openrouter/openai/o4-mini"],
            "meta_llm_kwargs": {"temperatures": [0.0], "max_tokens": 8192},
            "embedding_model": "openrouter/openai/text-embedding-3-small",
            "max_novelty_attempts": 2,
            "code_embed_sim_threshold": 0.99,
            "novelty_llm_models": ["openrouter/openai/o4-mini"],
            "novelty_llm_kwargs": {"temperatures": [0.0]},
            "max_api_costs": 15.0,
        },
        "db": {
            "num_islands": 1,
            "archive_size": 20,
            "elite_selection_ratio": 0.3,
            "num_archive_inspirations": 1,
            "num_top_k_inspirations": 1,
            "parent_selection_strategy": "weighted",
            "parent_selection_lambda": 10,
            "archive_selection_strategy": "crowding",
            "archive_criteria": {
                "combined_score": 1.0,
                "validation_accuracy_mean": 0.5,
                "generalization_gap_mean": -0.3,
                "n_params": -0.1,
            },
            "enable_dynamic_islands": False,
        },
    }


def main():
    for tag, model in MODELS.items():
        cfg = base_config(model)
        (HERE / f"shinka_config.{tag}.json").write_text(json.dumps(cfg, indent=2))
        print(f"wrote shinka_config.{tag}.json  model={model}")


if __name__ == "__main__":
    main()
