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
    # Initial rotation layer with mixed axes for symmetry breaking
    {"gate": "RY", "wire": 0, "param": "ry_init"},
    {"gate": "RX", "wire": 1, "param": "rx_init"},
    {"gate": "RY", "wire": 2, "param": "ry_init"},
    {"gate": "RX", "wire": 3, "param": "rx_init"},
    {"gate": "RY", "wire": 4, "param": "ry_init"},
    {"gate": "RX", "wire": 5, "param": "rx_init"},
    {"gate": "RY", "wire": 6, "param": "ry_init"},
    {"gate": "RX", "wire": 7, "param": "rx_init"},
    
    # Pre-entanglement RZ rotations (shared within pairs)
    {"gate": "RZ", "wire": 0, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre_b"},
    
    # Non-linear entanglement topology with adaptive coupling
    # Short-range nearest-neighbor with parametrized XX gates
    {"gate": "XX", "wires": [0, 1], "param": "xx_01"},
    {"gate": "XX", "wires": [2, 3], "param": "xx_23"},
    {"gate": "XX", "wires": [4, 5], "param": "xx_45"},
    {"gate": "XX", "wires": [6, 7], "param": "xx_67"},
    
    # Long-range connections with fixed CZ for topology diversity
    {"gate": "CZ", "wires": [0, 4]},
    {"gate": "CZ", "wires": [2, 6]},
    
    # Post-entanglement rotations
    {"gate": "RZ", "wire": 0, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 2, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 3, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 4, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 5, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 6, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 7, "param": "rz_post_b"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)