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
ANSATZ_SPEC = []

# 1. Grouped RY rotation layer: 8 qubits split into 4 groups of 2, sharing
#    a single trainable parameter per group (4 unique params total).
for wire in range(N_QUBITS):
    group = wire % 4
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": f"ry_g{group}"})

# 2. Fixed full-ring CZ entangler (zero extra trainable parameters), mixing
#    all qubits including wrap-around coupling (7 -> 0).
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 1) % N_QUBITS]})

# 3. Grouped RZ rotation layer, again 4 unique params shared across groups.
for wire in range(N_QUBITS):
    group = wire % 4
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": f"rz_g{group}"})

# 4. Shared controlled-rotation ring: a single trainable "entanglement
#    strength" parameter used across every neighboring pair on the ring.
for i in range(N_QUBITS):
    ANSATZ_SPEC.append(
        {"gate": "CRZ", "wires": [i, (i + 1) % N_QUBITS], "param": "crz_shared"}
    )
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)