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
    # Parity-broken initial rotation: even qubits share ry_a, odd qubits
    # share ry_b. This gives the encoding just enough asymmetry to separate
    # hard groups while keeping the parameter count minimal.
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 4, "param": "ry_a"},
    {"gate": "RY", "wire": 6, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_b"},
    {"gate": "RY", "wire": 3, "param": "ry_b"},
    {"gate": "RY", "wire": 5, "param": "ry_b"},
    {"gate": "RY", "wire": 7, "param": "ry_b"},

    # Shared nearest-neighbor ZZ Ising ring: a single continuously tunable
    # entangling strength across the whole register instead of fixed CNOTs.
    {"gate": "ZZ", "wires": [0, 1], "param": "zz_g"},
    {"gate": "ZZ", "wires": [1, 2], "param": "zz_g"},
    {"gate": "ZZ", "wires": [2, 3], "param": "zz_g"},
    {"gate": "ZZ", "wires": [3, 4], "param": "zz_g"},
    {"gate": "ZZ", "wires": [4, 5], "param": "zz_g"},
    {"gate": "ZZ", "wires": [5, 6], "param": "zz_g"},
    {"gate": "ZZ", "wires": [6, 7], "param": "zz_g"},
    {"gate": "ZZ", "wires": [7, 0], "param": "zz_g"},

    # Global shared phase mixing.
    {"gate": "RZ", "wire": 0, "param": "rz_c"},
    {"gate": "RZ", "wire": 1, "param": "rz_c"},
    {"gate": "RZ", "wire": 2, "param": "rz_c"},
    {"gate": "RZ", "wire": 3, "param": "rz_c"},
    {"gate": "RZ", "wire": 4, "param": "rz_c"},
    {"gate": "RZ", "wire": 5, "param": "rz_c"},
    {"gate": "RZ", "wire": 6, "param": "rz_c"},
    {"gate": "RZ", "wire": 7, "param": "rz_c"},

    # Long-range ZZ coupling connecting opposite halves of the register,
    # reusing the SAME shared parameter (zz_g) as the nearest-neighbor ring
    # so entanglement spreads globally without adding a new trainable name.
    {"gate": "ZZ", "wires": [0, 4], "param": "zz_g"},
    {"gate": "ZZ", "wires": [1, 5], "param": "zz_g"},
    {"gate": "ZZ", "wires": [2, 6], "param": "zz_g"},
    {"gate": "ZZ", "wires": [3, 7], "param": "zz_g"},

    # Final shared closing rotation.
    {"gate": "RY", "wire": 0, "param": "ry_d"},
    {"gate": "RY", "wire": 1, "param": "ry_d"},
    {"gate": "RY", "wire": 2, "param": "ry_d"},
    {"gate": "RY", "wire": 3, "param": "ry_d"},
    {"gate": "RY", "wire": 4, "param": "ry_d"},
    {"gate": "RY", "wire": 5, "param": "ry_d"},
    {"gate": "RY", "wire": 6, "param": "ry_d"},
    {"gate": "RY", "wire": 7, "param": "ry_d"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)
