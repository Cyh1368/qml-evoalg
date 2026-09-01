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
    # RY pre-rotation layer: single fully-shared parameter across all 8
    # qubits. Merging the previous two-group (ry_a/ry_b) split into one
    # shared parameter frees up parameter budget for a more expressive
    # entangling-ring structure below, while keeping total distinct
    # trainable parameters at 4 (matching the best-scoring prior seed).
    {"gate": "RY", "wire": 0, "param": "ry"},
    {"gate": "RY", "wire": 1, "param": "ry"},
    {"gate": "RY", "wire": 2, "param": "ry"},
    {"gate": "RY", "wire": 3, "param": "ry"},
    {"gate": "RY", "wire": 4, "param": "ry"},
    {"gate": "RY", "wire": 5, "param": "ry"},
    {"gate": "RY", "wire": 6, "param": "ry"},
    {"gate": "RY", "wire": 7, "param": "ry"},

    # RZ pre-entangling layer: fully shared single parameter.
    {"gate": "RZ", "wire": 0, "param": "rz"},
    {"gate": "RZ", "wire": 1, "param": "rz"},
    {"gate": "RZ", "wire": 2, "param": "rz"},
    {"gate": "RZ", "wire": 3, "param": "rz"},
    {"gate": "RZ", "wire": 4, "param": "rz"},
    {"gate": "RZ", "wire": 5, "param": "rz"},
    {"gate": "RZ", "wire": 6, "param": "rz"},
    {"gate": "RZ", "wire": 7, "param": "rz"},

    # Entangling structure split by topology rather than parity: all 8
    # nearest-neighbor ring bonds share "zz_nn" (local adjacency coupling),
    # while the 4 long-range diagonal cross-links share "zz_lr" (global
    # coupling). This differentiates local vs. long-range interaction
    # strength, giving the optimizer targeted control that helps separate
    # the hardest validation groups, at no extra parameter cost.
    {"gate": "ZZ", "wires": [0, 1], "param": "zz_nn"},
    {"gate": "ZZ", "wires": [1, 2], "param": "zz_nn"},
    {"gate": "ZZ", "wires": [2, 3], "param": "zz_nn"},
    {"gate": "ZZ", "wires": [3, 4], "param": "zz_nn"},
    {"gate": "ZZ", "wires": [4, 5], "param": "zz_nn"},
    {"gate": "ZZ", "wires": [5, 6], "param": "zz_nn"},
    {"gate": "ZZ", "wires": [6, 7], "param": "zz_nn"},
    {"gate": "ZZ", "wires": [7, 0], "param": "zz_nn"},

    {"gate": "ZZ", "wires": [0, 4], "param": "zz_lr"},
    {"gate": "ZZ", "wires": [1, 5], "param": "zz_lr"},
    {"gate": "ZZ", "wires": [2, 6], "param": "zz_lr"},
    {"gate": "ZZ", "wires": [3, 7], "param": "zz_lr"},

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