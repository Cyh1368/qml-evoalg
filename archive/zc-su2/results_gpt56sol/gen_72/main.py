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
    # Prepare a permutation-symmetric collective mode.
    {"gate": "RY", "wire": 0, "param": "collective_mode"},
    {"gate": "RY", "wire": 1, "param": "collective_mode"},
    {"gate": "RY", "wire": 2, "param": "collective_mode"},
    {"gate": "RY", "wire": 3, "param": "collective_mode"},
    {"gate": "RY", "wire": 4, "param": "collective_mode"},
    {"gate": "RY", "wire": 5, "param": "collective_mode"},
    {"gate": "RY", "wire": 6, "param": "collective_mode"},
    {"gate": "RY", "wire": 7, "param": "collective_mode"},

    # Rotate the collective signal into a phase-sensitive basis.
    {"gate": "RZ", "wire": 0, "param": "collective_mode"},
    {"gate": "RZ", "wire": 1, "param": "collective_mode"},
    {"gate": "RZ", "wire": 2, "param": "collective_mode"},
    {"gate": "RZ", "wire": 3, "param": "collective_mode"},
    {"gate": "RZ", "wire": 4, "param": "collective_mode"},
    {"gate": "RZ", "wire": 5, "param": "collective_mode"},
    {"gate": "RZ", "wire": 6, "param": "collective_mode"},
    {"gate": "RZ", "wire": 7, "param": "collective_mode"},

    # Periodic collective Ising ring: full connectivity propagation with no
    # additional independent trainable variables.
    {"gate": "XX", "wires": [0, 1], "param": "collective_mode"},
    {"gate": "XX", "wires": [1, 2], "param": "collective_mode"},
    {"gate": "XX", "wires": [2, 3], "param": "collective_mode"},
    {"gate": "XX", "wires": [3, 4], "param": "collective_mode"},
    {"gate": "XX", "wires": [4, 5], "param": "collective_mode"},
    {"gate": "XX", "wires": [5, 6], "param": "collective_mode"},
    {"gate": "XX", "wires": [6, 7], "param": "collective_mode"},
    {"gate": "XX", "wires": [7, 0], "param": "collective_mode"},

    # Collective echo converts the distributed correlations back toward the
    # fixed readout basis.
    {"gate": "RY", "wire": 0, "param": "collective_mode"},
    {"gate": "RY", "wire": 1, "param": "collective_mode"},
    {"gate": "RY", "wire": 2, "param": "collective_mode"},
    {"gate": "RY", "wire": 3, "param": "collective_mode"},
    {"gate": "RY", "wire": 4, "param": "collective_mode"},
    {"gate": "RY", "wire": 5, "param": "collective_mode"},
    {"gate": "RY", "wire": 6, "param": "collective_mode"},
    {"gate": "RY", "wire": 7, "param": "collective_mode"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)