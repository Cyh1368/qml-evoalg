"""Seed program. Only ANSATZ_SPEC inside the EVOLVE-BLOCK is evolved.

Everything else about the task, that is how inputs are encoded, how the circuit
is measured, how training works and how metrics are computed, is fixed and lives
in a module that is not reproduced here. No information about the data is
available in this file.
"""

from _backend import run_experiment as _run

N_QUBITS = 8
ALLOWED_SINGLE_QUBIT_GATES = {"RX", "RY", "RZ"}
ALLOWED_TWO_QUBIT_GATES = {"CNOT", "CZ"}
ALLOWED_PARAM_TWO_QUBIT_GATES = {"CRX", "CRY", "CRZ"}
ALLOWED_ISING_GATES = {"XX", "YY", "ZZ"}


# EVOLVE-BLOCK-START
ANSATZ_SPEC = []

# --- Layer 1: parity-split RY rotations -------------------------------
# Even qubits share "ry_a", odd qubits share "ry_b". This gives the
# encoder two independent single-qubit degrees of freedom while keeping
# the parameter count low (2 names for 8 gates).
for _i in range(0, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "ry_a"})
for _i in range(1, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "ry_b"})

# --- Layer 2: forward nearest-neighbor CNOT ladder ---------------------
# Non-parametrized entangler that spreads correlations linearly across
# the register without touching the trainable-parameter budget.
for _i in range(N_QUBITS - 1):
    ANSATZ_SPEC.append({"gate": "CNOT", "wires": [_i, _i + 1]})

# --- Layer 3: parity-split RZ rotations --------------------------------
for _i in range(0, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": _i, "param": "rz_a"})
for _i in range(1, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": _i, "param": "rz_b"})

# --- Layer 4: backward nearest-neighbor CNOT ladder --------------------
# Running the ladder in reverse mixes information the opposite direction,
# increasing the effective entangling depth for the same fixed-gate cost.
for _i in range(N_QUBITS - 1, 0, -1):
    ANSATZ_SPEC.append({"gate": "CNOT", "wires": [_i, _i - 1]})

# --- Layer 5+6: dual-generator entangling core on disjoint pairs -------
# CRZ and CRX act on the same four disjoint pairs and DELIBERATELY share
# the single parameter name "ent". Because RZ- and RX-type controlled
# rotations do not commute, this gives two independent non-Clifford
# entangling generators driven by one trainable angle -- richer
# expressivity than a single controlled-rotation family, at zero extra
# parameter cost.
for _i in range(0, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "CRZ", "wires": [_i, _i + 1], "param": "ent"})
for _i in range(0, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "CRX", "wires": [_i, _i + 1], "param": "ent"})

# --- Layer 7: final global shared rotation -----------------------------
# A single shared RY on every qubit gives the readout a flexible common
# basis rotation before measurement.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "ry_c"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)