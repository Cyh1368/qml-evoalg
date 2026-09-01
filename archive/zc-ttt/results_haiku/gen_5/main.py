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
    # Layer 1: Initial RY rotations with shared parameters
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_b"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 3, "param": "ry_b"},
    {"gate": "RY", "wire": 4, "param": "ry_a"},
    {"gate": "RY", "wire": 5, "param": "ry_b"},
    {"gate": "RY", "wire": 6, "param": "ry_a"},
    {"gate": "RY", "wire": 7, "param": "ry_b"},
    {"gate": "RY", "wire": 8, "param": "ry_a"},
    
    # Layer 1: RZ rotations with shared parameters
    {"gate": "RZ", "wire": 0, "param": "rz_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_b"},
    {"gate": "RZ", "wire": 2, "param": "rz_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_b"},
    {"gate": "RZ", "wire": 4, "param": "rz_a"},
    {"gate": "RZ", "wire": 5, "param": "rz_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_a"},
    {"gate": "RZ", "wire": 7, "param": "rz_b"},
    {"gate": "RZ", "wire": 8, "param": "rz_a"},
    
    # Layer 1: Sparse entanglement - hub-and-spoke pattern
    {"gate": "CZ", "wires": [0, 2]},
    {"gate": "CZ", "wires": [0, 3]},
    {"gate": "CZ", "wires": [1, 3]},
    {"gate": "CZ", "wires": [2, 4]},
    {"gate": "CZ", "wires": [3, 5]},
    {"gate": "CZ", "wires": [5, 7]},
    {"gate": "CZ", "wires": [6, 7]},
    
    # Layer 2: RY rotations with different shared parameters
    {"gate": "RY", "wire": 0, "param": "ry_c"},
    {"gate": "RY", "wire": 1, "param": "ry_d"},
    {"gate": "RY", "wire": 2, "param": "ry_c"},
    {"gate": "RY", "wire": 3, "param": "ry_d"},
    {"gate": "RY", "wire": 4, "param": "ry_c"},
    {"gate": "RY", "wire": 5, "param": "ry_d"},
    {"gate": "RY", "wire": 6, "param": "ry_c"},
    {"gate": "RY", "wire": 7, "param": "ry_d"},
    {"gate": "RY", "wire": 8, "param": "ry_c"},
    
    # Layer 2: RZ rotations with different shared parameters
    {"gate": "RZ", "wire": 0, "param": "rz_c"},
    {"gate": "RZ", "wire": 1, "param": "rz_d"},
    {"gate": "RZ", "wire": 2, "param": "rz_c"},
    {"gate": "RZ", "wire": 3, "param": "rz_d"},
    {"gate": "RZ", "wire": 4, "param": "rz_c"},
    {"gate": "RZ", "wire": 5, "param": "rz_d"},
    {"gate": "RZ", "wire": 6, "param": "rz_c"},
    {"gate": "RZ", "wire": 7, "param": "rz_d"},
    {"gate": "RZ", "wire": 8, "param": "rz_c"},
    
    # Layer 2: Complementary entanglement pattern
    {"gate": "CZ", "wires": [0, 7]},
    {"gate": "CZ", "wires": [0, 8]},
    {"gate": "CZ", "wires": [1, 8]},
    {"gate": "CZ", "wires": [2, 6]},
    {"gate": "CZ", "wires": [4, 8]},
    
    # Layer 3: Final RY rotations
    {"gate": "RY", "wire": 0, "param": "ry_e"},
    {"gate": "RY", "wire": 1, "param": "ry_f"},
    {"gate": "RY", "wire": 2, "param": "ry_e"},
    {"gate": "RY", "wire": 3, "param": "ry_f"},
    {"gate": "RY", "wire": 4, "param": "ry_e"},
    {"gate": "RY", "wire": 5, "param": "ry_f"},
    {"gate": "RY", "wire": 6, "param": "ry_e"},
    {"gate": "RY", "wire": 7, "param": "ry_f"},
    {"gate": "RY", "wire": 8, "param": "ry_e"},
    
    # Layer 3: Final RZ rotations
    {"gate": "RZ", "wire": 0, "param": "rz_e"},
    {"gate": "RZ", "wire": 1, "param": "rz_f"},
    {"gate": "RZ", "wire": 2, "param": "rz_e"},
    {"gate": "RZ", "wire": 3, "param": "rz_f"},
    {"gate": "RZ", "wire": 4, "param": "rz_e"},
    {"gate": "RZ", "wire": 5, "param": "rz_f"},
    {"gate": "RZ", "wire": 6, "param": "rz_e"},
    {"gate": "RZ", "wire": 7, "param": "rz_f"},
    {"gate": "RZ", "wire": 8, "param": "rz_e"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)
