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
    # This mild asymmetry has proven useful for separating hard groups while
    # keeping the parameter count low (only 2 params for the whole layer).
    {"gate": "RY", "wire": 0, "param": "ry_a"},
    {"gate": "RY", "wire": 2, "param": "ry_a"},
    {"gate": "RY", "wire": 4, "param": "ry_a"},
    {"gate": "RY", "wire": 6, "param": "ry_a"},
    {"gate": "RY", "wire": 1, "param": "ry_b"},
    {"gate": "RY", "wire": 3, "param": "ry_b"},
    {"gate": "RY", "wire": 5, "param": "ry_b"},
    {"gate": "RY", "wire": 7, "param": "ry_b"},

    # Fixed, parameter-free forward entangling ring: spreads information
    # cheaply without adding trainable parameters or overfitting risk.
    {"gate": "CNOT", "wires": [0, 1]},
    {"gate": "CNOT", "wires": [1, 2]},
    {"gate": "CNOT", "wires": [2, 3]},
    {"gate": "CNOT", "wires": [3, 4]},
    {"gate": "CNOT", "wires": [4, 5]},
    {"gate": "CNOT", "wires": [5, 6]},
    {"gate": "CNOT", "wires": [6, 7]},

    # Global shared phase rotation (single parameter instead of a parity
    # split): merging the mid-circuit RZ into one shared angle frees up a
    # parameter slot for the final readout twist without growing the total
    # parameter count.
    {"gate": "RZ", "wire": 0, "param": "rz_c"},
    {"gate": "RZ", "wire": 1, "param": "rz_c"},
    {"gate": "RZ", "wire": 2, "param": "rz_c"},
    {"gate": "RZ", "wire": 3, "param": "rz_c"},
    {"gate": "RZ", "wire": 4, "param": "rz_c"},
    {"gate": "RZ", "wire": 5, "param": "rz_c"},
    {"gate": "RZ", "wire": 6, "param": "rz_c"},
    {"gate": "RZ", "wire": 7, "param": "rz_c"},

    # Fixed backward entangling ring: re-mixes information in the opposite
    # direction, again with zero trainable-parameter cost.
    {"gate": "CNOT", "wires": [7, 6]},
    {"gate": "CNOT", "wires": [6, 5]},
    {"gate": "CNOT", "wires": [5, 4]},
    {"gate": "CNOT", "wires": [4, 3]},
    {"gate": "CNOT", "wires": [3, 2]},
    {"gate": "CNOT", "wires": [2, 1]},
    {"gate": "CNOT", "wires": [1, 0]},

    # Disjoint-pair controlled-phase entangling layer with one shared
    # parameter, giving tunable long-range correlation at minimal parameter
    # cost.
    {"gate": "CRZ", "wires": [0, 1], "param": "ent"},
    {"gate": "CRZ", "wires": [2, 3], "param": "ent"},
    {"gate": "CRZ", "wires": [4, 5], "param": "ent"},
    {"gate": "CRZ", "wires": [6, 7], "param": "ent"},

    # Concluding two-layer readout: a global RY rotation followed by a
    # global RZ "phase twist" just before measurement. This sharpens class
    # separation while adding only one extra shared parameter.
    {"gate": "RY", "wire": 0, "param": "ry_c"},
    {"gate": "RY", "wire": 1, "param": "ry_c"},
    {"gate": "RY", "wire": 2, "param": "ry_c"},
    {"gate": "RY", "wire": 3, "param": "ry_c"},
    {"gate": "RY", "wire": 4, "param": "ry_c"},
    {"gate": "RY", "wire": 5, "param": "ry_c"},
    {"gate": "RY", "wire": 6, "param": "ry_c"},
    {"gate": "RY", "wire": 7, "param": "ry_c"},

    {"gate": "RZ", "wire": 0, "param": "rz_out"},
    {"gate": "RZ", "wire": 1, "param": "rz_out"},
    {"gate": "RZ", "wire": 2, "param": "rz_out"},
    {"gate": "RZ", "wire": 3, "param": "rz_out"},
    {"gate": "RZ", "wire": 4, "param": "rz_out"},
    {"gate": "RZ", "wire": 5, "param": "rz_out"},
    {"gate": "RZ", "wire": 6, "param": "rz_out"},
    {"gate": "RZ", "wire": 7, "param": "rz_out"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)