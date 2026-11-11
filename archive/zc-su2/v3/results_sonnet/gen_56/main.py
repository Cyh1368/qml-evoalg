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

# Layer 0: alternating-parity RY rotations. Even qubits share "ry_a",
# odd qubits share "ry_b". This lets the classifier separately calibrate
# the two qubit groups with only two parameters.
for _i in range(0, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "ry_a"})
for _i in range(1, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "ry_b"})

# Fixed forward entangling chain (no parameters), nearest-neighbor
# connectivity, spreading information across all qubits.
for _i in range(N_QUBITS - 1):
    ANSATZ_SPEC.append({"gate": "CNOT", "wires": [_i, _i + 1]})

# Layer 1: alternating-parity RZ rotations, analogous to layer 0 but in
# the Z basis, reusing the same even/odd grouping idea with new names.
for _i in range(0, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": _i, "param": "rz_a"})
for _i in range(1, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": _i, "param": "rz_b"})

# Fixed backward entangling chain (no parameters), reversing direction to
# mix information the other way without adding trainable parameters.
for _i in range(N_QUBITS - 1, 0, -1):
    ANSATZ_SPEC.append({"gate": "CNOT", "wires": [_i, _i - 1]})

# Cheap parametrized entangling structure, split into two group-specific
# entanglers instead of one fully-shared parameter: even-indexed disjoint
# pairs share "ent_e", odd-indexed disjoint pairs share "ent_o". This is a
# zero-depth mutation (same gate count and depth) that gives finer-grained
# control over even vs. odd neighbor correlations.
ANSATZ_SPEC.append({"gate": "CRZ", "wires": [0, 1], "param": "ent_e"})
ANSATZ_SPEC.append({"gate": "CRZ", "wires": [4, 5], "param": "ent_e"})
ANSATZ_SPEC.append({"gate": "CRZ", "wires": [2, 3], "param": "ent_o"})
ANSATZ_SPEC.append({"gate": "CRZ", "wires": [6, 7], "param": "ent_o"})

# Final global shared rotation RY(ry_c) on every qubit, giving the
# readout a flexible final basis.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "ry_c"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)