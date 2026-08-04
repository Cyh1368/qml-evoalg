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
    # --- Global RY encoding layer (single shared parameter) ---
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_a"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 3, "param": "ry_a"},
    {"gate": "RY", "wire": 4, "param": "ry_a"},
    {"gate": "RY", "wire": 5, "param": "ry_a"},
    {"gate": "RY", "wire": 6, "param": "ry_a"},
    {"gate": "RY", "wire": 7, "param": "ry_a"},

    # --- Butterfly / hypercube entangling network, round 1 ---
    # Stage A: distance-1 pairs (ZZ)
    {"gate": "ZZ", "wires": [0, 1], "param": "ent"},
    {"gate": "ZZ", "wires": [2, 3], "param": "ent"},
    {"gate": "ZZ", "wires": [4, 5], "param": "ent"},
    {"gate": "ZZ", "wires": [6, 7], "param": "ent"},

    # Stage B: distance-2 pairs (XX) - orthogonal coupling
    {"gate": "XX", "wires": [0, 2], "param": "ent"},
    {"gate": "XX", "wires": [1, 3], "param": "ent"},
    {"gate": "XX", "wires": [4, 6], "param": "ent"},
    {"gate": "XX", "wires": [5, 7], "param": "ent"},

    # Stage C: distance-4 pairs (ZZ) - closes full connectivity across halves
    {"gate": "ZZ", "wires": [0, 4], "param": "ent"},
    {"gate": "ZZ", "wires": [1, 5], "param": "ent"},
    {"gate": "ZZ", "wires": [2, 6], "param": "ent"},
    {"gate": "ZZ", "wires": [3, 7], "param": "ent"},

    # --- Global RZ phase layer (single shared parameter) ---
    {"gate": "RZ", "wire": 0, "param": "rz_p"},
    {"gate": "RZ", "wire": 1, "param": "rz_p"},
    {"gate": "RZ", "wire": 2, "param": "rz_p"},
    {"gate": "RZ", "wire": 3, "param": "rz_p"},
    {"gate": "RZ", "wire": 4, "param": "rz_p"},
    {"gate": "RZ", "wire": 5, "param": "rz_p"},
    {"gate": "RZ", "wire": 6, "param": "rz_p"},
    {"gate": "RZ", "wire": 7, "param": "rz_p"},

    # --- Butterfly / hypercube entangling network, round 2 ---
    # gate types swapped (XX <-> ZZ) for orthogonal mixing, same shared param
    # Stage A: distance-1 pairs (XX)
    {"gate": "XX", "wires": [0, 1], "param": "ent"},
    {"gate": "XX", "wires": [2, 3], "param": "ent"},
    {"gate": "XX", "wires": [4, 5], "param": "ent"},
    {"gate": "XX", "wires": [6, 7], "param": "ent"},

    # Stage B: distance-2 pairs (ZZ)
    {"gate": "ZZ", "wires": [0, 2], "param": "ent"},
    {"gate": "ZZ", "wires": [1, 3], "param": "ent"},
    {"gate": "ZZ", "wires": [4, 6], "param": "ent"},
    {"gate": "ZZ", "wires": [5, 7], "param": "ent"},

    # Stage C: distance-4 pairs (XX)
    {"gate": "XX", "wires": [0, 4], "param": "ent"},
    {"gate": "XX", "wires": [1, 5], "param": "ent"},
    {"gate": "XX", "wires": [2, 6], "param": "ent"},
    {"gate": "XX", "wires": [3, 7], "param": "ent"},

    # --- Final global RY layer, reusing the very first parameter name ---
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_a"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 3, "param": "ry_a"},
    {"gate": "RY", "wire": 4, "param": "ry_a"},
    {"gate": "RY", "wire": 5, "param": "ry_a"},
    {"gate": "RY", "wire": 6, "param": "ry_a"},
    {"gate": "RY", "wire": 7, "param": "ry_a"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)