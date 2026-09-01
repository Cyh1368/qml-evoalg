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
    # Distance-1 parity echoes learn correlations inside adjacent pairs.
    {"gate": "CNOT", "wires": [0, 1]},
    {"gate": "CNOT", "wires": [2, 3]},
    {"gate": "CNOT", "wires": [4, 5]},
    {"gate": "CNOT", "wires": [6, 7]},

    {"gate": "RY", "wire": 1, "param": "global_angle"},
    {"gate": "RY", "wire": 3, "param": "global_angle"},
    {"gate": "RY", "wire": 5, "param": "global_angle"},
    {"gate": "RY", "wire": 7, "param": "global_angle"},

    {"gate": "CNOT", "wires": [0, 1]},
    {"gate": "CNOT", "wires": [2, 3]},
    {"gate": "CNOT", "wires": [4, 5]},
    {"gate": "CNOT", "wires": [6, 7]},

    # Distance-2 echoes aggregate pair responses within each four-wire half.
    {"gate": "CNOT", "wires": [0, 2]},
    {"gate": "CNOT", "wires": [1, 3]},
    {"gate": "CNOT", "wires": [4, 6]},
    {"gate": "CNOT", "wires": [5, 7]},

    {"gate": "RY", "wire": 2, "param": "global_angle"},
    {"gate": "RY", "wire": 3, "param": "global_angle"},
    {"gate": "RY", "wire": 6, "param": "global_angle"},
    {"gate": "RY", "wire": 7, "param": "global_angle"},

    {"gate": "CNOT", "wires": [0, 2]},
    {"gate": "CNOT", "wires": [1, 3]},
    {"gate": "CNOT", "wires": [4, 6]},
    {"gate": "CNOT", "wires": [5, 7]},

    # Distance-4 echoes create trainable correlations between circuit halves.
    {"gate": "CNOT", "wires": [0, 4]},
    {"gate": "CNOT", "wires": [1, 5]},
    {"gate": "CNOT", "wires": [2, 6]},
    {"gate": "CNOT", "wires": [3, 7]},

    {"gate": "RY", "wire": 4, "param": "global_angle"},
    {"gate": "RY", "wire": 5, "param": "global_angle"},
    {"gate": "RY", "wire": 6, "param": "global_angle"},
    {"gate": "RY", "wire": 7, "param": "global_angle"},

    {"gate": "CNOT", "wires": [0, 4]},
    {"gate": "CNOT", "wires": [1, 5]},
    {"gate": "CNOT", "wires": [2, 6]},
    {"gate": "CNOT", "wires": [3, 7]},

    # A noncommuting global readout mixer exposes the hierarchical parities.
    # Sharing its angle with every echo retains a single optimization degree.
    {"gate": "RX", "wire": 0, "param": "global_angle"},
    {"gate": "RX", "wire": 1, "param": "global_angle"},
    {"gate": "RX", "wire": 2, "param": "global_angle"},
    {"gate": "RX", "wire": 3, "param": "global_angle"},
    {"gate": "RX", "wire": 4, "param": "global_angle"},
    {"gate": "RX", "wire": 5, "param": "global_angle"},
    {"gate": "RX", "wire": 6, "param": "global_angle"},
    {"gate": "RX", "wire": 7, "param": "global_angle"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)