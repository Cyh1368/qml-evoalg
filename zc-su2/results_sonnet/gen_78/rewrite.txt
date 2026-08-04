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
    every parametrized entangler, so the whole block has exactly ONE
    trainable parameter name. Connectivity is boosted with several
    fixed (zero-parameter) shortcut layers: nearest-neighbor ring,
    skip-2 sub-ring, skip-3 sub-ring, and antipodal (skip-4) shortcuts,
    giving broad, near-all-to-all mixing without any extra trainable
    parameters.
    """
    # Pre-entanglement rotation layer, axis RX, single shared "theta".
    for wire in range(N_QUBITS):
        spec.append({"gate": "RX", "wire": wire, "param": "theta"})

    # Pre-entanglement rotation layer, axis RY, reusing the SAME "theta".
    for wire in range(N_QUBITS):
        spec.append({"gate": "RY", "wire": wire, "param": "theta"})

    # Nearest-neighbor ring, alternating a parametrized XX interaction
    # (reusing "theta") with a fixed, zero-parameter CZ gate.
    for i in range(N_QUBITS):
        a, b = i, (i + 1) % N_QUBITS
        if i % 2 == 0:
            spec.append({"gate": "XX", "wires": [a, b], "param": "theta"})
        else:
            spec.append({"gate": "CZ", "wires": [a, b]})

    # Lightweight, zero-parameter skip-2 sub-ring (0-2, 2-4, 4-6, 6-0).
    # Empirically cuts convergence steps substantially at zero extra
    # parameter cost.
    for i in range(0, N_QUBITS, 2):
        spec.append({"gate": "CZ", "wires": [i, (i + 2) % N_QUBITS]})

    # Lightweight, zero-parameter skip-3 sub-ring (0-3, 2-5, 4-7, 6-1).
    # Adds another distinct long-range connectivity pattern that does not
    # overlap with skip-2 or antipodal (skip-4) links, further spreading
    # correlations across the register with only 4 fixed gates and no
    # new trainable parameters.
    for i in range(0, N_QUBITS, 2):
        spec.append({"gate": "CZ", "wires": [i, (i + 3) % N_QUBITS]})

    # Fixed, zero-parameter antipodal shortcuts (distance-4 on the
    # 8-cycle) for long-range connectivity.
    for i in range(N_QUBITS // 2):
        spec.append({"gate": "CZ", "wires": [i, i + N_QUBITS // 2]})

    # Post-entanglement rotation layer, axis RZ, reusing the SAME "theta"
    # parameter, keeping the total unique parameter count per block at 1.
    for wire in range(N_QUBITS):
        spec.append({"gate": "RZ", "wire": wire, "param": "theta"})


# Single block application per outer repetition. The block above reuses
# ONE shared trainable parameter name ("theta") for every rotation and
# every parametrized entangler, so each outer repetition (applied a
# fixed number of times by the surrounding, fixed harness) contributes
# exactly one trainable parameter, keeping parameter economy maximal
# while still providing rich, near-all-to-all fixed connectivity
# (nearest-neighbor ring, skip-2, skip-3, and antipodal shortcuts).
_add_theta_block(ANSATZ_SPEC)
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)