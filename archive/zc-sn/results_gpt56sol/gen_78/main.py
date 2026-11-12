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
    # Parity-shared local adaptation reduces excess capacity while retaining
    # distinct transformations for the two sublattices.
    {"gate": "RY", "wire": 0, "param": "ry_in_even"},
    {"gate": "RY", "wire": 1, "param": "ry_in_odd"},
    {"gate": "RY", "wire": 2, "param": "ry_in_even"},
    {"gate": "RY", "wire": 3, "param": "ry_in_odd"},
    {"gate": "RY", "wire": 4, "param": "ry_in_even"},
    {"gate": "RY", "wire": 5, "param": "ry_in_odd"},
    {"gate": "RY", "wire": 6, "param": "ry_in_even"},
    {"gate": "RY", "wire": 7, "param": "ry_in_odd"},

    # Parity-shared phase layer for parameter-efficient regularization.
    {"gate": "RZ", "wire": 0, "param": "rz_pre_even"},
    {"gate": "RZ", "wire": 1, "param": "rz_pre_odd"},
    {"gate": "RZ", "wire": 2, "param": "rz_pre_even"},
    {"gate": "RZ", "wire": 3, "param": "rz_pre_odd"},
    {"gate": "RZ", "wire": 4, "param": "rz_pre_even"},
    {"gate": "RZ", "wire": 5, "param": "rz_pre_odd"},
    {"gate": "RZ", "wire": 6, "param": "rz_pre_even"},
    {"gate": "RZ", "wire": 7, "param": "rz_pre_odd"},

    # Trainable full-chain propagation is applied before the longer-range
    # ring, with parity sharing limiting the parameter cost.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CRZ", "wires": [0, 1], "param": "crz_chain_even"},
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CRZ", "wires": [1, 2], "param": "crz_chain_odd"},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CRZ", "wires": [2, 3], "param": "crz_chain_even"},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CRZ", "wires": [3, 4], "param": "crz_chain_odd"},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CRZ", "wires": [4, 5], "param": "crz_chain_even"},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CRZ", "wires": [5, 6], "param": "crz_chain_odd"},
    {"gate": "CZ", "wires": [6, 7]},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_chain_even"},

    # Noncommuting mixer converts chain correlations into populations before
    # the second phase-conditioned entangler block.
    {"gate": "RY", "wire": 0, "param": "ry_mid_even"},
    {"gate": "RY", "wire": 1, "param": "ry_mid_odd"},
    {"gate": "RY", "wire": 2, "param": "ry_mid_even"},
    {"gate": "RY", "wire": 3, "param": "ry_mid_odd"},
    {"gate": "RY", "wire": 4, "param": "ry_mid_even"},
    {"gate": "RY", "wire": 5, "param": "ry_mid_odd"},
    {"gate": "RY", "wire": 6, "param": "ry_mid_even"},
    {"gate": "RY", "wire": 7, "param": "ry_mid_odd"},

    {"gate": "RZ", "wire": 0, "param": "rz_ring_even"},
    {"gate": "RZ", "wire": 1, "param": "rz_ring_odd"},
    {"gate": "RZ", "wire": 2, "param": "rz_ring_even"},
    {"gate": "RZ", "wire": 3, "param": "rz_ring_odd"},
    {"gate": "RZ", "wire": 4, "param": "rz_ring_even"},
    {"gate": "RZ", "wire": 5, "param": "rz_ring_odd"},
    {"gate": "RZ", "wire": 6, "param": "rz_ring_even"},
    {"gate": "RZ", "wire": 7, "param": "rz_ring_odd"},

    # Distance-two trainable ring supplies longer-range correlations only
    # after nearest-neighbor information has propagated through the chain.
    {"gate": "CZ", "wires": [0, 2]},
    {"gate": "CRZ", "wires": [0, 2], "param": "crz_ring_even"},
    {"gate": "CZ", "wires": [1, 3]},
    {"gate": "CRZ", "wires": [1, 3], "param": "crz_ring_odd"},
    {"gate": "CZ", "wires": [2, 4]},
    {"gate": "CRZ", "wires": [2, 4], "param": "crz_ring_even"},
    {"gate": "CZ", "wires": [3, 5]},
    {"gate": "CRZ", "wires": [3, 5], "param": "crz_ring_odd"},
    {"gate": "CZ", "wires": [4, 6]},
    {"gate": "CRZ", "wires": [4, 6], "param": "crz_ring_even"},
    {"gate": "CZ", "wires": [5, 7]},
    {"gate": "CRZ", "wires": [5, 7], "param": "crz_ring_odd"},
    {"gate": "CZ", "wires": [6, 0]},
    {"gate": "CRZ", "wires": [6, 0], "param": "crz_ring_even"},
    {"gate": "CZ", "wires": [7, 1]},
    {"gate": "CRZ", "wires": [7, 1], "param": "crz_ring_odd"},

    # Final population mixer exposes both entangler blocks to the readout.
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