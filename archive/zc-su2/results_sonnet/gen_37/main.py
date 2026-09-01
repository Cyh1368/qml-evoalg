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

# ---- Sub-block A: tri-axis rotation + dense (ring + antipodal) CZ ----
# 0. RX layer: every qubit shares the SAME single trainable parameter
#    "theta" (extreme parameter sharing).
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": wire, "param": "theta"})

# 1. RY layer: reuse "theta" on a different axis.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "theta"})

# 2. Dense, fixed (parameter-free) entangling layer: nearest-neighbor CZ
#    ring plus antipodal CZ edges, giving every qubit degree-3 connectivity.
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 1) % N_QUBITS]})
for i in range(N_QUBITS // 2):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, i + N_QUBITS // 2]})

# 3. RZ layer: reuse "theta" again, closing sub-block A.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta"})

# ---- Sub-block B: repeat the same rotate-entangle-rotate pattern,
#      still reusing the SAME single "theta" parameter, to increase
#      circuit depth/expressivity at ZERO extra parameter cost. ----
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": wire, "param": "theta"})

for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "theta"})

for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 1) % N_QUBITS]})
for i in range(N_QUBITS // 2):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, i + N_QUBITS // 2]})

for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)