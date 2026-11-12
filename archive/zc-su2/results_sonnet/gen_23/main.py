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

# 1. Pre-entanglement RY layer: ALL 8 qubits share a SINGLE trainable
#    parameter "p_shared". This is the most extreme collapse of rotation
#    parameters explored so far (previous best designs used 2 unique
#    parameter names per block; this uses just 1).
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "p_shared"})

# 2. Fixed entangling layer: CLOSED RING of CZ gates (nearest-neighbor
#    chain plus a wrap-around edge connecting qubit 7 back to qubit 0).
#    Zero extra trainable parameters, but every qubit now has exactly two
#    entangling neighbours, compensating for the reduced rotation
#    parameter budget by shortening the effective mixing distance around
#    the register compared to an open chain.
for i in range(N_QUBITS - 1):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, i + 1]})
ANSATZ_SPEC.append({"gate": "CZ", "wires": [N_QUBITS - 1, 0]})

# 3. Post-entanglement RZ layer reusing the SAME single parameter name
#    "p_shared" as step 1 (different axis, so the single parameter still
#    drives a non-trivial entangled transformation), keeping the total
#    unique-parameter count per block at exactly 1.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "p_shared"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)