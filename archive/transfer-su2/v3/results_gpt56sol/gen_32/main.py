"""Seed program for ShinkaEvolve ansatz search: 8-qubit state classifier.

Inputs are precomputed 8-qubit quantum state vectors from an external
dataset, loaded opaquely and prepared with StatePrep. Labels are +1/-1 and
encode a property of the states determined by the dataset. The fixed readout
measures a set of two-qubit correlators on pairs given by the dataset and
averages them into one scalar, followed by a trainable gain/bias calibration.

Only ANSATZ_SPEC is inside the EVOLVE-BLOCK. The dataset, state preparation,
block layout, training loop, measurement and metric packaging are fixed so
candidates are compared on the same task.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pennylane as qml
from pennylane import numpy as pnp


# Problem constants. The input is a quantum state loaded once by StatePrep, so
# there is no data re-uploading dimension (it only exists for classical inputs).
# The block is applied N_REPEATS times with the SAME parameter values each time:
# the trainable parameter count equals the number of distinct param names.
N_QUBITS = 8
N_REPEATS = 3

_DATA_PATH = os.environ.get("TASK_DATA", str(Path(__file__).resolve().parent / "dataset.npz"))
_DATA = np.load(_DATA_PATH)
READOUT_PAIRS = [tuple(int(w) for w in row) for row in _DATA["readout_pairs"]]
# The two-qubit observable used by the fixed readout ships as an opaque
# numeric matrix in the dataset; nothing about it is defined in this file.
PAIR_OBSERVABLE = np.asarray(_DATA["pair_observable"], dtype=complex)
GROUP_VALIDATION = (
    np.asarray(_DATA["group_validation"], dtype=int)
    if "group_validation" in getattr(_DATA, "files", [])
    else None
)

ALLOWED_SINGLE_QUBIT_GATES = {"RX", "RY", "RZ"}
ALLOWED_TWO_QUBIT_GATES = {"CNOT", "CZ"}
ALLOWED_PARAM_TWO_QUBIT_GATES = {"CRX", "CRY", "CRZ", "XX", "YY", "ZZ"}


# EVOLVE-BLOCK-START
ANSATZ_SPEC = [
    # Collective rotations regularize the few-shot model while retaining
    # independent control of two noncommuting single-qubit axes.
    {"gate": "RY", "wire": 0, "param": "global_y"},
    {"gate": "RY", "wire": 1, "param": "global_y"},
    {"gate": "RY", "wire": 2, "param": "global_y"},
    {"gate": "RY", "wire": 3, "param": "global_y"},
    {"gate": "RY", "wire": 4, "param": "global_y"},
    {"gate": "RY", "wire": 5, "param": "global_y"},
    {"gate": "RY", "wire": 6, "param": "global_y"},
    {"gate": "RY", "wire": 7, "param": "global_y"},

    # Fixed cyclic links propagate local information, while one shared ZZ
    # angle tunes all diametric links coherently. This exposes long-range
    # correlation strength without introducing wire-specific parameters.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [6, 7]},
    {"gate": "CZ", "wires": [7, 0]},
    {"gate": "ZZ", "wires": [0, 4], "param": "cross_ent"},
    {"gate": "ZZ", "wires": [1, 5], "param": "cross_ent"},
    {"gate": "ZZ", "wires": [2, 6], "param": "cross_ent"},
    {"gate": "ZZ", "wires": [3, 7], "param": "cross_ent"},

    # Reuse the collective Y angle on the noncommuting Z layer, spending the
    # second model degree of freedom on long-range entanglement instead.
    {"gate": "RZ", "wire": 0, "param": "global_y"},
    {"gate": "RZ", "wire": 1, "param": "global_y"},
    {"gate": "RZ", "wire": 2, "param": "global_y"},
    {"gate": "RZ", "wire": 3, "param": "global_y"},
    {"gate": "RZ", "wire": 4, "param": "global_y"},
    {"gate": "RZ", "wire": 5, "param": "global_y"},
    {"gate": "RZ", "wire": 6, "param": "global_y"},
    {"gate": "RZ", "wire": 7, "param": "global_y"},
]
# EVOLVE-BLOCK-END


def load_splits() -> dict:
    x_train = np.asarray(_DATA["x_train"], dtype=complex)
    y_train = np.asarray(_DATA["y_train"], dtype=float)
    # Few-shot training: subsample the shipped train split to TRAIN_SIZE,
    # class-balanced and deterministic (same subset for every candidate).
    train_size = int(os.environ.get("TRAIN_SIZE", "0"))
    if 0 < train_size < len(x_train):
        rng = np.random.default_rng(int(os.environ.get("DATA_SEED", "2027")))
        pos = rng.permutation(np.flatnonzero(y_train > 0))
        neg = rng.permutation(np.flatnonzero(y_train < 0))
        half = train_size // 2
        sel = np.sort(np.concatenate([pos[:half], neg[: train_size - half]]))
        x_train, y_train = x_train[sel], y_train[sel]
    return {
        "train": (x_train, y_train),
        "validation": (np.asarray(_DATA["x_validation"], dtype=complex), np.asarray(_DATA["y_validation"], dtype=float)),
        "test": (np.asarray(_DATA["x_test"], dtype=complex), np.asarray(_DATA["y_test"], dtype=float)),
    }


def validate_ansatz_spec(spec: list[dict]) -> tuple[list[str], list[str]]:
    """Validate ANSATZ_SPEC and return errors plus ordered parameter keys."""
    errors = []
    parameter_keys = []
    if not isinstance(spec, list) or not spec:
        return ["ANSATZ_SPEC must be a non-empty list of gate dictionaries."], []

    for gate_index, item in enumerate(spec):
        prefix = f"gate {gate_index}"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: expected a dict, got {type(item).__name__}")
            continue
        gate = str(item.get("gate", "")).upper()
        if gate in ALLOWED_SINGLE_QUBIT_GATES:
            wire = item.get("wire")
            if not isinstance(wire, int) or not 0 <= wire < N_QUBITS:
                errors.append(f"{prefix}: {gate} requires integer wire in [0, {N_QUBITS - 1}]")
            param = item.get("param")
            if not isinstance(param, str) or not param:
                errors.append(f"{prefix}: {gate} requires a non-empty string param key")
            else:
                parameter_keys.append(param)
        elif gate in ALLOWED_TWO_QUBIT_GATES | ALLOWED_PARAM_TWO_QUBIT_GATES:
            wires = item.get("wires")
            if (
                not isinstance(wires, (list, tuple))
                or len(wires) != 2
                or not all(isinstance(w, int) for w in wires)
                or wires[0] == wires[1]
                or not all(0 <= w < N_QUBITS for w in wires)
            ):
                errors.append(f"{prefix}: {gate} requires two distinct integer wires")
            if gate in ALLOWED_PARAM_TWO_QUBIT_GATES:
                param = item.get("param")
                if not isinstance(param, str) or not param:
                    errors.append(f"{prefix}: {gate} requires a non-empty string param key")
                else:
                    parameter_keys.append(param)
        else:
            allowed = sorted(
                ALLOWED_SINGLE_QUBIT_GATES | ALLOWED_TWO_QUBIT_GATES | ALLOWED_PARAM_TWO_QUBIT_GATES
            )
            errors.append(f"{prefix}: unsupported gate {gate!r}; allowed gates are {allowed}")

    ordered_unique_keys = list(dict.fromkeys(parameter_keys))
    return errors, ordered_unique_keys


SPEC_ERRORS, PARAMETER_KEYS_PER_BLOCK = validate_ansatz_spec(ANSATZ_SPEC)
N_PARAMS_PER_BLOCK = len(PARAMETER_KEYS_PER_BLOCK)
N_CIRCUIT_PARAMS = N_PARAMS_PER_BLOCK
N_READOUT_PARAMS = 2  # trainable output calibration: gain, bias
N_PARAMS = N_CIRCUIT_PARAMS + N_READOUT_PARAMS


def apply_ansatz_block(params, block_index: int) -> None:
    """Apply one candidate ansatz block from the formal ANSATZ_SPEC.

    Parameters are shared across repetitions: every application of the block
    reads the same values, so block_index is accepted only for API symmetry.
    """
    if SPEC_ERRORS:
        raise ValueError("; ".join(SPEC_ERRORS))

    del block_index  # parameters are tied across repeats
    key_to_position = {key: i for i, key in enumerate(PARAMETER_KEYS_PER_BLOCK)}
    for item in ANSATZ_SPEC:
        gate = str(item["gate"]).upper()
        if gate in ALLOWED_SINGLE_QUBIT_GATES:
            angle = params[key_to_position[item["param"]]]
            wire = int(item["wire"])
            if gate == "RX":
                qml.RX(angle, wires=wire)
            elif gate == "RY":
                qml.RY(angle, wires=wire)
            elif gate == "RZ":
                qml.RZ(angle, wires=wire)
        elif gate in ALLOWED_TWO_QUBIT_GATES:
            wires = [int(w) for w in item["wires"]]
            if gate == "CNOT":
                qml.CNOT(wires=wires)
            elif gate == "CZ":
                qml.CZ(wires=wires)
        elif gate in ALLOWED_PARAM_TWO_QUBIT_GATES:
            angle = params[key_to_position[item["param"]]]
            wires = [int(w) for w in item["wires"]]
            if gate == "CRX":
                qml.CRX(angle, wires=wires)
            elif gate == "CRY":
                qml.CRY(angle, wires=wires)
            elif gate == "CRZ":
                qml.CRZ(angle, wires=wires)
            elif gate == "XX":
                qml.IsingXX(angle, wires=wires)
            elif gate == "YY":
                qml.IsingYY(angle, wires=wires)
            elif gate == "ZZ":
                qml.IsingZZ(angle, wires=wires)


_DEVICE = qml.device("default.qubit", wires=N_QUBITS, shots=None)


@qml.qnode(_DEVICE, interface="autograd", diff_method="backprop")
def circuit_pair_expectations(states, circuit_params):
    """Fixed pipeline: prepare the input state, apply ansatz blocks, measure
    the dataset's two-qubit observable on each of the dataset's pairs.
    """
    qml.StatePrep(states, wires=range(N_QUBITS))
    for repeat_index in range(N_REPEATS):
        apply_ansatz_block(circuit_params, repeat_index)
    return [
        qml.expval(qml.Hermitian(PAIR_OBSERVABLE, wires=[a, b]))
        for a, b in READOUT_PAIRS
    ]


def predict_batch(params, x_batch: np.ndarray):
    """Scalar prediction per state: calibrated mean of the fixed correlators."""
    circuit_params = params[:N_CIRCUIT_PARAMS]
    gain = params[N_CIRCUIT_PARAMS]
    bias = params[N_CIRCUIT_PARAMS + 1]
    states = pnp.array(np.asarray(x_batch, dtype=complex), requires_grad=False)
    z = pnp.stack(circuit_pair_expectations(states, circuit_params))  # (n_pairs, B)
    raw = pnp.mean(z, axis=0)
    return gain * (raw - bias)


def l2_loss(params, x_batch: np.ndarray, y_batch: np.ndarray):
    predictions = predict_batch(params, x_batch)
    targets = pnp.array(y_batch, requires_grad=False)
    return pnp.mean((predictions - targets) ** 2)


def evaluate_split(params, x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    predictions = np.asarray(predict_batch(params, x), dtype=float)
    loss = float(np.mean((predictions - y) ** 2))
    accuracy = float(np.mean(np.sign(predictions) == np.sign(y)))
    # Clipped signed margin: y*f in [-1, 1] per sample. Continuous companion to
    # 0/1 accuracy; the clip keeps it un-gameable by inflating the readout gain.
    margins = np.clip(predictions * y, -1.0, 1.0)
    return {"accuracy": accuracy, "loss": loss, "margin": float(np.mean(margins)),
            "margins": margins}


def _batch_indices(order: np.ndarray, step: int, batch_size: int) -> np.ndarray:
    start = (step * batch_size) % len(order)
    end = start + batch_size
    if end <= len(order):
        return order[start:end]
    return np.concatenate([order[start:], order[: end - len(order)]])


def _log(record: dict, log_file: Path | None, verbose: bool) -> None:
    line = json.dumps(record, sort_keys=True)
    if verbose:
        print(line)
    if log_file is not None:
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def circuit_metadata() -> dict:
    with qml.queuing.AnnotatedQueue() as queue:
        for repeat_index in range(N_REPEATS):
            apply_ansatz_block(np.zeros(max(N_CIRCUIT_PARAMS, 1)), repeat_index)
    tape = qml.tape.QuantumScript.from_queue(queue)
    operations = [(op.name, op.wires.tolist()) for op in tape.operations]
    depth = tape.graph.get_depth() if hasattr(tape.graph, "get_depth") else len(operations)
    return {
        "operations": operations,
        "depth": int(depth),
        "gate_count": int(len(operations)),
    }


def run_experiment(
    seed: int = 0,
    n_epochs: int | None = None,
    steps_per_epoch: int | None = None,
    batch_size: int | None = None,
    learning_rate: float | None = None,
    convergence_threshold: float | None = None,
    eval_every_epochs: int | None = None,
    verbose: bool | None = None,
    **_ignored,
) -> dict:
    """Train the candidate ansatz and return ShinkaEvolve metrics."""
    if SPEC_ERRORS:
        return {
            "spec_valid": False,
            "error": "; ".join(SPEC_ERRORS),
            "n_qubits": N_QUBITS,
            "n_repeats": N_REPEATS,
            "n_params": N_PARAMS,
            "operations": [],
            "train_accuracy": 0.0,
            "validation_accuracy": 0.0,
            "test_accuracy": 0.0,
            "train_loss": float("inf"),
            "validation_loss": float("inf"),
            "test_loss": float("inf"),
        }

    n_epochs = int(os.environ.get("N_EPOCHS", "1000") if n_epochs is None else n_epochs)
    steps_per_epoch = int(os.environ.get("STEPS_PER_EPOCH", "30") if steps_per_epoch is None else steps_per_epoch)
    batch_size = int(os.environ.get("BATCH_SIZE", "15") if batch_size is None else batch_size)
    learning_rate = float(os.environ.get("LEARNING_RATE", "0.03") if learning_rate is None else learning_rate)
    convergence_threshold = float(
        os.environ.get("CONVERGENCE_THRESHOLD", "0.90")
        if convergence_threshold is None
        else convergence_threshold
    )
    eval_every_epochs = int(os.environ.get("EVAL_EVERY_EPOCHS", "1") if eval_every_epochs is None else eval_every_epochs)
    verbose = bool(int(os.environ.get("VERBOSE_TRAINING", "0"))) if verbose is None else bool(verbose)
    early_stopping = bool(int(os.environ.get("EARLY_STOPPING", "1")))
    patience = int(os.environ.get("PATIENCE", "75"))
    min_delta = float(os.environ.get("MIN_DELTA", "1e-4"))

    splits = load_splits()
    x_train, y_train = splits["train"]
    x_validation, y_validation = splits["validation"]
    x_test, y_test = splits["test"]

    log_root = os.environ.get("TTT_LOG_DIR")
    log_file = None
    if log_root:
        Path(log_root).mkdir(parents=True, exist_ok=True)
        log_file = Path(log_root) / f"candidate_seed_{seed}.jsonl"
        if log_file.exists():
            log_file.unlink()

    rng = np.random.default_rng(seed)
    # Angles are initialised across the full period rather than near zero. A
    # near-identity start is a dead zone for some candidate structures, and the
    # ranking noise that produces is an optimiser artifact rather than a
    # property of the circuit. The wide init applies to every candidate alike.
    init_scale = float(os.environ.get("INIT_SCALE", str(np.pi)))
    init = rng.uniform(-init_scale, init_scale, size=N_PARAMS)
    init[N_CIRCUIT_PARAMS] = 1.0       # gain starts at 1
    init[N_CIRCUIT_PARAMS + 1] = 0.0   # bias starts at 0
    params = pnp.array(init, requires_grad=True)
    optimizer = qml.AdamOptimizer(stepsize=learning_rate)
    max_steps = n_epochs * steps_per_epoch
    global_step = 0
    convergence_epoch = None
    convergence_step = None
    history = []
    best_val_loss = float("inf")
    best_params = params.copy()
    epochs_no_improve = 0
    stop_reason = "max_epochs"

    _log(
        {
            "event": "start",
            "seed": int(seed),
            "n_params": int(N_PARAMS),
            "n_params_per_block": int(N_PARAMS_PER_BLOCK),
            "n_epochs": int(n_epochs),
            "steps_per_epoch": int(steps_per_epoch),
            "batch_size": int(batch_size),
            "learning_rate": float(learning_rate),
        },
        log_file,
        verbose,
    )

    for epoch in range(1, n_epochs + 1):
        order = rng.permutation(len(x_train))
        last_batch_loss = None
        for step in range(steps_per_epoch):
            batch_ids = _batch_indices(order, step, batch_size)
            batch_x = x_train[batch_ids]
            batch_y = y_train[batch_ids]
            params, last_batch_loss = optimizer.step_and_cost(
                lambda candidate_params: l2_loss(candidate_params, batch_x, batch_y),
                params,
            )
            global_step += 1

        if epoch == 1 or epoch == n_epochs or epoch % eval_every_epochs == 0:
            validation_metrics = evaluate_split(params, x_validation, y_validation)
            if convergence_epoch is None and validation_metrics["accuracy"] >= convergence_threshold:
                convergence_epoch = epoch
                convergence_step = global_step
            record = {
                "event": "epoch",
                "epoch": int(epoch),
                "global_step": int(global_step),
                "batch_loss": float(last_batch_loss),
                "validation_accuracy": validation_metrics["accuracy"],
                "validation_loss": validation_metrics["loss"],
            }
            history.append(record)
            _log(record, log_file, verbose)

            # Validation-loss early stopping with restore-best-weights.
            if validation_metrics["loss"] < best_val_loss - min_delta:
                best_val_loss = validation_metrics["loss"]
                best_params = params.copy()
                epochs_no_improve = 0
            else:
                epochs_no_improve += 1
                if early_stopping and epochs_no_improve >= patience:
                    stop_reason = "early_stopping"
                    break

    params = best_params
    final_train = evaluate_split(params, x_train, y_train)
    final_validation = evaluate_split(params, x_validation, y_validation)
    final_test = evaluate_split(params, x_test, y_test)
    metadata = circuit_metadata()
    generalization_gap = abs(final_train["accuracy"] - final_test["accuracy"])
    parameter_efficiency = final_test["accuracy"] / max(float(N_PARAMS), 1.0)

    result = {
        "spec_valid": True,
        "n_qubits": N_QUBITS,
        "n_repeats": N_REPEATS,
        "n_params_per_block": N_PARAMS_PER_BLOCK,
        "n_params": N_PARAMS,
        "depth": metadata["depth"],
        "gate_count": metadata["gate_count"],
        "operations": metadata["operations"],
        "train_accuracy": final_train["accuracy"],
        "validation_accuracy": final_validation["accuracy"],
        "test_accuracy": final_test["accuracy"],
        "train_loss": final_train["loss"],
        "validation_loss": final_validation["loss"],
        "test_loss": final_test["loss"],
        "train_margin": final_train["margin"],
        "validation_margin": final_validation["margin"],
        "test_margin": final_test["margin"],
        "validation_margins": [float(m) for m in final_validation["margins"]],
        "validation_groups": (
            [int(g) for g in GROUP_VALIDATION] if GROUP_VALIDATION is not None else None
        ),
        "generalization_gap": generalization_gap,
        "parameter_efficiency": parameter_efficiency,
        "convergence_threshold": convergence_threshold,
        "convergence_epoch": convergence_epoch,
        "convergence_step": convergence_step,
        "max_steps": max_steps,
        "stop_reason": stop_reason,
        "restore_best_weights": True,
        "history_tail": history[-10:],
        # Trained angles, for offline analysis of what the circuit became. The
        # evaluator's public metric block is a whitelist, so this never reaches
        # the proposer.
        "best_params": [float(v) for v in np.asarray(params, dtype=float)],
    }
    _log({"event": "final", **result}, log_file, verbose)
    return result