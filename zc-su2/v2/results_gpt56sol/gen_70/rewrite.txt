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
    # Begin with a globally shared mixer on one half of the register.
    {"gate": "RY", "wire": 0, "param": "global_mix"},
    {"gate": "RY", "wire": 1, "param": "global_mix"},
    {"gate": "RY", "wire": 2, "param": "global_mix"},
    {"gate": "RY", "wire": 3, "param": "global_mix"},

    # Immediately distribute those features across the full register.
    {"gate": "CZ", "wires": [0, 4]},
    {"gate": "CZ", "wires": [1, 5]},
    {"gate": "CZ", "wires": [2, 6]},
    {"gate": "CZ", "wires": [3, 7]},

    # Mix the receiving half after acquiring nonlocal phase information.
    {"gate": "RY", "wire": 4, "param": "global_mix"},
    {"gate": "RY", "wire": 5, "param": "global_mix"},
    {"gate": "RY", "wire": 6, "param": "global_mix"},
    {"gate": "RY", "wire": 7, "param": "global_mix"},

    # Adaptive medium-range correlations. All links share the existing angle,
    # increasing expressivity without introducing another trainable parameter.
    {"gate": "CRZ", "wires": [0, 2], "param": "global_mix"},
    {"gate": "CRZ", "wires": [1, 3], "param": "global_mix"},
    {"gate": "CRZ", "wires": [4, 6], "param": "global_mix"},
    {"gate": "CRZ", "wires": [5, 7], "param": "global_mix"},

    # Fixed local correlations supply a simple short-range inductive bias.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [6, 7]},

    # A shared noncommuting readout mixer exposes the accumulated phases.
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