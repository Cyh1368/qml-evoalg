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
    # Layer 1: alternating-wire RY encoding (even wires vs odd wires) -
    # this split, taken from the best-performing parent, gives the model
    # more expressivity than a single fully-shared rotation while still
    # only costing 2 distinct parameters.
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 4, "param": "ry_a"},
    {"gate": "RY", "wire": 6, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_b"},
    {"gate": "RY", "wire": 3, "param": "ry_b"},
    {"gate": "RY", "wire": 5, "param": "ry_b"},
    {"gate": "RY", "wire": 7, "param": "ry_b"},

    # Forward nearest-neighbor entangling chain (fixed, no parameters).
    {"gate": "CNOT", "wires": [0, 1]},
    {"gate": "CNOT", "wires": [1, 2]},
    {"gate": "CNOT", "wires": [2, 3]},
    {"gate": "CNOT", "wires": [3, 4]},
    {"gate": "CNOT", "wires": [4, 5]},
    {"gate": "CNOT", "wires": [5, 6]},
    {"gate": "CNOT", "wires": [6, 7]},

    # Layer 2: a single shared RZ across all wires (collapsed from the
    # two separate rz_a/rz_b parameters used in the parent, saving one
    # trainable parameter while keeping the same rotation axis coverage).
    {"gate": "RZ", "wire": 0, "param": "rz"},
    {"gate": "RZ", "wire": 1, "param": "rz"},
    {"gate": "RZ", "wire": 2, "param": "rz"},
    {"gate": "RZ", "wire": 3, "param": "rz"},
    {"gate": "RZ", "wire": 4, "param": "rz"},
    {"gate": "RZ", "wire": 5, "param": "rz"},
    {"gate": "RZ", "wire": 6, "param": "rz"},
    {"gate": "RZ", "wire": 7, "param": "rz"},

    # Backward nearest-neighbor entangling chain to further mix information
    # (fixed, no parameters), mirroring the parent's bidirectional design.
    {"gate": "CNOT", "wires": [7, 6]},
    {"gate": "CNOT", "wires": [6, 5]},
    {"gate": "CNOT", "wires": [5, 4]},
    {"gate": "CNOT", "wires": [4, 3]},
    {"gate": "CNOT", "wires": [3, 2]},
    {"gate": "CNOT", "wires": [2, 1]},
    {"gate": "CNOT", "wires": [1, 0]},

    # Cheap disjoint-pair parametrized entangler with a single shared
    # parameter - this was central to the best-performing parent's margin.
    {"gate": "CRZ", "wires": [0, 1], "param": "ent"},
    {"gate": "CRZ", "wires": [2, 3], "param": "ent"},
    {"gate": "CRZ", "wires": [4, 5], "param": "ent"},
    {"gate": "CRZ", "wires": [6, 7], "param": "ent"},

    # Final global shared rotation to read out the entangled state.
    {"gate": "RY", "wire": 0, "param": "ry_c"},
    {"gate": "RY", "wire": 1, "param": "ry_c"},
    {"gate": "RY", "wire": 2, "param": "ry_c"},
    {"gate": "RY", "wire": 3, "param": "ry_c"},
    {"gate": "RY", "wire": 4, "param": "ry_c"},
    {"gate": "RY", "wire": 5, "param": "ry_c"},
    {"gate": "RY", "wire": 6, "param": "ry_c"},
    {"gate": "RY", "wire": 7, "param": "ry_c"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)