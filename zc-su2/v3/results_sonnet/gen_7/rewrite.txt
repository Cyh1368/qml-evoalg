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

# Layer 1: shared single-qubit rotation combo (RY then RZ) with the SAME
# scalar parameter "a" reused across both rotation axes. This gives a
# richer single-qubit unitary (two-axis rotation) at zero extra parameter
# cost, since the trainable value is shared.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "a"})
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": _i, "param": "a"})

# Fixed (parameter-free) forward entangling chain to seed connectivity
# before the parametrized entangler acts.
for _i in range(N_QUBITS - 1):
    ANSATZ_SPEC.append({"gate": "CNOT", "wires": [_i, _i + 1]})

# Layer 2: parametrized ring entangler (shared parameter "b") connecting
# every qubit to its neighbor, INCLUDING the wrap-around edge (7 -> 0).
# A full ring gives more uniform, order-independent entanglement coverage
# than an open chain, which should help the hardest validation groups.
for _i in range(N_QUBITS):
    _j = (_i + 1) % N_QUBITS
    ANSATZ_SPEC.append({"gate": "CRZ", "wires": [_i, _j], "param": "b"})

# Layer 3: second shared single-qubit rotation combo with a different
# scalar "c", again reused across both RY and RZ axes.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "c"})
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": _i, "param": "c"})

# Fixed reversed-direction entangling chain after the rotation layer, to
# further mix amplitudes without adding any trainable parameters.
for _i in range(N_QUBITS - 1, 0, -1):
    ANSATZ_SPEC.append({"gate": "CNOT", "wires": [_i, _i - 1]})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)