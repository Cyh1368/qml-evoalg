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

    # Forward linear chain with parametrized CRZ gates (alternating parameters)
    {"gate": "CRZ", "wires": [0, 1], "param": "crz_fwd_a"},
    {"gate": "CRZ", "wires": [1, 2], "param": "crz_fwd_b"},
    {"gate": "CRZ", "wires": [2, 3], "param": "crz_fwd_a"},
    {"gate": "CRZ", "wires": [3, 4], "param": "crz_fwd_b"},
    {"gate": "CRZ", "wires": [4, 5], "param": "crz_fwd_a"},
    {"gate": "CRZ", "wires": [5, 6], "param": "crz_fwd_b"},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_fwd_a"},

    # Mid-circuit selective RZ rotations on even/odd qubits
    {"gate": "RZ", "wire": 0, "param": "rz_mid_a"},
    {"gate": "RZ", "wire": 2, "param": "rz_mid_a"},
    {"gate": "RZ", "wire": 4, "param": "rz_mid_a"},
    {"gate": "RZ", "wire": 6, "param": "rz_mid_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_mid_b"},
    {"gate": "RZ", "wire": 3, "param": "rz_mid_b"},
    {"gate": "RZ", "wire": 5, "param": "rz_mid_b"},
    {"gate": "RZ", "wire": 7, "param": "rz_mid_b"},

    # Reverse chain with parametrized CRZ gates (proven pattern from prior)
    {"gate": "CRZ", "wires": [7, 6], "param": "crz_rev_a"},
    {"gate": "CRZ", "wires": [6, 5], "param": "crz_rev_b"},
    {"gate": "CRZ", "wires": [5, 4], "param": "crz_rev_a"},
    {"gate": "CRZ", "wires": [4, 3], "param": "crz_rev_b"},
    {"gate": "CRZ", "wires": [3, 2], "param": "crz_rev_a"},
    {"gate": "CRZ", "wires": [2, 1], "param": "crz_rev_b"},
    {"gate": "CRZ", "wires": [1, 0], "param": "crz_rev_a"},

    # Fused post-entanglement RZ rotations: reuse rz_pre_a and rz_pre_b
    # This merges pre and post phase logic, reducing unique parameter count
    # while maintaining phase flexibility through dual-parameter modulation
    {"gate": "RZ", "wire": 0, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre_b"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre_a"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre_b"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)