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

# 1. Coarse-grained RY rotation layer: 8 qubits split into 2 halves,
#    sharing a single trainable parameter per half (2 unique params total).
for wire in range(N_QUBITS):
    group = wire // 4
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": f"p_g{group}"})

# 2. Fixed nearest-neighbor CZ entangling chain (no wrap-around), zero
#    extra trainable parameters, providing full connectivity across the
#    register at minimal depth/gate cost.
for i in range(N_QUBITS - 1):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, i + 1]})

# 2b. Fixed 2-skip "twisted" ring of CZ gates, adding extra non-local
#     entangling loops with zero additional trainable parameters. This
#     probes whether richer connectivity improves expressivity/score
#     while keeping the parameter count identical.
for a, b in [(0, 2), (2, 4), (4, 6), (6, 0)]:
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [a, b]})

# 3. Post-entanglement rotation layer reusing the SAME parameter names as
#    step 1 (same 2 unique parameters), just on a different axis (RZ),
#    giving the circuit extra expressivity at zero extra parameter cost.
for wire in range(N_QUBITS):
    group = wire // 4
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": f"p_g{group}"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)