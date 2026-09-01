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

# 1. Dual-axis pre-entanglement rotation: ALL 8 qubits share the SAME single
#    trainable parameter "theta" on RX, then again on RY (non-commuting
#    axes). This gives the single shared scalar two effective rotation
#    directions before any entangling gate is applied, borrowed from the
#    fast-converging seed design, without adding any new parameter names.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": wire, "param": "theta"})
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "theta"})

# 2. Cheap, fixed (parameter-free) nearest-neighbor CZ ring backbone —
#    zero trainable parameters, minimal gate count (8 gates), same
#    entangling topology as the low-gate-count / low-loss seed.
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 1) % N_QUBITS]})

# 3. A single small layer of tunable long-range entanglers (antipodal
#    pairs, distance 4 on the 8-cycle), reusing the SAME "theta"
#    parameter. Only 4 extra gates, but injects one non-commuting
#    entangling interaction tied to the trainable scalar, which appeared
#    to help convergence speed in the richer seed.
for i in range(N_QUBITS // 2):
    ANSATZ_SPEC.append({"gate": "CRZ", "wires": [i, i + N_QUBITS // 2], "param": "theta"})

# 4. Post-entanglement rotation layer, axis RZ, reusing the SAME "theta"
#    parameter, closing out the block with a third rotation axis while
#    keeping the total unique parameter count per block at exactly 1.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)