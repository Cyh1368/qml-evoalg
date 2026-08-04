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
    """Nearest-neighbor ring entanglement with alternating shared strength."""
    gates = []
    for i in range(n):
        j = (i + 1) % n
        param = even_param if i % 2 == 0 else odd_param
        gates.append({"gate": "CRZ", "wires": [i, j], "param": param})
    return gates


def _skip_crz(n, step=2, even_param="crz_skip_even", odd_param="crz_skip_odd"):
    """Sparse skip-`step` entanglement with two alternating shared
    parameters (even/odd indexed edges), mirroring the proven alternating
    strength pattern used in the nearest-neighbor ring layer. This gives
    mid-range entanglers slightly more expressive freedom than a single
    shared knob, while still keeping the parameter count low via sharing."""
    gates = []
    for i in range(n):
        j = (i + step) % n
        param = even_param if i % 2 == 0 else odd_param
        gates.append({"gate": "CRZ", "wires": [i, j], "param": param})
    return gates


def _diameter_crx(n, param="crx_diam"):
    """Antipodal (distance n/2) entanglement with a single shared parameter
    on a different rotation axis (CRX), giving cheap global mixing."""
    half = n // 2
    return [{"gate": "CRX", "wires": [i, i + half], "param": param} for i in range(half)]


def _build_block(n=N_QUBITS):
    """Compose one full ansatz block from modular layers:
      1. Per-qubit RY rotations (expressivity).
      2. Ring CRZ entanglement, alternating shared strength (local mixing).
      3. Per-qubit RX rotations (second rotation axis, more expressivity).
      4. Skip-2 CRZ entanglement, alternating shared parameters (mid-range
         mixing with slightly more freedom than a single shared knob).
      5. Skip-3 CRZ entanglement, alternating shared parameters (fills the
         distance-3 connectivity gap with the same alternating pattern).
      6. Diameter CRX entanglement, single shared parameter (global mixing
         on a different rotation axis).
    """
    block = []
    block += _ry_layer(range(n))
    block += _ring_crz(n)
    block += _rx_layer(range(n))
    block += _skip_crz(n, step=2, even_param="crz_skip2_even", odd_param="crz_skip2_odd")
    block += _skip_crz(n, step=3, even_param="crz_skip3_even", odd_param="crz_skip3_odd")
    block += _diameter_crx(n)
    return block


_BLOCK = _build_block(N_QUBITS)

# Duplicate the block, reusing the same parameter names, to double the
# effective depth while keeping the parameter count unchanged.
ANSATZ_SPEC = _BLOCK + _BLOCK
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)