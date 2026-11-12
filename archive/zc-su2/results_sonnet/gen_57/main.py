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

# 0. Pre-entanglement rotation, axis RX: ALL 8 qubits share ONE trainable
#    parameter "theta_r" dedicated exclusively to single-qubit rotation
#    degrees of freedom (decoupled from the entangling parameter below).
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": wire, "param": "theta_r"})

# 1. Second rotation axis (RY), reusing the SAME "theta_r". RX then RY
#    with the same angle is a genuinely non-trivial 2D rotation since the
#    two axes do not commute, at zero extra parameter cost.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "theta_r"})

# 2. Fixed nearest-neighbor CZ ring (closed chain) for baseline
#    connectivity. Zero trainable parameters -- purely structural
#    entanglement, kept lightweight (only N_QUBITS gates).
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 1) % N_QUBITS]})

# 3. A single parametrized long-range entangling sweep (CRZ at distance
#    2), using a SEPARATE shared parameter "theta_e". This decouples the
#    "how much do we entangle" knob from the "how do we rotate each
#    qubit" knob, giving the optimizer independent control over each
#    aspect while still keeping only 2 unique parameter names per block
#    repetition (down from heavier multi-layer entangling stacks used in
#    earlier variants).
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CRZ", "wires": [i, (i + 2) % N_QUBITS], "param": "theta_e"})

# 4. Post-entanglement rotation, axis RZ, reusing "theta_r" to complete an
#    all-three-axis single-qubit rotation basis built from exactly the
#    rotation-dedicated scalar.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta_r"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)