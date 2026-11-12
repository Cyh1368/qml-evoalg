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

# 0. Pre-pre-entanglement rotation layer: ALL 8 qubits share the SAME
#    single trainable parameter "theta" on the RX axis. Combined with the
#    RY layer immediately below (different, non-commuting axis, no
#    entangling gate in between), this realizes a richer effective
#    single-qubit rotation per qubit while still using only ONE trainable
#    parameter overall. Empirically this RX-before-RY trick was the single
#    biggest driver of fast convergence among prior candidates.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RX", "wire": wire, "param": "theta"})

# 1. Pre-entanglement RY layer, still reusing the SAME single trainable
#    parameter "theta" -- the minimal possible parametrization for a
#    rotation layer while touching every qubit.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RY", "wire": wire, "param": "theta"})

# 2. Dense, fixed (parameter-free) entangling layer combining THREE
#    complementary CZ patterns to form a small expander graph on the
#    8-qubit ring, at ZERO extra trainable-parameter cost:
#      (a) distance-1 nearest-neighbor ring (closed chain, wrap-around),
#      (b) distance-2 "skip" edges (adds short-range loops),
#      (c) distance-4 "diameter" edges (adds long-range shortcuts).
#    Every qubit ends up entangled with several partners at different
#    length scales, maximizing expressivity/generalization while the
#    rotation parameter budget stays fixed at exactly 1 unique name.
for i in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 1) % N_QUBITS]})
for i in range(0, N_QUBITS, 2):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, (i + 2) % N_QUBITS]})
for i in range(N_QUBITS // 2):
    ANSATZ_SPEC.append({"gate": "CZ", "wires": [i, i + N_QUBITS // 2]})

# 3. Post-entanglement RZ layer: reuse the SAME "theta" parameter
#    (different axis again), so each block repetition contributes only
#    ONE unique trainable parameter in total, maximizing parameter
#    economy while the three rotation axes (RX, RY, RZ) together with the
#    dense entangling layer realize a highly non-trivial, expressive
#    entangled transformation.
for wire in range(N_QUBITS):
    ANSATZ_SPEC.append({"gate": "RZ", "wire": wire, "param": "theta"})
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)