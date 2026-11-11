"""Frozen task adapters for the three benchmark families (see INTERFACES.md).

Each family exposes a :class:`TaskSpec`: the true transformation group (used
only by trusted code paths), the fixed feature map and observable set, the
dataset arrays with their train/validation splits, and a ``label_oracle`` that
recomputes every target from arbitrary input rows so that hypothesis
label-preservation can be tested on transformed data.

Locked holdout access is an access contract, not a filesystem boundary:
``load_family(..., locked=True)`` prints a loud warning and is forbidden inside
``research/search`` (see ``LOCKED_FORBIDDEN_IN`` in research/search/harness.py).
"""
from dataclasses import dataclass
from itertools import combinations
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS = REPO_ROOT / "research" / "datasets"

# Grep-able mirror of the search-side guard; locked data never enters search.
LOCKED_FORBIDDEN_IN = ("research/search",)
LOCKED_WARNING = (
    "*" * 78 + "\n"
    "*** LOCKED HOLDOUT OPENED *** sealed test arrays are being read.\n"
    "*** These rows are for the ONE-TIME final evaluation only. They must never\n"
    "*** reach model selection, hyperparameter tuning, or anything under\n"
    "*** research/search (LOCKED_FORBIDDEN_IN=%s).\n" % (LOCKED_FORBIDDEN_IN,) +
    "*" * 78)

# Graph edge order: lexicographic node pairs, matching manifest.json feature_pairs.
GRAPH_PAIRS = list(combinations(range(6), 2))
RING_ALPHAS = (0.0, 0.1, 0.25, 0.5, 1.0)
TTT_LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
             (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))
TTT_ROTATION = (6, 3, 0, 7, 4, 1, 8, 5, 2)
TTT_REFLECTION = (2, 1, 0, 5, 4, 3, 8, 7, 6)
# target -> designated cell whose winning lines flip the winner's sign
# (None = the plain D4-invariant winner; cell 4 is the D4-fixed sham control).
TTT_DESIGNATED = {"winner": None, "winner_designated": 4,
                  "winner_designated_corner": 0}


@dataclass
class TaskSpec:
    """One benchmark family: inputs, group, fixed ansatz ingredients, targets."""
    name: str
    n_qubits: int
    group_name: str
    generators: list
    feature_map: object
    observables: list
    targets: dict
    x: np.ndarray
    orbit: np.ndarray
    splits: dict
    label_oracle: object
    primary_target: str
    target_keys: tuple = ()
    dataset_path: str = ""


# --------------------------------------------------------------- ingredients
def z_observables(n):
    """Diagonal observables: every Z_i, then every Z_iZ_j (lexicographic)."""
    obs = [{(i,): 1.0} for i in range(n)]
    obs += [{(i, j): 1.0} for i, j in combinations(range(n), 2)]
    return obs


def adjacent_transpositions(n):
    """S_n adjacent transpositions (i, i+1), one-line notation."""
    result = []
    for i in range(n - 1):
        perm = list(range(n))
        perm[i], perm[i + 1] = perm[i + 1], perm[i]
        result.append(perm)
    return result


def _dihedral(n):
    """D_n on n sites: the n-cycle and the reflection i -> -i mod n."""
    return [[(i + 1) % n for i in range(n)], [(-i) % n for i in range(n)]]


def _manifest_feature_pairs():
    """Edge order from research/datasets/manifest.json (falls back to lex)."""
    try:
        manifest = json.loads((DATASETS / "manifest.json").read_text())
        pairs = [tuple(pair) for pair in
                 manifest["families"]["graphs_n6"]["feature_pairs"]]
    except (OSError, KeyError, ValueError):
        return list(GRAPH_PAIRS)
    return pairs if pairs else list(GRAPH_PAIRS)


# --------------------------------------------------------------- label oracles
def graph_oracle_column(key, rows):
    """Recompute graph labels on 15-bit edge rows: BFS connectedness/triangle."""
    rows = np.asarray(rows)
    if rows.ndim == 1:
        rows = rows[None, :]
    if rows.shape[1] != len(GRAPH_PAIRS):
        raise ValueError("graphs rows must have %d edge bits, got %d"
                         % (len(GRAPH_PAIRS), rows.shape[1]))
    bits = rows.astype(np.int64) != 0
    adjacency = np.zeros((len(bits), 6, 6), dtype=bool)
    for k, (a, b) in enumerate(GRAPH_PAIRS):
        adjacency[:, a, b] = adjacency[:, b, a] = bits[:, k]
    if key == "connected":
        reach = adjacency.copy()          # transitive closure (BFS-equivalent)
        for k in range(6):
            reach |= reach[:, :, k, None] & reach[:, None, k, :]
        values = reach.all(axis=(1, 2))
    elif key == "triangle":
        values = np.zeros(len(bits), dtype=bool)
        for a, b, c in combinations(range(6), 3):
            values |= (adjacency[:, a, b] & adjacency[:, b, c]
                       & adjacency[:, a, c])
    else:
        raise ValueError("unknown graphs target %r" % key)
    return values.astype(np.int8) * 2 - 1


def ring_oracle_column(key, rows):
    """alpha target recomputed analytically: mean_i x_i x_{i+1} + alpha (x_0 - mean x)."""
    rows = np.asarray(rows, dtype=float)
    if rows.ndim == 1:
        rows = rows[None, :]
    if rows.shape[1] != 6:
        raise ValueError("ring rows must have 6 sites, got %d" % rows.shape[1])
    try:
        alpha = float(key.split("_", 1)[1])
    except (IndexError, ValueError):
        raise ValueError("ring target must look like 'alpha_<value>', got %r" % key)
    invariant = np.mean(rows * np.roll(rows, 1, axis=1), axis=1)
    breaking = rows[:, 0] - rows.mean(axis=1)
    return invariant + alpha * breaking


def ttt_oracle_column(key, rows):
    """Terminal classification (+1 X line first, -1 O line, else 0) and the
    designated-cell sign flip, recomputed on arbitrary (rows, 9) boards."""
    rows = np.asarray(rows, dtype=float)
    if rows.ndim == 1:
        rows = rows[None, :]
    if rows.shape[1] != 9:
        raise ValueError("tictactoe rows must have 9 cells, got %d" % rows.shape[1])
    if key not in TTT_DESIGNATED:
        raise ValueError("unknown tictactoe target %r" % key)
    board = np.rint(rows).astype(np.int64)
    lines_x = np.stack([(board[:, list(line)] == 1).all(axis=1) for line in TTT_LINES])
    lines_o = np.stack([(board[:, list(line)] == -1).all(axis=1) for line in TTT_LINES])
    winner = np.where(lines_x.any(axis=0), 1,
                      np.where(lines_o.any(axis=0), -1, 0))
    cell = TTT_DESIGNATED[key]
    if cell is None:
        return winner.astype(np.int8)
    owned_x = np.zeros(len(board), dtype=bool)
    owned_o = np.zeros(len(board), dtype=bool)
    for values, line, mask in ((lines_x, TTT_LINES, owned_x),
                               (lines_o, TTT_LINES, owned_o)):
        for line_values, line_cells in zip(values, line):
            if cell in line_cells:
                mask |= line_values
    flipped = np.where(winner == 1, owned_x, np.where(winner == -1, owned_o, False))
    return np.where(flipped, -winner, winner).astype(np.int8)


_ORACLE_COLUMNS = {"graphs_n6": graph_oracle_column, "ring_n6": ring_oracle_column,
                   "tictactoe_n9": ttt_oracle_column}


def _make_label_oracle(family, target_keys):
    column = _ORACLE_COLUMNS[family]
    keys = tuple(target_keys)

    def label_oracle(x_rows, target=None):
        """Recompute labels for arbitrary rows.

        Returns an ``(m, len(target_keys))`` float array whose columns follow
        ``target_keys``; pass ``target=<key>`` for a single ``(m,)`` column.
        """
        columns = [np.asarray(column(family_key, x_rows), dtype=float).reshape(-1)
                   for family_key in keys]
        matrix = np.stack(columns, axis=1)
        if target is None:
            return matrix
        if target not in keys:
            raise KeyError("unknown target %r; family %s has %s"
                           % (target, family, list(keys)))
        return matrix[:, keys.index(target)]

    label_oracle.__name__ = "%s_label_oracle" % family
    return label_oracle


# --------------------------------------------------------------- feature maps
def _graphs_feature_map(x):
    """RZZ(pi/2) on every edge whose bit is 1, in manifest edge order."""
    bits = np.asarray(x).reshape(-1)
    if bits.size != len(GRAPH_PAIRS):
        raise ValueError("graphs input must have %d edge bits, got %d"
                         % (len(GRAPH_PAIRS), bits.size))
    pairs = _manifest_feature_pairs()
    return [{"gate": "RZZ", "wires": [int(a), int(b)], "angle": np.pi / 2}
            for (a, b), bit in zip(pairs, bits) if float(bit) != 0.0]


def _ring_feature_map(x):
    """RY(x_i) on wire i (angle = x_i)."""
    values = np.asarray(x, dtype=float).reshape(-1)
    if values.size != 6:
        raise ValueError("ring input must have 6 sites, got %d" % values.size)
    return [{"gate": "RY", "wire": i, "angle": float(value)}
            for i, value in enumerate(values)]


def _tictactoe_feature_map(x):
    """RY(theta_c) with theta in {0, pi/2, pi} for O / empty / X."""
    cells = np.asarray(x, dtype=float).reshape(-1)
    if cells.size != 9:
        raise ValueError("tictactoe input must have 9 cells, got %d" % cells.size)
    return [{"gate": "RY", "wire": c, "angle": (float(value) + 1.0) * np.pi / 2}
            for c, value in enumerate(cells)]


_BUILDERS = {
    "graphs_n6": {
        "dir": DATASETS, "n_qubits": 6, "group_name": "S6",
        "generators": lambda: adjacent_transpositions(6),
        "feature_map": _graphs_feature_map,
        "primary_target": "connected",
    },
    "ring_n6": {
        "dir": DATASETS, "n_qubits": 6, "group_name": "D6",
        "generators": lambda: _dihedral(6),
        "feature_map": _ring_feature_map,
        "primary_target": "alpha_0",
    },
    "tictactoe_n9": {
        "dir": DATASETS / "tictactoe", "n_qubits": 9, "group_name": "D4",
        "generators": lambda: [list(TTT_ROTATION), list(TTT_REFLECTION)],
        "feature_map": _tictactoe_feature_map,
        "primary_target": "winner",
    },
}


# --------------------------------------------------------------- loading
def _target_keys(keys, split):
    suffix = "_" + split
    return tuple(key[2:-len(suffix)] for key in keys
                 if key.startswith("y_") and key.endswith(suffix))


def dataset_path(name, locked=False):
    spec = _BUILDERS.get(name)
    if spec is None:
        raise ValueError("unknown family %r; known families: %s"
                         % (name, ", ".join(sorted(_BUILDERS))))
    folder = "locked_holdout" if locked else "development"
    return spec["dir"] / folder / (name + ".npz")


def load_family(name, development=True, locked=False):
    """Load one family. ``locked=True`` reads the sealed holdout (loud warning)."""
    if name not in _BUILDERS:
        raise ValueError("unknown family %r; known families: %s"
                         % (name, ", ".join(sorted(_BUILDERS))))
    spec = _BUILDERS[name]
    path = dataset_path(name, locked=locked)
    if locked:
        print(LOCKED_WARNING)
        print(LOCKED_WARNING, file=sys.stderr)
        splits_wanted = ("test",)
    else:
        if not development:
            raise ValueError("load_family(name, development=False) is meaningless "
                             "without locked=True; use locked=True for the holdout")
        splits_wanted = ("train", "validation")
    if not path.exists():
        raise FileNotFoundError("dataset artifact missing: %s" % path)
    with np.load(path) as data:
        keys = list(data.keys())
        target_keys = _target_keys(keys, splits_wanted[0])
        blocks, oracles, targets = [], [], {key: [] for key in target_keys}
        for split in splits_wanted:
            blocks.append(np.asarray(data["x_" + split]))
            oracles.append(np.asarray(data["orbit_" + split]))
            for key in target_keys:
                targets[key].append(np.asarray(data["y_%s_%s" % (key, split)]))
    x = np.concatenate(blocks, axis=0)
    orbit = np.concatenate(oracles, axis=0)
    merged = {key: np.concatenate(values, axis=0) for key, values in targets.items()}
    offsets, cursor = {}, 0
    for split, block in zip(splits_wanted, blocks):
        mask = np.zeros(len(x), dtype=bool)
        mask[cursor:cursor + len(block)] = True
        offsets[split] = mask
        cursor += len(block)
    for key, values in merged.items():
        if len(values) != len(x):
            raise ValueError("target %s has %d rows, inputs have %d"
                             % (key, len(values), len(x)))
    return TaskSpec(
        name=name, n_qubits=int(spec["n_qubits"]), group_name=spec["group_name"],
        generators=[list(p) for p in spec["generators"]()],
        feature_map=spec["feature_map"], observables=z_observables(int(spec["n_qubits"])),
        targets=merged, x=x, orbit=orbit, splits=offsets,
        label_oracle=_make_label_oracle(name, target_keys),
        primary_target=spec["primary_target"], target_keys=target_keys,
        dataset_path=str(path))
