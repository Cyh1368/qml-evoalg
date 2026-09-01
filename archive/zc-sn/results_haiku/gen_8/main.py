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


# EVOLVE-BLOCK-START
ANSATZ_SPEC = [
    {"gate": "RY", "wire": 0, "param": "ry_shared"},
    {"gate": "RY", "wire": 1, "param": "ry_shared"},
    {"gate": "RY", "wire": 2, "param": "ry_shared"},
    {"gate": "RY", "wire": 3, "param": "ry_shared"},
    {"gate": "RY", "wire": 4, "param": "ry_shared"},
    {"gate": "RY", "wire": 5, "param": "ry_shared"},
    {"gate": "RY", "wire": 6, "param": "ry_shared"},
    {"gate": "RY", "wire": 7, "param": "ry_shared"},
    {"gate": "RX", "wire": 0, "param": "rx_0"},
    {"gate": "RX", "wire": 1, "param": "rx_1"},
    {"gate": "RX", "wire": 2, "param": "rx_2"},
    {"gate": "RX", "wire": 3, "param": "rx_3"},
    {"gate": "RX", "wire": 4, "param": "rx_4"},
    {"gate": "RX", "wire": 5, "param": "rx_5"},
    {"gate": "RX", "wire": 6, "param": "rx_6"},
    {"gate": "RX", "wire": 7, "param": "rx_7"},
    {"gate": "RZ", "wire": 0, "param": "rz_pre_0"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre_1"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre_2"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre_3"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre_4"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre_5"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre_6"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre_7"},
    {"gate": "CRY", "wires": [0, 1], "param": "cry_01"},
    {"gate": "CRY", "wires": [2, 3], "param": "cry_23"},
    {"gate": "CRY", "wires": [4, 5], "param": "cry_45"},
    {"gate": "CRY", "wires": [6, 7], "param": "cry_67"},
    {"gate": "CRY", "wires": [1, 2], "param": "cry_12"},
    {"gate": "CRY", "wires": [3, 4], "param": "cry_34"},
    {"gate": "CRY", "wires": [5, 6], "param": "cry_56"},
    {"gate": "CRY", "wires": [0, 4], "param": "cry_04"},
    {"gate": "CRY", "wires": [1, 5], "param": "cry_15"},
    {"gate": "CRY", "wires": [2, 6], "param": "cry_26"},
    {"gate": "CRY", "wires": [3, 7], "param": "cry_37"},
    {"gate": "RZ", "wire": 0, "param": "rz_post_0"},
    {"gate": "RZ", "wire": 1, "param": "rz_post_1"},
    {"gate": "RZ", "wire": 2, "param": "rz_post_2"},
    {"gate": "RZ", "wire": 3, "param": "rz_post_3"},
    {"gate": "RZ", "wire": 4, "param": "rz_post_4"},
    {"gate": "RZ", "wire": 5, "param": "rz_post_5"},
    {"gate": "RZ", "wire": 6, "param": "rz_post_6"},
    {"gate": "RZ", "wire": 7, "param": "rz_post_7"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)