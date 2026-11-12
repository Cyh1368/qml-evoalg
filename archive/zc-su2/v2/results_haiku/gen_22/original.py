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
    # Initial rotation layer: individual parameters for first layer encoding
    {"gate": "RY", "wire": 0, "param": "p_0"},
    {"gate": "RY", "wire": 1, "param": "p_1"},
    {"gate": "RY", "wire": 2, "param": "p_2"},
    {"gate": "RY", "wire": 3, "param": "p_3"},
    {"gate": "RY", "wire": 4, "param": "p_4"},
    {"gate": "RY", "wire": 5, "param": "p_5"},
    {"gate": "RY", "wire": 6, "param": "p_6"},
    {"gate": "RY", "wire": 7, "param": "p_7"},

    # First entangling block: nearest-neighbor CRZ gates with parameter reuse
    {"gate": "CRZ", "wires": [0, 1], "param": "p_0"},
    {"gate": "CRZ", "wires": [2, 3], "param": "p_1"},
    {"gate": "CRZ", "wires": [4, 5], "param": "p_2"},
    {"gate": "CRZ", "wires": [6, 7], "param": "p_3"},

    # Offset nearest-neighbor CRZ gates
    {"gate": "CRZ", "wires": [1, 2], "param": "p_4"},
    {"gate": "CRZ", "wires": [3, 4], "param": "p_5"},
    {"gate": "CRZ", "wires": [5, 6], "param": "p_6"},

    # Long-range entanglement: ZZ gates for non-local correlations
    {"gate": "ZZ", "wires": [0, 3], "param": "p_7"},
    {"gate": "ZZ", "wires": [1, 4], "param": "p_0"},
    {"gate": "ZZ", "wires": [2, 5], "param": "p_1"},
    {"gate": "ZZ", "wires": [3, 6], "param": "p_2"},
    {"gate": "ZZ", "wires": [4, 7], "param": "p_3"},

    # Final rotation layer with parameter sharing
    {"gate": "RZ", "wire": 0, "param": "p_0"},
    {"gate": "RZ", "wire": 1, "param": "p_1"},
    {"gate": "RZ", "wire": 2, "param": "p_2"},
    {"gate": "RZ", "wire": 3, "param": "p_3"},
    {"gate": "RZ", "wire": 4, "param": "p_4"},
    {"gate": "RZ", "wire": 5, "param": "p_5"},
    {"gate": "RZ", "wire": 6, "param": "p_6"},
    {"gate": "RZ", "wire": 7, "param": "p_7"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)