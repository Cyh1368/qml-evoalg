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
    # A single globally tied local mixer provides strong regularization and
    # minimizes the number of parameters needed for local basis adaptation.
    {"gate": "RY", "wire": 0, "param": "global_mix"},
    {"gate": "RY", "wire": 1, "param": "global_mix"},
    {"gate": "RY", "wire": 2, "param": "global_mix"},
    {"gate": "RY", "wire": 3, "param": "global_mix"},
    {"gate": "RY", "wire": 4, "param": "global_mix"},
    {"gate": "RY", "wire": 5, "param": "global_mix"},
    {"gate": "RY", "wire": 6, "param": "global_mix"},
    {"gate": "RY", "wire": 7, "param": "global_mix"},

    # Fixed short-range butterfly correlations.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [6, 7]},

    # Continuously tunable intermediate-range correlations reuse the sole
    # parameter, enriching mesoscopic structure without reducing economy.
    {"gate": "CRZ", "wires": [0, 2], "param": "global_mix"},
    {"gate": "CRZ", "wires": [1, 3], "param": "global_mix"},
    {"gate": "CRZ", "wires": [4, 6], "param": "global_mix"},
    {"gate": "CRZ", "wires": [5, 7], "param": "global_mix"},

    # Fixed cross-half phase correlations complete the economical butterfly
    # without introducing interaction-specific trainable parameters.
    {"gate": "CZ", "wires": [0, 4]},
    {"gate": "CZ", "wires": [1, 5]},

    # Retain complementary fixed cross-half phase correlations.
    {"gate": "CZ", "wires": [2, 6]},
    {"gate": "CZ", "wires": [3, 7]},

    # Reuse the sole mixer angle on a noncommuting axis, exposing accumulated
    # phase correlations while preserving maximal parameter economy.
    {"gate": "RX", "wire": 0, "param": "global_mix"},
    {"gate": "RX", "wire": 1, "param": "global_mix"},
    {"gate": "RX", "wire": 2, "param": "global_mix"},
    {"gate": "RX", "wire": 3, "param": "global_mix"},
    {"gate": "RX", "wire": 4, "param": "global_mix"},
    {"gate": "RX", "wire": 5, "param": "global_mix"},
    {"gate": "RX", "wire": 6, "param": "global_mix"},
    {"gate": "RX", "wire": 7, "param": "global_mix"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)