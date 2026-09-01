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


def _rz_mid_layer(n, prefix="rz_mid"):
    """Per-qubit RZ rotations with mirror-pair parameter sharing
    (wire i shares its parameter with wire n-1-i). This yields only
    ceil(n/2) unique parameters (4 for n=8) while still giving every
    qubit an extra phase-control rotation right before the longer-range
    entangling layers, sharpening local expressivity at negligible
    parameter cost."""
    gates = []
    for i in range(n):
        j = n - 1 - i
        idx = min(i, j)
        gates.append({"gate": "RZ", "wire": i, "param": f"{prefix}_{idx}"})
    return gates


def _ring_crz(n, even_param="crz_ring_even", odd_param="crz_ring_odd"):
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


def _diameter_crz(n, even_param="crz_diam_even", odd_param="crz_diam_odd"):
    """Antipodal (distance n/2) entanglement with two shared parameters,
    following an alternating-strength pattern analogous to the ring layer.
    Adds genuinely global connectivity at minimal parameter cost."""
    half = n // 2
    gates = []
    for i in range(half):
        j = i + half
        param = even_param if i % 2 == 0 else odd_param
        gates.append({"gate": "CRZ", "wires": [i, j], "param": param})
    return gates


def _build_block(n=N_QUBITS):
    """Compose one full ansatz block from modular layers:
      1. Per-qubit RY rotations (expressivity).
      2. Ring CRZ entanglement, alternating shared strength (local mixing).
      3. Per-qubit RX rotations (second rotation axis, more expressivity).
      4. Skip-2 CRZ entanglement, single shared parameter (mid-range mixing,
         regularized via sharing).
      5. Diameter CRZ entanglement, two shared parameters (global mixing,
         regularized via sharing).
    """
    block = []
    block += _ry_layer(range(n))
    block += _ring_crz(n)
    block += _rx_layer(range(n))
    block += _rz_mid_layer(n)
    block += _skip_crz(n, step=2)
    block += _diameter_crz(n)
    return block


_BLOCK = _build_block(N_QUBITS)

# Apply the block twice, reusing identical parameter names across both
# copies. This deepens the circuit (more expressive power, more entangling
# layers) while keeping the parameter count unchanged compared to a single
# copy -- the same regularizing "shared depth" trick that drove the previous
# generation's accuracy gain, now combined with an added global (diameter)
# entangling layer for richer long-range mixing at minimal extra parameter
# cost (+2 unique parameters only).
ANSATZ_SPEC = _BLOCK + _BLOCK
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)