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
    # Per-wire input adaptation.
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},

    # Shared noncommuting pre-mixer.
    {"gate": "RX", "wire": 0, "param": "rx_input_even"},
    {"gate": "RX", "wire": 1, "param": "rx_input_odd"},
    {"gate": "RX", "wire": 2, "param": "rx_input_even"},
    {"gate": "RX", "wire": 3, "param": "rx_input_odd"},
    {"gate": "RX", "wire": 4, "param": "rx_input_even"},
    {"gate": "RX", "wire": 5, "param": "rx_input_odd"},
    {"gate": "RX", "wire": 6, "param": "rx_input_even"},
    {"gate": "RX", "wire": 7, "param": "rx_input_odd"},

    # Butterfly scale 1: local pair interactions.
    {"gate": "CNOT", "wires": [0, 1]},
    {"gate": "CNOT", "wires": [2, 3]},
    {"gate": "CNOT", "wires": [4, 5]},
    {"gate": "CNOT", "wires": [6, 7]},
    {"gate": "CRY", "wires": [0, 1], "param": "cry_scale_1"},
    {"gate": "CRY", "wires": [2, 3], "param": "cry_scale_1"},
    {"gate": "CRY", "wires": [4, 5], "param": "cry_scale_1"},
    {"gate": "CRY", "wires": [6, 7], "param": "cry_scale_1"},

    # Butterfly scale 2: interactions between adjacent local blocks.
    {"gate": "CNOT", "wires": [0, 2]},
    {"gate": "CNOT", "wires": [1, 3]},
    {"gate": "CNOT", "wires": [4, 6]},
    {"gate": "CNOT", "wires": [5, 7]},
    {"gate": "CRY", "wires": [0, 2], "param": "cry_scale_2"},
    {"gate": "CRY", "wires": [1, 3], "param": "cry_scale_2"},
    {"gate": "CRY", "wires": [4, 6], "param": "cry_scale_2"},
    {"gate": "CRY", "wires": [5, 7], "param": "cry_scale_2"},

    # Butterfly scale 4: global interactions between both halves.
    {"gate": "CNOT", "wires": [0, 4]},
    {"gate": "CNOT", "wires": [1, 5]},
    {"gate": "CNOT", "wires": [2, 6]},
    {"gate": "CNOT", "wires": [3, 7]},
    {"gate": "CRY", "wires": [0, 4], "param": "cry_scale_4"},
    {"gate": "CRY", "wires": [1, 5], "param": "cry_scale_4"},
    {"gate": "CRY", "wires": [2, 6], "param": "cry_scale_4"},
    {"gate": "CRY", "wires": [3, 7], "param": "cry_scale_4"},

    # Global parity-dependent phase layer.
    {"gate": "RZ", "wire": 0, "param": "rz_global_even"},
    {"gate": "RZ", "wire": 1, "param": "rz_global_odd"},
    {"gate": "RZ", "wire": 2, "param": "rz_global_even"},
    {"gate": "RZ", "wire": 3, "param": "rz_global_odd"},
    {"gate": "RZ", "wire": 4, "param": "rz_global_even"},
    {"gate": "RZ", "wire": 5, "param": "rz_global_odd"},
    {"gate": "RZ", "wire": 6, "param": "rz_global_even"},
    {"gate": "RZ", "wire": 7, "param": "rz_global_odd"},

    # Reverse butterfly broadcasts global parity information back to all wires.
    {"gate": "CNOT", "wires": [4, 0]},
    {"gate": "CNOT", "wires": [5, 1]},
    {"gate": "CNOT", "wires": [6, 2]},
    {"gate": "CNOT", "wires": [7, 3]},

    {"gate": "CNOT", "wires": [2, 0]},
    {"gate": "CNOT", "wires": [3, 1]},
    {"gate": "CNOT", "wires": [6, 4]},
    {"gate": "CNOT", "wires": [7, 5]},

    {"gate": "CNOT", "wires": [1, 0]},
    {"gate": "CNOT", "wires": [3, 2]},
    {"gate": "CNOT", "wires": [5, 4]},
    {"gate": "CNOT", "wires": [7, 6]},

    # Two-axis output mixer converts phases and correlations to populations.
    {"gate": "RX", "wire": 0, "param": "rx_final_even"},
    {"gate": "RX", "wire": 1, "param": "rx_final_odd"},
    {"gate": "RX", "wire": 2, "param": "rx_final_even"},
    {"gate": "RX", "wire": 3, "param": "rx_final_odd"},
    {"gate": "RX", "wire": 4, "param": "rx_final_even"},
    {"gate": "RX", "wire": 5, "param": "rx_final_odd"},
    {"gate": "RX", "wire": 6, "param": "rx_final_even"},
    {"gate": "RX", "wire": 7, "param": "rx_final_odd"},

    {"gate": "RY", "wire": 0, "param": "ry_final_even"},
    {"gate": "RY", "wire": 1, "param": "ry_final_odd"},
    {"gate": "RY", "wire": 2, "param": "ry_final_even"},
    {"gate": "RY", "wire": 3, "param": "ry_final_odd"},
    {"gate": "RY", "wire": 4, "param": "ry_final_even"},
    {"gate": "RY", "wire": 5, "param": "ry_final_odd"},
    {"gate": "RY", "wire": 6, "param": "ry_final_even"},
    {"gate": "RY", "wire": 7, "param": "ry_final_odd"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)