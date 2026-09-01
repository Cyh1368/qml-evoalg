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

    Cheap local mixing: only two trainable parameters regardless of qubit
    count, but every qubit is coupled to both of its neighbors.
    """
    gates = []
    for i in range(n):
        j = (i + 1) % n
        param = even_param if i % 2 == 0 else odd_param
        gates.append({"gate": "CRZ", "wires": [i, j], "param": param})
    return gates


def _skip2_alternating(n, even_param="crz_skip2_even", odd_param="cry_skip2_odd"):
    """Distance-2 entanglement that alternates gate *type* (CRZ / CRY) as
    well as parameter, coupled with the alternating index parity.

    Mixing rotation axes on the entangling gates (rather than using a
    single gate type everywhere) increases the set of reachable unitaries
    without spending any extra parameters -- this is the key idea borrowed
    from the CRZ/CRY skip layer that performed well in an earlier
    generation, now applied on top of the richer multi-distance topology
    of the modular block design.
    """
    gates = []
    for i in range(n):
        j = (i + 2) % n
        if i % 2 == 0:
            gates.append({"gate": "CRZ", "wires": [i, j], "param": even_param})
        else:
            gates.append({"gate": "CRY", "wires": [i, j], "param": odd_param})
    return gates


def _skip_crz(n, step, param):
    """Sparse skip-`step` entanglement with a single shared parameter,
    acting as an implicit regularizer while still providing longer-range
    mixing than the nearest-neighbor ring."""
    return [{"gate": "CRZ", "wires": [i, (i + step) % n], "param": param} for i in range(n)]


def _diameter_crz(n, param="crz_diam"):
    """Antipodal (distance n/2) entanglement with a single shared parameter.
    Gives global connectivity at minimal parameter cost."""
    half = n // 2
    return [{"gate": "CRZ", "wires": [i, i + half], "param": param} for i in range(half)]


def _build_block(n=N_QUBITS):
    """Compose one full ansatz block from modular layers:
      1. Per-qubit RY rotations (expressivity).
      2. Ring CRZ entanglement, alternating shared strength (local mixing).
      3. Per-qubit RX rotations (second rotation axis, more expressivity).
      4. Skip-2 entanglement alternating CRZ/CRY gate type and shared
         parameter (mid-range mixing with richer, non-commuting gate mix).
      5. Skip-3 CRZ entanglement, single shared parameter (fills the
         distance-3 connectivity gap).
      6. Diameter CRZ entanglement, single shared parameter (global mixing).
    """
    block = []
    block += _ry_layer(range(n))
    block += _ring_crz(n)
    block += _rx_layer(range(n))
    block += _skip2_alternating(n)
    block += _skip_crz(n, step=3, param="crz_skip3")
    block += _diameter_crz(n)
    return block


_BLOCK = _build_block(N_QUBITS)

# Apply the block twice, reusing identical parameter names across both
# copies. This deepens the circuit (more expressive power, more entangling
# layers) while keeping the parameter count unchanged compared to a single
# copy -- the shared-depth trick that drove earlier generations' accuracy
# gains -- now combined with a richer, cheaper entanglement topology
# (ring + skip-2 alternating CRZ/CRY + skip-3 + diameter) that covers more
# inter-qubit distances and gate types at a much lower total parameter
# count than either parent program.
ANSATZ_SPEC = _BLOCK + _BLOCK
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)
