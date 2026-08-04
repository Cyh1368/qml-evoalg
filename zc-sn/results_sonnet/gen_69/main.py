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


def _ring_crz(n, even_param, odd_param):
    """Nearest-neighbor ring entanglement with alternating shared strength."""
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
    """Antipodal (distance n/2) entanglement with a single shared parameter.
    Global connectivity at minimal parameter cost."""
    half = n // 2
    return [{"gate": "CRZ", "wires": [i, i + half], "param": param} for i in range(half)]


def _build_block(n, block_idx):
    """Compose one full ansatz block from modular layers:
      1. Per-qubit RY rotations (expressivity).
      2. Ring CRZ entanglement with block-local parameters (local mixing;
         de-shared across blocks so each repetition can adapt its
         nearest-neighbor coupling independently).
      3. Per-qubit RX rotations (second rotation axis, more expressivity).
      4. Skip-2 CRZ entanglement, shared across blocks (mid-range mixing).
      5. Skip-3 CRZ entanglement, shared across blocks (fills the
         distance-3 connectivity gap).
      6. Diameter CRZ entanglement, shared across blocks (global mixing).
    """
    block = []
    block += _ry_layer(range(n))
    block += _ring_crz(
        n,
        even_param=f"crz_ring_even_b{block_idx}",
        odd_param=f"crz_ring_odd_b{block_idx}",
    )
    block += _rx_layer(range(n))
    block += _skip_crz(n, step=2, param="crz_skip2")
    block += _skip_crz(n, step=3, param="crz_skip3")
    block += _diameter_crz(n, param="crz_diam")
    return block


_BLOCK_0 = _build_block(N_QUBITS, block_idx=0)
_BLOCK_1 = _build_block(N_QUBITS, block_idx=1)

# Two repetitions of the block, with block-local ring parameters but fully
# shared skip-2/skip-3/diameter parameters. This gives the position-sensitive
# nearest-neighbor entangling layer a little extra flexibility per block
# while preserving the regularizing effect of parameter sharing for the
# mid- and long-range entanglers.
ANSATZ_SPEC = _BLOCK_0 + _BLOCK_1
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)