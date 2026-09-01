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
def _build_ansatz_spec(n_qubits=N_QUBITS):
    """Build a modular ansatz block.

    Structure:
      1. Full single-qubit rotation layer (RX, RY, RZ) with independent
         parameters per qubit -> spans the complete single-qubit rotation
         group, unlike an RY+RZ-only layer which misses one degree of
         freedom.
      2. A ring-entangling layer of trainable CRZ gates connecting every
         qubit to its neighbor (including the wrap-around edge), using only
         two shared parameters (even-indexed edges share one parameter,
         odd-indexed edges share another) to keep the parameter budget low
         while making the entangling strength learnable instead of fixed.
      3. A cheap shared-parameter RZ "phase trim" layer applied to every
         qubit after entanglement, using a single shared parameter to allow
         a global phase-style correction at minimal parameter cost.
    """
    spec = []

    # 1. Full single-qubit rotation layer: RX, RY, RZ per qubit.
    for i in range(n_qubits):
        spec.append({"gate": "RX", "wire": i, "param": f"rx_{i}"})
    for i in range(n_qubits):
        spec.append({"gate": "RY", "wire": i, "param": f"ry_{i}"})
    for i in range(n_qubits):
        spec.append({"gate": "RZ", "wire": i, "param": f"rz_{i}"})

    # 2. Ring-entangling layer with trainable CRZ gates, two shared params.
    for i in range(n_qubits):
        control = i
        target = (i + 1) % n_qubits
        shared_name = "crz_even" if i % 2 == 0 else "crz_odd"
        spec.append(
            {"gate": "CRZ", "wires": [control, target], "param": shared_name}
        )

    # 3. Lightweight shared phase-trim layer.
    for i in range(n_qubits):
        spec.append({"gate": "RZ", "wire": i, "param": "phase_trim"})

    return spec


ANSATZ_SPEC = _build_ansatz_spec()
# EVOLVE-BLOCK-END


def run_experiment(**kwargs):
    return _run(ANSATZ_SPEC, **kwargs)
