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
    # Single rotation layer with shared RY
    {"gate": "RY", "wire": 0, "param": "ry_shared"},
    {"gate": "RY", "wire": 1, "param": "ry_shared"},
    {"gate": "RY", "wire": 2, "param": "ry_shared"},
    {"gate": "RY", "wire": 3, "param": "ry_shared"},
    {"gate": "RY", "wire": 4, "param": "ry_shared"},
    {"gate": "RY", "wire": 5, "param": "ry_shared"},
    {"gate": "RY", "wire": 6, "param": "ry_shared"},
    {"gate": "RY", "wire": 7, "param": "ry_shared"},
    # Pre-entanglement RZ layer with shared parameter
    {"gate": "RZ", "wire": 0, "param": "rz_shared"},
    {"gate": "RZ", "wire": 1, "param": "rz_shared"},
    {"gate": "RZ", "wire": 2, "param": "rz_shared"},
    {"gate": "RZ", "wire": 3, "param": "rz_shared"},
    {"gate": "RZ", "wire": 4, "param": "rz_shared"},
    {"gate": "RZ", "wire": 5, "param": "rz_shared"},
    {"gate": "RZ", "wire": 6, "param": "rz_shared"},
    {"gate": "RZ", "wire": 7, "param": "rz_shared"},
    # Linear entangling ladder with parametrized CRZ gates
    {"gate": "CRZ", "wires": [0, 1], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [1, 2], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [2, 3], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [3, 4], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [4, 5], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [5, 6], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_shared"},
    # Post-entanglement RZ layer with shared parameter
    {"gate": "RZ", "wire": 0, "param": "rz_shared"},
    {"gate": "RZ", "wire": 1, "param": "rz_shared"},
    {"gate": "RZ", "wire": 2, "param": "rz_shared"},
    {"gate": "RZ", "wire": 3, "param": "rz_shared"},
    {"gate": "RZ", "wire": 4, "param": "rz_shared"},
    {"gate": "RZ", "wire": 5, "param": "rz_shared"},
    {"gate": "RZ", "wire": 6, "param": "rz_shared"},
    {"gate": "RZ", "wire": 7, "param": "rz_shared"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)