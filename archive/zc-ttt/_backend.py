"""Seed program for an evolutionary variational-quantum-circuit search.

Task: a fixed 9-qubit, 3-class classification problem. Each input is a length-9
vector of values in {-1, 0, +1} loaded onto the nine qubits by a fixed feature
map. The fixed code trains each candidate ANSATZ_SPEC with Adam and reports
accuracy / loss / generalization metrics. Only the ANSATZ_SPEC block is evolved;
the feature map, data, re-uploading layout (l=3, p=2), training loop, and
readout are frozen so every candidate is judged on the same task.

The precomputed dataset is loaded from an .npz file (path in env var
TASK_DATA_NPZ). Labels and inputs are fixed. Nothing about the task's underlying
structure is encoded in this file; any structure a good ansatz exploits must be
inferred from the training signal.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pennylane as qml
from pennylane import numpy as pnp


# Problem constants
N_QUBITS = 9
N_UPLOADS = 3
N_REPEATS = 2
FEATURE_SCALE = 2 * np.pi / 3

# Hardware-native two-qubit connectivity. Two-qubit gates may act ONLY on these
# qubit pairs; three-qubit gates have no connectivity restriction.
HARDWARE_EDGES = (
    (0, 2), (0, 3), (0, 7), (0, 8), (1, 3), (1, 8),
    (2, 4), (2, 6), (3, 5), (4, 8), (5, 7), (6, 7),
)
HARDWARE_EDGE_SET = {tuple(sorted(edge)) for edge in HARDWARE_EDGES}

# Readout: the three class scores are fixed linear functions of the final
# per-qubit Pauli-Z expectations. These groupings are part of the fixed task.
READOUT_GROUP_0 = (2, 3, 7, 8)   # class_0 score = mean Z over these qubits
READOUT_GROUP_1 = (1, 4, 5, 6)   # class_1 score = mean Z over these qubits
READOUT_QUBIT_2 = 0              # class_2 score = Z on this qubit

CLASS_NAMES = ("class_0", "class_1", "class_2")
CLASS_TO_INDEX = {name: i for i, name in enumerate(CLASS_NAMES)}

ALLOWED_SINGLE_QUBIT_GATES = {"RX", "RY", "RZ"}
ALLOWED_TWO_QUBIT_GATES = {"CNOT", "CZ"}
ALLOWED_PARAM_TWO_QUBIT_GATES = {"CRX", "CRY", "CRZ"}
# Parametrized three-qubit interactions on ANY three distinct qubits (no
# connectivity restriction). ZZZ is a collective exp(-i theta/2 Z x Z x Z)
# rotation (qml.MultiRZ on 3 wires); CCRZ is a doubly-controlled RZ with
# wires = [control_1, control_2, target].
ALLOWED_PARAM_THREE_QUBIT_GATES = {"ZZZ", "CCRZ"}




def _load_splits() -> dict:
    """Load the fixed precomputed train/validation/test splits."""
    path = os.environ.get("TASK_DATA_NPZ")
    if not path:
        path = str(Path(__file__).resolve().with_name("data_splits.npz"))
    d = np.load(path)
    return {
        "train": (np.asarray(d["x_train"]), np.asarray(d["y_train"])),
        "validation": (np.asarray(d["x_val"]), np.asarray(d["y_val"])),
        "test": (np.asarray(d["x_test"]), np.asarray(d["y_test"])),
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
            elif tuple(sorted(wires)) not in HARDWARE_EDGE_SET:
                errors.append(f"{prefix}: {gate} uses non-native qubit pair {wires}")
            if gate in ALLOWED_PARAM_TWO_QUBIT_GATES:
                param = item.get("param")
                if not isinstance(param, str) or not param:
                    errors.append(f"{prefix}: {gate} requires a non-empty string param key")
                else:
                    parameter_keys.append(param)
        elif gate in ALLOWED_PARAM_THREE_QUBIT_GATES:
            wires = item.get("wires")
            if (
                not isinstance(wires, (list, tuple))
                or len(wires) != 3
                or not all(isinstance(w, int) for w in wires)
                or len(set(wires)) != 3
                or not all(0 <= w < N_QUBITS for w in wires)
            ):
                errors.append(f"{prefix}: {gate} requires three distinct integer wires")
            param = item.get("param")
            if not isinstance(param, str) or not param:
                errors.append(f"{prefix}: {gate} requires a non-empty string param key")
            else:
                parameter_keys.append(param)
        else:
            allowed = sorted(
                ALLOWED_SINGLE_QUBIT_GATES | ALLOWED_TWO_QUBIT_GATES
                | ALLOWED_PARAM_TWO_QUBIT_GATES | ALLOWED_PARAM_THREE_QUBIT_GATES
            )
            errors.append(f"{prefix}: unsupported gate {gate!r}; allowed gates are {allowed}")

    ordered_unique_keys = list(dict.fromkeys(parameter_keys))
    return errors, ordered_unique_keys


ANSATZ_SPEC: list = []
SPEC_ERRORS: list = []
PARAMETER_KEYS_PER_BLOCK: list = []
N_PARAMS_PER_BLOCK = 0
N_PARAMS = 0


def bind_spec(spec):
    """Install the candidate spec and recompute the derived sizes."""
    global ANSATZ_SPEC
    global SPEC_ERRORS
    global PARAMETER_KEYS_PER_BLOCK
    global N_PARAMS_PER_BLOCK
    global N_PARAMS
    ANSATZ_SPEC = spec
    SPEC_ERRORS, PARAMETER_KEYS_PER_BLOCK = validate_ansatz_spec(spec)
    N_PARAMS_PER_BLOCK = len(PARAMETER_KEYS_PER_BLOCK)
    N_PARAMS = N_PARAMS_PER_BLOCK * N_UPLOADS * N_REPEATS


def feature_map(inp: np.ndarray) -> None:
    """Encode input values as equidistant Pauli-X rotations (one per qubit)."""
    for wire in range(N_QUBITS):
        qml.RX(FEATURE_SCALE * inp[..., wire], wires=wire)


def apply_ansatz_block(params, block_index: int) -> None:
    """Apply one candidate ansatz block from the formal ANSATZ_SPEC."""
    if SPEC_ERRORS:
        raise ValueError("; ".join(SPEC_ERRORS))

    offset = block_index * N_PARAMS_PER_BLOCK
    key_to_position = {key: i for i, key in enumerate(PARAMETER_KEYS_PER_BLOCK)}
    for item in ANSATZ_SPEC:
        gate = str(item["gate"]).upper()
        if gate in ALLOWED_SINGLE_QUBIT_GATES:
            angle = params[offset + key_to_position[item["param"]]]
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
            angle = params[offset + key_to_position[item["param"]]]
            wires = [int(w) for w in item["wires"]]
            if gate == "CRX":
                qml.CRX(angle, wires=wires)
            elif gate == "CRY":
                qml.CRY(angle, wires=wires)
            elif gate == "CRZ":
                qml.CRZ(angle, wires=wires)
        elif gate in ALLOWED_PARAM_THREE_QUBIT_GATES:
            angle = params[offset + key_to_position[item["param"]]]
            wires = [int(w) for w in item["wires"]]
            if gate == "ZZZ":
                qml.MultiRZ(angle, wires=wires)
            elif gate == "CCRZ":
                qml.ctrl(qml.RZ, control=wires[:2])(angle, wires=wires[2])


_DEVICE = qml.device("default.qubit", wires=N_QUBITS, shots=None)


@qml.qnode(_DEVICE, interface="autograd", diff_method="backprop")
def circuit_z_expectations(inp, params):
    """Full simulated circuit returning per-qubit Z expectations."""
    for upload_index in range(N_UPLOADS):
        feature_map(inp)
        for repeat_index in range(N_REPEATS):
            block_index = upload_index * N_REPEATS + repeat_index
            apply_ansatz_block(params, block_index)
    return [qml.expval(qml.PauliZ(wire)) for wire in range(N_QUBITS)]


def class_expectations(inp, params):
    """Map nine Z expectations to the three fixed class scores."""
    z = pnp.stack(circuit_z_expectations(inp, params))
    c0 = (z[2] + z[3] + z[7] + z[8]) / 4.0
    c1 = (z[1] + z[4] + z[5] + z[6]) / 4.0
    c2 = z[0]
    return pnp.stack([c0, c1, c2])


def predict_batch(params, x_batch: np.ndarray):
    # Execute the whole batch in a SINGLE broadcasted circuit call.
    inp_arr = pnp.array(np.asarray(x_batch, dtype=float), requires_grad=False)
    z = pnp.stack(circuit_z_expectations(inp_arr, params))  # (N_QUBITS, B)
    c0 = (z[2] + z[3] + z[7] + z[8]) / 4.0
    c1 = (z[1] + z[4] + z[5] + z[6]) / 4.0
    c2 = z[0]
    return pnp.stack([c0, c1, c2], axis=1)  # (B, 3)


def l2_loss(params, x_batch: np.ndarray, y_batch: np.ndarray):
    predictions = predict_batch(params, x_batch)
    targets = pnp.array(y_batch, requires_grad=False)
    return pnp.mean(pnp.sum((predictions - targets) ** 2, axis=1))


def evaluate_split(params, x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    predictions = np.asarray(predict_batch(params, x), dtype=float)
    loss = float(np.mean(np.sum((predictions - y) ** 2, axis=1)))
    accuracy = float(np.mean(np.argmax(predictions, axis=1) == np.argmax(y, axis=1)))
    return {"accuracy": accuracy, "loss": loss}


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


def circuit_metadata(params) -> dict:
    with qml.queuing.AnnotatedQueue() as queue:
        for upload_index in range(N_UPLOADS):
            feature_map(np.zeros(N_QUBITS, dtype=np.int8))
            for repeat_index in range(N_REPEATS):
                block_index = upload_index * N_REPEATS + repeat_index
                apply_ansatz_block(params, block_index)
    tape = qml.tape.QuantumScript.from_queue(queue)
    operations = [(op.name, op.wires.tolist()) for op in tape.operations]
    depth = tape.graph.get_depth() if hasattr(tape.graph, "get_depth") else len(operations)
    return {
        "operations": operations,
        "depth": int(depth),
        "gate_count": int(len(operations)),
    }


def _dataset_summary(splits) -> dict:
    out = {}
    for name, (x, y) in splits.items():
        cls = np.argmax(y, axis=1)
        out[name] = {
            "rows": int(len(x)),
            "class_counts": [int(c) for c in np.bincount(cls, minlength=3)],
        }
    return out


def run_experiment(
    spec,
    seed: int = 0,
    data_seed: int | None = None,
    n_epochs: int | None = None,
    steps_per_epoch: int | None = None,
    batch_size: int | None = None,
    learning_rate: float | None = None,
    validation_size: int | None = None,
    convergence_threshold: float | None = None,
    eval_every_epochs: int | None = None,
    verbose: bool | None = None,
) -> dict:
    """Train the candidate ansatz and return ShinkaEvolve metrics."""
    bind_spec(spec)
    if SPEC_ERRORS:
        return {
            "spec_valid": False,
            "error": "; ".join(SPEC_ERRORS),
            "n_qubits": N_QUBITS,
            "n_uploads": N_UPLOADS,
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

    n_epochs = int(os.environ.get("N_EPOCHS", "100") if n_epochs is None else n_epochs)
    steps_per_epoch = int(os.environ.get("STEPS_PER_EPOCH", "30") if steps_per_epoch is None else steps_per_epoch)
    batch_size = int(os.environ.get("BATCH_SIZE", "15") if batch_size is None else batch_size)
    learning_rate = float(os.environ.get("LEARNING_RATE", "0.03") if learning_rate is None else learning_rate)
    convergence_threshold = float(
        os.environ.get("CONVERGENCE_THRESHOLD", "0.90")
        if convergence_threshold is None
        else convergence_threshold
    )
    eval_every_epochs = int(os.environ.get("EVAL_EVERY_EPOCHS", "1") if eval_every_epochs is None else eval_every_epochs)
    verbose = bool(int(os.environ.get("VERBOSE_TRAINING", "1"))) if verbose is None else bool(verbose)

    splits = _load_splits()
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
    params = pnp.array(rng.uniform(-0.05, 0.05, size=N_PARAMS), requires_grad=True)
    optimizer = qml.AdamOptimizer(stepsize=learning_rate)
    max_steps = n_epochs * steps_per_epoch
    global_step = 0
    convergence_epoch = None
    convergence_step = None
    history = []

    _log(
        {
            "event": "start",
            "seed": int(seed),
            "n_params": int(N_PARAMS),
            "n_params_per_block": int(N_PARAMS_PER_BLOCK),
            "n_uploads": int(N_UPLOADS),
            "n_repeats": int(N_REPEATS),
            "n_epochs": int(n_epochs),
            "steps_per_epoch": int(steps_per_epoch),
            "batch_size": int(batch_size),
            "learning_rate": float(learning_rate),
            "dataset": _dataset_summary(splits),
        },
        log_file,
        verbose,
    )

    early_stopping = bool(int(os.environ.get("EARLY_STOPPING", "1")))
    patience = int(os.environ.get("PATIENCE", "75"))
    min_delta = float(os.environ.get("MIN_DELTA", "1e-4"))
    best_val_loss = float("inf")
    best_params = params.copy()
    best_epoch = 0
    epochs_no_improve = 0
    stop_reason = "max_epochs"
    stopped_epoch = 0

    for epoch in range(1, n_epochs + 1):
        stopped_epoch = epoch
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

        train_metrics = evaluate_split(params, x_train, y_train)
        validation_metrics = evaluate_split(params, x_validation, y_validation)
        test_metrics = evaluate_split(params, x_test, y_test)
        if convergence_epoch is None and validation_metrics["accuracy"] >= convergence_threshold:
            convergence_epoch = epoch
            convergence_step = global_step
        record = {
            "event": "epoch",
            "epoch": int(epoch),
            "global_step": int(global_step),
            "batch_loss": float(last_batch_loss),
            "train_accuracy": train_metrics["accuracy"],
            "validation_accuracy": validation_metrics["accuracy"],
            "test_accuracy": test_metrics["accuracy"],
            "train_loss": train_metrics["loss"],
            "validation_loss": validation_metrics["loss"],
            "test_loss": test_metrics["loss"],
        }
        history.append(record)
        _log(record, log_file, verbose)

        if validation_metrics["loss"] < best_val_loss - min_delta:
            best_val_loss = validation_metrics["loss"]
            best_params = params.copy()
            best_epoch = epoch
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
    metadata = circuit_metadata(params)
    generalization_gap = abs(final_train["accuracy"] - final_test["accuracy"])
    parameter_efficiency = final_test["accuracy"] / max(float(N_PARAMS), 1.0)

    result = {
        "spec_valid": True,
        "n_qubits": N_QUBITS,
        "n_uploads": N_UPLOADS,
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
        "generalization_gap": generalization_gap,
        "parameter_efficiency": parameter_efficiency,
        "convergence_threshold": convergence_threshold,
        "convergence_epoch": convergence_epoch,
        "convergence_step": convergence_step,
        "max_steps": max_steps,
        "best_epoch": best_epoch,
        "stopped_epoch": stopped_epoch,
        "stop_reason": stop_reason,
        "best_val_loss": float(best_val_loss),
        "early_stopping_cfg": {
            "monitor": "val_loss",
            "patience": patience,
            "min_delta": min_delta,
            "max_epochs": n_epochs,
            "restore_best_weights": True,
        },
        "history_tail": history[-10:],
    }
    _log({"event": "final", **result}, log_file, verbose)
    return result
