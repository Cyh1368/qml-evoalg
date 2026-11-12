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
    # Alternating axes provide heterogeneous feature mixing with one shared
    # trainable angle.
    {"gate": "RY", "wire": 0, "param": "shared_mix"},
    {"gate": "RX", "wire": 1, "param": "shared_mix"},
    {"gate": "RY", "wire": 2, "param": "shared_mix"},
    {"gate": "RX", "wire": 3, "param": "shared_mix"},
    {"gate": "RY", "wire": 4, "param": "shared_mix"},
    {"gate": "RX", "wire": 5, "param": "shared_mix"},
    {"gate": "RY", "wire": 6, "param": "shared_mix"},
    {"gate": "RX", "wire": 7, "param": "shared_mix"},

    # First form stable local correlations on disjoint pairs.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [6, 7]},

    # Complementary axes introduce noncommuting transformations after the
    # first entangling stage without increasing the parameter count.
    {"gate": "RX", "wire": 0, "param": "shared_mix"},
    {"gate": "RY", "wire": 1, "param": "shared_mix"},
    {"gate": "RX", "wire": 2, "param": "shared_mix"},
    {"gate": "RY", "wire": 3, "param": "shared_mix"},
    {"gate": "RX", "wire": 4, "param": "shared_mix"},
    {"gate": "RY", "wire": 5, "param": "shared_mix"},
    {"gate": "RX", "wire": 6, "param": "shared_mix"},
    {"gate": "RY", "wire": 7, "param": "shared_mix"},

    # Couple opposite halves to establish diameter-spanning correlations.
    {"gate": "CZ", "wires": [0, 4]},
    {"gate": "CZ", "wires": [1, 5]},
    {"gate": "CZ", "wires": [2, 6]},
    {"gate": "CZ", "wires": [3, 7]},

    # Finish with staggered boundaries that distribute global correlations
    # through the full ring.
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [7, 0]},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)