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
    # Pre-entanglement rotations: ALL qubits share a SINGLE trainable
    # parameter "theta" for maximal parameter economy.
    {"gate": "RY", "wire": 0, "param": "theta"},
    {"gate": "RY", "wire": 1, "param": "theta"},
    {"gate": "RY", "wire": 2, "param": "theta"},
    {"gate": "RY", "wire": 3, "param": "theta"},
    {"gate": "RY", "wire": 4, "param": "theta"},
    {"gate": "RY", "wire": 5, "param": "theta"},
    {"gate": "RY", "wire": 6, "param": "theta"},
    {"gate": "RY", "wire": 7, "param": "theta"},

    # Nearest-neighbor entangling chain (fixed, no parameters).
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [6, 7]},
    {"gate": "CZ", "wires": [7, 0]},

    # Parametrized entangling layer on disjoint pairs, sharing a single
    # extra trainable parameter "phi" to tune interaction strength while
    # adding only one parameter to the whole block.
    {"gate": "CRZ", "wires": [0, 1], "param": "phi"},
    {"gate": "CRZ", "wires": [2, 3], "param": "phi"},
    {"gate": "CRZ", "wires": [4, 5], "param": "phi"},
    {"gate": "CRZ", "wires": [6, 7], "param": "phi"},

    # Post-entanglement rotations: reuse the SAME "theta" parameter,
    # different axis (RZ), keeping total unique parameters minimal.
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