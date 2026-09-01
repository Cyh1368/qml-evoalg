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
#    single trainable parameter "theta1".
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": wire, "param": "theta1"})

# 1. Pre-entanglement rotation layer, axis RY, reusing the SAME "theta1".
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "theta1"})

# 2. Fixed nearest-neighbor CZ ring (closed chain), zero trainable
#    parameters, giving local connectivity across the whole register.
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 1) % N_QUBITS]})

# 3. Parametrized long-range entangler on antipodal pairs (distance 4 on
#    the 8-cycle), using a SECOND shared parameter "theta2", independent
#    from the rotation-layer parameter "theta1". This decouples local
#    rotation strength from long-range entangling strength while keeping
#    the total unique-parameter count per block at exactly 2.
for i in range(N_QUBITS // 2):
    ANSATZ_SPEC.append(
        {"gate": "CRZ", "wires": [i, i + N_QUBITS // 2], "param": "theta2"}
    )

# 4. Post-entanglement rotation layer, axis RZ, reusing the SAME "theta1"
#    parameter, keeping the total unique parameter count per block at
#    exactly 2 ("theta1", "theta2").
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta1"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)