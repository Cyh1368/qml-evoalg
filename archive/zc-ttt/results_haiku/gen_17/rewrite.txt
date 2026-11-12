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
    # Layer 1: Shared single-qubit rotations (reduced parameter count)
    # Lower qubits (0-4) share ry_low, upper qubits (5-8) share ry_high
    {"gate": "RY", "wire": 0, "param": "ry_low"},
    {"gate": "RY", "wire": 1, "param": "ry_low"},
    {"gate": "RY", "wire": 2, "param": "ry_low"},
    {"gate": "RY", "wire": 3, "param": "ry_low"},
    {"gate": "RY", "wire": 4, "param": "ry_low"},
    {"gate": "RY", "wire": 5, "param": "ry_high"},
    {"gate": "RY", "wire": 6, "param": "ry_high"},
    {"gate": "RY", "wire": 7, "param": "ry_high"},
    {"gate": "RY", "wire": 8, "param": "ry_high"},

    # Layer 1: Shared RX rotations (lower/upper split)
    {"gate": "RX", "wire": 0, "param": "rx_low"},
    {"gate": "RX", "wire": 1, "param": "rx_low"},
    {"gate": "RX", "wire": 2, "param": "rx_low"},
    {"gate": "RX", "wire": 3, "param": "rx_low"},
    {"gate": "RX", "wire": 4, "param": "rx_low"},
    {"gate": "RX", "wire": 5, "param": "rx_high"},
    {"gate": "RX", "wire": 6, "param": "rx_high"},
    {"gate": "RX", "wire": 7, "param": "rx_high"},
    {"gate": "RX", "wire": 8, "param": "rx_high"},

    # Layer 1: Shared RZ rotations
    {"gate": "RZ", "wire": 0, "param": "rz_pre"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre"},
    {"gate": "RZ", "wire": 8, "param": "rz_pre"},

    # Layer 2: Parametrized entanglement on allowed pairs
    # Original CRZ+CZ pattern
    {"gate": "CRZ", "wires": [0, 2], "param": "crz_0"},
    {"gate": "CZ", "wires": [0, 3]},
    {"gate": "CRZ", "wires": [0, 7], "param": "crz_1"},
    {"gate": "CRZ", "wires": [0, 8], "param": "crz_2"},
    {"gate": "CRZ", "wires": [1, 3], "param": "crz_3"},
    {"gate": "CZ", "wires": [1, 8]},
    {"gate": "CRZ", "wires": [2, 4], "param": "crz_4"},
    {"gate": "CZ", "wires": [2, 6]},
    
    # Rewired CRZ+CZ pair: [3,5]→[4,7] and [4,8]→[3,5]
    {"gate": "CRZ", "wires": [4, 7], "param": "crz_5"},
    {"gate": "CZ", "wires": [3, 5]},
    
    {"gate": "CRZ", "wires": [5, 7], "param": "crz_6"},
    {"gate": "CZ", "wires": [6, 7]},

    # Layer 3: Three-qubit interactions for expressivity
    {"gate": "ZZZ", "wires": [0, 4, 8], "param": "zzz_0"},
    {"gate": "ZZZ", "wires": [1, 5, 6], "param": "zzz_1"},
    {"gate": "ZZZ", "wires": [2, 3, 7], "param": "zzz_2"},

    # Layer 4: Final RZ rotations with shared parameter
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