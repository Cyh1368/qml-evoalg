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


def _add_tri_axis_dense_block(spec):
    # Pre-entanglement rotation layer: ALL 8 qubits share the SAME single
    # trainable parameter "theta" on the RX axis.
    for wire in range(N_QUBITS):
        spec.append({"gate": "RX", "wire": wire, "param": "theta"})

    # Pre-entanglement rotation layer: ALL 8 qubits share the SAME single
    # trainable parameter "theta" on the RY axis.
    for wire in range(N_QUBITS):
        spec.append({"gate": "RY", "wire": wire, "param": "theta"})

    # Dense, fixed (parameter-free) entangling layer combining a closed
    # nearest-neighbor CZ ring plus antipodal CZ edges, giving every qubit
    # degree 3 in the entangling graph with zero extra trainable
    # parameters.
    for i in range(N_QUBITS):
        spec.append({"gate": "CZ", "wires": [i, (i + 1) % N_QUBITS]})
    for i in range(N_QUBITS // 2):
        spec.append({"gate": "CZ", "wires": [i, i + N_QUBITS // 2]})

    # Post-entanglement rotation layer: reuse the SAME "theta" parameter on
    # the RZ axis, keeping the unique parameter count at exactly 1 for the
    # whole block.
    for wire in range(N_QUBITS):
        spec.append({"gate": "RZ", "wire": wire, "param": "theta"})


# Stack two copies of the tri-axis + dense-CZ block, both reusing the SAME
# single shared parameter "theta". Duplicating the block increases circuit
# expressivity/depth without adding any new trainable parameters, which is
# expected to speed up convergence while preserving parameter economy.
_add_tri_axis_dense_block(ANSATZ_SPEC)
_add_tri_axis_dense_block(ANSATZ_SPEC)
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)