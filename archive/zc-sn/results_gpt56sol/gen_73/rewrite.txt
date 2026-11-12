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
    # Independent local adaptation.
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},

    # Parity-shared phase preparation.
    {"gate": "RZ", "wire": 0, "param": "rz_pre_even"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre_odd"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre_even"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre_odd"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre_even"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre_odd"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre_even"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre_odd"},

    # Parallel even-bond matching with one shared trainable interaction.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [6, 7]},
    {"gate": "CRZ", "wires": [0, 1], "param": "crz_even_match"},
    {"gate": "CRZ", "wires": [2, 3], "param": "crz_even_match"},
    {"gate": "CRZ", "wires": [4, 5], "param": "crz_even_match"},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_even_match"},

    # Noncommuting mixer between the two ring matchings.
    {"gate": "RY", "wire": 0, "param": "ry_mix_even"},
    {"gate": "RY", "wire": 1, "param": "ry_mix_odd"},
    {"gate": "RY", "wire": 2, "param": "ry_mix_even"},
    {"gate": "RY", "wire": 3, "param": "ry_mix_odd"},
    {"gate": "RY", "wire": 4, "param": "ry_mix_even"},
    {"gate": "RY", "wire": 5, "param": "ry_mix_odd"},
    {"gate": "RY", "wire": 6, "param": "ry_mix_even"},
    {"gate": "RY", "wire": 7, "param": "ry_mix_odd"},

    # Shifted matching completes nearest-neighbor ring connectivity.
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [7, 0]},
    {"gate": "CRZ", "wires": [1, 2], "param": "crz_odd_match"},
    {"gate": "CRZ", "wires": [3, 4], "param": "crz_odd_match"},
    {"gate": "CRZ", "wires": [5, 6], "param": "crz_odd_match"},
    {"gate": "CRZ", "wires": [7, 0], "param": "crz_odd_match"},

    # Independent post-interaction phases.
    {"gate": "RZ", "wire": 0, "param": "rz_post_even"},
    {"gate": "RZ", "wire": 1, "param": "rz_post_odd"},
    {"gate": "RZ", "wire": 2, "param": "rz_post_even"},
    {"gate": "RZ", "wire": 3, "param": "rz_post_odd"},
    {"gate": "RZ", "wire": 4, "param": "rz_post_even"},
    {"gate": "RZ", "wire": 5, "param": "rz_post_odd"},
    {"gate": "RZ", "wire": 6, "param": "rz_post_even"},
    {"gate": "RZ", "wire": 7, "param": "rz_post_odd"},

    # Distance-two ring coupling from the lower-loss parent.
    {"gate": "CZ", "wires": [0, 2]},
    {"gate": "CZ", "wires": [1, 3]},
    {"gate": "CZ", "wires": [2, 4]},
    {"gate": "CZ", "wires": [3, 5]},
    {"gate": "CZ", "wires": [4, 6]},
    {"gate": "CZ", "wires": [5, 7]},
    {"gate": "CZ", "wires": [6, 0]},
    {"gate": "CZ", "wires": [7, 1]},

    # Population mixers for readout and repeated-block propagation.
    {"gate": "RY", "wire": 0, "param": "ry_mix2_even"},
    {"gate": "RY", "wire": 1, "param": "ry_mix2_odd"},
    {"gate": "RY", "wire": 2, "param": "ry_mix2_even"},
    {"gate": "RY", "wire": 3, "param": "ry_mix2_odd"},
    {"gate": "RY", "wire": 4, "param": "ry_mix2_even"},
    {"gate": "RY", "wire": 5, "param": "ry_mix2_odd"},
    {"gate": "RY", "wire": 6, "param": "ry_mix2_even"},
    {"gate": "RY", "wire": 7, "param": "ry_mix2_odd"},

    {"gate": "RX", "wire": 0, "param": "rx_final_even"},
    {"gate": "RX", "wire": 1, "param": "rx_final_odd"},
    {"gate": "RX", "wire": 2, "param": "rx_final_even"},
    {"gate": "RX", "wire": 3, "param": "rx_final_odd"},
    {"gate": "RX", "wire": 4, "param": "rx_final_even"},
    {"gate": "RX", "wire": 5, "param": "rx_final_odd"},
    {"gate": "RX", "wire": 6, "param": "rx_final_even"},
    {"gate": "RX", "wire": 7, "param": "rx_final_odd"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)