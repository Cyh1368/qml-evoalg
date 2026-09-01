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
#    This mirrors the best-scoring seed's extreme parameter reduction.
for wire in range(N_QUBITS):
    group = wire // 4
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": f"p_g{group}"})

# 2. Parametrized nearest-neighbor entangling chain (no wrap-around),
#    using CRZ gates instead of fixed CZ gates. Crucially, the entangling
#    rotation angles REUSE the two existing group parameters (alternating
#    p_g0 / p_g1 along the chain) instead of introducing new parameter
#    names. This injects tunable, data-dependent entanglement strength
#    (an idea borrowed from parametrized two-qubit ansatze) while keeping
#    the total trainable-parameter count fixed at 2 per block, avoiding
#    the convergence/efficiency penalty observed when a genuinely new
#    entangling parameter was added.
for i in range(N_QUBITS - 1):
    group = i % 2
    ANSATZ_SPEC.append({"gate": "CRZ", "wires": [i, i + 1], "param": f"p_g{group}"})

# 3. Post-entanglement rotation layer reusing the SAME 2 parameters as
#    step 1, just on a different axis (RZ), giving the circuit extra
#    expressivity at zero extra parameter cost.
for wire in range(N_QUBITS):
    group = wire // 4
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": f"p_g{group}"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)