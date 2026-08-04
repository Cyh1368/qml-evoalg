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
    # Pre-entanglement rotations: ALL 8 qubits share a SINGLE global "theta"
    # parameter (collapsing the previous 2-parameter design back to 1,
    # matching the best-scoring designs seen so far).
    {"gate": "RY", "wire": 0, "param": "theta"},
    {"gate": "RY", "wire": 1, "param": "theta"},
    {"gate": "RY", "wire": 2, "param": "theta"},
    {"gate": "RY", "wire": 3, "param": "theta"},
    {"gate": "RY", "wire": 4, "param": "theta"},
    {"gate": "RY", "wire": 5, "param": "theta"},
    {"gate": "RY", "wire": 6, "param": "theta"},
    {"gate": "RY", "wire": 7, "param": "theta"},

    # Entangling layer: closed ring (nearest-neighbor chain + wrap-around
    # edge) PLUS antipodal-pair CZ edges (distance 4 on the 8-cycle). This
    # gives every qubit entangling-degree 3 at zero extra trainable
    # parameter cost, which previously produced much faster convergence
    # (60 vs 240 steps) at the same accuracy/score.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [6, 7]},
    {"gate": "CZ", "wires": [7, 0]},
    {"gate": "CZ", "wires": [0, 4]},
    {"gate": "CZ", "wires": [1, 5]},
    {"gate": "CZ", "wires": [2, 6]},
    {"gate": "CZ", "wires": [3, 7]},

    # Post-entanglement rotations: ALL 8 qubits share the SAME global
    # "theta" parameter as the RY layer (different axis, so the single
    # scalar still drives a non-trivial entangled transformation), keeping
    # the total unique-parameter count per block at exactly 1.
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