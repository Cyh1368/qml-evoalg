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
    # Layer 1: Alternating basis rotations - RX basis encoding
    {"gate": "RX", "wire": 0, "param": "rx_0"},
    {"gate": "RX", "wire": 1, "param": "rx_1"},
    {"gate": "RX", "wire": 2, "param": "rx_2"},
    {"gate": "RX", "wire": 3, "param": "rx_3"},
    {"gate": "RX", "wire": 4, "param": "rx_4"},
    {"gate": "RX", "wire": 5, "param": "rx_5"},
    {"gate": "RX", "wire": 6, "param": "rx_6"},
    {"gate": "RX", "wire": 7, "param": "rx_7"},
    {"gate": "RX", "wire": 8, "param": "rx_8"},

    # Layer 2: Alternating basis rotations - RY basis
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},
    {"gate": "RY", "wire": 8, "param": "ry_8"},

    # Layer 3: Varied two-qubit entanglement with mixed parametrized gates
    {"gate": "CRX", "wires": [0, 2], "param": "crx_0"},
    {"gate": "CZ", "wires": [0, 3]},
    {"gate": "CRY", "wires": [0, 7], "param": "cry_0"},
    {"gate": "CRZ", "wires": [0, 8], "param": "crz_0"},
    {"gate": "CRY", "wires": [1, 3], "param": "cry_1"},
    {"gate": "CZ", "wires": [1, 8]},
    {"gate": "CRX", "wires": [2, 4], "param": "crx_1"},
    {"gate": "CZ", "wires": [2, 6]},
    {"gate": "CRZ", "wires": [3, 5], "param": "crz_1"},
    {"gate": "CZ", "wires": [4, 8]},
    {"gate": "CRX", "wires": [5, 7], "param": "crx_2"},
    {"gate": "CZ", "wires": [6, 7]},

    # Layer 4: Three-qubit interactions on diverse qubit triples
    {"gate": "ZZZ", "wires": [0, 4, 8], "param": "zzz_0"},
    {"gate": "CCRZ", "wires": [1, 3, 6], "param": "ccrz_0"},
    {"gate": "ZZZ", "wires": [2, 5, 7], "param": "zzz_1"},

    # Layer 5: Final RZ basis for output preparation
    {"gate": "RZ", "wire": 0, "param": "rz_0"},
    {"gate": "RZ", "wire": 1, "param": "rz_1"},
    {"gate": "RZ", "wire": 2, "param": "rz_2"},
    {"gate": "RZ", "wire": 3, "param": "rz_3"},
    {"gate": "RZ", "wire": 4, "param": "rz_4"},
    {"gate": "RZ", "wire": 5, "param": "rz_5"},
    {"gate": "RZ", "wire": 6, "param": "rz_6"},
    {"gate": "RZ", "wire": 7, "param": "rz_7"},
    {"gate": "RZ", "wire": 8, "param": "rz_8"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)