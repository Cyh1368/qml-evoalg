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

# Fixed (parameter-free) skip-2 entangling backbone: two interleaved rings
# that connect qubits two apart, giving longer-range mixing than a simple
# nearest-neighbor chain while remaining parameter-free.
for _i in [0, 2, 4, 6]:
    ANSATZ_SPEC.append({"gate": "CNOT", "wires": [_i, (_i + 2) % N_QUBITS]})
for _i in [1, 3, 5, 7]:
    ANSATZ_SPEC.append({"gate": "CNOT", "wires": [_i, (_i + 2) % N_QUBITS]})

# Fixed (parameter-free) backward CZ ladder to add further entangling
# connectivity in the reverse direction using phase-type gates, which tend
# to be more robust to bit-flip noise than CNOT chains. No new trainable
# parameters are introduced.
for _i in range(N_QUBITS - 1, 0, -1):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [_i, _i - 1]})

# Parametrized entangling layer along the same chain, split into two shared
# angles alternating by edge parity for finer-grained phase control.
for _i in range(N_QUBITS - 1):
    _p = "ent1a" if _i % 2 == 0 else "ent1b"
    ANSATZ_SPEC.append({"gate": "CRZ", "wires": [_i, _i + 1], "param": _p})

# Final shared RY rotation to mix entangled amplitudes before readout.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "ry2"})

# Concluding disjoint ZZ-Ising output layer: a single shared parameter
# coupling adjacent qubit pairs right before readout. This harnesses
# residual phase correlations post-rotation to sharpen decision margins,
# at the cost of only one additional trainable parameter.
ANSATZ_SPEC.append({"gate": "ZZ", "wires": [0, 1], "param": "zz_out"})
ANSATZ_SPEC.append({"gate": "ZZ", "wires": [2, 3], "param": "zz_out"})
ANSATZ_SPEC.append({"gate": "ZZ", "wires": [4, 5], "param": "zz_out"})
ANSATZ_SPEC.append({"gate": "ZZ", "wires": [6, 7], "param": "zz_out"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)