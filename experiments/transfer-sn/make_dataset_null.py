"""Null-symmetry control dataset for the validation-criteria experiment.

Run locally, NEVER shipped to the evolution loop (same rule as make_dataset.py).

Purpose
-------
VALIDATION_CRITERIA.md proposes that a structural motif recurring across
independent reruns is evidence the structure is real. Every test so far has
been on a task that HAS the structure. This builds the negative control: a task
with no permutation symmetry to find, so we can check whether the criterion
correctly returns "nothing here" rather than manufacturing agreement.

Design
------
Inputs are byte-identical in distribution to the real task. Same 8 vertices,
same 28 upper-triangle adjacency bits, same scrambled qubit relabeling and pair
order (same RNG seed and same call sequence, so FEATURE_PAIRS matches
dataset.npz exactly), same edge-density sampling. The evolution loop cannot
tell the two datasets apart from the feature format.

Only the labelling rule changes:

    real:  label = +1 iff the graph is CONNECTED       -> invariant under S_8
    null:  label = +1 iff deg(v*) >= THRESHOLD         -> NOT invariant under S_8

v* is one fixed vertex. Relabelling vertices moves v*, so the label is not
preserved by a generic permutation. The stabilizer of the rule is S_7 acting on
the other seven vertices, which does NOT act on the ansatz the way S_8 does:
the optimal circuit must single out one qubit, i.e. it must be ASYMMETRIC,
which is the opposite of the tied-parameter structure the real task rewards.

Expected outcome if the criterion in VALIDATION_CRITERIA.md is sound: frontier
runs on this dataset should NOT converge on a fully tied parameter family, and
the motif recurrence across runs should be low. If instead frontier ties
parameters consistently here too, the criterion is detecting "frontier models
like tying parameters" rather than "the problem has a symmetry", and the
hypothesis fails.

Usage:  viz/.venv_render/bin/python transfer-sn/make_dataset_null.py
Writes: dataset_null.npz + answer_key_null.json (local only)
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
N = 8

# Same seed and same first two draws as make_dataset.py, so the scrambled
# presentation is IDENTICAL to the real task. Do not reorder these.
RNG = np.random.default_rng(2027)
QUBIT_RELABEL = RNG.permutation(N)
PAIRS_CANON = list(combinations(range(N), 2))
PAIR_ORDER = RNG.permutation(len(PAIRS_CANON))

FEATURE_PAIRS = [
    tuple(int(QUBIT_RELABEL[v]) for v in PAIRS_CANON[PAIR_ORDER[k]])
    for k in range(len(PAIRS_CANON))
]

# The distinguished vertex and threshold. V_STAR is arbitrary but fixed;
# THRESHOLD is tuned in calibrate() to give a ~50/50 split under the same
# edge-density sampling the real task uses.
V_STAR = 3
THRESHOLD = 2

INCIDENT = [k for k, pc in enumerate(PAIRS_CANON) if V_STAR in pc]  # canonical idx


def degree_vstar(adj_bits: np.ndarray) -> int:
    """Degree of V_STAR from canonical-order adjacency bits."""
    return int(adj_bits[INCIDENT].sum())


def label_null(adj_bits: np.ndarray) -> int:
    return 1 if degree_vstar(adj_bits) >= THRESHOLD else -1


def connected(adj_bits: np.ndarray) -> bool:
    """Real-task rule, kept only so we can report how the two labellings differ."""
    adj = np.zeros((N, N), dtype=bool)
    for idx, (a, b) in enumerate(PAIRS_CANON):
        if adj_bits[idx]:
            adj[a, b] = adj[b, a] = True
    seen, stack = {0}, [0]
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
        p = RNG.uniform(0.12, 0.45)          # identical density range to real task
        bits = (RNG.random(len(PAIRS_CANON)) < p).astype(np.int8)
        key = bits.tobytes()
        if key in seen:
            continue
        if label_null(bits) != target_label:
            continue
        seen.add(key)
        out.append(bits[PAIR_ORDER])          # scrambled presentation
    return out


def calibrate() -> None:
    """Report the class split for each candidate threshold under the real
    task's density sampling, so THRESHOLD is chosen on evidence."""
    rng = np.random.default_rng(99)
    bits = np.stack([
        (rng.random(len(PAIRS_CANON)) < rng.uniform(0.12, 0.45)).astype(np.int8)
        for _ in range(20000)
    ])
    degs = bits[:, INCIDENT].sum(axis=1)
    print("threshold calibration (fraction labelled +1):")
    for t in range(0, 8):
        print(f"   deg(v*) >= {t}:  {np.mean(degs >= t):.3f}")
    print(f"   mean deg(v*) = {degs.mean():.2f}")


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
        HERE / "dataset_null.npz",
        x_train=splits["train"][0], y_train=splits["train"][1],
        x_validation=splits["validation"][0], y_validation=splits["validation"][1],
        x_test=splits["test"][0], y_test=splits["test"][1],
        feature_pairs=np.array(FEATURE_PAIRS, dtype=np.int8),
    )
    (HERE / "answer_key_null.json").write_text(json.dumps({
        "task": f"n=8 Erdos-Renyi, label = deg(v{V_STAR}) >= {THRESHOLD}",
        "symmetry": "NONE under S_8; rule singles out one vertex",
        "v_star": V_STAR,
        "threshold": THRESHOLD,
        "incident_features_canonical": INCIDENT,
        "qubit_relabel": QUBIT_RELABEL.tolist(),
        "pair_order": PAIR_ORDER.tolist(),
    }, indent=2))
    for name, (x, y) in splits.items():
        print(f"{name}: {len(x)} rows, class balance {np.mean(y > 0):.2f}, "
              f"mean edge density {x.mean():.3f}")
    print("saved dataset_null.npz + answer_key_null.json (local only)")


if __name__ == "__main__":
    import sys
    if "--calibrate" in sys.argv:
        calibrate()
    else:
        main()
