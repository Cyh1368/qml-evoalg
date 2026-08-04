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

# Layer 0: seed long-range correlations FIRST, before any local rotations.
# A single shared CRZ(g) parameter connects each qubit to its "opposite"
# partner across the register (distance 4). This is a disjoint (non-
# overlapping) set of pairs, so the four gates act in parallel on all
# 8 qubits, injecting global structure early -- before local single-qubit
# rotations and nearest-neighbor entanglers refine it. This follows the
# empirical pattern that disjoint nonlocal gates applied early tend to
# improve generalization more than the same gates applied late.
for _i in range(4):
    ANSATZ_SPEC.append({"gate": "CRZ", "wires": [_i, _i + 4], "param": "g"})

# Layer 1: shared global RX rotation (1 parameter, acts differently per
# qubit because each qubit's input encoding differs).
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": _i, "param": "a"})

# Layer 2: shared global RY rotation (1 parameter).
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "b"})

# Layer 3: a single fixed (parameter-free) nearest-neighbor entangling ring.
# Kept to a single ring (not doubled) to limit model capacity and reduce
# the train/validation gap observed when using denser local backbones.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CNOT", "wires": [_i, (_i + 1) % N_QUBITS]})

# Layer 4: parametrized nonlocal mixing along the chain, one shared
# parameter reused across all links -- adds expressivity without growing
# the parameter count.
for _i in range(N_QUBITS - 1):
    ANSATZ_SPEC.append({"gate": "CRZ", "wires": [_i, _i + 1], "param": "d"})

# Layer 5: final rotation reuses the SAME parameter "b" as layer 2 instead
# of introducing a new one. This keeps the total distinct parameter count
# at 4 (g, a, b, d) while still providing a post-entanglement rotation
# that helps align the entangled amplitudes with the readout basis.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "b"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)