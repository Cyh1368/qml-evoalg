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
    # --- Local expressivity / feature-refresh layer (individual params) ---
    {"gate": "RY", "wire": 0, "param": "ry_0"},
    {"gate": "RY", "wire": 1, "param": "ry_1"},
    {"gate": "RY", "wire": 2, "param": "ry_2"},
    {"gate": "RY", "wire": 3, "param": "ry_3"},
    {"gate": "RY", "wire": 4, "param": "ry_4"},
    {"gate": "RY", "wire": 5, "param": "ry_5"},
    {"gate": "RY", "wire": 6, "param": "ry_6"},
    {"gate": "RY", "wire": 7, "param": "ry_7"},
    {"gate": "RY", "wire": 8, "param": "ry_8"},

    # --- Fixed full-connectivity backbone (zero trainable cost) ---
    # Every physically allowed 2-qubit pair gets a CNOT once, guaranteeing the
    # whole 9-qubit register becomes one connected entangled graph before any
    # parametrized correlation is introduced.
    {"gate": "CNOT", "wires": [0, 2]},
    {"gate": "CNOT", "wires": [0, 3]},
    {"gate": "CNOT", "wires": [0, 7]},
    {"gate": "CNOT", "wires": [0, 8]},
    {"gate": "CNOT", "wires": [1, 3]},
    {"gate": "CNOT", "wires": [1, 8]},
    {"gate": "CNOT", "wires": [2, 4]},
    {"gate": "CNOT", "wires": [2, 6]},
    {"gate": "CNOT", "wires": [3, 5]},
    {"gate": "CNOT", "wires": [4, 8]},
    {"gate": "CNOT", "wires": [5, 7]},
    {"gate": "CNOT", "wires": [6, 7]},

    # --- Heavily-shared parametrized two-body correlation layer ---
    # Same physical edges as the backbone above, but grouped into just 4
    # tunable hub angles instead of 12 independent ones.
    {"gate": "CRZ", "wires": [0, 2], "param": "crz_hub0"},
    {"gate": "CRZ", "wires": [0, 3], "param": "crz_hub0"},
    {"gate": "CRZ", "wires": [0, 7], "param": "crz_hub0"},
    {"gate": "CRZ", "wires": [0, 8], "param": "crz_hub0"},
    {"gate": "CRZ", "wires": [1, 3], "param": "crz_hub1"},
    {"gate": "CRZ", "wires": [1, 8], "param": "crz_hub1"},
    {"gate": "CRZ", "wires": [2, 4], "param": "crz_hub2"},
    {"gate": "CRZ", "wires": [2, 6], "param": "crz_hub2"},
    {"gate": "CRZ", "wires": [3, 5], "param": "crz_rest"},
    {"gate": "CRZ", "wires": [4, 8], "param": "crz_rest"},
    {"gate": "CRZ", "wires": [5, 7], "param": "crz_rest"},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_rest"},

    # --- Explicit three-qubit high-order interactions ---
    # Two CCRZ gates sharing a single angle each capture genuine 3-body
    # correlation across disjoint qubit triples, something no stack of
    # 2-qubit gates can represent without much more depth.
    {"gate": "CCRZ", "wires": [0, 4, 6], "param": "ccrz_a"},
    {"gate": "CCRZ", "wires": [1, 5, 7], "param": "ccrz_a"},
    {"gate": "CCRZ", "wires": [2, 3, 8], "param": "ccrz_b"},

    # A single shared ZZZ term spanning two more disjoint triples adds a
    # further global 3-body phase correlation at only one extra parameter.
    {"gate": "ZZZ", "wires": [0, 1, 2], "param": "zzz_a"},
    {"gate": "ZZZ", "wires": [6, 7, 8], "param": "zzz_a"},

    # --- Final readout-phase layer (individual params) ---
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