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
    # RY pre-rotation layer: single fully-shared parameter across all qubits
    # (merged from the previous two-group ry_a/ry_b split) to minimize
    # distinct trainable parameter count.
    {"gate": "RY", "wire": 0, "param": "ry"},
    {"gate": "RY", "wire": 1, "param": "ry"},
    {"gate": "RY", "wire": 2, "param": "ry"},
    {"gate": "RY", "wire": 3, "param": "ry"},
    {"gate": "RY", "wire": 4, "param": "ry"},
    {"gate": "RY", "wire": 5, "param": "ry"},
    {"gate": "RY", "wire": 6, "param": "ry"},
    {"gate": "RY", "wire": 7, "param": "ry"},

    # RZ pre-entangling layer: single fully-shared parameter.
    {"gate": "RZ", "wire": 0, "param": "rz"},
    {"gate": "RZ", "wire": 1, "param": "rz"},
    {"gate": "RZ", "wire": 2, "param": "rz"},
    {"gate": "RZ", "wire": 3, "param": "rz"},
    {"gate": "RZ", "wire": 4, "param": "rz"},
    {"gate": "RZ", "wire": 5, "param": "rz"},
    {"gate": "RZ", "wire": 6, "param": "rz"},
    {"gate": "RZ", "wire": 7, "param": "rz"},

    # Fully shared ZZ entangling ring, closed into a full cycle.
    {"gate": "ZZ", "wires": [0, 1], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [1, 2], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [2, 3], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [3, 4], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [4, 5], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [5, 6], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [6, 7], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [7, 0], "param": "zz_ring"},

    # RZ post-entangling layer: reuse the same fully-shared "rz" parameter.
    {"gate": "RZ", "wire": 0, "param": "rz"},
    {"gate": "RZ", "wire": 1, "param": "rz"},
    {"gate": "RZ", "wire": 2, "param": "rz"},
    {"gate": "RZ", "wire": 3, "param": "rz"},
    {"gate": "RZ", "wire": 4, "param": "rz"},
    {"gate": "RZ", "wire": 5, "param": "rz"},
    {"gate": "RZ", "wire": 6, "param": "rz"},
    {"gate": "RZ", "wire": 7, "param": "rz"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)