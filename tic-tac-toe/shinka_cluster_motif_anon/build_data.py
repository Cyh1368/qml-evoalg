"""HIDDEN build step for the anonymized motif-discovery experiment.

NOT shown to the evolving LLM. Generates the precomputed, qubit-label-PERMUTED
data splits and the secret metadata (permutation, permuted winning lines,
permuted hardware edges, permuted readout groups) that the anonymized seed,
evaluator, and analysis all consume.

The learning problem is an exact relabeling of the original 9-qubit tic-tac-toe
task (isomorphic: identical labels, identical optimal accuracy), so results stay
comparable to the leaky run while removing every geometric hint about which
qubit triples are winning lines.

Run once:  python build_data.py
Outputs:   data_splits.npz , permutation_meta.json
"""
from __future__ import annotations
import json
from itertools import combinations
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent

# ---- original (unpermuted) task definition, used ONLY here to make labels ----
N_QUBITS = 9
WIN_LINES = (
    (0, 1, 2), (7, 8, 3), (6, 5, 4),
    (0, 7, 6), (1, 8, 5), (2, 3, 4),
    (0, 8, 4), (2, 8, 6),
)
GRID_EDGES = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (4, 5), (5, 6), (6, 7), (7, 0),
    (1, 8), (3, 8), (5, 8), (7, 8),
)
CORNERS = (0, 2, 4, 6)   # original readout: "circle"
EDGES = (1, 3, 5, 7)     # original readout: "cross"
CENTER = 8               # original readout: "draw"
CLASS_NAMES = ("class_0", "class_1", "class_2")  # was cross, circle, draw
LABEL_VECTORS = {
    "class_0": np.array([1.0, -1.0, -1.0]),   # was cross  (readout on EDGES)
    "class_1": np.array([-1.0, 1.0, -1.0]),   # was circle (readout on CORNERS)
    "class_2": np.array([-1.0, -1.0, 1.0]),   # was draw   (readout on CENTER)
}
# map board -> class using the ORIGINAL winning-line rule
def board_winner(board):
    for line in WIN_LINES:
        total = int(sum(int(board[i]) for i in line))
        if total == 3:
            return "class_0"   # cross wins
        if total == -3:
            return "class_1"   # circle wins
    return None
def board_label(board):
    return board_winner(board) or "class_2"
def enumerate_valid_boards():
    seen = set()
    def visit(board, player):
        if board in seen:
            return
        seen.add(board)
        if board_winner(board) is not None or all(v != 0 for v in board):
            return
        for wire, value in enumerate(board):
            if value == 0:
                nb = list(board); nb[wire] = player
                visit(tuple(nb), -player)
    visit((0,) * N_QUBITS, 1)
    return np.array(sorted(seen), dtype=np.int8)
def make_balanced_split(grouped, size, rng, replace):
    if size % len(CLASS_NAMES) != 0:
        raise ValueError("size must divide by 3")
    per = size // len(CLASS_NAMES)
    xs, ys = [], []
    for label in CLASS_NAMES:
        pool = grouped[label]
        local_replace = replace or per > len(pool)
        idx = rng.choice(len(pool), size=per, replace=local_replace)
        xs.append(pool[idx]); ys.append(np.tile(LABEL_VECTORS[label], (per, 1)))
    x = np.concatenate(xs, 0); y = np.concatenate(ys, 0)
    order = rng.permutation(len(x))
    return x[order], y[order]
def build_splits(seed=2027, sizes=(450, 300, 600), replace=True):
    rng = np.random.default_rng(seed)
    boards = enumerate_valid_boards()
    grouped = {n: [] for n in CLASS_NAMES}
    for b in boards:
        grouped[board_label(b)].append(b)
    grouped = {n: np.array(v, dtype=np.int8) for n, v in grouped.items()}
    tr = make_balanced_split(grouped, sizes[0], rng, replace)
    va = make_balanced_split(grouped, sizes[1], rng, replace)
    te = make_balanced_split(grouped, sizes[2], rng, replace)
    return tr, va, te

# ---- secret permutation: cell c is physically encoded on qubit PI[c] ----
PERM_SEED = 777
PI = np.random.default_rng(PERM_SEED).permutation(N_QUBITS)  # cell -> qubit
INV = np.argsort(PI)                                          # qubit -> cell

def permute_cols(x):
    # value of cell c must land in column PI[c]; column j holds cell INV[j]
    return x[:, INV]

def main():
    (x_tr, y_tr), (x_va, y_va), (x_te, y_te) = build_splits()
    np.savez(
        HERE / "data_splits.npz",
        x_train=permute_cols(x_tr).astype(np.int8), y_train=y_tr.astype(np.float32),
        x_val=permute_cols(x_va).astype(np.int8),   y_val=y_va.astype(np.float32),
        x_test=permute_cols(x_te).astype(np.int8),  y_test=y_te.astype(np.float32),
    )
    pwin = sorted(tuple(sorted(int(PI[i]) for i in t)) for t in WIN_LINES)
    pedges = sorted(tuple(sorted((int(PI[a]), int(PI[b])))) for a, b in GRID_EDGES)
    meta = {
        "perm_seed": PERM_SEED,
        "PI_cell_to_qubit": PI.tolist(),
        "INV_qubit_to_cell": INV.tolist(),
        "permuted_win_lines": pwin,
        "permuted_hardware_edges": pedges,
        "readout_group_a_was_edges": sorted(int(PI[i]) for i in EDGES),     # class_0
        "readout_group_b_was_corners": sorted(int(PI[i]) for i in CORNERS), # class_1
        "readout_group_c_was_center": int(PI[CENTER]),                      # class_2
        "n_all_triples": len(list(combinations(range(9), 3))),
        "note": "SECRET. Never expose to the evolving model. Ground truth for motif_analysis.",
    }
    (HERE / "permutation_meta.json").write_text(json.dumps(meta, indent=2))
    # sanity print
    for name, (x, y) in [("train", (x_tr, y_tr)), ("val", (x_va, y_va)), ("test", (x_te, y_te))]:
        cls = np.argmax(y, 1)
        print(f"{name}: n={len(x)} class_counts={np.bincount(cls, minlength=3).tolist()}")
    print("PI:", PI.tolist(), "permuted_win_lines:", pwin)
    print("wrote data_splits.npz + permutation_meta.json")

if __name__ == "__main__":
    main()
