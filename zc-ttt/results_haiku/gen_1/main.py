"""Seed program. Only ANSATZ_SPEC inside the EVOLVE-BLOCK is evolved.

Everything else about the task, that is how inputs are encoded, how the circuit
is measured, how training works and how metrics are computed, is fixed and lives
in a module that is not reproduced here. No information about the data is
available in this file.
"""

from _backend import run_experiment as _run

N_QUBITS = 9
ALLOWED_SINGLE_QUBIT_GATES = {"RX", "RY", "RZ"}
ALLOWED_TWO_QUBIT_GATES = {"CNOT", "CZ"}
ALLOWED_PARAM_TWO_QUBIT_GATES = {"CRX", "CRY", "CRZ"}
ALLOWED_THREE_QUBIT_GATES = {"ZZZ", "CCRZ"}


# EVOLVE-BLOCK-START
ANSATZ_SPEC = [
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_0"},
    {"gate": "RY", "wire": 3, "param": "ry_1"},
    {"gate": "RY", "wire": 4, "param": "ry_2"},
    {"gate": "RY", "wire": 5, "param": "ry_2"},
    {"gate": "RY", "wire": 6, "param": "ry_1"},
    {"gate": "RY", "wire": 7, "param": "ry_0"},
    {"gate": "RY", "wire": 8, "param": "ry_2"},
    {"gate": "CRX", "wires": [0, 2], "param": "crx_0"},
    {"gate": "CRX", "wires": [1, 3], "param": "crx_1"},
    {"gate": "CRX", "wires": [2, 4], "param": "crx_0"},
    {"gate": "CRX", "wires": [3, 5], "param": "crx_2"},
    {"gate": "CRY", "wires": [0, 3], "param": "cry_0"},
    {"gate": "CRY", "wires": [1, 8], "param": "cry_1"},
    {"gate": "CRY", "wires": [2, 6], "param": "cry_0"},
    {"gate": "CRY", "wires": [5, 7], "param": "cry_2"},
    {"gate": "CZ", "wires": [0, 7]},
    {"gate": "CZ", "wires": [0, 8]},
    {"gate": "CZ", "wires": [4, 8]},
    {"gate": "CZ", "wires": [6, 7]},
    {"gate": "RZ", "wire": 0, "param": "rz_0"},
    {"gate": "RZ", "wire": 1, "param": "rz_1"},
    {"gate": "RZ", "wire": 2, "param": "rz_0"},
    {"gate": "RZ", "wire": 3, "param": "rz_2"},
    {"gate": "RZ", "wire": 4, "param": "rz_1"},
    {"gate": "RZ", "wire": 5, "param": "rz_2"},
    {"gate": "RZ", "wire": 6, "param": "rz_0"},
    {"gate": "RZ", "wire": 7, "param": "rz_1"},
    {"gate": "RZ", "wire": 8, "param": "rz_2"},
    {"gate": "ZZZ", "wires": [0, 4, 8], "param": "zzz_0"},
    {"gate": "ZZZ", "wires": [1, 5, 6], "param": "zzz_1"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)