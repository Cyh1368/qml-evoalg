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
def _build_ansatz():
    spec = []

    # Layer 1: parity-shared RY rotation (2 distinct params)
    for wire in range(N_QUBITS):
        param = "ry_even" if wire % 2 == 0 else "ry_odd"
        spec.append({"gate": "RY", "wire": wire, "param": param})

    # Layer 2: parameterized ring entangler, single shared angle (1 distinct param)
    # Connects every qubit to its neighbor in a ring, giving the entangling
    # structure its own trainable strength rather than being purely fixed.
    for i in range(N_QUBITS):
        j = (i + 1) % N_QUBITS
        spec.append({"gate": "CRZ", "wires": [i, j], "param": "crz_ring"})

    # Layer 3: parity-shared RZ rotation (2 distinct params)
    for wire in range(N_QUBITS):
        param = "rz_even" if wire % 2 == 0 else "rz_odd"
        spec.append({"gate": "RZ", "wire": wire, "param": param})

    # Layer 4: fixed CZ ring for additional mixing without adding parameters.
    for i in range(N_QUBITS):
        j = (i + 1) % N_QUBITS
        spec.append({"gate": "CZ", "wires": [i, j]})

    return spec


ANSATZ_SPEC = _build_ansatz()
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)