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
    # Parity-broken initial rotation: even qubits get ry_a, odd qubits get ry_b.
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 4, "param": "ry_a"},
    {"gate": "RY", "wire": 6, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_b"},
    {"gate": "RY", "wire": 3, "param": "ry_b"},
    {"gate": "RY", "wire": 5, "param": "ry_b"},
    {"gate": "RY", "wire": 7, "param": "ry_b"},

    # Shared nearest-neighbor ZZ Ising ring: continuously tunable entangling
    # strength instead of fixed CNOTs.
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

    # Long-range shared ZZ coupling connecting opposite halves of the register.
    # Reuses zz_g so the optimizer settles on one consistent entangling
    # strength across both short- and long-range links, reducing overfitting.
    {"gate": "ZZ", "wires": [0, 4], "param": "zz_g"},
    {"gate": "ZZ", "wires": [1, 5], "param": "zz_g"},
    {"gate": "ZZ", "wires": [2, 6], "param": "zz_g"},
    {"gate": "ZZ", "wires": [3, 7], "param": "zz_g"},

    # Symmetric phase-alignment: reuse rz_c after the entangling layers to
    # match the earlier rz_c rotation, without adding a new parameter.
    {"gate": "RZ", "wire": 0, "param": "rz_c"},
    {"gate": "RZ", "wire": 1, "param": "rz_c"},
    {"gate": "RZ", "wire": 2, "param": "rz_c"},
    {"gate": "RZ", "wire": 3, "param": "rz_c"},
    {"gate": "RZ", "wire": 4, "param": "rz_c"},
    {"gate": "RZ", "wire": 5, "param": "rz_c"},
    {"gate": "RZ", "wire": 6, "param": "rz_c"},
    {"gate": "RZ", "wire": 7, "param": "rz_c"},

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