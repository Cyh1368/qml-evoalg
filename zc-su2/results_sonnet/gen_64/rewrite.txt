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
def _shared_rotation_layer(gate, param, wires=range(N_QUBITS)):
    """Return gate dicts applying `gate` on every wire, all sharing `param`.

    Using a single shared parameter per axis keeps the parameter count for
    the whole rotation layer at exactly 1, regardless of qubit count.
    """
    return [{"gate": gate, "wire": w, "param": param} for w in wires]


def _ring_entangler(ising_gate, param, fixed_gate, n_qubits=N_QUBITS):
    """Nearest-neighbor ring alternating a parametrized Ising interaction
    (shared single parameter `param`) with a fixed, zero-parameter gate.

    This mixes a tunable, non-commuting entangling term into the ring
    while keeping the fixed gate cheap (no trainable parameters), which
    was the key ingredient behind fast convergence in prior designs.
    """
    ops = []
    for i in range(n_qubits):
        a, b = i, (i + 1) % n_qubits
        if i % 2 == 0:
            ops.append({"gate": ising_gate, "wires": [a, b], "param": param})
        else:
            ops.append({"gate": fixed_gate, "wires": [a, b]})
    return ops


def _antipodal_shortcuts(fixed_gate, n_qubits=N_QUBITS):
    """Fixed, zero-parameter long-range links connecting antipodal qubits
    on the n-cycle (distance n/2), giving global connectivity cheaply.
    """
    half = n_qubits // 2
    return [{"gate": fixed_gate, "wires": [i, i + half]} for i in range(half)]


def build_ansatz():
    """Compose the ansatz block from small, reusable layer builders.

    Parameter budget per block: exactly 4 shared scalars —
      - "theta_rx": pre-entanglement RX layer (all qubits)
      - "theta_ry": pre-entanglement RY layer (all qubits)
      - "theta_e" : entangling XX interactions inside the ring
      - "theta_rz": post-entanglement RZ layer (all qubits)
    Fixed gates (CZ ring links, antipodal CZ shortcuts) contribute zero
    trainable parameters, preserving the depth/gate-count profile of the
    best-performing single-parameter ancestor while giving each rotation
    axis and the entangler independent, bespoke tunability.
    """
    spec = []
    spec += _shared_rotation_layer("RX", "theta_rx")
    spec += _shared_rotation_layer("RY", "theta_ry")
    spec += _ring_entangler("XX", "theta_e", fixed_gate="CZ")
    spec += _antipodal_shortcuts("CZ")
    spec += _shared_rotation_layer("RZ", "theta_rz")
    return spec


ANSATZ_SPEC = build_ansatz()
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)