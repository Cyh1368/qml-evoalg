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
    # Shared noncommuting rotations add expressivity without new parameters.
    {"gate": "RX", "wire": 0, "param": "phase_stitch"},
    {"gate": "RY", "wire": 0, "param": "phase_stitch"},
    {"gate": "RX", "wire": 1, "param": "phase_stitch"},
    {"gate": "RY", "wire": 1, "param": "phase_stitch"},
    {"gate": "RX", "wire": 2, "param": "phase_stitch"},
    {"gate": "RY", "wire": 2, "param": "phase_stitch"},
    {"gate": "RX", "wire": 3, "param": "phase_stitch"},
    {"gate": "RY", "wire": 3, "param": "phase_stitch"},
    {"gate": "RX", "wire": 4, "param": "phase_stitch"},
    {"gate": "RY", "wire": 4, "param": "phase_stitch"},
    {"gate": "RX", "wire": 5, "param": "phase_stitch"},
    {"gate": "RY", "wire": 5, "param": "phase_stitch"},
    {"gate": "RX", "wire": 6, "param": "phase_stitch"},
    {"gate": "RY", "wire": 6, "param": "phase_stitch"},
    {"gate": "RX", "wire": 7, "param": "phase_stitch"},
    {"gate": "RY", "wire": 7, "param": "phase_stitch"},

    # Stable local correlations from the successful parallel matching.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [6, 7]},

    # Complementary matching joins the local pairs into a connected ring.
    # Reusing the collective angle adds tunable phase correlations without
    # introducing another independent parameter.
    {"gate": "CRZ", "wires": [1, 2], "param": "phase_stitch"},
    {"gate": "CRZ", "wires": [3, 4], "param": "phase_stitch"},
    {"gate": "CRZ", "wires": [5, 6], "param": "phase_stitch"},
    {"gate": "CRZ", "wires": [7, 0], "param": "phase_stitch"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)