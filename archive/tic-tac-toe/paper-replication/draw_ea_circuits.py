"""Render circuit diagrams for the top-3 EA-evolved tic-tac-toe ansatze.

For each program we draw:
  * one evolved ANSATZ_SPEC block (the part the EA actually optimised), and
  * the full re-uploading circuit (3 uploads x 2 repeats).

Outputs: ea_circuit_<short_id>_block.png and ea_circuit_<short_id>_full.png
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pennylane as qml

HERE = Path(__file__).resolve().parent
PROG_DIR = HERE / "ea_programs"
MANIFEST = json.loads((PROG_DIR / "manifest.json").read_text())


def load_module(short_id, idx):
    path = PROG_DIR / f"prog_{short_id}.py"
    spec = importlib.util.spec_from_file_location(f"ea_prog_draw_{idx}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def draw_block(mod, info):
    """Draw a single evolved ansatz block."""
    dev = qml.device("default.qubit", wires=mod.N_QUBITS)

    @qml.qnode(dev)
    def block_circuit(params):
        mod.apply_ansatz_block(params, 0)
        return [qml.expval(qml.PauliZ(w)) for w in range(mod.N_QUBITS)]

    params = np.linspace(0.1, 0.5, mod.N_PARAMS)
    fig, ax = qml.draw_mpl(block_circuit, decimals=None, style="pennylane")(params)
    fig.suptitle(
        f"EA program {info['short_id']} — one evolved ANSATZ block\n"
        f"gen {info['generation']}, {info['n_params']} params total, "
        f"{mod.N_PARAMS_PER_BLOCK} params/block, depth {info['depth']:.0f}",
        fontsize=11,
    )
    out = HERE / f"ea_circuit_{info['short_id']}_block.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {out}")


def draw_full(mod, info):
    """Draw the full re-uploading circuit."""
    dev = qml.device("default.qubit", wires=mod.N_QUBITS)

    @qml.qnode(dev)
    def full_circuit(board, params):
        return mod.circuit_z_expectations(board, params)

    board = np.zeros(mod.N_QUBITS, dtype=np.int8)
    params = np.linspace(0.1, 0.5, mod.N_PARAMS)
    fig, ax = qml.draw_mpl(full_circuit, decimals=None, style="pennylane")(board, params)
    fig.suptitle(
        f"EA program {info['short_id']} — full circuit "
        f"({mod.N_UPLOADS} uploads x {mod.N_REPEATS} repeats)\n"
        f"test acc {info['test_acc']:.3f}, depth {info['depth']:.0f}",
        fontsize=11,
    )
    out = HERE / f"ea_circuit_{info['short_id']}_full.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {out}")


def main():
    for idx, info in enumerate(MANIFEST):
        mod = load_module(info["short_id"], idx)
        draw_block(mod, info)
        draw_full(mod, info)


if __name__ == "__main__":
    main()
