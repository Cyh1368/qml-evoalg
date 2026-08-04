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

# 0. Pre-pre-entanglement rotation layer: ALL 8 qubits share the SAME
#    single trainable parameter "theta" but on the RX axis. Combined with
#    the RY layer below (different axis, no entangling gate in between),
#    this realizes a richer single-qubit rotation (spanning two
#    non-commuting axes) per qubit while still using only ONE trainable
#    parameter overall. This restores the fast-convergence benefit
#    observed when three rotation axes (RX, RY, RZ) all share one scalar.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": wire, "param": "theta"})

# 1. Pre-entanglement RY layer: ALL 8 qubits share the SAME single
#    trainable parameter "theta" as step 0.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "theta"})

# 2a. Fixed nearest-neighbor CZ ring (closed chain), zero trainable
#     parameters. Every qubit entangles with its immediate neighbours.
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 1) % N_QUBITS]})

# 2b. Fixed "skip-2" CZ ring layered on top of the nearest-neighbor ring,
#     still zero extra trainable parameters. This adds non-local
#     entangling loops (qubit i with qubit i+2), forming a dual-ring
#     topology that improved validation/test loss in the previous
#     generation, while keeping the total unique-parameter count at 1.
for i in range(0, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 2) % N_QUBITS]})

# 3. Post-entanglement RZ layer reusing the SAME single parameter name
#    "theta" as steps 0-1 (different axis), so the single scalar still
#    drives a non-trivial entangled transformation across three
#    non-commuting rotation axes, keeping the total unique-parameter
#    count per block at exactly 1.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)