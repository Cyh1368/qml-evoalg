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
def _single_layer(gate, wires, param):
    """Single-qubit rotation layer, all wires sharing one parameter name."""
    return [{"gate": gate, "wire": w, "param": param} for w in wires]


def _cnot_ladder(wires):
    """Fixed (parameter-free) nearest-neighbor CNOT ladder over `wires` in order."""
    return [{"gate": "CNOT", "wires": [wires[i], wires[i + 1]]}
            for i in range(len(wires) - 1)]


def _ising_shell(gate, n_qubits, skip, param):
    """Parametrized Ising coupling shell connecting qubit i to (i+skip) mod n,
    all sharing one parameter name. `skip` sets the connectivity range
    (1 = nearest neighbor ring, 2/3 = longer-range shells, n/2 = opposite pair)."""
    pairs = []
    seen = set()
    for i in range(n_qubits):
        j = (i + skip) % n_qubits
        key = frozenset((i, j))
        if i == j or key in seen:
            continue
        seen.add(key)
        pairs.append((i, j))
    return [{"gate": gate, "wires": list(p), "param": param} for p in pairs]


N = N_QUBITS
QUBITS = list(range(N))
THETA = "theta"

ANSATZ_SPEC = (
    # Pre-rotation layer: single shared parameter across all qubits, keeps
    # distinct-parameter count minimal while still driven by per-qubit
    # data encoding.
    _single_layer("RY", QUBITS, "ry_a")

    # Fixed forward CNOT ladder: zero-parameter mixing before the
    # parametrized entangling shells.
    + _cnot_ladder(QUBITS)

    # Global phase layer BEFORE the entangling shells, sharing THETA with
    # every coupler below to collapse everything into one parameter.
    + _single_layer("RZ", QUBITS, THETA)

    # Nearest-neighbor ZZ ring (skip-1), open chain (no wraparound edge to
    # keep depth economical, matches best-performing ancestor).
    + _ising_shell("ZZ", N, 1, THETA)

    # Opposite-qubit long-range ZZ shell (skip-4 / hypercube-like).
    + _ising_shell("ZZ", N, 4, THETA)

    # Skip-2 ZZ shell: enriches mid-range connectivity.
    + _ising_shell("ZZ", N, 2, THETA)

    # NEW: Skip-3 ZZ shell, deepening long-range entanglement coverage
    # between the skip-2 shell and the XX ring, still sharing THETA.
    + _ising_shell("ZZ", N, 3, THETA)

    # Orthogonal XX nearest-neighbor ring, same shared parameter, enriches
    # the reachable operator space with a second Pauli basis.
    + _ising_shell("XX", N, 1, THETA)

    # Fixed backward CNOT ladder: additional zero-parameter mixing.
    + _cnot_ladder(list(reversed(QUBITS)))

    # Global phase layer AFTER the entangling shells, reusing THETA again.
    + _single_layer("RZ", QUBITS, THETA)
)
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)