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
def _rot_layer(qubits, axis, prefix):
    """Per-qubit single-axis rotation layer with individually trainable params."""
    return [{"gate": axis, "wire": q, "param": f"{prefix}_{q}"} for q in qubits]


def _stage1_even(n, param="crz_s1"):
    """Nearest-neighbor entanglement on even-offset pairs: (0,1),(2,3),(4,5),(6,7)."""
    return [{"gate": "CRZ", "wires": [i, i + 1], "param": param} for i in range(0, n, 2)]


def _stage2_odd(n, param="cry_s2"):
    """Nearest-neighbor entanglement on odd-offset pairs (wrap-around), different
    rotation axis (CRY) than stage 1 to diversify the local interaction type."""
    return [{"gate": "CRY", "wires": [i, (i + 1) % n], "param": param} for i in range(1, n, 2)]


def _stage3_distance2(n, param="crz_s3"):
    """Distance-2 entanglement organized as two disjoint 4-cycles
    (0-2-4-6-0) and (1-3-5-7-1), providing mid-range mixing while still
    respecting a structured, scale-consistent topology."""
    gates = []
    for start in (0, 1):
        ring = [start + 2 * k for k in range(n // 2)]
        for idx in range(len(ring)):
            a = ring[idx]
            b = ring[(idx + 1) % len(ring)]
            gates.append({"gate": "CRZ", "wires": [a, b], "param": param})
    return gates


def _stage4_antipodal(n, param="crx_s4"):
    """Antipodal (distance n/2) entanglement for global mixing, using a
    third rotation axis (CRX) for maximal axis diversity across scales."""
    half = n // 2
    return [{"gate": "CRX", "wires": [i, i + half], "param": param} for i in range(half)]


def _build_block(n=N_QUBITS):
    """One hierarchical, scale-progressive entangling block:
      1. RY rotations (local phase/expressivity).
      2. Stage-1: nearest-neighbor, even offsets (CRZ).
      3. RX rotations (second axis).
      4. Stage-2: nearest-neighbor, odd offsets (CRY, distinct axis).
      5. RZ rotations (third axis).
      6. Stage-3: distance-2, two disjoint 4-cycles (CRZ).
      7. RY rotations (revisit first axis for a second expressivity pass).
      8. Stage-4: antipodal / distance-4, global mixing (CRX).
    This mirrors a QCNN-like coarse-graining: information first mixes
    locally, then at increasing length scales, terminating in a fully
    global interaction, in contrast to the flat ring/skip topologies used
    previously.
    """
    block = []
    block += _rot_layer(range(n), "RY", "ry_a")
    block += _stage1_even(n)
    block += _rot_layer(range(n), "RX", "rx_a")
    block += _stage2_odd(n)
    block += _rot_layer(range(n), "RZ", "rz_a")
    block += _stage3_distance2(n)
    block += _rot_layer(range(n), "RY", "ry_b")
    block += _stage4_antipodal(n)
    return block


_BLOCK = _build_block(N_QUBITS)

# Repeat the hierarchical block multiple times, reusing identical parameter
# names across all copies. This builds up depth (and thus expressivity /
# richer effective interference across scales) without increasing the
# parameter count -- the same "shared-depth" trick that worked well in
# earlier generations -- while the underlying per-copy topology is a
# fundamentally different, scale-hierarchical entangling structure rather
# than a ring/skip/diameter mixture.
ANSATZ_SPEC = _BLOCK + _BLOCK + _BLOCK + _BLOCK
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)