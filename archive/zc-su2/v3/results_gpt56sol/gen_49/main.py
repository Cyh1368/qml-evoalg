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
    # A single shared parameter regularizes the small-data model while the
    # alternating axes provide complementary transformations by wire parity.
    {"gate": "RY", "wire": 0, "param": "shared_mix"},
    {"gate": "RX", "wire": 1, "param": "shared_mix"},
    {"gate": "RY", "wire": 2, "param": "shared_mix"},
    {"gate": "RX", "wire": 3, "param": "shared_mix"},
    {"gate": "RY", "wire": 4, "param": "shared_mix"},
    {"gate": "RX", "wire": 5, "param": "shared_mix"},
    {"gate": "RY", "wire": 6, "param": "shared_mix"},
    {"gate": "RX", "wire": 7, "param": "shared_mix"},

    # First local brickwork entangling layer.
    {"gate": "CZ", "wires": [0, 1]},
    {"gate": "CZ", "wires": [2, 3]},
    {"gate": "CZ", "wires": [4, 5]},
    {"gate": "CZ", "wires": [6, 7]},

    # Refresh the local bases between entangling stages. Sharing the original
    # angle increases expressivity without increasing the parameter count.
    {"gate": "RY", "wire": 0, "param": "shared_mix"},
    {"gate": "RX", "wire": 1, "param": "shared_mix"},
    {"gate": "RY", "wire": 2, "param": "shared_mix"},
    {"gate": "RX", "wire": 3, "param": "shared_mix"},
    {"gate": "RY", "wire": 4, "param": "shared_mix"},
    {"gate": "RX", "wire": 5, "param": "shared_mix"},
    {"gate": "RY", "wire": 6, "param": "shared_mix"},
    {"gate": "RX", "wire": 7, "param": "shared_mix"},

    # Staggered ring links propagate the refreshed features across partitions.
    {"gate": "CZ", "wires": [1, 2]},
    {"gate": "CZ", "wires": [3, 4]},
    {"gate": "CZ", "wires": [5, 6]},
    {"gate": "CZ", "wires": [7, 0]},

    # Antipodal links complete global communication at no parameter cost.
    {"gate": "CZ", "wires": [0, 4]},
    {"gate": "CZ", "wires": [1, 5]},
    {"gate": "CZ", "wires": [2, 6]},
    {"gate": "CZ", "wires": [3, 7]},
]
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)