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
    # A globally tied local mixer regularizes the small-data model and reserves
    # capacity for trainable medium-range phase correlations.
    {"gate": "RY", "wire": 0, "param": "global_mix"},
    {"gate": "RY", "wire": 1, "param": "global_mix"},
    {"gate": "RY", "wire": 2, "param": "global_mix"},
    {"gate": "RY", "wire": 3, "param": "global_mix"},
    {"gate": "RY", "wire": 4, "param": "global_mix"},
    {"gate": "RY", "wire": 5, "param": "global_mix"},
    {"gate": "RY", "wire": 6, "param": "global_mix"},
    {"gate": "RY", "wire": 7, "param": "global_mix"},

    # Distance-1 butterfly layer.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [6, 7]},

    # Tunable distance-2 phase correlations share one strongly regularized
    # angle, targeting the medium-range structure relevant to hard samples.
    {"gate": "CRZ", "wires": [0, 2], "param": "global_phase"},
    {"gate": "CRZ", "wires": [1, 3], "param": "global_phase"},
    {"gate": "CRZ", "wires": [4, 6], "param": "global_phase"},
    {"gate": "CRZ", "wires": [5, 7], "param": "global_phase"},

    # Distance-4 butterfly layer connects the two halves.
    {"gate": "CZ", "wires": [0, 4]},
    {"gate": "CZ", "wires": [1, 5]},
    {"gate": "CZ", "wires": [2, 6]},
    {"gate": "CZ", "wires": [3, 7]},

    # Extra parameter-free links capture endpoint and central-boundary
    # correlations not directly represented by the butterfly matching.
    {"gate": "CZ", "wires": [0, 7]},
    {"gate": "CZ", "wires": [3, 4]},

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