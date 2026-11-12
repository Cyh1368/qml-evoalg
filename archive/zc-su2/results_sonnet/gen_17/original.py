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
    # Pre-entanglement rotations: 3 groups (3,3,2 qubits), each group driven
    # by a single shared parameter (RY on all wires of the group).
    {"gate": "RY", "wire": 0, "param": "p_g0"},
    {"gate": "RY", "wire": 1, "param": "p_g0"},
    {"gate": "RY", "wire": 2, "param": "p_g0"},
    {"gate": "RY", "wire": 3, "param": "p_g1"},
    {"gate": "RY", "wire": 4, "param": "p_g1"},
    {"gate": "RY", "wire": 5, "param": "p_g1"},
    {"gate": "RY", "wire": 6, "param": "p_g2"},
    {"gate": "RY", "wire": 7, "param": "p_g2"},

    # Nearest-neighbor entangling chain (fixed, no parameters).
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [6, 7]},

    # Post-entanglement rotations: reuse the SAME parameters as the
    # corresponding pre-entanglement RY gates, but on a different axis (RZ),
    # keeping the parameter count at 3 unique values per repetition.
    {"gate": "RZ", "wire": 0, "param": "p_g0"},
    {"gate": "RZ", "wire": 1, "param": "p_g0"},
    {"gate": "RZ", "wire": 2, "param": "p_g0"},
    {"gate": "RZ", "wire": 3, "param": "p_g1"},
    {"gate": "RZ", "wire": 4, "param": "p_g1"},
    {"gate": "RZ", "wire": 5, "param": "p_g1"},
    {"gate": "RZ", "wire": 6, "param": "p_g2"},
    {"gate": "RZ", "wire": 7, "param": "p_g2"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)