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
    # Layer 1: Initial encoding with RY rotations on all qubits
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},
    {"gate": "RY", "wire": 8, "param": "ry_8"},

    # Layer 2: Pre-entanglement phase shift with regional sharing
    # Lower region (qubits 0-4) with rz_pre_a
    {"gate": "RZ", "wire": 0, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre_a"},
    # Upper region (qubits 5-8) with rz_pre_b
    {"gate": "RZ", "wire": 5, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 8, "param": "rz_pre_b"},

    # Layer 3: Two-qubit entanglement with CRZ gates on allowed pairs
    # Removed crz_2 on [0,8] to reduce overfitting
    {"gate": "CRZ", "wires": [0, 2], "param": "crz_0"},
    {"gate": "CZ", "wires": [0, 3]},
    {"gate": "CRZ", "wires": [0, 7], "param": "crz_1"},
    {"gate": "CZ", "wires": [1, 8]},
    {"gate": "CRZ", "wires": [2, 4], "param": "crz_2"},
    {"gate": "CZ", "wires": [2, 6]},
    {"gate": "CRZ", "wires": [3, 5], "param": "crz_3"},
    {"gate": "CZ", "wires": [4, 8]},
    {"gate": "CRZ", "wires": [5, 7], "param": "crz_4"},
    {"gate": "CZ", "wires": [6, 7]},

    # Layer 4: Three-qubit interactions with selective gate types
    {"gate": "ZZZ", "wires": [0, 4, 8], "param": "zzz_0"},
    {"gate": "ZZZ", "wires": [1, 5, 6], "param": "zzz_1"},
    # Replace third ZZZ with CCRZ for more controlled interaction
    {"gate": "CCRZ", "wires": [2, 6, 7], "param": "ccrz_0"},

    # Layer 5: Post-entanglement phase shift with regional sharing
    # Lower region (qubits 0-4) with rz_post_a
    {"gate": "RZ", "wire": 0, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 2, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 4, "param": "rz_post_a"},
    # Upper region (qubits 5-8) with rz_post_b
    {"gate": "RZ", "wire": 5, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 7, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 8, "param": "rz_post_b"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)