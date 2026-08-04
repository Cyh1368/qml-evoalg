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

# Input encoding layer: alternating shared RY angle for even/odd qubits.
# Only 2 parameters, but qubit-specific input encoding still makes the
# resulting states differ across qubits.
for _i in range(N_QUBITS):
    _p = "ry_even" if _i % 2 == 0 else "ry_odd"
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": _p})

# Shared RZ phase before entangling.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": _i, "param": "rz_pre"})

# Entangling ring (nearest-neighbor, including wraparound 7-0) with a single
# shared parameter.
for _i in range(N_QUBITS):
    _j = (_i + 1) % N_QUBITS
    ANSATZ_SPEC.append({"gate": "CRZ", "wires": [_i, _j], "param": "ent"})

# Second entangling layer with skip-2 connectivity, reusing the SAME shared
# parameter to increase entanglement depth/connectivity without adding any
# new trainable parameters.
for _i in range(N_QUBITS):
    _j = (_i + 2) % N_QUBITS
    ANSATZ_SPEC.append({"gate": "CRZ", "wires": [_i, _j], "param": "ent"})

# Final shared RZ phase to mix entangled amplitudes before readout.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": _i, "param": "rz_post"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)