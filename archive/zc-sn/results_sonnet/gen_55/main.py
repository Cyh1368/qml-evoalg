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


# EVOLVE-BLOCK-START
def _ry_layer(qubits, prefix="ry"):
    """Per-qubit RY rotations, one trainable parameter each."""
    return [{"gate": "RY", "wire": q, "param": f"{prefix}_{q}"} for q in qubits]


def _rx_layer(qubits, prefix="rx"):
    """Per-qubit RX rotations, one trainable parameter each."""
    return [{"gate": "RX", "wire": q, "param": f"{prefix}_{q}"} for q in qubits]


def _ring_crz(n, even_param="crz_ring_even", odd_param="crz_ring_odd"):
    """Nearest-neighbor ring entanglement with alternating shared strength.

    Only two unique parameters regardless of the number of qubits, which
    keeps the parameter budget small while still providing full-ring local
    mixing (fast to optimize; contributed to the 150-step convergence seen
    in prior generations)."""
    gates = []
    for i in range(n):
        j = (i + 1) % n
        param = even_param if i % 2 == 0 else odd_param
        gates.append({"gate": "CRZ", "wires": [i, j], "param": param})
    return gates


def _skip_crz(n, step=2, param="crz_skip"):
    """Sparse skip-`step` entanglement with a single shared parameter,
    acting as an implicit regularizer while still providing longer-range
    mixing than the nearest-neighbor ring."""
    return [{"gate": "CRZ", "wires": [i, (i + step) % n], "param": param} for i in range(n)]


def _diameter_crz(n, param="crz_diam"):
    """Antipodal (distance n/2) entanglement using a *single* shared
    parameter.

    Prior experiments showed that adding global (antipodal) connectivity
    improves the train/test generalization gap (0.03 vs 0.06 without it),
    but using two alternating parameters for it slowed convergence
    (540 vs 150 steps). Using just one shared parameter for all antipodal
    pairs keeps the extra global-mixing benefit while adding only a single
    extra parameter to the optimization landscape, aiming to retain the
    faster convergence of the simpler variant."""
    half = n // 2
    return [{"gate": "CRZ", "wires": [i, i + half], "param": param} for i in range(half)]


def _build_block(n=N_QUBITS):
    """Compose one full ansatz block from modular layers:
      1. Per-qubit RY rotations (expressivity).
      2. Ring CRZ entanglement, alternating shared strength (local mixing,
         fast-converging).
      3. Per-qubit RX rotations (second rotation axis, more expressivity).
      4. Skip-2 CRZ entanglement, single shared parameter (mid-range mixing,
         regularized via sharing).
      5. Diameter CRZ entanglement, single shared parameter (global mixing
         at minimal extra parameter cost, improves generalization gap).
    """
    block = []
    block += _ry_layer(range(n))
    block += _ring_crz(n)
    block += _rx_layer(range(n))
    block += _skip_crz(n, step=2)
    block += _diameter_crz(n)
    return block


_BLOCK = _build_block(N_QUBITS)

# Apply the block twice, reusing identical parameter names across both
# copies. This deepens the circuit (more expressive power, more entangling
# layers, better mixing) while keeping the parameter count unchanged
# compared to a single copy. Combined with the single-parameter diameter
# layer, this keeps the total unique-parameter count at just 20 (8 RY +
# 8 RX + 2 ring + 1 skip + 1 diameter), aiming for both fast convergence
# (few, well-shared parameters) and good generalization (global mixing via
# the diameter layer).
ANSATZ_SPEC = _BLOCK + _BLOCK
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)