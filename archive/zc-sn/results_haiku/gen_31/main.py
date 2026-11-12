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
    # ========== Layer 1: Initial RY Encoding ==========
    # Shared initial RY rotations - pairs of qubits share parameters for efficiency
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_b"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 3, "param": "ry_b"},
    {"gate": "RY", "wire": 4, "param": "ry_a"},
    {"gate": "RY", "wire": 5, "param": "ry_b"},
    {"gate": "RY", "wire": 6, "param": "ry_a"},
    {"gate": "RY", "wire": 7, "param": "ry_b"},
    
    # ========== Layer 2: Pre-entanglement RZ ==========
    # Shared pre-entanglement RZ rotations - pairs share parameters
    {"gate": "RZ", "wire": 0, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre_b"},
    
    # ========== Layer 3: Primary Entanglement (Linear Chain) ==========
    # Linear chain CZ gates for low-depth nearest-neighbor entanglement
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [6, 7]},
    
    # ========== Layer 4: Mid-circuit RX Rotation ==========
    # Global X-mixing with single shared parameter for enhanced expressivity
    {"gate": "RX", "wire": 0, "param": "rx_mid"},
    {"gate": "RX", "wire": 1, "param": "rx_mid"},
    {"gate": "RX", "wire": 2, "param": "rx_mid"},
    {"gate": "RX", "wire": 3, "param": "rx_mid"},
    {"gate": "RX", "wire": 4, "param": "rx_mid"},
    {"gate": "RX", "wire": 5, "param": "rx_mid"},
    {"gate": "RX", "wire": 6, "param": "rx_mid"},
    {"gate": "RX", "wire": 7, "param": "rx_mid"},
    
    # ========== Layer 5: Reverse chain with Parametrized CRZ ==========
    # Reverse chain with shared CRZ gate for amplitude-based entanglement control
    {"gate": "CRZ", "wires": [7, 6], "param": "crz_rev"},
    {"gate": "CRZ", "wires": [6, 5], "param": "crz_rev"},
    {"gate": "CRZ", "wires": [5, 4], "param": "crz_rev"},
    {"gate": "CRZ", "wires": [4, 3], "param": "crz_rev"},
    {"gate": "CRZ", "wires": [3, 2], "param": "crz_rev"},
    {"gate": "CRZ", "wires": [2, 1], "param": "crz_rev"},
    {"gate": "CRZ", "wires": [1, 0], "param": "crz_rev"},
    
    # ========== Layer 6: Post-entanglement RZ ==========
    # Shared post-entanglement RZ rotations - pairs share parameters
    {"gate": "RZ", "wire": 0, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 2, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 4, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 5, "param": "rz_post_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_post_a"},
    {"gate": "RZ", "wire": 7, "param": "rz_post_b"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)