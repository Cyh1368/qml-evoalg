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
    # RY layer: two shared groups (wires 0-3 vs 4-7) preserve class-relevant
    # asymmetry between qubit groups; only 2 trainable params here.
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_a"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 3, "param": "ry_a"},
    {"gate": "RY", "wire": 4, "param": "ry_b"},
    {"gate": "RY", "wire": 5, "param": "ry_b"},
    {"gate": "RY", "wire": 6, "param": "ry_b"},
    {"gate": "RY", "wire": 7, "param": "ry_b"},

    # Fixed entangling ladder (forward) - alternating CNOT/CZ to mix both
    # bit-flip and phase-only entangling interactions at zero parameter
    # cost, building richer connectivity across all 8 qubits.
    {"gate": "CNOT", "wires": [0, 1]},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CNOT", "wires": [2, 3]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CNOT", "wires": [4, 5]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CNOT", "wires": [6, 7]},

    # Single shared global phase parameter applied to all qubits before the
    # parametrized entangling ring.
    {"gate": "RZ", "wire": 0, "param": "rz_p"},
    {"gate": "RZ", "wire": 1, "param": "rz_p"},
    {"gate": "RZ", "wire": 2, "param": "rz_p"},
    {"gate": "RZ", "wire": 3, "param": "rz_p"},
    {"gate": "RZ", "wire": 4, "param": "rz_p"},
    {"gate": "RZ", "wire": 5, "param": "rz_p"},
    {"gate": "RZ", "wire": 6, "param": "rz_p"},
    {"gate": "RZ", "wire": 7, "param": "rz_p"},

    # Parametrized entangling ring: one shared coupling strength across the
    # full ring topology (wraps around 7-0).
    {"gate": "ZZ", "wires": [0, 1], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [1, 2], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [2, 3], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [3, 4], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [4, 5], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [5, 6], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [6, 7], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [7, 0], "param": "zz_ring"},

    # Long-range ZZ couplings across opposite qubits, sharing the same ring
    # parameter, to give the ansatz a richer (hypercube-like) connectivity
    # without adding new trainable parameters.
    {"gate": "ZZ", "wires": [0, 4], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [1, 5], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [2, 6], "param": "zz_ring"},
    {"gate": "ZZ", "wires": [3, 7], "param": "zz_ring"},

    # Fixed entangling ladder (backward) - alternating CZ/CNOT (opposite
    # phase to the forward ladder) for additional mixed-basis entangling
    # mixing, still no extra trainable parameters.
    {"gate": "CZ", "wires": [7, 6]},
    {"gate": "CNOT", "wires": [6, 5]},
    {"gate": "CZ", "wires": [5, 4]},
    {"gate": "CNOT", "wires": [4, 3]},
    {"gate": "CZ", "wires": [3, 2]},
    {"gate": "CNOT", "wires": [2, 1]},
    {"gate": "CZ", "wires": [1, 0]},

    # Reuse the same global phase parameter after the entangling ring,
    # reinforcing the encoding without adding a new trainable name.
    {"gate": "RZ", "wire": 0, "param": "rz_p"},
    {"gate": "RZ", "wire": 1, "param": "rz_p"},
    {"gate": "RZ", "wire": 2, "param": "rz_p"},
    {"gate": "RZ", "wire": 3, "param": "rz_p"},
    {"gate": "RZ", "wire": 4, "param": "rz_p"},
    {"gate": "RZ", "wire": 5, "param": "rz_p"},
    {"gate": "RZ", "wire": 6, "param": "rz_p"},
    {"gate": "RZ", "wire": 7, "param": "rz_p"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)