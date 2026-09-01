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
    # Independent amplitude control preserves local flexibility.
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},
    {"gate": "RY", "wire": 8, "param": "ry_8"},

    # Share phase parameters across graph-related vertex pairs.
    {"gate": "RZ", "wire": 0, "param": "rz_0"},
    {"gate": "RZ", "wire": 1, "param": "rz_14"},
    {"gate": "RZ", "wire": 2, "param": "rz_23"},
    {"gate": "RZ", "wire": 3, "param": "rz_23"},
    {"gate": "RZ", "wire": 4, "param": "rz_14"},
    {"gate": "RZ", "wire": 5, "param": "rz_56"},
    {"gate": "RZ", "wire": 6, "param": "rz_56"},
    {"gate": "RZ", "wire": 7, "param": "rz_7"},
    {"gate": "RZ", "wire": 8, "param": "rz_8"},

    # Complementary higher-order correlation channels.
    {"gate": "ZZZ", "wires": [2, 4, 6], "param": "zzz_2_4_6"},
    {"gate": "ZZZ", "wires": [1, 3, 8], "param": "zzz_1_3_8"},

    # Sparse graph entanglement; omit the non-critical (3,5) edge.
    {"gate": "CZ", "wires": [0, 2]},
    {"gate": "CZ", "wires": [0, 3]},
    {"gate": "CZ", "wires": [0, 7]},
    {"gate": "CZ", "wires": [0, 8]},
    {"gate": "CZ", "wires": [1, 3]},
    {"gate": "CZ", "wires": [1, 8]},
    {"gate": "CZ", "wires": [2, 4]},
    {"gate": "CZ", "wires": [2, 6]},
    {"gate": "CZ", "wires": [4, 8]},
    {"gate": "CZ", "wires": [5, 7]},
    {"gate": "CZ", "wires": [6, 7]},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)