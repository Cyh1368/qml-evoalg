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
    # Single-qubit RY layer: two shared groups (wires 0-3 vs 4-7)
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_a"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 3, "param": "ry_a"},
    {"gate": "RY", "wire": 4, "param": "ry_b"},
    {"gate": "RY", "wire": 5, "param": "ry_b"},
    {"gate": "RY", "wire": 6, "param": "ry_b"},
    {"gate": "RY", "wire": 7, "param": "ry_b"},

    # Pre-entanglement RZ layer: two shared groups
    {"gate": "RZ", "wire": 0, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre_b"},

    # Ring entangling layer split into even/odd edges, each with its own
    # shared parameter to give the entangling structure two independent
    # degrees of freedom instead of one.
    {"gate": "ZZ", "wires": [0, 1], "param": "zz_e"},
    {"gate": "ZZ", "wires": [2, 3], "param": "zz_e"},
    {"gate": "ZZ", "wires": [4, 5], "param": "zz_e"},
    {"gate": "ZZ", "wires": [6, 7], "param": "zz_e"},
    {"gate": "ZZ", "wires": [1, 2], "param": "zz_o"},
    {"gate": "ZZ", "wires": [3, 4], "param": "zz_o"},
    {"gate": "ZZ", "wires": [5, 6], "param": "zz_o"},
    {"gate": "ZZ", "wires": [7, 0], "param": "zz_o"},

    # Post-entanglement RZ layer: two shared groups
    {"gate": "RZ", "wire": 0, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 2, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 4, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 5, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 7, "param": "rz_post_b"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)