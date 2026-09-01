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
    # --- Pre-entangling single-qubit rotations (RY then RZ, 2 free angles/qubit) ---
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},
    {"gate": "RZ", "wire": 0, "param": "rz_pre_0"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre_1"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre_2"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre_3"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre_3"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre_2"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre_1"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre_0"},

    # --- Nearest-neighbour entangling ring with alternating shared trainable strength ---
    {"gate": "CRZ", "wires": [0, 1], "param": "crz_ring_even"},
    {"gate": "CRZ", "wires": [1, 2], "param": "crz_ring_odd"},
    {"gate": "CRZ", "wires": [2, 3], "param": "crz_ring_even"},
    {"gate": "CRZ", "wires": [3, 4], "param": "crz_ring_odd"},
    {"gate": "CRZ", "wires": [4, 5], "param": "crz_ring_even"},
    {"gate": "CRZ", "wires": [5, 6], "param": "crz_ring_odd"},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_ring_even"},
    {"gate": "CRZ", "wires": [7, 0], "param": "crz_ring_odd"},

    # --- Single shared-parameter long-range entangler (max-distance pairs on the ring) ---
    {"gate": "CRZ", "wires": [0, 4], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [1, 5], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [2, 6], "param": "crz_shared"},
    {"gate": "CRZ", "wires": [3, 7], "param": "crz_shared"},

    # --- Post-entangling single-qubit phase rotation ---
    {"gate": "RZ", "wire": 0, "param": "rz_post_0"},
    {"gate": "RZ", "wire": 1, "param": "rz_post_1"},
    {"gate": "RZ", "wire": 2, "param": "rz_post_2"},
    {"gate": "RZ", "wire": 3, "param": "rz_post_3"},
    {"gate": "RZ", "wire": 4, "param": "rz_post_3"},
    {"gate": "RZ", "wire": 5, "param": "rz_post_2"},
    {"gate": "RZ", "wire": 6, "param": "rz_post_1"},
    {"gate": "RZ", "wire": 7, "param": "rz_post_0"},

    # --- Final single-qubit RY rotations (readout preparation) ---
    {"gate": "RY", "wire": 0, "param": "ry_final_0"},
    {"gate": "RY", "wire": 1, "param": "ry_final_1"},
    {"gate": "RY", "wire": 2, "param": "ry_final_2"},
    {"gate": "RY", "wire": 3, "param": "ry_final_3"},
    {"gate": "RY", "wire": 4, "param": "ry_final_4"},
    {"gate": "RY", "wire": 5, "param": "ry_final_5"},
    {"gate": "RY", "wire": 6, "param": "ry_final_6"},
    {"gate": "RY", "wire": 7, "param": "ry_final_7"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)