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
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 4, "param": "ry_a"},
    {"gate": "RY", "wire": 6, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_b"},
    {"gate": "RY", "wire": 3, "param": "ry_b"},
    {"gate": "RY", "wire": 5, "param": "ry_b"},
    {"gate": "RY", "wire": 7, "param": "ry_b"},
    {"gate": "CNOT", "wires": [0, 1]},
    {"gate": "CNOT", "wires": [1, 2]},
    {"gate": "CNOT", "wires": [2, 3]},
    {"gate": "CNOT", "wires": [3, 4]},
    {"gate": "CNOT", "wires": [4, 5]},
    {"gate": "CNOT", "wires": [5, 6]},
    {"gate": "CNOT", "wires": [6, 7]},
    {"gate": "RZ", "wire": 0, "param": "rz_a"},
    {"gate": "RZ", "wire": 2, "param": "rz_a"},
    {"gate": "RZ", "wire": 4, "param": "rz_a"},
    {"gate": "RZ", "wire": 6, "param": "rz_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_b"},
    {"gate": "RZ", "wire": 3, "param": "rz_b"},
    {"gate": "RZ", "wire": 5, "param": "rz_b"},
    {"gate": "RZ", "wire": 7, "param": "rz_b"},
    {"gate": "CNOT", "wires": [7, 6]},
    {"gate": "CNOT", "wires": [6, 5]},
    {"gate": "CNOT", "wires": [5, 4]},
    {"gate": "CNOT", "wires": [4, 3]},
    {"gate": "CNOT", "wires": [3, 2]},
    {"gate": "CNOT", "wires": [2, 1]},
    {"gate": "CNOT", "wires": [1, 0]},
    {"gate": "CRZ", "wires": [0, 1], "param": "ent_e"},
    {"gate": "CRZ", "wires": [4, 5], "param": "ent_e"},
    {"gate": "CRZ", "wires": [2, 3], "param": "ent_o"},
    {"gate": "CRZ", "wires": [6, 7], "param": "ent_o"},
    {"gate": "RY", "wire": 0, "param": "ry_c"},
    {"gate": "RY", "wire": 1, "param": "ry_c"},
    {"gate": "RY", "wire": 2, "param": "ry_c"},
    {"gate": "RY", "wire": 3, "param": "ry_c"},
    {"gate": "RY", "wire": 4, "param": "ry_c"},
    {"gate": "RY", "wire": 5, "param": "ry_c"},
    {"gate": "RY", "wire": 6, "param": "ry_c"},
    {"gate": "RY", "wire": 7, "param": "ry_c"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)