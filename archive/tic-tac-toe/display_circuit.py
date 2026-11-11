"""Plot circuits for the tic-tac-toe QML experiment.

Saves two PNGs:
  circuit.png        — full ANSATZ_SPEC circuit from initial_program.py
  cemoid_circuit.png — invariant cemoid circuit (l=1, p=1)
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import initial_program as initial_circuit  # noqa: E402

import pennylane as qml  # noqa: E402

# ---------------------------------------------------------------------------
# Grid constants (match the paper's tic-tac-toe qubit layout)
#   0 -- 1 -- 2
#   |    |    |
#   7 -- 8 -- 3
#   |    |    |
#   6 -- 5 -- 4
# ---------------------------------------------------------------------------
N_QUBITS = 9
CORNERS = (0, 2, 4, 6)
EDGES   = (1, 3, 5, 7)
CENTER  = 8
FEATURE_SCALE = 2 * np.pi / 3

# Outer (o): each corner controls its two neighbouring edge qubits
OUTER_PAIRS = [(0, 1), (0, 7), (2, 1), (2, 3), (4, 3), (4, 5), (6, 5), (6, 7)]
# Inner (i): each edge qubit controls the centre
INNER_PAIRS = [(1, 8), (3, 8), (5, 8), (7, 8)]
# Diagonal (d): centre controls each corner
DIAG_PAIRS  = [(8, 0), (8, 2), (8, 4), (8, 6)]

# 9 shared parameters per cemoid block
# Single-qubit: cx, cz (corners), ex, ez (edges), mx, mz (middle)
# Entangling:   o (outer), i (inner), d (diagonal)
CEMOID_PARAMS = ("θ_cx", "θ_cz", "θ_ex", "θ_ez", "θ_mx", "θ_mz", "θ_o", "θ_i", "θ_d")
N_CEMOID_PARAMS = len(CEMOID_PARAMS)


def feature_map(board: np.ndarray) -> None:
    """RX encoding: each cell value in {-1, 0, +1} → rotation by x·2π/3."""
    for wire in range(N_QUBITS):
        qml.RX(float(FEATURE_SCALE * int(board[wire])), wires=wire)


def cemoid_block(params) -> None:
    """One cemoid block W(θ) with 9 shared parameters.

    Single-qubit layer (18 gates): RX+RZ on each qubit, parameter shared
    within corners / edges / middle.
    Entangling layer (16 CRY gates): outer, inner, diagonal — one shared
    parameter each.
    """
    theta_cx, theta_cz, theta_ex, theta_ez, theta_mx, theta_mz, theta_o, theta_i, theta_d = params
    # Single-qubit rotations
    for q in CORNERS:
        qml.RX(theta_cx, wires=q)
        qml.RZ(theta_cz, wires=q)
    for q in EDGES:
        qml.RX(theta_ex, wires=q)
        qml.RZ(theta_ez, wires=q)
    qml.RX(theta_mx, wires=CENTER)
    qml.RZ(theta_mz, wires=CENTER)
    # Controlled-RY entanglers
    for ctrl, tgt in OUTER_PAIRS:
        qml.CRY(theta_o, wires=[ctrl, tgt])
    for ctrl, tgt in INNER_PAIRS:
        qml.CRY(theta_i, wires=[ctrl, tgt])
    for ctrl, tgt in DIAG_PAIRS:
        qml.CRY(theta_d, wires=[ctrl, tgt])


_dev_cemoid = qml.device("default.qubit", wires=N_QUBITS, shots=None)


@qml.qnode(_dev_cemoid, interface="autograd", diff_method="backprop")
def cemoid_circuit(board, params):
    """Invariant cemoid circuit: l=1 upload, p=1 block."""
    feature_map(board)
    cemoid_block(params)
    return [qml.expval(qml.PauliZ(wire)) for wire in range(N_QUBITS)]


HERE = Path(__file__).parent
_zero_board = np.zeros(N_QUBITS, dtype=np.int8)


# ---------------------------------------------------------------------------
# Plot 1: initial_program.py ANSATZ_SPEC circuit
# ---------------------------------------------------------------------------
fig1, ax1 = qml.draw_mpl(initial_circuit.circuit_z_expectations, decimals=None)(
    _zero_board, np.zeros(initial_circuit.N_PARAMS)
)
ax1.set_title(
    f"ANSATZ_SPEC circuit  |  "
    f"l={initial_circuit.N_UPLOADS} uploads, p={initial_circuit.N_REPEATS} repeats/upload, "
    f"{initial_circuit.N_PARAMS_PER_BLOCK} params/block, "
    f"{initial_circuit.N_PARAMS} params total"
)
out1 = HERE / "circuit.png"
fig1.savefig(out1, dpi=150, bbox_inches="tight")
print(f"Saved: {out1}")
plt.close(fig1)

# ---------------------------------------------------------------------------
# Plot 2: invariant cemoid circuit (l=1, p=1)
# ---------------------------------------------------------------------------
fig2, ax2 = qml.draw_mpl(cemoid_circuit, decimals=None)(
    _zero_board, np.zeros(N_CEMOID_PARAMS)
)
ax2.set_title(
    f"Invariant cemoid circuit  |  l=1, p=1  |  "
    f"{N_CEMOID_PARAMS} shared params  "
    f"(cx, cz, ex, ez, mx, mz, o, i, d)  |  "
    f"18 single-qubit + 16 CRY gates"
)
out2 = HERE / "cemoid_circuit.png"
fig2.savefig(out2, dpi=150, bbox_inches="tight")
print(f"Saved: {out2}")
plt.close(fig2)
