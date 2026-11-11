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
    # --- Encoding layer: individual RY rotations ---
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},
    {"gate": "RY", "wire": 8, "param": "ry_8"},

    # --- Entangling layer: full parametrized CRZ over all allowed pairs ---
    # (proven best-performing backbone; light deliberate sharing keeps
    # parameter count efficient while preserving symmetric expressivity)
    {"gate": "CRZ", "wires": [0, 2], "param": "crz_0"},
    {"gate": "CRZ", "wires": [0, 3], "param": "crz_1"},
    {"gate": "CRZ", "wires": [0, 7], "param": "crz_2"},
    {"gate": "CRZ", "wires": [0, 8], "param": "crz_2"},
    {"gate": "CRZ", "wires": [1, 3], "param": "crz_3"},
    {"gate": "CRZ", "wires": [1, 8], "param": "crz_3"},
    {"gate": "CRZ", "wires": [2, 4], "param": "crz_4"},
    {"gate": "CRZ", "wires": [2, 6], "param": "crz_4"},
    {"gate": "CRZ", "wires": [3, 5], "param": "crz_5"},
    {"gate": "CRZ", "wires": [4, 8], "param": "crz_9"},
    {"gate": "CRZ", "wires": [5, 7], "param": "crz_10"},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_11"},

    # --- Mid-layer amplitude refresh: RY on high-connectivity qubits ---
    # Targets qubits 1, 3, 5, 7, each touching 2-3 entangling edges above,
    # giving the readout layer a locally-refreshed feature before the
    # final phase rotations.
    {"gate": "RY", "wire": 1, "param": "ry_mid_1"},
    {"gate": "RY", "wire": 3, "param": "ry_mid_3"},
    {"gate": "RY", "wire": 5, "param": "ry_mid_5"},
    {"gate": "RY", "wire": 7, "param": "ry_mid_7"},

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