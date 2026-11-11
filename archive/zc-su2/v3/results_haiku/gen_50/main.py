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
# First block with shared rz_pre
ANSATZ_SPEC = [
    {"gate": "RY", "wire": 0, "param": "ry_1"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_1"},
    {"gate": "RY", "wire": 3, "param": "ry_1"},
    {"gate": "RY", "wire": 4, "param": "ry_1"},
    {"gate": "RY", "wire": 5, "param": "ry_1"},
    {"gate": "RY", "wire": 6, "param": "ry_1"},
    {"gate": "RY", "wire": 7, "param": "ry_1"},
    {"gate": "RZ", "wire": 0, "param": "rz_pre"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre"},
    {"gate": "XX", "wires": [0, 1], "param": "xx_1"},
    {"gate": "YY", "wires": [2, 3], "param": "yy_1"},
    {"gate": "ZZ", "wires": [4, 5], "param": "zz_1"},
    {"gate": "CRX", "wires": [6, 7], "param": "crx_1"},
    {"gate": "CRY", "wires": [1, 4], "param": "cry_1"},
    {"gate": "XX", "wires": [3, 6], "param": "xx_1b"},
    {"gate": "RZ", "wire": 0, "param": "rz_post"},
    {"gate": "RZ", "wire": 1, "param": "rz_post"},
    {"gate": "RZ", "wire": 2, "param": "rz_post"},
    {"gate": "RZ", "wire": 3, "param": "rz_post"},
    {"gate": "RZ", "wire": 4, "param": "rz_post"},
    {"gate": "RZ", "wire": 5, "param": "rz_post"},
    {"gate": "RZ", "wire": 6, "param": "rz_post"},
    {"gate": "RZ", "wire": 7, "param": "rz_post"},
    # Second block with shared rz_pre and rz_post
    {"gate": "RY", "wire": 0, "param": "ry_2"},
    {"gate": "RY", "wire": 1, "param": "ry_2"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_2"},
    {"gate": "RY", "wire": 4, "param": "ry_2"},
    {"gate": "RY", "wire": 5, "param": "ry_2"},
    {"gate": "RY", "wire": 6, "param": "ry_2"},
    {"gate": "RY", "wire": 7, "param": "ry_2"},
    {"gate": "RZ", "wire": 0, "param": "rz_pre"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre"},
    {"gate": "XX", "wires": [1, 2], "param": "xx_2"},
    {"gate": "YY", "wires": [3, 4], "param": "yy_2"},
    {"gate": "ZZ", "wires": [5, 6], "param": "zz_2"},
    {"gate": "CRX", "wires": [0, 7], "param": "crx_2"},
    {"gate": "CRY", "wires": [2, 5], "param": "cry_2"},
    {"gate": "YY", "wires": [4, 7], "param": "yy_2b"},
    {"gate": "RZ", "wire": 0, "param": "rz_post"},
    {"gate": "RZ", "wire": 1, "param": "rz_post"},
    {"gate": "RZ", "wire": 2, "param": "rz_post"},
    {"gate": "RZ", "wire": 3, "param": "rz_post"},
    {"gate": "RZ", "wire": 4, "param": "rz_post"},
    {"gate": "RZ", "wire": 5, "param": "rz_post"},
    {"gate": "RZ", "wire": 6, "param": "rz_post"},
    {"gate": "RZ", "wire": 7, "param": "rz_post"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)