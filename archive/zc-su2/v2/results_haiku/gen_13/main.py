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
    # Initial rotation layer: pair-wise parameter sharing
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_0"},
    {"gate": "RY", "wire": 2, "param": "ry_1"},
    {"gate": "RY", "wire": 3, "param": "ry_1"},
    {"gate": "RY", "wire": 4, "param": "ry_2"},
    {"gate": "RY", "wire": 5, "param": "ry_2"},
    {"gate": "RY", "wire": 6, "param": "ry_3"},
    {"gate": "RY", "wire": 7, "param": "ry_3"},

    # First entangling block: nearest-neighbor XX gates on pairs
    {"gate": "XX", "wires": [0, 1], "param": "ent_0"},
    {"gate": "XX", "wires": [2, 3], "param": "ent_1"},
    {"gate": "XX", "wires": [4, 5], "param": "ent_2"},
    {"gate": "XX", "wires": [6, 7], "param": "ent_3"},

    # Second entangling block: cross-pair YY gates
    {"gate": "YY", "wires": [1, 2], "param": "cross_ent"},
    {"gate": "YY", "wires": [3, 4], "param": "cross_ent"},
    {"gate": "YY", "wires": [5, 6], "param": "cross_ent"},

    # Third entangling block: long-range ZZ gates
    {"gate": "ZZ", "wires": [0, 3], "param": "lr_ent"},
    {"gate": "ZZ", "wires": [1, 4], "param": "lr_ent"},
    {"gate": "ZZ", "wires": [2, 5], "param": "lr_ent"},
    {"gate": "ZZ", "wires": [3, 6], "param": "lr_ent"},
    {"gate": "ZZ", "wires": [4, 7], "param": "lr_ent"},

    # Final rotation layer: unified pair-wise RZ
    {"gate": "RZ", "wire": 0, "param": "rz_0"},
    {"gate": "RZ", "wire": 1, "param": "rz_0"},
    {"gate": "RZ", "wire": 2, "param": "rz_1"},
    {"gate": "RZ", "wire": 3, "param": "rz_1"},
    {"gate": "RZ", "wire": 4, "param": "rz_2"},
    {"gate": "RZ", "wire": 5, "param": "rz_2"},
    {"gate": "RZ", "wire": 6, "param": "rz_3"},
    {"gate": "RZ", "wire": 7, "param": "rz_3"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)