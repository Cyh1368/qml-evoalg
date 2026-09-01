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
    # RY pre-rotation layer: two symmetric groups sharing one parameter each.
    # Kept split (rather than fully merged) since the two halves of the
    # register likely correspond to different portions of the data encoding.
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_a"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 3, "param": "ry_a"},
    {"gate": "RY", "wire": 4, "param": "ry_b"},
    {"gate": "RY", "wire": 5, "param": "ry_b"},
    {"gate": "RY", "wire": 6, "param": "ry_b"},
    {"gate": "RY", "wire": 7, "param": "ry_b"},

    # RZ pre-entangling layer: fully shared single parameter (merged from
    # the two-group rz_a/rz_b split used in the higher-parameter seeds,
    # trading a little group-specific expressiveness for one fewer
    # distinct trainable parameter).
    {"gate": "RZ", "wire": 0, "param": "rz"},
    {"gate": "RZ", "wire": 1, "param": "rz"},
    {"gate": "RZ", "wire": 2, "param": "rz"},
    {"gate": "RZ", "wire": 3, "param": "rz"},
    {"gate": "RZ", "wire": 4, "param": "rz"},
    {"gate": "RZ", "wire": 5, "param": "rz"},
    {"gate": "RZ", "wire": 6, "param": "rz"},
    {"gate": "RZ", "wire": 7, "param": "rz"},

    # Fully shared entangling ring, closed into a full cycle (adds the
    # wrap-around edge 7-0) for stronger connectivity across the whole
    # register at zero extra parameter cost.
    {"gate": "ZZ", "wires": [0, 1], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [1, 2], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [2, 3], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [3, 4], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [4, 5], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [5, 6], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [6, 7], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [7, 0], "param": "zz_ring"},

    # Long-range "opposite qubit" couplings reusing the SAME shared
    # parameter, giving a hypercube-like connectivity without adding a new
    # trainable parameter name.
    {"gate": "ZZ", "wires": [0, 4], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [1, 5], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [2, 6], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [3, 7], "param": "zz_ring"},

    # Additional "skip-2" shell, still sharing zz_ring, enriching
    # connectivity further to help separate the hardest validation group
    # without introducing any new trainable parameter.
    {"gate": "ZZ", "wires": [0, 2], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [1, 3], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [2, 4], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [3, 5], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [4, 6], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [5, 7], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [6, 0], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [7, 1], "param": "zz_ring"},

    # Second shell repetition: replicate the ring, opposite-qubit, and
    # skip-2 ZZ couplings again under the SAME "zz_ring" parameter. This
    # deepens the entangling structure (a second hypercube-style shell)
    # without adding any new trainable parameter, increasing expressivity
    # per parameter for better worst-group separation.
    {"gate": "ZZ", "wires": [0, 1], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [1, 2], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [2, 3], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [3, 4], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [4, 5], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [5, 6], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [6, 7], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [7, 0], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [0, 4], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [1, 5], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [2, 6], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [3, 7], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [0, 2], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [1, 3], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [2, 4], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [3, 5], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [4, 6], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [5, 7], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [6, 0], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [7, 1], "param": "zz_ring"},

    # Orthogonal YY shell on the same skip-2 connectivity, reusing the SAME
    # shared "zz_ring" parameter to densify the reachable entangled state
    # space without adding any new trainable parameter name.
    {"gate": "YY", "wires": [0, 2], "param": "zz_ring"},
    {"gate": "YY", "wires": [1, 3], "param": "zz_ring"},
    {"gate": "YY", "wires": [2, 4], "param": "zz_ring"},
    {"gate": "YY", "wires": [3, 5], "param": "zz_ring"},
    {"gate": "YY", "wires": [4, 6], "param": "zz_ring"},
    {"gate": "YY", "wires": [5, 7], "param": "zz_ring"},
    {"gate": "YY", "wires": [6, 0], "param": "zz_ring"},
    {"gate": "YY", "wires": [7, 1], "param": "zz_ring"},

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