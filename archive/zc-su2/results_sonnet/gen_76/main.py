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

# 0. Pre-entanglement rotation layer, axis RX: ALL 8 qubits share the SAME
#    single trainable parameter "theta". Combined with the RY layer below
#    (different, non-commuting axis, no entangler in between) this gives a
#    richer per-qubit rotation while keeping only ONE trainable parameter
#    for the entire block.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": wire, "param": "theta"})

# 1. Pre-entanglement rotation layer, axis RY, reusing the SAME "theta".
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "theta"})

# 2. Nearest-neighbor ring, alternating between a parametrized XX
#    interaction and a parametrized CRX interaction, BOTH reusing the
#    SAME shared "theta" parameter (no new trainable name introduced).
#    Unlike the earlier design that used a fixed, zero-parameter CZ on
#    the odd edges, every edge of this ring is now tunable and
#    non-commuting with its rotation-layer neighbors, giving richer
#    entangling dynamics for the same single-parameter budget.
for i in range(N_QUBITS):
    a, b = i, (i + 1) % N_QUBITS
    if i % 2 == 0:
        ANSATZ_SPEC.append({"gate": "XX", "wires": [a, b], "param": "theta"})
    else:
        ANSATZ_SPEC.append({"gate": "CRX", "wires": [a, b], "param": "theta"})

# 3. Lightweight, zero-parameter skip-2 sub-ring (0-2, 2-4, 4-6, 6-0) for
#    extra local connectivity beyond nearest neighbors. This was shown to
#    materially speed up convergence in prior experiments at zero extra
#    parameter cost.
for i in range(0, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 2) % N_QUBITS]})

# 4. Fixed, zero-parameter antipodal shortcuts (distance-4 on the
#    8-cycle) for long-range connectivity. Kept lightweight (only 4
#    gates) to minimize depth/gate-count while preserving global
#    connectivity across the register.
for i in range(N_QUBITS // 2):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, i + N_QUBITS // 2]})

# 5. Post-entanglement rotation layer, axis RZ, reusing the SAME "theta"
#    parameter, keeping the total unique parameter count per block at
#    exactly 1.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)