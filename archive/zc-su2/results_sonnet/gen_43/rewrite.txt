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

# 0. Pre-entanglement two-axis rotation: ALL 8 qubits share a SINGLE
#    trainable parameter "theta" for the RX axis, giving a rich per-qubit
#    rotation basis while contributing zero extra trainable parameters.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": wire, "param": "theta"})

# 1. Second axis (RY) reusing the SAME shared parameter "theta". Because
#    RX and RY do not commute, chaining them with the same angle still
#    yields a genuinely 2D single-qubit rotation, not a trivial identity.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "theta"})

# 2. Fixed, parameter-free entangling backbone:
#    (a) nearest-neighbor CZ ring (wrap-around), giving every qubit degree 2
#        in the entangling graph at minimal gate cost;
#    (b) antipodal "diameter" CZ edges, giving every qubit one additional
#        long-range partner (degree 3 total).
#    This provides strong, well-distributed connectivity with zero
#    trainable-parameter cost.
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 1) % N_QUBITS]})
for i in range(N_QUBITS // 2):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, i + N_QUBITS // 2]})

# 3. A single shallow parametrized entangling layer (CRZ) on qubits offset
#    by 2, reusing the SAME shared "theta" parameter. This adds a
#    non-commuting, parametrized long-range interaction that boosts
#    circuit expressivity without introducing any new trainable
#    parameters, while staying shallow (only N_QUBITS extra gates) to keep
#    depth and convergence time low.
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CRZ", "wires": [i, (i + 2) % N_QUBITS], "param": "theta"})

# 4. Post-entanglement rotation reusing the SAME single shared parameter
#    "theta" (third axis, RZ), completing an all-three-axis single-qubit
#    rotation basis built from exactly one trainable angle per block
#    repetition.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)