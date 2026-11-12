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
    # Block 1: [RX with param rx_1] → [RZ with param rz_1] → [CZ chain] → [RZ with param rz_1]
    {"gate": "RX", "wire": 0, "param": "rx_1"},
    {"gate": "RX", "wire": 1, "param": "rx_1"},
    {"gate": "RX", "wire": 2, "param": "rx_1"},
    {"gate": "RX", "wire": 3, "param": "rx_1"},
    {"gate": "RX", "wire": 4, "param": "rx_1"},
    {"gate": "RX", "wire": 5, "param": "rx_1"},
    {"gate": "RX", "wire": 6, "param": "rx_1"},
    {"gate": "RX", "wire": 7, "param": "rx_1"},
    {"gate": "RZ", "wire": 0, "param": "rz_1"},
    {"gate": "RZ", "wire": 1, "param": "rz_1"},
    {"gate": "RZ", "wire": 2, "param": "rz_1"},
    {"gate": "RZ", "wire": 3, "param": "rz_1"},
    {"gate": "RZ", "wire": 4, "param": "rz_1"},
    {"gate": "RZ", "wire": 5, "param": "rz_1"},
    {"gate": "RZ", "wire": 6, "param": "rz_1"},
    {"gate": "RZ", "wire": 7, "param": "rz_1"},
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [6, 7]},
    {"gate": "RZ", "wire": 0, "param": "rz_1"},
    {"gate": "RZ", "wire": 1, "param": "rz_1"},
    {"gate": "RZ", "wire": 2, "param": "rz_1"},
    {"gate": "RZ", "wire": 3, "param": "rz_1"},
    {"gate": "RZ", "wire": 4, "param": "rz_1"},
    {"gate": "RZ", "wire": 5, "param": "rz_1"},
    {"gate": "RZ", "wire": 6, "param": "rz_1"},
    {"gate": "RZ", "wire": 7, "param": "rz_1"},
    # Block 2: [RX with param rx_2] → [RZ with param rz_2] → [CZ chain] → [RZ with param rz_2]
    {"gate": "RX", "wire": 0, "param": "rx_2"},
    {"gate": "RX", "wire": 1, "param": "rx_2"},
    {"gate": "RX", "wire": 2, "param": "rx_2"},
    {"gate": "RX", "wire": 3, "param": "rx_2"},
    {"gate": "RX", "wire": 4, "param": "rx_2"},
    {"gate": "RX", "wire": 5, "param": "rx_2"},
    {"gate": "RX", "wire": 6, "param": "rx_2"},
    {"gate": "RX", "wire": 7, "param": "rx_2"},
    {"gate": "RZ", "wire": 0, "param": "rz_2"},
    {"gate": "RZ", "wire": 1, "param": "rz_2"},
    {"gate": "RZ", "wire": 2, "param": "rz_2"},
    {"gate": "RZ", "wire": 3, "param": "rz_2"},
    {"gate": "RZ", "wire": 4, "param": "rz_2"},
    {"gate": "RZ", "wire": 5, "param": "rz_2"},
    {"gate": "RZ", "wire": 6, "param": "rz_2"},
    {"gate": "RZ", "wire": 7, "param": "rz_2"},
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [6, 7]},
    {"gate": "RZ", "wire": 0, "param": "rz_2"},
    {"gate": "RZ", "wire": 1, "param": "rz_2"},
    {"gate": "RZ", "wire": 2, "param": "rz_2"},
    {"gate": "RZ", "wire": 3, "param": "rz_2"},
    {"gate": "RZ", "wire": 4, "param": "rz_2"},
    {"gate": "RZ", "wire": 5, "param": "rz_2"},
    {"gate": "RZ", "wire": 6, "param": "rz_2"},
    {"gate": "RZ", "wire": 7, "param": "rz_2"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)