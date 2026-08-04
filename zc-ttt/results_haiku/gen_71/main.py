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
    # Layer 1: Efficient single-qubit encoding with shared RY basis
    {"gate": "RY", "wire": 0, "param": "ry_input"},
    {"gate": "RY", "wire": 1, "param": "ry_input"},
    {"gate": "RY", "wire": 2, "param": "ry_input"},
    {"gate": "RY", "wire": 3, "param": "ry_input"},
    {"gate": "RY", "wire": 4, "param": "ry_input"},
    {"gate": "RY", "wire": 5, "param": "ry_input"},
    {"gate": "RY", "wire": 6, "param": "ry_input"},
    {"gate": "RY", "wire": 7, "param": "ry_input"},
    {"gate": "RY", "wire": 8, "param": "ry_input"},

    # Layer 2: Local RZ phase coherence layer
    {"gate": "RZ", "wire": 0, "param": "rz_0"},
    {"gate": "RZ", "wire": 1, "param": "rz_0"},
    {"gate": "RZ", "wire": 2, "param": "rz_0"},
    {"gate": "RZ", "wire": 3, "param": "rz_1"},
    {"gate": "RZ", "wire": 4, "param": "rz_1"},
    {"gate": "RZ", "wire": 5, "param": "rz_1"},
    {"gate": "RZ", "wire": 6, "param": "rz_2"},
    {"gate": "RZ", "wire": 7, "param": "rz_2"},
    {"gate": "RZ", "wire": 8, "param": "rz_2"},

    # Layer 3: Hierarchical cluster-based entanglement
    # Cluster 1 (qubits 0,2,3,7,8): peripheral and control qubits
    {"gate": "CRZ", "wires": [0, 2], "param": "crz_tier1"},
    {"gate": "CZ", "wires": [0, 3]},
    {"gate": "CRY", "wires": [0, 7], "param": "cry_tier1"},
    {"gate": "CRZ", "wires": [0, 8], "param": "crz_tier1"},
    
    # Cluster 2 (qubits 1,3,8): secondary entanglement
    {"gate": "CRZ", "wires": [1, 3], "param": "crz_tier2"},
    {"gate": "CZ", "wires": [1, 8]},
    
    # Cluster 3 (qubits 2,4,6): mid-layer connectivity
    {"gate": "CRY", "wires": [2, 4], "param": "cry_tier1"},
    {"gate": "CZ", "wires": [2, 6]},
    
    # Cluster 4 (qubits 3,5,7): upper layer
    {"gate": "CRY", "wires": [3, 5], "param": "cry_tier2"},
    {"gate": "CRZ", "wires": [5, 7], "param": "crz_tier2"},
    
    # Cross-cluster bridge
    {"gate": "CZ", "wires": [4, 8]},
    {"gate": "CZ", "wires": [6, 7]},

    # Layer 4: Selective three-qubit interactions for non-linearity
    {"gate": "ZZZ", "wires": [0, 4, 8], "param": "zzz_bridge"},
    {"gate": "CCRZ", "wires": [1, 3, 6], "param": "ccrz_main"},
    {"gate": "ZZZ", "wires": [2, 5, 7], "param": "zzz_core"},

    # Layer 5: Final RX basis rotation for expressive output (shared for efficiency)
    {"gate": "RX", "wire": 0, "param": "rx_out"},
    {"gate": "RX", "wire": 1, "param": "rx_out"},
    {"gate": "RX", "wire": 2, "param": "rx_out"},
    {"gate": "RX", "wire": 3, "param": "rx_out"},
    {"gate": "RX", "wire": 4, "param": "rx_out"},
    {"gate": "RX", "wire": 5, "param": "rx_out"},
    {"gate": "RX", "wire": 6, "param": "rx_out"},
    {"gate": "RX", "wire": 7, "param": "rx_out"},
    {"gate": "RX", "wire": 8, "param": "rx_out"},

    # Layer 6: Final RZ layer with cluster-aware sharing for regularization
    {"gate": "RZ", "wire": 0, "param": "rz_final_0"},
    {"gate": "RZ", "wire": 1, "param": "rz_final_0"},
    {"gate": "RZ", "wire": 2, "param": "rz_final_0"},
    {"gate": "RZ", "wire": 3, "param": "rz_final_1"},
    {"gate": "RZ", "wire": 4, "param": "rz_final_1"},
    {"gate": "RZ", "wire": 5, "param": "rz_final_1"},
    {"gate": "RZ", "wire": 6, "param": "rz_final_2"},
    {"gate": "RZ", "wire": 7, "param": "rz_final_2"},
    {"gate": "RZ", "wire": 8, "param": "rz_final_2"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)