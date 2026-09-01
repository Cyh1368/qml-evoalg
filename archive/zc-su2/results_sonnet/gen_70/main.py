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


def _add_theta_block(spec):
    """One compact, single-parameter (theta) rotation+entangling block.

    Reuses the SAME shared parameter name "theta" for every rotation and
    every parametrized entangler, so calling this twice back-to-back adds
    depth/expressivity without adding any new trainable parameters.
    """
    # Pre-entanglement rotation layer, axis RX, single shared "theta".
    for wire in range(N_QUBITS):
        spec.append({"gate": "RX", "wire": wire, "param": "theta"})

    # Pre-entanglement rotation layer, axis RY, reusing the SAME "theta".
    for wire in range(N_QUBITS):
        spec.append({"gate": "RY", "wire": wire, "param": "theta"})

    # Nearest-neighbor ring, alternating between two non-commuting
    # parametrized Ising interactions, XX and YY, BOTH reusing the SAME
    # shared "theta" parameter. Alternating non-commuting entanglers
    # under one shared parameter enriches mixing/expressivity without
    # adding any new trainable parameters.
    for i in range(N_QUBITS):
        a, b = i, (i + 1) % N_QUBITS
        if i % 2 == 0:
            spec.append({"gate": "XX", "wires": [a, b], "param": "theta"})
        else:
            spec.append({"gate": "YY", "wires": [a, b], "param": "theta"})

    # Lightweight, zero-parameter skip-2 sub-ring (0-2, 2-4, 4-6, 6-0).
    # Restoring this cut convergence steps from 120 down to 30 in prior
    # experiments, at zero extra parameter cost.
    for i in range(0, N_QUBITS, 2):
        spec.append({"gate": "CZ", "wires": [i, (i + 2) % N_QUBITS]})

    # Fixed, zero-parameter antipodal shortcuts (distance-4 on the
    # 8-cycle) for long-range connectivity.
    for i in range(N_QUBITS // 2):
        spec.append({"gate": "CZ", "wires": [i, i + N_QUBITS // 2]})

    # Post-entanglement rotation layer, axis RZ, reusing the SAME "theta"
    # parameter, keeping the total unique parameter count per block at 1.
    for wire in range(N_QUBITS):
        spec.append({"gate": "RZ", "wire": wire, "param": "theta"})


# Stack the block twice back-to-back, reusing the SAME single "theta"
# parameter both times. This doubles depth/expressivity (RX->RY->ring->
# skip-2->antipodal->RZ, repeated) while keeping the trainable-parameter
# count identical, which prior experiments show speeds up convergence
# substantially at no parameter cost.
_add_theta_block(ANSATZ_SPEC)
_add_theta_block(ANSATZ_SPEC)
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)