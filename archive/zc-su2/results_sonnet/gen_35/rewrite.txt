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

# 0. Pre-entanglement rotation layer, axis RX: ALL 8 qubits share the
#    SAME single trainable scalar "theta". Combined with the RY layer
#    below (different, non-commuting axis) this gives each qubit a
#    genuinely 2D rotation from a single shared scalar, which earlier
#    experiments showed converges markedly faster than a single-axis
#    pre-layer.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": wire, "param": "theta"})

# 1. Pre-entanglement rotation layer, axis RY: same shared scalar "theta".
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "theta"})

# 2a. Fixed nearest-neighbor CZ ring (closed chain), zero trainable
#     parameters, giving local connectivity across the whole register.
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 1) % N_QUBITS]})

# 2b. Parametrized long-range entangler on antipodal pairs (distance 4 on
#     the 8-cycle), reusing the SAME shared scalar "theta" as the
#     rotation layers. Unlike a fixed CZ diameter connection, this CRZ is
#     genuinely trainable (its rotation angle is driven by "theta"),
#     letting the single shared scalar also control long-range
#     entangling strength -- adding expressivity at ZERO extra
#     trainable-parameter cost.
for i in range(N_QUBITS // 2):
    ANSATZ_SPEC.append(
        {"gate": "CRZ", "wires": [i, i + N_QUBITS // 2], "param": "theta"}
    )

# 3. Post-entanglement rotation layer, axis RZ: reuse the SAME shared
#    scalar "theta", keeping the total unique-parameter count per block
#    at exactly 1.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)