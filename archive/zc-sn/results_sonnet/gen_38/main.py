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
    # --- Layer 1: single-qubit RY rotations (per-qubit trainable) ---
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},

    # --- Layer 2: nearest-neighbor ring entanglement with shared alternating strength ---
    {"gate": "CRZ", "wires": [0, 1], "param": "crz_ring_even"},
    {"gate": "CRZ", "wires": [1, 2], "param": "crz_ring_odd"},
    {"gate": "CRZ", "wires": [2, 3], "param": "crz_ring_even"},
    {"gate": "CRZ", "wires": [3, 4], "param": "crz_ring_odd"},
    {"gate": "CRZ", "wires": [4, 5], "param": "crz_ring_even"},
    {"gate": "CRZ", "wires": [5, 6], "param": "crz_ring_odd"},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_ring_even"},
    {"gate": "CRZ", "wires": [7, 0], "param": "crz_ring_odd"},

    # --- Layer 3: single-qubit RX rotations (second rotation axis) ---
    {"gate": "RX", "wire": 0, "param": "rx_0"},
    {"gate": "RX", "wire": 1, "param": "rx_1"},
    {"gate": "RX", "wire": 2, "param": "rx_2"},
    {"gate": "RX", "wire": 3, "param": "rx_3"},
    {"gate": "RX", "wire": 4, "param": "rx_4"},
    {"gate": "RX", "wire": 5, "param": "rx_5"},
    {"gate": "RX", "wire": 6, "param": "rx_6"},
    {"gate": "RX", "wire": 7, "param": "rx_7"},

    # --- Layer 4: sparse skip-2 entanglement with alternating shared parameters ---
    # Splitting the single shared parameter into two alternating ones mirrors the
    # proven benefit of alternating strengths in the ring entangler, giving this
    # long-range layer more expressivity while retaining parameter-efficient
    # regularization through sharing.
    {"gate": "CRZ", "wires": [0, 2], "param": "crz_skip_even"},
    {"gate": "CRY", "wires": [1, 3], "param": "cry_skip_odd"},
    {"gate": "CRZ", "wires": [2, 4], "param": "crz_skip_even"},
    {"gate": "CRY", "wires": [3, 5], "param": "cry_skip_odd"},
    {"gate": "CRZ", "wires": [4, 6], "param": "crz_skip_even"},
    {"gate": "CRY", "wires": [5, 7], "param": "cry_skip_odd"},
    {"gate": "CRZ", "wires": [6, 0], "param": "crz_skip_even"},
    {"gate": "CRY", "wires": [7, 1], "param": "cry_skip_odd"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)