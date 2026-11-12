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

# 2. Fixed (parameter-free) dense entangling layer:
#    (a) closed ring of nearest-neighbor CZ edges (wrap-around) so every
#        qubit entangles with both immediate neighbors, and
#    (b) "diameter" CZ edges connecting each qubit to its antipodal
#        partner (distance 4 on the 8-cycle), giving every qubit one
#        additional long-range entangling partner.
#    This gives every qubit entangling-degree 3 at ZERO extra trainable
#    parameter cost, and previously produced the fastest convergence and
#    lowest validation/test loss among tested designs.
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 1) % N_QUBITS]})
for i in range(N_QUBITS // 2):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, i + N_QUBITS // 2]})

# 3. Parametrized entangling layer on the SAME antipodal pairs, reusing the
#    SAME shared "theta" parameter (no new trainable parameter name is
#    introduced). This injects a non-commuting, tunable entangling
#    interaction reinforcing the fixed long-range connectivity above,
#    without any parameter-count penalty.
for i in range(N_QUBITS // 2):
    ANSATZ_SPEC.append({"gate": "CRZ", "wires": [i, i + N_QUBITS // 2], "param": "theta"})

# 4. Post-entanglement rotation layer, axis RZ, reusing the SAME "theta"
#    parameter, keeping the total unique parameter count per block at
#    exactly 1.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)