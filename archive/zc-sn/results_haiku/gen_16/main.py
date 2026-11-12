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


# EVOLVE-BLOCK-START
ANSATZ_SPEC = [
    # Layer 1: Shared initial RY rotations - pairs of qubits share parameters
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_b"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 3, "param": "ry_b"},
    {"gate": "RY", "wire": 4, "param": "ry_a"},
    {"gate": "RY", "wire": 5, "param": "ry_b"},
    {"gate": "RY", "wire": 6, "param": "ry_a"},
    {"gate": "RY", "wire": 7, "param": "ry_b"},
    
    # Layer 1b: Shared pre-entanglement RZ rotations
    {"gate": "RZ", "wire": 0, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre_b"},
    
    # Layer 2: Ring topology with parametrized CRZ gates
    # Ring connections with alternating parameters for expressivity
    {"gate": "CRZ", "wires": [0, 1], "param": "crz_ring_a"},
    {"gate": "CRZ", "wires": [2, 3], "param": "crz_ring_b"},
    {"gate": "CRZ", "wires": [4, 5], "param": "crz_ring_a"},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_ring_b"},
    
    # Cross-links for enhanced connectivity
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [7, 0]},
    
    # Second ring of CRZ with offset
    {"gate": "CRZ", "wires": [1, 3], "param": "crz_cross_a"},
    {"gate": "CRZ", "wires": [5, 7], "param": "crz_cross_b"},
    
    # Layer 3: Post-entanglement shared RZ rotations
    {"gate": "RZ", "wire": 0, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 2, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 4, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 5, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 7, "param": "rz_post_b"},
    
    # Layer 4: Global RX finishing layer with shared pairs for minimal overhead
    {"gate": "RX", "wire": 0, "param": "rx_global_a"},
    {"gate": "RX", "wire": 1, "param": "rx_global_b"},
    {"gate": "RX", "wire": 2, "param": "rx_global_a"},
    {"gate": "RX", "wire": 3, "param": "rx_global_b"},
    {"gate": "RX", "wire": 4, "param": "rx_global_a"},
    {"gate": "RX", "wire": 5, "param": "rx_global_b"},
    {"gate": "RX", "wire": 6, "param": "rx_global_a"},
    {"gate": "RX", "wire": 7, "param": "rx_global_b"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)