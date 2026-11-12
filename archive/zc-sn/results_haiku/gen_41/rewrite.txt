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
    # Shared initial RY rotations - pairs of qubits share parameters
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_b"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 3, "param": "ry_b"},
    {"gate": "RY", "wire": 4, "param": "ry_a"},
    {"gate": "RY", "wire": 5, "param": "ry_b"},
    {"gate": "RY", "wire": 6, "param": "ry_a"},
    {"gate": "RY", "wire": 7, "param": "ry_b"},

    # Shared pre-entanglement RZ rotations
    {"gate": "RZ", "wire": 0, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre_b"},

    # Forward linear chain CZ gates for low-depth entanglement
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [6, 7]},

    # Mid-circuit selective RZ rotations on even/odd qubits
    # Shared across all even qubits and all odd qubits respectively
    {"gate": "RZ", "wire": 0, "param": "rz_mid_even"},
    {"gate": "RZ", "wire": 2, "param": "rz_mid_even"},
    {"gate": "RZ", "wire": 4, "param": "rz_mid_even"},
    {"gate": "RZ", "wire": 6, "param": "rz_mid_even"},
    {"gate": "RZ", "wire": 1, "param": "rz_mid_odd"},
    {"gate": "RZ", "wire": 3, "param": "rz_mid_odd"},
    {"gate": "RZ", "wire": 5, "param": "rz_mid_odd"},
    {"gate": "RZ", "wire": 7, "param": "rz_mid_odd"},

    # Reverse chain with alternating CRZ and CRX gates for spectral diversity
    # Pattern cycles between two parameter sets with gate-type variation
    {"gate": "CRZ", "wires": [7, 6], "param": "crz_rev_a"},
    {"gate": "CRX", "wires": [6, 5], "param": "crx_rev_b"},
    {"gate": "CRZ", "wires": [5, 4], "param": "crz_rev_a"},
    {"gate": "CRX", "wires": [4, 3], "param": "crx_rev_b"},
    {"gate": "CRZ", "wires": [3, 2], "param": "crz_rev_a"},
    {"gate": "CRX", "wires": [2, 1], "param": "crx_rev_b"},
    {"gate": "CRZ", "wires": [1, 0], "param": "crz_rev_a"},

    # Shared post-entanglement RZ rotations
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