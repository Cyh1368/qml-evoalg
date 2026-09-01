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

# Layer 0: front-loaded long-range ZZ entangling layer on opposite-qubit
# pairs. These four pairs are mutually disjoint, so they execute in a
# single parallel depth-layer. Crucially, this layer REUSES the "a"
# parameter (shared with the very next RX layer) rather than introducing
# a new trainable name, so the distinct-parameter count stays unchanged
# while the classifier gets an early global entangling cue before any
# single-qubit rotation has been applied.
for _i in range(4):
    ANSATZ_SPEC.append({"gate": "ZZ", "wires": [_i, _i + 4], "param": "a"})

# Layer 1: global shared rotation RX(a) on every qubit (same "a" as above).
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": _i, "param": "a"})

# Layer 2: global shared rotation RY(b) on every qubit.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "b"})

# Fixed entangling ring 1 (no parameters), nearest-neighbor connectivity.
for _i in range(N_QUBITS - 1):
    ANSATZ_SPEC.append({"gate": "CNOT", "wires": [_i, _i + 1]})
ANSATZ_SPEC.append({"gate": "CNOT", "wires": [N_QUBITS - 1, 0]})

# Layer 3: global shared rotation RZ(c) on every qubit.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": _i, "param": "c"})

# Cheap parametrized entangling structure: CRZ(d)/CRX(d) mixed-axis gates
# shared across disjoint pairs. Reusing the SAME parameter name "d" for
# both gate types keeps the distinct-parameter count unchanged while
# giving the circuit access to complementary Z- and X-axis controlled
# correlations from a single trainable angle.
for _idx, _i in enumerate(range(0, N_QUBITS, 2)):
    _gate = "CRX" if _idx % 2 == 1 else "CRZ"
    ANSATZ_SPEC.append({"gate": _gate, "wires": [_i, _i + 1], "param": "d"})

# Fixed entangling ring 2, offset to spread information further without
# adding trainable parameters.
for _i in range(1, N_QUBITS, 2):
    _j = (_i + 1) % N_QUBITS
    ANSATZ_SPEC.append({"gate": "CNOT", "wires": [_i, _j]})

# Final global shared rotation RY(e) on every qubit, giving the readout a
# flexible final basis.
for _i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": _i, "param": "e"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)