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
    # Pre-entanglement rotations: ALL 8 qubits share a SINGLE global
    # parameter "theta" (RY axis). This restores the extreme parameter
    # sharing of the earlier best-scoring candidate.
    {"gate": "RY", "wire": 0, "param": "theta"},
    {"gate": "RY", "wire": 1, "param": "theta"},
    {"gate": "RY", "wire": 2, "param": "theta"},
    {"gate": "RY", "wire": 3, "param": "theta"},
    {"gate": "RY", "wire": 4, "param": "theta"},
    {"gate": "RY", "wire": 5, "param": "theta"},
    {"gate": "RY", "wire": 6, "param": "theta"},
    {"gate": "RY", "wire": 7, "param": "theta"},

    # Entangling layer: closed ring (nearest-neighbor chain + wrap-around
    # edge). The XX-entangling gates also reuse the SAME "theta" parameter,
    # so no new trainable parameters are introduced by entanglement.
    {"gate": "XX", "wires": [0, 1], "param": "theta"},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "XX", "wires": [2, 3], "param": "theta"},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "XX", "wires": [4, 5], "param": "theta"},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "XX", "wires": [6, 7], "param": "theta"},
    {"gate": "CZ", "wires": [7, 0]},

    # Post-entanglement rotations: ALL 8 qubits share the SAME global
    # "theta" parameter (RZ axis), so the entire block uses only ONE
    # unique trainable parameter overall, maximizing parameter economy.
    {"gate": "RZ", "wire": 0, "param": "theta"},
    {"gate": "RZ", "wire": 1, "param": "theta"},
    {"gate": "RZ", "wire": 2, "param": "theta"},
    {"gate": "RZ", "wire": 3, "param": "theta"},
    {"gate": "RZ", "wire": 4, "param": "theta"},
    {"gate": "RZ", "wire": 5, "param": "theta"},
    {"gate": "RZ", "wire": 6, "param": "theta"},
    {"gate": "RZ", "wire": 7, "param": "theta"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)