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
    # A globally tied mixer provides a stronger small-data symmetry prior.
    {"gate": "RY", "wire": 0, "param": "global_mix"},
    {"gate": "RY", "wire": 1, "param": "global_mix"},
    {"gate": "RY", "wire": 2, "param": "global_mix"},
    {"gate": "RY", "wire": 3, "param": "global_mix"},
    {"gate": "RY", "wire": 4, "param": "global_mix"},
    {"gate": "RY", "wire": 5, "param": "global_mix"},
    {"gate": "RY", "wire": 6, "param": "global_mix"},
    {"gate": "RY", "wire": 7, "param": "global_mix"},

    # Distance-1 correlations.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [6, 7]},

    # Trainable medium-range phase correlations with one shared angle.
    {"gate": "CRZ", "wires": [0, 2], "param": "mid_crz"},
    {"gate": "CRZ", "wires": [1, 3], "param": "mid_crz"},
    {"gate": "CRZ", "wires": [4, 6], "param": "mid_crz"},
    {"gate": "CRZ", "wires": [5, 7], "param": "mid_crz"},

    # Distance-4 correlations connect both halves.
    {"gate": "CZ", "wires": [0, 4]},
    {"gate": "CZ", "wires": [1, 5]},
    {"gate": "CZ", "wires": [2, 6]},
    {"gate": "CZ", "wires": [3, 7]},

    # Noncommuting global basis mixer.
    {"gate": "RX", "wire": 0, "param": "global_tilt"},
    {"gate": "RX", "wire": 1, "param": "global_tilt"},
    {"gate": "RX", "wire": 2, "param": "global_tilt"},
    {"gate": "RX", "wire": 3, "param": "global_tilt"},
    {"gate": "RX", "wire": 4, "param": "global_tilt"},
    {"gate": "RX", "wire": 5, "param": "global_tilt"},
    {"gate": "RX", "wire": 6, "param": "global_tilt"},
    {"gate": "RX", "wire": 7, "param": "global_tilt"},

    # Second recurrent pass reuses the same economical parameter set.
    {"gate": "RY", "wire": 0, "param": "global_mix"},
    {"gate": "RY", "wire": 1, "param": "global_mix"},
    {"gate": "RY", "wire": 2, "param": "global_mix"},
    {"gate": "RY", "wire": 3, "param": "global_mix"},
    {"gate": "RY", "wire": 4, "param": "global_mix"},
    {"gate": "RY", "wire": 5, "param": "global_mix"},
    {"gate": "RY", "wire": 6, "param": "global_mix"},
    {"gate": "RY", "wire": 7, "param": "global_mix"},

    # Repeat the complete butterfly after basis conversion.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [6, 7]},

    {"gate": "CRZ", "wires": [0, 2], "param": "mid_crz"},
    {"gate": "CRZ", "wires": [1, 3], "param": "mid_crz"},
    {"gate": "CRZ", "wires": [4, 6], "param": "mid_crz"},
    {"gate": "CRZ", "wires": [5, 7], "param": "mid_crz"},

    {"gate": "CZ", "wires": [0, 4]},
    {"gate": "CZ", "wires": [1, 5]},
    {"gate": "CZ", "wires": [2, 6]},
    {"gate": "CZ", "wires": [3, 7]},

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