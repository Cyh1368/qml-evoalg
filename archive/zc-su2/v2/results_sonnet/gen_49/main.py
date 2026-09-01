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
    # Merging the previous two-group split (ry_a / ry_b) into one name cuts
    # the distinct-parameter count from 4 to 3 while the entangling
    # structure below is kept (and slightly enriched) to preserve
    # separability of the hardest validation group.
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_a"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 3, "param": "ry_a"},
    {"gate": "RY", "wire": 4, "param": "ry_a"},
    {"gate": "RY", "wire": 5, "param": "ry_a"},
    {"gate": "RY", "wire": 6, "param": "ry_a"},
    {"gate": "RY", "wire": 7, "param": "ry_a"},

    # Fixed CNOT ladder (forward) - zero-parameter entangling mixing across
    # all 8 qubits before the parametrized entangling ring.
    {"gate": "CNOT", "wires": [0, 1]},
    {"gate": "CNOT", "wires": [1, 2]},
    {"gate": "CNOT", "wires": [2, 3]},
    {"gate": "CNOT", "wires": [3, 4]},
    {"gate": "CNOT", "wires": [4, 5]},
    {"gate": "CNOT", "wires": [5, 6]},
    {"gate": "CNOT", "wires": [6, 7]},

    # Single shared global phase parameter applied to all qubits before the
    # entangling ring.
    {"gate": "RZ", "wire": 0, "param": "rz_p"},
    {"gate": "RZ", "wire": 1, "param": "rz_p"},
    {"gate": "RZ", "wire": 2, "param": "rz_p"},
    {"gate": "RZ", "wire": 3, "param": "rz_p"},
    {"gate": "RZ", "wire": 4, "param": "rz_p"},
    {"gate": "RZ", "wire": 5, "param": "rz_p"},
    {"gate": "RZ", "wire": 6, "param": "rz_p"},
    {"gate": "RZ", "wire": 7, "param": "rz_p"},

    # Parametrized entangling ring: one shared coupling strength across the
    # full nearest-neighbor ring topology (wraps around 7-0).
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

    # Second pass of the full ZZ entangling block (ring + opposite-qubit +
    # skip-2 shell), again sharing "zz_ring". This deepens the entangling
    # structure without introducing any new trainable parameter, trading a
    # mild depth increase for improved separation of the hardest group.
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

    # Fixed CNOT ladder (backward) - additional entangling mixing, still no
    # extra trainable parameters.
    {"gate": "CNOT", "wires": [7, 6]},
    {"gate": "CNOT", "wires": [6, 5]},
    {"gate": "CNOT", "wires": [5, 4]},
    {"gate": "CNOT", "wires": [4, 3]},
    {"gate": "CNOT", "wires": [3, 2]},
    {"gate": "CNOT", "wires": [2, 1]},
    {"gate": "CNOT", "wires": [1, 0]},

    # Reuse the same global phase parameter after the entangling ring,
    # reinforcing the encoding without adding a new trainable name.
    {"gate": "RZ", "wire": 0, "param": "rz_p"},
    {"gate": "RZ", "wire": 1, "param": "rz_p"},
    {"gate": "RZ", "wire": 2, "param": "rz_p"},
    {"gate": "RZ", "wire": 3, "param": "rz_p"},
    {"gate": "RZ", "wire": 4, "param": "rz_p"},
    {"gate": "RZ", "wire": 5, "param": "rz_p"},
    {"gate": "RZ", "wire": 6, "param": "rz_p"},
    {"gate": "RZ", "wire": 7, "param": "rz_p"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)