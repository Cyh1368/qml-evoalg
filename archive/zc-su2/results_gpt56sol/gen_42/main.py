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
    # A parallel Ising matching combines trainable mixing and entanglement.
    # Parameter sharing leaves only one trainable mode per repeated block.
    {"gate": "XX", "wires": [0, 1], "param": "collective_ising"},
    {"gate": "XX", "wires": [2, 3], "param": "collective_ising"},
    {"gate": "XX", "wires": [4, 5], "param": "collective_ising"},
    {"gate": "XX", "wires": [6, 7], "param": "collective_ising"},

    # Parameter-free bridges connect the four Ising pairs into a ring.
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [7, 0]},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)