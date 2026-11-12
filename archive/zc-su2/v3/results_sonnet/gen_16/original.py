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

# Layer 1: shared RY rotation applied identically to every qubit.
# Since each qubit carries different input-encoded state, a single shared
# angle still produces qubit-specific effects while using only 1 parameter.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "ry1"})

# Layer 2: shared RZ rotation, again a single parameter for all qubits.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": _i, "param": "rz1"})

# Fixed (parameter-free) nearest-neighbor entangling backbone.
for _i in range(N_QUBITS - 1):
    ANSATZ_SPEC.append({"gate": "CNOT", "wires": [_i, _i + 1]})

# Parametrized entangling layer along the same chain, sharing one angle.
for _i in range(N_QUBITS - 1):
    ANSATZ_SPEC.append({"gate": "CRZ", "wires": [_i, _i + 1], "param": "ent1"})

# Final shared RY rotation to mix entangled amplitudes before readout.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "ry2"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)