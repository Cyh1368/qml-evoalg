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
    # Layer 1: Individual qubit rotations (qubit-specific parameters)
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},
    {"gate": "RZ", "wire": 0, "param": "rz_0"},
    {"gate": "RZ", "wire": 1, "param": "rz_1"},
    {"gate": "RZ", "wire": 2, "param": "rz_2"},
    {"gate": "RZ", "wire": 3, "param": "rz_3"},
    {"gate": "RZ", "wire": 4, "param": "rz_4"},
    {"gate": "RZ", "wire": 5, "param": "rz_5"},
    {"gate": "RZ", "wire": 6, "param": "rz_6"},
    {"gate": "RZ", "wire": 7, "param": "rz_7"},
    # Layer 2: Parametrized Ising gates for learnable entanglement
    {"gate": "XX", "wires": [0, 1], "param": "xx_01"},
    {"gate": "YY", "wires": [1, 2], "param": "yy_12"},
    {"gate": "ZZ", "wires": [2, 3], "param": "zz_23"},
    {"gate": "XX", "wires": [3, 4], "param": "xx_34"},
    {"gate": "YY", "wires": [4, 5], "param": "yy_45"},
    {"gate": "ZZ", "wires": [5, 6], "param": "zz_56"},
    {"gate": "XX", "wires": [6, 7], "param": "xx_67"},
    {"gate": "YY", "wires": [7, 0], "param": "yy_70"},
    # Layer 3: Additional qubit rotations for fine-tuning
    {"gate": "RY", "wire": 0, "param": "ry2_0"},
    {"gate": "RY", "wire": 1, "param": "ry2_1"},
    {"gate": "RY", "wire": 2, "param": "ry2_2"},
    {"gate": "RY", "wire": 3, "param": "ry2_3"},
    {"gate": "RY", "wire": 4, "param": "ry2_4"},
    {"gate": "RY", "wire": 5, "param": "ry2_5"},
    {"gate": "RY", "wire": 6, "param": "ry2_6"},
    {"gate": "RY", "wire": 7, "param": "ry2_7"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)