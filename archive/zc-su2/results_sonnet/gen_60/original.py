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
    # Global RX pre-rotation: single shared parameter "theta1" across all
    # 8 qubits.
    {"gate": "RX", "wire": 0, "param": "theta1"},
    {"gate": "RX", "wire": 1, "param": "theta1"},
    {"gate": "RX", "wire": 2, "param": "theta1"},
    {"gate": "RX", "wire": 3, "param": "theta1"},
    {"gate": "RX", "wire": 4, "param": "theta1"},
    {"gate": "RX", "wire": 5, "param": "theta1"},
    {"gate": "RX", "wire": 6, "param": "theta1"},
    {"gate": "RX", "wire": 7, "param": "theta1"},

    # Global RY rotation, reusing "theta1" (non-commuting axis chain).
    {"gate": "RY", "wire": 0, "param": "theta1"},
    {"gate": "RY", "wire": 1, "param": "theta1"},
    {"gate": "RY", "wire": 2, "param": "theta1"},
    {"gate": "RY", "wire": 3, "param": "theta1"},
    {"gate": "RY", "wire": 4, "param": "theta1"},
    {"gate": "RY", "wire": 5, "param": "theta1"},
    {"gate": "RY", "wire": 6, "param": "theta1"},
    {"gate": "RY", "wire": 7, "param": "theta1"},

    # Fixed nearest-neighbor CZ ring (zero trainable parameters).
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [6, 7]},
    {"gate": "CZ", "wires": [7, 0]},

    # Parametrized long-range entangling layer: single shared parameter
    # "theta2", distinct from the rotation angle "theta1", giving the
    # circuit an independent entanglement-strength degree of freedom.
    {"gate": "CRZ", "wires": [0, 2], "param": "theta2"},
    {"gate": "CRZ", "wires": [1, 3], "param": "theta2"},
    {"gate": "CRZ", "wires": [2, 4], "param": "theta2"},
    {"gate": "CRZ", "wires": [3, 5], "param": "theta2"},
    {"gate": "CRZ", "wires": [4, 6], "param": "theta2"},
    {"gate": "CRZ", "wires": [5, 7], "param": "theta2"},
    {"gate": "CRZ", "wires": [6, 0], "param": "theta2"},
    {"gate": "CRZ", "wires": [7, 1], "param": "theta2"},

    # Final global RZ rotation reusing "theta1" to complete the
    # single-qubit rotation basis.
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