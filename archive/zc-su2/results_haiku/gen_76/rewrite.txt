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
    # Block 1: Minimal prep + parametric ring with XX gates
    {"gate": "RX", "wire": 0, "param": "rx_prep"},
    {"gate": "RX", "wire": 1, "param": "rx_prep"},
    {"gate": "RX", "wire": 2, "param": "rx_prep"},
    {"gate": "RX", "wire": 3, "param": "rx_prep"},
    {"gate": "RX", "wire": 4, "param": "rx_prep"},
    {"gate": "RX", "wire": 5, "param": "rx_prep"},
    {"gate": "RX", "wire": 6, "param": "rx_prep"},
    {"gate": "RX", "wire": 7, "param": "rx_prep"},
    # Parametric ring: nearest-neighbor XX interactions
    {"gate": "XX", "wires": [0, 1], "param": "xx_0_1"},
    {"gate": "XX", "wires": [1, 2], "param": "xx_1_2"},
    {"gate": "XX", "wires": [2, 3], "param": "xx_2_3"},
    {"gate": "XX", "wires": [3, 4], "param": "xx_3_4"},
    {"gate": "XX", "wires": [4, 5], "param": "xx_4_5"},
    {"gate": "XX", "wires": [5, 6], "param": "xx_5_6"},
    {"gate": "XX", "wires": [6, 7], "param": "xx_6_7"},
    {"gate": "XX", "wires": [7, 0], "param": "xx_7_0"},
    # Single-qubit phase adjustment
    {"gate": "RZ", "wire": 0, "param": "rz_phase"},
    {"gate": "RZ", "wire": 1, "param": "rz_phase"},
    {"gate": "RZ", "wire": 2, "param": "rz_phase"},
    {"gate": "RZ", "wire": 3, "param": "rz_phase"},
    {"gate": "RZ", "wire": 4, "param": "rz_phase"},
    {"gate": "RZ", "wire": 5, "param": "rz_phase"},
    {"gate": "RZ", "wire": 6, "param": "rz_phase"},
    {"gate": "RZ", "wire": 7, "param": "rz_phase"},
    # Block 2: RY prep + parametric ring with YY gates + long-range
    {"gate": "RY", "wire": 0, "param": "ry_prep"},
    {"gate": "RY", "wire": 1, "param": "ry_prep"},
    {"gate": "RY", "wire": 2, "param": "ry_prep"},
    {"gate": "RY", "wire": 3, "param": "ry_prep"},
    {"gate": "RY", "wire": 4, "param": "ry_prep"},
    {"gate": "RY", "wire": 5, "param": "ry_prep"},
    {"gate": "RY", "wire": 6, "param": "ry_prep"},
    {"gate": "RY", "wire": 7, "param": "ry_prep"},
    # Parametric ring: nearest-neighbor YY interactions
    {"gate": "YY", "wires": [0, 1], "param": "yy_0_1"},
    {"gate": "YY", "wires": [1, 2], "param": "yy_1_2"},
    {"gate": "YY", "wires": [2, 3], "param": "yy_2_3"},
    {"gate": "YY", "wires": [3, 4], "param": "yy_3_4"},
    {"gate": "YY", "wires": [4, 5], "param": "yy_4_5"},
    {"gate": "YY", "wires": [5, 6], "param": "yy_5_6"},
    {"gate": "YY", "wires": [6, 7], "param": "yy_6_7"},
    {"gate": "YY", "wires": [7, 0], "param": "yy_7_0"},
    # Long-range diagonal interactions for global entanglement
    {"gate": "ZZ", "wires": [0, 4], "param": "zz_diag_0_4"},
    {"gate": "ZZ", "wires": [1, 5], "param": "zz_diag_1_5"},
    {"gate": "ZZ", "wires": [2, 6], "param": "zz_diag_2_6"},
    {"gate": "ZZ", "wires": [3, 7], "param": "zz_diag_3_7"},
    # Final phase adjustment
    {"gate": "RZ", "wire": 0, "param": "rz_final"},
    {"gate": "RZ", "wire": 1, "param": "rz_final"},
    {"gate": "RZ", "wire": 2, "param": "rz_final"},
    {"gate": "RZ", "wire": 3, "param": "rz_final"},
    {"gate": "RZ", "wire": 4, "param": "rz_final"},
    {"gate": "RZ", "wire": 5, "param": "rz_final"},
    {"gate": "RZ", "wire": 6, "param": "rz_final"},
    {"gate": "RZ", "wire": 7, "param": "rz_final"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)