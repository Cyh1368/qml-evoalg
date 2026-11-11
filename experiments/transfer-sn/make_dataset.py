"""Offline dataset generator for transfer task A (run locally, NEVER shipped
to the evolution loop). Produces dataset.npz consumed opaquely by
initial_program.py, so the labeling rule exists nowhere in code the LLM sees.

Task (known only to us): n=8 undirected Erdos-Renyi graphs, label = connected
(+1) vs disconnected (-1). Features are the 28 upper-triangle adjacency bits,
presented in a SCRAMBLED fixed pair order under a SCRAMBLED qubit labeling so
the feature list carries no lexicographic hint of "all pairs of 8 items".

Ground-truth symmetry (the answer key, absent from all shipped artifacts):
S_8 — any relabeling of the 8 vertices permutes features and qubits jointly
and leaves the label invariant.
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
N = 8
RNG = np.random.default_rng(2027)

# Scrambled presentation (fixed): random qubit relabeling + random pair order.
QUBIT_RELABEL = RNG.permutation(N)                     # vertex v -> qubit QUBIT_RELABEL[v]
PAIRS_CANON = list(combinations(range(N), 2))          # 28 vertex pairs, canonical order
PAIR_ORDER = RNG.permutation(len(PAIRS_CANON))         # feature k -> canonical pair PAIR_ORDER[k]

FEATURE_PAIRS = [
    tuple(int(QUBIT_RELABEL[v]) for v in PAIRS_CANON[PAIR_ORDER[k]])
    for k in range(len(PAIRS_CANON))
]  # feature index k couples this (scrambled) qubit pair


def connected(adj_bits: np.ndarray) -> bool:
    adj = np.zeros((N, N), dtype=bool)
    for idx, (a, b) in enumerate(PAIRS_CANON):
        if adj_bits[idx]:
            adj[a, b] = adj[b, a] = True
    seen = {0}
    stack = [0]
    while stack:
        u = stack.pop()
        for v in range(N):
            if adj[u, v] and v not in seen:
                seen.add(v)
                stack.append(v)
    return len(seen) == N


def sample_class(target_label: int, count: int, seen: set) -> list:
    out = []
    while len(out) < count:
        p = RNG.uniform(0.12, 0.45)
        bits = (RNG.random(len(PAIRS_CANON)) < p).astype(np.int8)
        key = bits.tobytes()
        if key in seen:
            continue
        lab = 1 if connected(bits) else -1
        if lab != target_label:
            continue
        seen.add(key)
        # present features in the scrambled order
        out.append(bits[PAIR_ORDER])
    return out


def main() -> None:
    sizes = {"train": 450, "validation": 300, "test": 600}
    seen: set = set()
    splits = {}
    for name, size in sizes.items():
        per = size // 2
        xs = sample_class(1, per, seen) + sample_class(-1, per, seen)
        ys = np.array([1.0] * per + [-1.0] * per)
        order = RNG.permutation(size)
        splits[name] = (np.array(xs, dtype=np.int8)[order], ys[order])

    np.savez_compressed(
        HERE / "dataset.npz",
        x_train=splits["train"][0], y_train=splits["train"][1],
        x_validation=splits["validation"][0], y_validation=splits["validation"][1],
        x_test=splits["test"][0], y_test=splits["test"][1],
        feature_pairs=np.array(FEATURE_PAIRS, dtype=np.int8),
    )
    # Answer key kept LOCAL only (gitignored from the shipped dir if needed):
    (HERE / "answer_key.json").write_text(json.dumps({
        "task": "n=8 Erdos-Renyi connectedness (+1 connected)",
        "symmetry": "S_8 joint permutation of qubits/features",
        "qubit_relabel": QUBIT_RELABEL.tolist(),
        "pair_order": PAIR_ORDER.tolist(),
    }, indent=2))
    for name, (x, y) in splits.items():
        print(f"{name}: {len(x)} rows, class balance {np.mean(y > 0):.2f}, "
              f"mean edge density {x.mean():.3f}")
    print("saved dataset.npz + answer_key.json (local only)")


if __name__ == "__main__":
    main()
