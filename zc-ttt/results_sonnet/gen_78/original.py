"""Seed program. Only ANSATZ_SPEC inside the EVOLVE-BLOCK is evolved.

Everything else about the task, that is how inputs are encoded, how the circuit
is measured, how training works and how metrics are computed, is fixed and lives
in a module that is not reproduced here. No information about the data is
available in this file.
"""

from _backend import run_experiment as _run

N_QUBITS = 9
ALLOWED_SINGLE_QUBIT_GATES = {"RX", "RY", "RZ"}
ALLOWED_TWO_QUBIT_GATES = {"CNOT", "CZ"}
ALLOWED_PARAM_TWO_QUBIT_GATES = {"CRX", "CRY", "CRZ"}
ALLOWED_THREE_QUBIT_GATES = {"ZZZ", "CCRZ"}


# EVOLVE-BLOCK-START
ANSATZ_SPEC = [
    # --- Encoding-like rotation layer (individual params) ---
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},
    {"gate": "RY", "wire": 8, "param": "ry_8"},

    # --- Entangling layer: CRZ gates grouped into 4 parallel sublayers ---
    # (matching decomposition of the allowed connectivity graph; gates within
    # a sublayer act on disjoint wires and can be scheduled concurrently)
    # Sublayer 1
    {"gate": "CRZ", "wires": [0, 2], "param": "crz_0"},
    {"gate": "CRZ", "wires": [1, 3], "param": "crz_b"},
    {"gate": "CRZ", "wires": [4, 8], "param": "crz_d"},
    {"gate": "CRZ", "wires": [5, 7], "param": "crz_e"},
    # Sublayer 2
    {"gate": "CRZ", "wires": [0, 3], "param": "crz_f"},
    {"gate": "CRZ", "wires": [2, 4], "param": "crz_c"},
    {"gate": "CRZ", "wires": [1, 8], "param": "crz_b"},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_g"},
    # Sublayer 3
    {"gate": "CRZ", "wires": [0, 7], "param": "crz_a"},
    {"gate": "CRZ", "wires": [2, 6], "param": "crz_c"},
    {"gate": "CRZ", "wires": [3, 5], "param": "crz_h"},
    # Sublayer 4
    {"gate": "CRZ", "wires": [0, 8], "param": "crz_a"},

    # --- Mid-circuit refresh on hub qubit 0 ---
    {"gate": "RX", "wire": 0, "param": "rx_mid_0"},

    # --- Final output rotation layer (individual params) ---
    {"gate": "RZ", "wire": 0, "param": "rz_post_0"},
    {"gate": "RZ", "wire": 1, "param": "rz_post_1"},
    {"gate": "RZ", "wire": 2, "param": "rz_post_2"},
    {"gate": "RZ", "wire": 3, "param": "rz_post_3"},
    {"gate": "RZ", "wire": 4, "param": "rz_post_4"},
    {"gate": "RZ", "wire": 5, "param": "rz_post_5"},
    {"gate": "RZ", "wire": 6, "param": "rz_post_6"},
    {"gate": "RZ", "wire": 7, "param": "rz_post_7"},
    {"gate": "RZ", "wire": 8, "param": "rz_post_8"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)