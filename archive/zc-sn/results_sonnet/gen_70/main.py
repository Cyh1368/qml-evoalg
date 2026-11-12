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
    """Per-qubit RY rotations, one trainable parameter each (shared across blocks)."""
    return [{"gate": "RY", "wire": q, "param": f"{prefix}_{q}"} for q in qubits]


def _rx_layer(qubits, prefix="rx"):
    """Per-qubit RX rotations, one trainable parameter each (shared across blocks)."""
    return [{"gate": "RX", "wire": q, "param": f"{prefix}_{q}"} for q in qubits]


def _ring_crz(n, even_param, odd_param):
    """Nearest-neighbor ring entanglement with alternating shared strength.
    Parameter names are passed in so different block copies can either
    share or use their own dedicated ring parameters."""
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
    """Antipodal (distance n/2) entanglement with a single shared parameter,
    giving cheap global connectivity."""
    half = n // 2
    return [{"gate": "CRZ", "wires": [i, i + half], "param": param} for i in range(half)]


def _build_block(n, ring_even, ring_odd):
    """Compose one full ansatz block. RY/RX single-qubit layers and the
    skip-2/skip-3/diameter entanglers always use fixed shared names (so
    they are shared across every block copy), while the ring parameter
    names are passed in explicitly so different block copies can be
    partially de-shared."""
    block = []
    block += _ry_layer(range(n))
    block += _ring_crz(n, even_param=ring_even, odd_param=ring_odd)
    block += _rx_layer(range(n))
    block += _skip_crz(n, step=2, param="crz_skip2")
    block += _skip_crz(n, step=3, param="crz_skip3")
    block += _diameter_crz(n)
    return block


# First block gets its own dedicated ring parameters, while the second
# block uses the base ring parameter names. All other layers (RY, RX,
# skip-2, skip-3, diameter) share identical parameter names between the
# two blocks, since they are looked up by fixed string inside
# `_build_block`. This partial de-sharing gives each block a little extra
# local-mixing flexibility without inflating the parameter count as much
# as fully independent blocks would.
_BLOCK0 = _build_block(N_QUBITS, ring_even="crz_ring_even_b0", ring_odd="crz_ring_odd_b0")
_BLOCK1 = _build_block(N_QUBITS, ring_even="crz_ring_even", ring_odd="crz_ring_odd")

ANSATZ_SPEC = _BLOCK0 + _BLOCK1
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)