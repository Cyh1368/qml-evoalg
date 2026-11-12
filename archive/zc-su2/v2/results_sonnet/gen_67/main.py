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
    # RY pre-rotation layer: single shared parameter across ALL 8 qubits.
    # Minimizes distinct parameter count while giving every qubit an
    # independent-value rotation input driven by the data encoding.
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_a"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 3, "param": "ry_a"},
    {"gate": "RY", "wire": 4, "param": "ry_a"},
    {"gate": "RY", "wire": 5, "param": "ry_a"},
    {"gate": "RY", "wire": 6, "param": "ry_a"},
    {"gate": "RY", "wire": 7, "param": "ry_a"},

    # Fixed CNOT ladder (forward) - zero-parameter entangling mixing across
    # all 8 qubits before the parametrized entangling shells.
    {"gate": "CNOT", "wires": [0, 1]},
    {"gate": "CNOT", "wires": [1, 2]},
    {"gate": "CNOT", "wires": [2, 3]},
    {"gate": "CNOT", "wires": [3, 4]},
    {"gate": "CNOT", "wires": [4, 5]},
    {"gate": "CNOT", "wires": [5, 6]},
    {"gate": "CNOT", "wires": [6, 7]},

    # Global phase layer BEFORE the entangling shells. Reuses the SAME
    # parameter name ("theta") that also drives every ZZ/XX/YY coupler
    # below, collapsing everything into a single shared parameter.
    {"gate": "RZ", "wire": 0, "param": "theta"},
    {"gate": "RZ", "wire": 1, "param": "theta"},
    {"gate": "RZ", "wire": 2, "param": "theta"},
    {"gate": "RZ", "wire": 3, "param": "theta"},
    {"gate": "RZ", "wire": 4, "param": "theta"},
    {"gate": "RZ", "wire": 5, "param": "theta"},
    {"gate": "RZ", "wire": 6, "param": "theta"},
    {"gate": "RZ", "wire": 7, "param": "theta"},

    # Parametrized entangling ring: nearest-neighbor ring (wraps 7-0), all
    # sharing "theta".
    {"gate": "ZZ", "wires": [0, 1], "param": "theta"},
    {"gate": "ZZ", "wires": [1, 2], "param": "theta"},
    {"gate": "ZZ", "wires": [2, 3], "param": "theta"},
    {"gate": "ZZ", "wires": [3, 4], "param": "theta"},
    {"gate": "ZZ", "wires": [4, 5], "param": "theta"},
    {"gate": "ZZ", "wires": [5, 6], "param": "theta"},
    {"gate": "ZZ", "wires": [6, 7], "param": "theta"},
    {"gate": "ZZ", "wires": [7, 0], "param": "theta"},

    # Long-range "opposite qubit" couplings, still sharing "theta", giving
    # a hypercube-like connectivity shell - helps separate the hardest
    # validation group without adding any new trainable parameter.
    {"gate": "ZZ", "wires": [0, 4], "param": "theta"},
    {"gate": "ZZ", "wires": [1, 5], "param": "theta"},
    {"gate": "ZZ", "wires": [2, 6], "param": "theta"},
    {"gate": "ZZ", "wires": [3, 7], "param": "theta"},

    # Additional "skip-2" shell, still sharing "theta", enriching
    # connectivity further.
    {"gate": "ZZ", "wires": [0, 2], "param": "theta"},
    {"gate": "ZZ", "wires": [1, 3], "param": "theta"},
    {"gate": "ZZ", "wires": [2, 4], "param": "theta"},
    {"gate": "ZZ", "wires": [3, 5], "param": "theta"},
    {"gate": "ZZ", "wires": [4, 6], "param": "theta"},
    {"gate": "ZZ", "wires": [5, 7], "param": "theta"},
    {"gate": "ZZ", "wires": [6, 0], "param": "theta"},
    {"gate": "ZZ", "wires": [7, 1], "param": "theta"},

    # Orthogonal XX nearest-neighbor ring, reusing the SAME shared
    # parameter "theta". Interleaving an X-basis coupling with the Z-basis
    # couplings above enriches the reachable operator space without
    # adding any new trainable name.
    {"gate": "XX", "wires": [0, 1], "param": "theta"},
    {"gate": "XX", "wires": [1, 2], "param": "theta"},
    {"gate": "XX", "wires": [2, 3], "param": "theta"},
    {"gate": "XX", "wires": [3, 4], "param": "theta"},
    {"gate": "XX", "wires": [4, 5], "param": "theta"},
    {"gate": "XX", "wires": [5, 6], "param": "theta"},
    {"gate": "XX", "wires": [6, 7], "param": "theta"},
    {"gate": "XX", "wires": [7, 0], "param": "theta"},

    # NEW: orthogonal YY nearest-neighbor ring, still reusing "theta".
    # Together with the ZZ and XX rings above this completes a fuller
    # Heisenberg-like (XX+YY+ZZ) coupling on every ring edge, maximizing
    # the entangling power per edge at zero extra parameter cost, which
    # should help push apart the hardest-to-separate validation group.
    {"gate": "YY", "wires": [0, 1], "param": "theta"},
    {"gate": "YY", "wires": [1, 2], "param": "theta"},
    {"gate": "YY", "wires": [2, 3], "param": "theta"},
    {"gate": "YY", "wires": [3, 4], "param": "theta"},
    {"gate": "YY", "wires": [4, 5], "param": "theta"},
    {"gate": "YY", "wires": [5, 6], "param": "theta"},
    {"gate": "YY", "wires": [6, 7], "param": "theta"},
    {"gate": "YY", "wires": [7, 0], "param": "theta"},

    # Fixed CNOT ladder (backward) - additional entangling mixing, still no
    # extra trainable parameters.
    {"gate": "CNOT", "wires": [7, 6]},
    {"gate": "CNOT", "wires": [6, 5]},
    {"gate": "CNOT", "wires": [5, 4]},
    {"gate": "CNOT", "wires": [4, 3]},
    {"gate": "CNOT", "wires": [3, 2]},
    {"gate": "CNOT", "wires": [2, 1]},
    {"gate": "CNOT", "wires": [1, 0]},

    # Global phase layer AFTER the entangling shells, reusing "theta" again
    # - reinforces the encoding without adding a new trainable name.
    {"gate": "RZ", "wire": 0, "param": "theta"},
    {"gate": "RZ", "wire": 1, "param": "theta"},
    {"gate": "RZ", "wire": 2, "param": "theta"},
    {"gate": "RZ", "wire": 3, "param": "theta"},
    {"gate": "RZ", "wire": 4, "param": "theta"},
    {"gate": "RZ", "wire": 5, "param": "theta"},
    {"gate": "RZ", "wire": 6, "param": "theta"},
    {"gate": "RZ", "wire": 7, "param": "theta"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)