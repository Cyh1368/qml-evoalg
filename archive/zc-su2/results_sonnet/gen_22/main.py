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

# 1. Pre-entanglement rotation layer: ALL 8 qubits driven by a SINGLE shared
#    parameter ("theta"). This is the maximal collapse of the group-of-2 /
#    group-of-4 sharing schemes explored previously, minimizing parameter
#    count while still allowing a globally-tunable rotation amplitude.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "theta"})

# 2. Fixed nearest-neighbor CZ entangling chain (no wrap-around edge).
#    Zero extra trainable parameters. This topology previously converged
#    in ~30 steps (vs ~150 for a closed ring) at identical accuracy, and
#    has lower depth/gate-count, so it is kept as the entangling backbone.
for i in range(N_QUBITS - 1):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, i + 1]})

# 3. Post-entanglement rotation layer reusing the SAME single parameter
#    ("theta") on a different axis (RZ). Sharing across both layers means
#    the entire ansatz block is driven by just one trainable number per
#    repetition, maximizing parameter economy while the fixed entangling
#    chain still provides the necessary qubit-qubit correlations.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)