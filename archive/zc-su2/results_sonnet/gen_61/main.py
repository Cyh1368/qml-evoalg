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
#    single trainable parameter "theta".
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": wire, "param": "theta"})

# 1. Pre-entanglement rotation layer, axis RY, reusing the SAME "theta".
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "theta"})

# 2a. Nearest-neighbor ring, alternating between a fixed CZ and a
#     parametrized XX interaction that REUSES the same shared "theta"
#     parameter. Non-commuting, tunable entangling interaction without a
#     new trainable parameter name.
for i in range(N_QUBITS):
    a, b = i, (i + 1) % N_QUBITS
    if i % 2 == 0:
        ANSATZ_SPEC.append({"gate": "XX", "wires": [a, b], "param": "theta"})
    else:
        ANSATZ_SPEC.append({"gate": "CZ", "wires": [a, b]})

# 2b. Skip-2 sub-ring linking every other qubit (0-2, 2-4, 4-6, 6-0), now
#     parametrized with a CRY gate sharing a SINGLE new parameter
#     "theta_e" across all four links. This boosts local expressivity in
#     the lightweight skip-2 topology while introducing only one extra
#     trainable parameter name per block.
for i in range(0, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "CRY", "wires": [i, (i + 2) % N_QUBITS], "param": "theta_e"})

# 2c. Fixed, zero-parameter antipodal shortcuts (distance-4 on the
#     8-cycle) for long-range connectivity.
for i in range(N_QUBITS // 2):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, i + N_QUBITS // 2]})

# 3. Post-entanglement rotation layer, axis RZ, reusing the SAME "theta"
#    parameter, keeping the total unique parameter count per block at
#    exactly 2 ("theta" and "theta_e").
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)