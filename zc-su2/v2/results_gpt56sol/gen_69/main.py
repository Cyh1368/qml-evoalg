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
    # A globally shared input mixer imposes a strong symmetry prior.
    {"gate": "RY", "wire": 0, "param": "global_flow"},
    {"gate": "RY", "wire": 1, "param": "global_flow"},
    {"gate": "RY", "wire": 2, "param": "global_flow"},
    {"gate": "RY", "wire": 3, "param": "global_flow"},
    {"gate": "RY", "wire": 4, "param": "global_flow"},
    {"gate": "RY", "wire": 5, "param": "global_flow"},
    {"gate": "RY", "wire": 6, "param": "global_flow"},
    {"gate": "RY", "wire": 7, "param": "global_flow"},

    # Trainable distance-4 Ising bridges concentrate adaptive capacity on the
    # nonlocal links while introducing no additional distinct parameter.
    {"gate": "ZZ", "wires": [0, 4], "param": "global_flow"},
    {"gate": "ZZ", "wires": [1, 5], "param": "global_flow"},
    {"gate": "ZZ", "wires": [2, 6], "param": "global_flow"},
    {"gate": "ZZ", "wires": [3, 7], "param": "global_flow"},

    # Fixed distance-2 correlations distribute information within each half.
    {"gate": "CZ", "wires": [0, 2]},
    {"gate": "CZ", "wires": [1, 3]},
    {"gate": "CZ", "wires": [4, 6]},
    {"gate": "CZ", "wires": [5, 7]},

    # Local correlations complete the multiscale interaction graph.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [6, 7]},

    # A tied noncommuting output mixer converts accumulated phase and Ising
    # correlations into observable population differences.
    {"gate": "RX", "wire": 0, "param": "global_flow"},
    {"gate": "RX", "wire": 1, "param": "global_flow"},
    {"gate": "RX", "wire": 2, "param": "global_flow"},
    {"gate": "RX", "wire": 3, "param": "global_flow"},
    {"gate": "RX", "wire": 4, "param": "global_flow"},
    {"gate": "RX", "wire": 5, "param": "global_flow"},
    {"gate": "RX", "wire": 6, "param": "global_flow"},
    {"gate": "RX", "wire": 7, "param": "global_flow"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)