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
    {"gate": "RY", "wire": 0, "param": "ry_01"},
    {"gate": "RY", "wire": 1, "param": "ry_01"},
    {"gate": "RY", "wire": 2, "param": "ry_23"},
    {"gate": "RY", "wire": 3, "param": "ry_23"},
    {"gate": "RY", "wire": 4, "param": "ry_45"},
    {"gate": "RY", "wire": 5, "param": "ry_45"},
    {"gate": "RY", "wire": 6, "param": "ry_67"},
    {"gate": "RY", "wire": 7, "param": "ry_67"},
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [6, 7]},
    {"gate": "CRZ", "wires": [0, 4], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [1, 5], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [2, 6], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [3, 7], "param": "crz_shared"},

    # Second stacked copy of the same RY-CZ-CRZ block, reusing the identical
    # parameter names so no new trainable parameters are introduced. This
    # doubles the effective depth/expressivity of a single ansatz-block
    # application while keeping the unique parameter count fixed at 5.
    {"gate": "RY", "wire": 0, "param": "ry_01"},
    {"gate": "RY", "wire": 1, "param": "ry_01"},
    {"gate": "RY", "wire": 2, "param": "ry_23"},
    {"gate": "RY", "wire": 3, "param": "ry_23"},
    {"gate": "RY", "wire": 4, "param": "ry_45"},
    {"gate": "RY", "wire": 5, "param": "ry_45"},
    {"gate": "RY", "wire": 6, "param": "ry_67"},
    {"gate": "RY", "wire": 7, "param": "ry_67"},
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [6, 7]},
    {"gate": "CRZ", "wires": [0, 4], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [1, 5], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [2, 6], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [3, 7], "param": "crz_shared"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)