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
    # Two tied local mixers preserve limited positional flexibility while
    # strongly regularizing the model.
    {"gate": "RY", "wire": 0, "param": "mix_even"},
    {"gate": "RY", "wire": 1, "param": "mix_odd"},
    {"gate": "RY", "wire": 2, "param": "mix_even"},
    {"gate": "RY", "wire": 3, "param": "mix_odd"},
    {"gate": "RY", "wire": 4, "param": "mix_even"},
    {"gate": "RY", "wire": 5, "param": "mix_odd"},
    {"gate": "RY", "wire": 6, "param": "mix_even"},
    {"gate": "RY", "wire": 7, "param": "mix_odd"},

    # Distance-1 butterfly layer.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [6, 7]},

    # Distance-2 butterfly layer.
    {"gate": "CZ", "wires": [0, 2]},
    {"gate": "CZ", "wires": [1, 3]},
    {"gate": "CZ", "wires": [4, 6]},
    {"gate": "CZ", "wires": [5, 7]},

    # Distance-4 butterfly layer connects the two halves.
    {"gate": "CZ", "wires": [0, 4]},
    {"gate": "CZ", "wires": [1, 5]},
    {"gate": "CZ", "wires": [2, 6]},
    {"gate": "CZ", "wires": [3, 7]},

    # A shared noncommuting mixer converts global phase correlations into
    # observable population differences in subsequent repetitions/readout.
    {"gate": "RX", "wire": 0, "param": "global_tilt"},
    {"gate": "RX", "wire": 1, "param": "global_tilt"},
    {"gate": "RX", "wire": 2, "param": "global_tilt"},
    {"gate": "RX", "wire": 3, "param": "global_tilt"},
    {"gate": "RX", "wire": 4, "param": "global_tilt"},
    {"gate": "RX", "wire": 5, "param": "global_tilt"},
    {"gate": "RX", "wire": 6, "param": "global_tilt"},
    {"gate": "RX", "wire": 7, "param": "global_tilt"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)
