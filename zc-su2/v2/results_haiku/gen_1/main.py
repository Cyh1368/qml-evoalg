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
    # Initial rotations with shared parameters
    {"gate": "RY", "wire": 0, "param": "ry_even"},
    {"gate": "RY", "wire": 1, "param": "ry_odd"},
    {"gate": "RY", "wire": 2, "param": "ry_even"},
    {"gate": "RY", "wire": 3, "param": "ry_odd"},
    {"gate": "RY", "wire": 4, "param": "ry_even"},
    {"gate": "RY", "wire": 5, "param": "ry_odd"},
    {"gate": "RY", "wire": 6, "param": "ry_even"},
    {"gate": "RY", "wire": 7, "param": "ry_odd"},
    {"gate": "RZ", "wire": 0, "param": "rz_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_b"},
    {"gate": "RZ", "wire": 2, "param": "rz_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_b"},
    {"gate": "RZ", "wire": 4, "param": "rz_a"},
    {"gate": "RZ", "wire": 5, "param": "rz_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_a"},
    {"gate": "RZ", "wire": 7, "param": "rz_b"},
    # Parametrized two-qubit entanglement: linear chain with shared params
    {"gate": "XX", "wires": [0, 1], "param": "xx"},
    {"gate": "YY", "wires": [1, 2], "param": "yy"},
    {"gate": "ZZ", "wires": [2, 3], "param": "zz"},
    {"gate": "XX", "wires": [3, 4], "param": "xx"},
    {"gate": "YY", "wires": [4, 5], "param": "yy"},
    {"gate": "ZZ", "wires": [5, 6], "param": "zz"},
    {"gate": "XX", "wires": [6, 7], "param": "xx"},
    # Diagonal cross-connections for richer entanglement
    {"gate": "YY", "wires": [0, 2], "param": "yy"},
    {"gate": "ZZ", "wires": [1, 3], "param": "zz"},
    {"gate": "XX", "wires": [2, 4], "param": "xx"},
    {"gate": "YY", "wires": [3, 5], "param": "yy"},
    {"gate": "ZZ", "wires": [4, 6], "param": "zz"},
    {"gate": "XX", "wires": [5, 7], "param": "xx"},
    # Final rotation layer
    {"gate": "RZ", "wire": 0, "param": "rz_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_b"},
    {"gate": "RZ", "wire": 2, "param": "rz_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_b"},
    {"gate": "RZ", "wire": 4, "param": "rz_a"},
    {"gate": "RZ", "wire": 5, "param": "rz_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_a"},
    {"gate": "RZ", "wire": 7, "param": "rz_b"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)