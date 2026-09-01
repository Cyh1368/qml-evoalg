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
    # RX shared layer for rotational diversity (single new parameter)
    {"gate": "RX", "wire": 0, "param": "rx_shared"},
    {"gate": "RX", "wire": 1, "param": "rx_shared"},
    {"gate": "RX", "wire": 2, "param": "rx_shared"},
    {"gate": "RX", "wire": 3, "param": "rx_shared"},
    {"gate": "RX", "wire": 4, "param": "rx_shared"},
    {"gate": "RX", "wire": 5, "param": "rx_shared"},
    {"gate": "RX", "wire": 6, "param": "rx_shared"},
    {"gate": "RX", "wire": 7, "param": "rx_shared"},
    
    # Initial RY layer with per-qubit parameters
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},
    
    # First entangling block: nearest-neighbor XX gates with shared parameter
    {"gate": "XX", "wires": [0, 1], "param": "ent_nn"},
    {"gate": "XX", "wires": [2, 3], "param": "ent_nn"},
    {"gate": "XX", "wires": [4, 5], "param": "ent_nn"},
    {"gate": "XX", "wires": [6, 7], "param": "ent_nn"},
    
    # Second entangling block: offset nearest-neighbor YY gates
    {"gate": "YY", "wires": [1, 2], "param": "ent_off"},
    {"gate": "YY", "wires": [3, 4], "param": "ent_off"},
    {"gate": "YY", "wires": [5, 6], "param": "ent_off"},
    
    # Third entangling block: long-range ZZ gates
    {"gate": "ZZ", "wires": [0, 3], "param": "ent_lr"},
    {"gate": "ZZ", "wires": [1, 4], "param": "ent_lr"},
    {"gate": "ZZ", "wires": [2, 5], "param": "ent_lr"},
    {"gate": "ZZ", "wires": [3, 6], "param": "ent_lr"},
    {"gate": "ZZ", "wires": [4, 7], "param": "ent_lr"},
    
    # Post-entanglement RZ layer with shared parameter pairs
    {"gate": "RZ", "wire": 0, "param": "rz_post_even"},
    {"gate": "RZ", "wire": 1, "param": "rz_post_odd"},
    {"gate": "RZ", "wire": 2, "param": "rz_post_even"},
    {"gate": "RZ", "wire": 3, "param": "rz_post_odd"},
    {"gate": "RZ", "wire": 4, "param": "rz_post_even"},
    {"gate": "RZ", "wire": 5, "param": "rz_post_odd"},
    {"gate": "RZ", "wire": 6, "param": "rz_post_even"},
    {"gate": "RZ", "wire": 7, "param": "rz_post_odd"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)