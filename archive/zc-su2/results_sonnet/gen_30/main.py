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

# 1. First rotation layer (RY) on all qubits, sharing a SINGLE trainable
#    scalar parameter "theta" -- the maximal parameter-economy choice
#    validated by the highest-scoring prior generation (n_params=8,
#    score=0.80).
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "theta"})

# 2. Fixed nearest-neighbor entangling ring (distance-1, wrap-around).
#    Zero extra trainable parameters.
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 1) % N_QUBITS]})

# 3. Second rotation layer (RZ), reusing the SAME "theta" parameter on a
#    different axis -- adds expressivity at zero extra parameter cost.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta"})

# 4. Fixed antipodal "diameter" entangling layer (distance-4 pairs),
#    giving every qubit a long-range partner. Zero extra parameters.
for i in range(N_QUBITS // 2):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, i + N_QUBITS // 2]})

# 5. Third rotation layer (RX), again reusing the SAME "theta" parameter,
#    completing a full 3-axis rotation cycle driven by one scalar per
#    block repetition, maximizing expressivity-per-parameter.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": wire, "param": "theta"})

# 6. Fixed "skip-2" twisted entangling ring (distance-2 pairs), adding a
#    third independent entangling topology for near-all-to-all coverage
#    across the register, again at zero trainable-parameter cost.
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 2) % N_QUBITS]})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)