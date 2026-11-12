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
ANSATZ_SPEC = [
    # Pre-entanglement rotations: ALL 8 qubits share a single global RY
    # parameter "theta1". This keeps the rotation budget at the minimal
    # possible single scalar for the whole layer.
    {"gate": "RY", "wire": 0, "param": "theta1"},
    {"gate": "RY", "wire": 1, "param": "theta1"},
    {"gate": "RY", "wire": 2, "param": "theta1"},
    {"gate": "RY", "wire": 3, "param": "theta1"},
    {"gate": "RY", "wire": 4, "param": "theta1"},
    {"gate": "RY", "wire": 5, "param": "theta1"},
    {"gate": "RY", "wire": 6, "param": "theta1"},
    {"gate": "RY", "wire": 7, "param": "theta1"},

    # Entangling layer: parametrized CRZ gates on antipodal (distance-4)
    # links and skip-2 (distance-2) links, ALL sharing a single second
    # parameter "theta2". This gives every qubit non-local entangling
    # partners at two different length scales while introducing only
    # one extra trainable scalar for the whole entangling layer.
    {"gate": "CRZ", "wires": [0, 4], "param": "theta2"},
    {"gate": "CRZ", "wires": [1, 5], "param": "theta2"},
    {"gate": "CRZ", "wires": [2, 6], "param": "theta2"},
    {"gate": "CRZ", "wires": [3, 7], "param": "theta2"},
    {"gate": "CRZ", "wires": [0, 2], "param": "theta2"},
    {"gate": "CRZ", "wires": [2, 4], "param": "theta2"},
    {"gate": "CRZ", "wires": [4, 6], "param": "theta2"},
    {"gate": "CRZ", "wires": [6, 0], "param": "theta2"},

    # Post-entanglement rotations: ALL 8 qubits share the SAME "theta1"
    # parameter (different axis: RZ), so the block realizes a richer,
    # non-trivial entangled transformation while the total unique
    # trainable-parameter count per block stays fixed at exactly 2.
    {"gate": "RZ", "wire": 0, "param": "theta1"},
    {"gate": "RZ", "wire": 1, "param": "theta1"},
    {"gate": "RZ", "wire": 2, "param": "theta1"},
    {"gate": "RZ", "wire": 3, "param": "theta1"},
    {"gate": "RZ", "wire": 4, "param": "theta1"},
    {"gate": "RZ", "wire": 5, "param": "theta1"},
    {"gate": "RZ", "wire": 6, "param": "theta1"},
    {"gate": "RZ", "wire": 7, "param": "theta1"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)