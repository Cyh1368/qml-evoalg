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
    # Global shared RX rotation
    {"gate": "RX", "wire": 0, "param": "rx1"},
    {"gate": "RX", "wire": 1, "param": "rx1"},
    {"gate": "RX", "wire": 2, "param": "rx1"},
    {"gate": "RX", "wire": 3, "param": "rx1"},
    {"gate": "RX", "wire": 4, "param": "rx1"},
    {"gate": "RX", "wire": 5, "param": "rx1"},
    {"gate": "RX", "wire": 6, "param": "rx1"},
    {"gate": "RX", "wire": 7, "param": "rx1"},

    # Global shared RY rotation
    {"gate": "RY", "wire": 0, "param": "ry1"},
    {"gate": "RY", "wire": 1, "param": "ry1"},
    {"gate": "RY", "wire": 2, "param": "ry1"},
    {"gate": "RY", "wire": 3, "param": "ry1"},
    {"gate": "RY", "wire": 4, "param": "ry1"},
    {"gate": "RY", "wire": 5, "param": "ry1"},
    {"gate": "RY", "wire": 6, "param": "ry1"},
    {"gate": "RY", "wire": 7, "param": "ry1"},

    # Fixed full entangling ring (parameter-free)
    {"gate": "CNOT", "wires": [0, 1]},
    {"gate": "CNOT", "wires": [1, 2]},
    {"gate": "CNOT", "wires": [2, 3]},
    {"gate": "CNOT", "wires": [3, 4]},
    {"gate": "CNOT", "wires": [4, 5]},
    {"gate": "CNOT", "wires": [5, 6]},
    {"gate": "CNOT", "wires": [6, 7]},
    {"gate": "CNOT", "wires": [7, 0]},

    # Shared-angle parametrized entangling layer on disjoint pairs
    # (sparser than a full ring, reducing depth and overfitting risk
    # while keeping the same single trainable angle)
    {"gate": "CRZ", "wires": [0, 1], "param": "ent1"},
    {"gate": "CRZ", "wires": [2, 3], "param": "ent1"},
    {"gate": "CRZ", "wires": [4, 5], "param": "ent1"},
    {"gate": "CRZ", "wires": [6, 7], "param": "ent1"},

    # Global shared RZ rotation
    {"gate": "RZ", "wire": 0, "param": "rz1"},
    {"gate": "RZ", "wire": 1, "param": "rz1"},
    {"gate": "RZ", "wire": 2, "param": "rz1"},
    {"gate": "RZ", "wire": 3, "param": "rz1"},
    {"gate": "RZ", "wire": 4, "param": "rz1"},
    {"gate": "RZ", "wire": 5, "param": "rz1"},
    {"gate": "RZ", "wire": 6, "param": "rz1"},
    {"gate": "RZ", "wire": 7, "param": "rz1"},

    # Final global shared RY rotation
    {"gate": "RY", "wire": 0, "param": "ry2"},
    {"gate": "RY", "wire": 1, "param": "ry2"},
    {"gate": "RY", "wire": 2, "param": "ry2"},
    {"gate": "RY", "wire": 3, "param": "ry2"},
    {"gate": "RY", "wire": 4, "param": "ry2"},
    {"gate": "RY", "wire": 5, "param": "ry2"},
    {"gate": "RY", "wire": 6, "param": "ry2"},
    {"gate": "RY", "wire": 7, "param": "ry2"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)