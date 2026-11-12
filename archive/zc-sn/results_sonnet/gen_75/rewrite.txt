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


def _skip_crz_alt(n, step=2, even_param="crz_skip_even", odd_param="crz_skip_odd"):
    """Sparse skip-`step` entanglement with two alternating shared
    parameters (even/odd edge index). This mirrors the proven even/odd
    motif already used in the ring layer, giving mid-range entanglers
    direction-dependent coupling strength at the cost of just one extra
    parameter per skip distance, while still remaining far cheaper than a
    fully independent parameter per edge."""
    gates = []
    for i in range(n):
        param = even_param if i % 2 == 0 else odd_param
        gates.append({"gate": "CRZ", "wires": [i, (i + step) % n], "param": param})
    return gates


def _diameter_crz(n, param="crz_diam"):
    """Antipodal (distance n/2) entanglement with a single shared parameter.
    Keeps global connectivity at minimal parameter cost."""
    half = n // 2
    return [{"gate": "CRZ", "wires": [i, i + half], "param": param} for i in range(half)]


def _build_block(n=N_QUBITS):
    """Compose one full ansatz block from modular layers:
      1. Per-qubit RY rotations (expressivity).
      2. Ring CRZ entanglement, alternating shared strength (local mixing).
      3. Per-qubit RX rotations (second rotation axis, more expressivity).
      4. Skip-2 CRZ entanglement, alternating (even/odd) shared parameters
         (mid-range mixing with finer-grained coupling strength).
      5. Skip-3 CRZ entanglement, alternating (even/odd) shared parameters
         (fills the distance-3 connectivity gap with the same motif).
      6. Diameter CRZ entanglement, single shared parameter (global mixing).
    """
    block = []
    block += _ry_layer(range(n))
    block += _ring_crz(n)
    block += _rx_layer(range(n))
    block += _skip_crz_alt(n, step=2, even_param="crz_skip2_even", odd_param="crz_skip2_odd")
    block += _skip_crz_alt(n, step=3, even_param="crz_skip3_even", odd_param="crz_skip3_odd")
    block += _diameter_crz(n)
    return block


_BLOCK = _build_block(N_QUBITS)

# Apply the block twice, reusing identical parameter names across both
# copies. This deepens the circuit (more expressive power, more entangling
# layers) while keeping the parameter count unchanged compared to a single
# copy -- the same regularizing "shared depth" trick that drove earlier
# generations' accuracy gains, now combined with a richer entanglement
# topology (alternating skip-2, skip-3, and single-parameter diameter)
# that covers more inter-qubit distances and finer-grained coupling
# strengths at a modest total parameter count.
ANSATZ_SPEC = _BLOCK + _BLOCK
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)