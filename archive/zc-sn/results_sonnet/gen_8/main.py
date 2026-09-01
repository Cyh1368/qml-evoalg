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


# EVOLVE-BLOCK-START
ANSATZ_SPEC = [
    # Initial per-qubit rotations: RY then RZ (unique params -> full local expressivity)
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},
    {"gate": "RZ", "wire": 0, "param": "rz_0"},
    {"gate": "RZ", "wire": 1, "param": "rz_1"},
    {"gate": "RZ", "wire": 2, "param": "rz_2"},
    {"gate": "RZ", "wire": 3, "param": "rz_3"},
    {"gate": "RZ", "wire": 4, "param": "rz_4"},
    {"gate": "RZ", "wire": 5, "param": "rz_5"},
    {"gate": "RZ", "wire": 6, "param": "rz_6"},
    {"gate": "RZ", "wire": 7, "param": "rz_7"},

    # Fixed entangling ring (chain + wrap-around edge) using CNOT for stronger
    # entangling power than CZ, and full ring connectivity instead of an open chain.
    {"gate": "CNOT", "wires": [0, 1]},
    {"gate": "CNOT", "wires": [1, 2]},
    {"gate": "CNOT", "wires": [2, 3]},
    {"gate": "CNOT", "wires": [3, 4]},
    {"gate": "CNOT", "wires": [4, 5]},
    {"gate": "CNOT", "wires": [5, 6]},
    {"gate": "CNOT", "wires": [6, 7]},
    {"gate": "CNOT", "wires": [7, 0]},

    # Trainable entangling layer on the same ring, sharing a single parameter
    # across all edges. This is a cheap (1-parameter) way to make the
    # entanglement strength learnable rather than fixed.
    {"gate": "CRZ", "wires": [0, 1], "param": "crz_ring"},
    {"gate": "CRZ", "wires": [1, 2], "param": "crz_ring"},
    {"gate": "CRZ", "wires": [2, 3], "param": "crz_ring"},
    {"gate": "CRZ", "wires": [3, 4], "param": "crz_ring"},
    {"gate": "CRZ", "wires": [4, 5], "param": "crz_ring"},
    {"gate": "CRZ", "wires": [5, 6], "param": "crz_ring"},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_ring"},
    {"gate": "CRZ", "wires": [7, 0], "param": "crz_ring"},

    # Closing local rotation layer (basis change not redundant with the
    # initial RY/RZ layer since it comes after entanglement).
    {"gate": "RY", "wire": 0, "param": "ry_out_0"},
    {"gate": "RY", "wire": 1, "param": "ry_out_1"},
    {"gate": "RY", "wire": 2, "param": "ry_out_2"},
    {"gate": "RY", "wire": 3, "param": "ry_out_3"},
    {"gate": "RY", "wire": 4, "param": "ry_out_4"},
    {"gate": "RY", "wire": 5, "param": "ry_out_5"},
    {"gate": "RY", "wire": 6, "param": "ry_out_6"},
    {"gate": "RY", "wire": 7, "param": "ry_out_7"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)
