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
    # Pairs of qubits share parameters for efficiency
    {"gate": "RY", "wire": 0, "param": "ry_init_a"},
    {"gate": "RY", "wire": 1, "param": "ry_init_b"},
    {"gate": "RY", "wire": 2, "param": "ry_init_a"},
    {"gate": "RY", "wire": 3, "param": "ry_init_b"},
    {"gate": "RY", "wire": 4, "param": "ry_init_a"},
    {"gate": "RY", "wire": 5, "param": "ry_init_b"},
    {"gate": "RY", "wire": 6, "param": "ry_init_a"},
    {"gate": "RY", "wire": 7, "param": "ry_init_b"},

    # ========== Layer 2: Pre-entanglement RZ ==========
    # Single shared RZ parameter per pair
    {"gate": "RZ", "wire": 0, "param": "rz_prep_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_prep_b"},
    {"gate": "RZ", "wire": 2, "param": "rz_prep_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_prep_b"},
    {"gate": "RZ", "wire": 4, "param": "rz_prep_a"},
    {"gate": "RZ", "wire": 5, "param": "rz_prep_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_prep_a"},
    {"gate": "RZ", "wire": 7, "param": "rz_prep_b"},

    # ========== Layer 3: Primary Entanglement (Forward Chain) ==========
    # Linear nearest-neighbor chain with selective parametrized CRZ for expressivity
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CRZ", "wires": [1, 2], "param": "crz_fwd"},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CRZ", "wires": [5, 6], "param": "crz_fwd"},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [6, 7]},

    # ========== Layer 4: Secondary Entanglement (Reverse Chain) ==========
    # Reverse direction CRZ for bi-directional information flow with trainability
    {"gate": "CRZ", "wires": [7, 6], "param": "crz_back"},
    {"gate": "CRZ", "wires": [6, 5], "param": "crz_back"},
    {"gate": "CRZ", "wires": [5, 4], "param": "crz_back"},
    {"gate": "CRZ", "wires": [4, 3], "param": "crz_back"},
    {"gate": "CRZ", "wires": [3, 2], "param": "crz_back"},
    {"gate": "CRZ", "wires": [2, 1], "param": "crz_back"},
    {"gate": "CRZ", "wires": [1, 0], "param": "crz_back"},

    # ========== Layer 6: Mid-circuit RX Rotation ==========
    # Single shared parameter for global X-mixing
    {"gate": "RX", "wire": 0, "param": "rx_mid"},
    {"gate": "RX", "wire": 1, "param": "rx_mid"},
    {"gate": "RX", "wire": 2, "param": "rx_mid"},
    {"gate": "RX", "wire": 3, "param": "rx_mid"},
    {"gate": "RX", "wire": 4, "param": "rx_mid"},
    {"gate": "RX", "wire": 5, "param": "rx_mid"},
    {"gate": "RX", "wire": 6, "param": "rx_mid"},
    {"gate": "RX", "wire": 7, "param": "rx_mid"},

    # ========== Layer 7: Post-entanglement RZ ==========
    # Pairs of qubits share parameters (same pattern as pre-entanglement)
    {"gate": "RZ", "wire": 0, "param": "rz_final_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_final_b"},
    {"gate": "RZ", "wire": 2, "param": "rz_final_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_final_b"},
    {"gate": "RZ", "wire": 4, "param": "rz_final_a"},
    {"gate": "RZ", "wire": 5, "param": "rz_final_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_final_a"},
    {"gate": "RZ", "wire": 7, "param": "rz_final_b"},

    # ========== Layer 8: Final RY for Output Basis Rotation ==========
    # Pairs of qubits share parameters for efficient basis rotation
    {"gate": "RY", "wire": 0, "param": "ry_final_a"},
    {"gate": "RY", "wire": 1, "param": "ry_final_b"},
    {"gate": "RY", "wire": 2, "param": "ry_final_a"},
    {"gate": "RY", "wire": 3, "param": "ry_final_b"},
    {"gate": "RY", "wire": 4, "param": "ry_final_a"},
    {"gate": "RY", "wire": 5, "param": "ry_final_b"},
    {"gate": "RY", "wire": 6, "param": "ry_final_a"},
    {"gate": "RY", "wire": 7, "param": "ry_final_b"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)