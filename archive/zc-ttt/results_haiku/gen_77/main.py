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
    # Layer 0: Initial RX encoding for orthogonal basis exploration
    {"gate": "RX", "wire": 0, "param": "rx_init"},
    {"gate": "RX", "wire": 1, "param": "rx_init"},
    {"gate": "RX", "wire": 2, "param": "rx_init"},
    {"gate": "RX", "wire": 3, "param": "rx_init"},
    {"gate": "RX", "wire": 4, "param": "rx_init"},
    {"gate": "RX", "wire": 5, "param": "rx_init"},
    {"gate": "RX", "wire": 6, "param": "rx_init"},
    {"gate": "RX", "wire": 7, "param": "rx_init"},
    {"gate": "RX", "wire": 8, "param": "rx_init"},

    # Layer 1: Individual RY encoding on all qubits
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},
    {"gate": "RY", "wire": 8, "param": "ry_8"},

    # Layer 2: Hierarchical entanglement - Level 1: Short-range interactions
    # Using CRY for amplitude modulation on core pairs
    {"gate": "CRY", "wires": [0, 2], "param": "cry_short_0"},
    {"gate": "CZ", "wires": [0, 3]},
    {"gate": "CRY", "wires": [1, 3], "param": "cry_short_1"},
    {"gate": "CZ", "wires": [2, 4]},
    {"gate": "CRY", "wires": [3, 5], "param": "cry_short_2"},
    {"gate": "CZ", "wires": [4, 8]},
    {"gate": "CRY", "wires": [5, 7], "param": "cry_short_3"},
    {"gate": "CZ", "wires": [6, 7]},

    # Layer 3: Hierarchical entanglement - Level 2: Long-range interactions
    # Using CRZ for phase interactions on distant pairs
    {"gate": "CRZ", "wires": [0, 7], "param": "crz_long_0"},
    {"gate": "CRZ", "wires": [0, 8], "param": "crz_long_1"},
    {"gate": "CZ", "wires": [1, 8]},
    {"gate": "CRZ", "wires": [2, 6], "param": "crz_long_2"},

    # Layer 4: Three-qubit interactions for enhanced expressivity
    # Using ZZZ for symmetric three-body correlations
    {"gate": "ZZZ", "wires": [0, 4, 8], "param": "zzz_0"},
    {"gate": "ZZZ", "wires": [2, 5, 7], "param": "zzz_1"},
    
    # Using CCRZ for controlled three-body phase interactions
    {"gate": "CCRZ", "wires": [1, 3, 6], "param": "ccrz_0"},
    {"gate": "CCRZ", "wires": [0, 5, 8], "param": "ccrz_1"},

    # Layer 5: Post-entanglement RZ phase layer for coherence adjustment
    {"gate": "RZ", "wire": 0, "param": "rz_post"},
    {"gate": "RZ", "wire": 1, "param": "rz_post"},
    {"gate": "RZ", "wire": 2, "param": "rz_post"},
    {"gate": "RZ", "wire": 3, "param": "rz_post"},
    {"gate": "RZ", "wire": 4, "param": "rz_post"},
    {"gate": "RZ", "wire": 5, "param": "rz_post"},
    {"gate": "RZ", "wire": 6, "param": "rz_post"},
    {"gate": "RZ", "wire": 7, "param": "rz_post"},
    {"gate": "RZ", "wire": 8, "param": "rz_post"},

    # Layer 6: Final RY output preparation layer
    {"gate": "RY", "wire": 0, "param": "ry_out_0"},
    {"gate": "RY", "wire": 1, "param": "ry_out_1"},
    {"gate": "RY", "wire": 2, "param": "ry_out_2"},
    {"gate": "RY", "wire": 3, "param": "ry_out_3"},
    {"gate": "RY", "wire": 4, "param": "ry_out_4"},
    {"gate": "RY", "wire": 5, "param": "ry_out_5"},
    {"gate": "RY", "wire": 6, "param": "ry_out_6"},
    {"gate": "RY", "wire": 7, "param": "ry_out_7"},
    {"gate": "RY", "wire": 8, "param": "ry_out_8"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)