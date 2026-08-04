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
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_0"},
    {"gate": "RY", "wire": 3, "param": "ry_1"},
    {"gate": "RY", "wire": 4, "param": "ry_0"},
    {"gate": "RY", "wire": 5, "param": "ry_1"},
    {"gate": "RY", "wire": 6, "param": "ry_0"},
    {"gate": "RY", "wire": 7, "param": "ry_1"},
    {"gate": "RZ", "wire": 0, "param": "rz_pre"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre"},
    {"gate": "XX", "wires": [0, 1], "param": "xx_01"},
    {"gate": "XX", "wires": [6, 7], "param": "xx_67"},
    {"gate": "XX", "wires": [0, 7], "param": "xx_07"},
    {"gate": "YY", "wires": [2, 3], "param": "yy_23"},
    {"gate": "YY", "wires": [1, 4], "param": "yy_14"},
    {"gate": "ZZ", "wires": [4, 5], "param": "zz_45"},
    {"gate": "ZZ", "wires": [3, 6], "param": "zz_36"},
    {"gate": "RY", "wire": 0, "param": "ry_1"},
    {"gate": "RY", "wire": 1, "param": "ry_0"},
    {"gate": "RY", "wire": 2, "param": "ry_1"},
    {"gate": "RY", "wire": 3, "param": "ry_0"},
    {"gate": "RY", "wire": 4, "param": "ry_1"},
    {"gate": "RY", "wire": 5, "param": "ry_0"},
    {"gate": "RY", "wire": 6, "param": "ry_1"},
    {"gate": "RY", "wire": 7, "param": "ry_0"},
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