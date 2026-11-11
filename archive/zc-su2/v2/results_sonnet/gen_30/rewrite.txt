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
    # ---- Stage 1: local state preparation ----
    # Single shared rotation parameter across all 8 qubits. This is the
    # "leaf" preparation layer before any pooling/entangling happens.
    {"gate": "RY", "wire": 0, "param": "ry_in"},
    {"gate": "RY", "wire": 1, "param": "ry_in"},
    {"gate": "RY", "wire": 2, "param": "ry_in"},
    {"gate": "RY", "wire": 3, "param": "ry_in"},
    {"gate": "RY", "wire": 4, "param": "ry_in"},
    {"gate": "RY", "wire": 5, "param": "ry_in"},
    {"gate": "RY", "wire": 6, "param": "ry_in"},
    {"gate": "RY", "wire": 7, "param": "ry_in"},

    # ---- Stage 2: hierarchical (QCNN-style) pooling tree ----
    # Level 1: couple adjacent leaf pairs. All CRZ gates below reuse a single
    # shared "crz_e" parameter, so the tree adds NO extra trainable names
    # regardless of depth.
    {"gate": "CRZ", "wires": [0, 1], "param": "crz_e"},
    {"gate": "CRZ", "wires": [2, 3], "param": "crz_e"},
    {"gate": "CRZ", "wires": [4, 5], "param": "crz_e"},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_e"},

    # Level 2: couple the "winning" wires from level 1 (1 and 3, 5 and 7),
    # pooling 4 local clusters into 2 medium-range clusters.
    {"gate": "CRZ", "wires": [1, 3], "param": "crz_e"},
    {"gate": "CRZ", "wires": [5, 7], "param": "crz_e"},

    # Level 3: couple the two medium-range aggregators (3 and 7) into a
    # single global aggregator qubit (7), completing the pooling tree with
    # a total of only log2(8) = 3 entangling levels.
    {"gate": "CRZ", "wires": [3, 7], "param": "crz_e"},

    # ---- Stage 3: fixed global fan-out (zero trainable parameters) ----
    # Redistribute the globally-pooled information sitting on aggregator
    # qubit 7 back out to every other qubit, so downstream readout can
    # combine both local (leaf) and global (pooled) structure. This uses
    # only fixed CNOTs, so it costs zero additional trainable parameters
    # no matter how it is wired.
    {"gate": "CNOT", "wires": [7, 0]},
    {"gate": "CNOT", "wires": [7, 1]},
    {"gate": "CNOT", "wires": [7, 2]},
    {"gate": "CNOT", "wires": [7, 3]},
    {"gate": "CNOT", "wires": [7, 4]},
    {"gate": "CNOT", "wires": [7, 5]},
    {"gate": "CNOT", "wires": [7, 6]},

    # ---- Stage 4: final shared rotation for readout preparation ----
    # A single shared parameter tunes how the combined local/global features
    # are mapped onto the measurement basis used by the fixed readout.
    {"gate": "RY", "wire": 0, "param": "ry_out"},
    {"gate": "RY", "wire": 1, "param": "ry_out"},
    {"gate": "RY", "wire": 2, "param": "ry_out"},
    {"gate": "RY", "wire": 3, "param": "ry_out"},
    {"gate": "RY", "wire": 4, "param": "ry_out"},
    {"gate": "RY", "wire": 5, "param": "ry_out"},
    {"gate": "RY", "wire": 6, "param": "ry_out"},
    {"gate": "RY", "wire": 7, "param": "ry_out"},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)