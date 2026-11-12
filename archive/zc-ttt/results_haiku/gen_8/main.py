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
    # Initial rotation layer with RX and RY for better coverage
    {"gate": "RX", "wire": 0, "param": "rx_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RX", "wire": 2, "param": "rx_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RX", "wire": 4, "param": "rx_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RX", "wire": 6, "param": "rx_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},
    {"gate": "RX", "wire": 8, "param": "rx_8"},
    # Shared RZ layer for efficiency
    {"gate": "RZ", "wire": 0, "param": "rz_pre"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre"},
    {"gate": "RZ", "wire": 8, "param": "rz_pre"},
    # Parametrized two-qubit entanglement layer
    {"gate": "CRZ", "wires": [0, 2], "param": "crz_0"},
    {"gate": "CRZ", "wires": [0, 3], "param": "crz_01"},
    {"gate": "CRZ", "wires": [0, 7], "param": "crz_1"},
    {"gate": "CRZ", "wires": [0, 8], "param": "crz_2"},
    {"gate": "CRZ", "wires": [1, 3], "param": "crz_3"},
    {"gate": "CRZ", "wires": [1, 8], "param": "crz_1b"},
    {"gate": "CRZ", "wires": [2, 4], "param": "crz_4"},
    {"gate": "CRZ", "wires": [2, 6], "param": "crz_2b"},
    {"gate": "CRZ", "wires": [3, 5], "param": "crz_5"},
    {"gate": "CRZ", "wires": [4, 8], "param": "crz_4b"},
    {"gate": "CRZ", "wires": [5, 7], "param": "crz_6"},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_6b"},
    # Enhanced three-qubit interactions for expressivity
    {"gate": "ZZZ", "wires": [0, 4, 8], "param": "zzz_0"},
    {"gate": "ZZZ", "wires": [1, 5, 6], "param": "zzz_1"},
    {"gate": "ZZZ", "wires": [2, 3, 7], "param": "zzz_2"},
    {"gate": "ZZZ", "wires": [0, 1, 4], "param": "zzz_3"},
    # Final rotation layer
    {"gate": "RZ", "wire": 0, "param": "rz_post"},
    {"gate": "RZ", "wire": 1, "param": "rz_post"},
    {"gate": "RZ", "wire": 2, "param": "rz_post"},
    {"gate": "RZ", "wire": 3, "param": "rz_post"},
    {"gate": "RZ", "wire": 4, "param": "rz_post"},
    {"gate": "RZ", "wire": 5, "param": "rz_post"},
    {"gate": "RZ", "wire": 6, "param": "rz_post"},
    {"gate": "RZ", "wire": 7, "param": "rz_post"},
    {"gate": "RZ", "wire": 8, "param": "rz_post"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)