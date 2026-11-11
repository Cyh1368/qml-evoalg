"""WP-TTT: tic-tac-toe terminal-board family (`tictactoe_n9`).

Run from the repository root (system python3 has no NumPy):

    cd ~/qml-evoalg
    module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
    python3 research/datasets/tictactoe/generate.py

Enumeration: every board reachable by alternating play from the empty board (X
moves first, cells -1=O, 0=empty, +1=X). Play is *not* stopped at the first win,
so boards that contain a completed line plus later marks are reachable too. Only
TERMINAL boards are kept, where terminal means: X has a line of three, or O has a
line of three, or the board is full.

Artifacts mirror `save_family` in ../generate.py: `development/<name>.npz` holds
the train+validation arrays, `locked_holdout/<name>.npz` holds the sealed test
arrays. Keys are `x_<split>`, `orbit_<split>`, `y_<target>_<split>`. The manifest
is self-contained in this directory; the parent research/datasets/manifest.json is
not edited.

Holdout files are an access contract, not a filesystem security boundary.
"""
from hashlib import sha256
from pathlib import Path
import json

import numpy as np

HERE = Path(__file__).resolve().parent
SEED = 20261110
NAME = 'tictactoe_n9'
X, O = 1, -1
# D4 on row-major 3x3 cell indices; a board transforms as (g.x)[i] = x[p[i]].
ROTATION = (6, 3, 0, 7, 4, 1, 8, 5, 2)
REFLECTION = (2, 1, 0, 5, 4, 3, 8, 7, 6)
LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))
# Counterfactual targets: sign of `winner` flips when the winner owns a line
# through this designated cell.
DESIGNATED = {'winner_designated': 4, 'winner_designated_corner': 0}


def d4_elements():
    """Closure of the two generators: all 8 D4 permutations of the 9 cells."""
    def compose(p, q):  # apply q, then p: (p*q)[i] = p[q[i]]
        return tuple(p[q[i]] for i in range(9))
    identity = tuple(range(9))
    elements = {identity}
    frontier = [identity]
    while frontier:
        p = frontier.pop()
        for g in (ROTATION, REFLECTION):
            for h in (compose(p, g), compose(g, p)):
                if h not in elements:
                    elements.add(h)
                    frontier.append(h)
    assert len(elements) == 8, 'D4 generators produced %d elements' % len(elements)
    return sorted(elements)


D4 = d4_elements()


def winning_lines(board, value):
    return [line for line in LINES if all(board[i] == value for i in line)]


def winner_of(board):
    """+1 if X has a line (checked first), else -1 if O has a line, else 0."""
    if winning_lines(board, X):
        return 1
    if winning_lines(board, O):
        return -1
    return 0


def designated_of(board, cell):
    """`winner`, sign-flipped when the winner owns a line through `cell`; draws stay 0."""
    winner = winner_of(board)
    if winner == 0:
        return 0
    return -winner if any(cell in line for line in winning_lines(board, winner)) else winner


def is_terminal(board):
    return bool(winning_lines(board, X) or winning_lines(board, O) or all(board))


def reachable_boards():
    """All boards reachable by alternating play from the empty board, X first."""
    empty = (0,) * 9
    seen = {empty}
    frontier = [(empty, X)]
    while frontier:
        nxt = []
        for board, player in frontier:
            for cell, mark in enumerate(board):
                if mark:
                    continue
                moved = list(board)
                moved[cell] = player
                moved = tuple(moved)
                if moved not in seen:
                    seen.add(moved)
                    nxt.append((moved, -player))
        frontier = nxt
    return sorted(seen)


def transform(row, perm):
    return tuple(row[i] for i in perm)


def canonical_orbit_ids(x):
    """Exact canonical orbit ids: lexicographic minimum over all 8 group elements."""
    rows = x.tolist()
    canonical = np.array([min(transform(row, p) for p in D4) for row in rows], dtype=np.int8)
    _, inverse = np.unique(canonical, axis=0, return_inverse=True)
    return canonical, inverse.reshape(-1).astype(np.int64)


def violation_fraction(x, y, oracle):
    """Fraction of (row, group element) pairs whose recomputed label differs."""
    rows = x.tolist()
    violations = 0
    for row, label in zip(rows, y.tolist()):
        for perm in D4:
            violations += oracle(transform(row, perm)) != label
    return violations / (len(rows) * len(D4))


def split_orbits(ids, rng):
    unique = np.unique(ids)
    rng.shuffle(unique)
    a, b = int(.6 * len(unique)), int(.8 * len(unique))
    return {name: np.isin(ids, group)
            for name, group in zip(('train', 'validation', 'test'), (unique[:a], unique[a:b], unique[b:]))}


def save_family(name, x, ys, orbit, split, metadata):
    development, locked = HERE / 'development', HERE / 'locked_holdout'
    development.mkdir(exist_ok=True)
    locked.mkdir(exist_ok=True)
    payload, test, counts = {}, {}, {}
    for s, mask in split.items():
        dest = test if s == 'test' else payload
        dest['x_' + s] = x[mask]
        dest['orbit_' + s] = orbit[mask]
        for task, y in ys.items():
            dest['y_' + task + '_' + s] = y[mask]
        counts[s] = {'rows': int(mask.sum()),
                     'orbits': int(len(np.unique(orbit[mask]))),
                     'target_means': {task: float(y[mask].mean()) for task, y in ys.items()}}
    paths = [development / (name + '.npz'), locked / (name + '.npz')]
    np.savez_compressed(paths[0], **payload)
    np.savez_compressed(paths[1], **test)
    return dict(metadata, counts=counts,
                files={str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest() for p in paths})


def main():
    rng = np.random.default_rng(SEED)
    boards = [board for board in reachable_boards() if is_terminal(board)]
    x = np.array(boards, dtype=np.float64)
    ys = {'winner': np.array([winner_of(b) for b in boards], dtype=np.int8)}
    for task, cell in DESIGNATED.items():
        ys[task] = np.array([designated_of(b, cell) for b in boards], dtype=np.int8)
    _, orbit = canonical_orbit_ids(x.astype(np.int8))
    split = split_orbits(orbit, rng)
    oracles = {'winner': winner_of}
    oracles.update({task: (lambda b, c=cell: designated_of(b, c)) for task, cell in DESIGNATED.items()})
    invariance = {task: {'designated_cell': DESIGNATED.get(task),
                         'measured_violation_fraction': violation_fraction(x, y, oracles[task])}
                  for task, y in ys.items()}
    invariance['winner']['designated_cell'] = None
    metadata = {
        'n': 9,
        'group': 'D4',
        'generators': {'rotation': list(ROTATION), 'reflection': list(REFLECTION)},
        'lines': [list(line) for line in LINES],
        'encoding': 'row-major 3x3 cells; -1=O, 0=empty, +1=X; x arrays are float64 shape (rows, 9)',
        'sampling': ('All terminal tic-tac-toe boards reachable by alternating play from the empty '
                     'board with X first. Play continues after a win, so boards carrying extra marks '
                     'beyond a completed line are reachable and are kept when terminal. Exact D4 '
                     'orbits (lexicographic minimum over all 8 elements) are shuffled once with '
                     'default_rng(20261110) and allocated 60/20/20 to train/validation/test; whole '
                     'orbits never cross splits. Labeled boards are weighted uniformly within each '
                     'split, so larger orbits carry more weight. No class balancing.'),
        'reachability_rule': 'board reachable from the empty board by alternating X,O,X,... moves with X first; move counts satisfy nX == nO or nX == nO + 1',
        'terminal_rule': 'X owns at least one of the 8 lines, or O owns at least one line, or the board is full (no empty cell)',
        'tasks': list(ys),
        'targets': {
            'winner': ('D4-invariant target. +1 if X owns at least one line (tested first), else -1 if O '
                       'owns at least one line, else 0 (full board with no line, i.e. a draw). X is '
                       'tested first, which resolves the boards where play continued past a win and '
                       'both players own a line; that tie-break is itself D4-invariant.'),
            'winner_designated': ('Counterfactual requested by WP-TTT. Exact rule: let w = winner(board) '
                                  'and L = the lines owned by w. If w == 0 the label is 0. Otherwise the '
                                  'label is -w (a sign flip) if at least one line in L contains cell 4 (the centre), '
                                  'and +w otherwise. Cell 4 is fixed by every element of D4 and lines map '
                                  'to lines, so this predicate is D4-invariant: measured violation '
                                  'fraction is 0.0, i.e. as specified it does NOT break D4. See notes.'),
            'winner_designated_corner': ('Supplementary counterfactual that does break D4. Exact rule: '
                                         'let w = winner(board) and L = the lines owned by w. If w == 0 the '
                                         'label is 0. Otherwise the label is -w if at least one line in L '
                                         'contains cell 0 (the top-left corner), and +w otherwise; i.e. the '
                                         'same sign flip as winner_designated but keyed on a corner. Cell 0 '
                                         'is not fixed by D4 (its orbit is the four corners), so a line '
                                         'through cell 0 can move off cell 0 under a rotation or reflection '
                                         'and the label changes.'),
        },
        'invariance': invariance,
        'notes': [
            'X-priority tie-break in `winner` matters: because play is not stopped at the first win, '
            'terminal boards exist where both players own a line (e.g. X top row, O middle row, X bottom '
            'row). They are labeled +1.',
            'WP-TTT asked for a D4-breaking counterfactual using the centre cell. The centre is fixed by '
            'all 8 group elements, so any predicate of the form "the winning line contains cell 4" is '
            'D4-invariant and cannot break the symmetry; validate.py reports the measured violation '
            'fraction (0.0) and flags the specification defect. `winner_designated` is kept exactly as '
            'requested and `winner_designated_corner` (designated cell 0) is provided as the working '
            'counterfactual.',
            'The terminal predicate is applied to every reachable board, so play is not stopped at the '
            'first win. Under the stricter stop-at-first-win-or-full-board convention the family would '
            'hold 958 boards instead of 1526; the 156 boards where both players own a line, and the '
            'X-priority tie-break, arise only under the convention used here. Draws are the 16 full '
            'boards with no line for either player.',
            'This family is discrete classification on {-1,0,1} boards. It has no continuous '
            'symmetry-breaking control variable and no quadratic defect law; unlike ring_n6 there are no '
            'alpha conditions and no alpha-squared target-defect scaling to report.',
        ],
    }
    record = save_family(NAME, x, ys, orbit, split, metadata)
    manifest = {
        'seed': SEED,
        'protocol': ('WP-TTT prospective family, generated independently of the parent datasets '
                     'manifest. Split and targets are fixed before training. The locked holdout is '
                     'sealed: locked_holdout/tictactoe_n9.npz must stay outside every search context and '
                     'is opened once, only after architecture, optimizer, seeds and analysis choices are '
                     'frozen. This directory naming is an access contract, not a filesystem security '
                     'boundary.'),
        'families': {NAME: record},
    }
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'reachable_states': len(reachable_boards()), 'terminal_rows': len(x),
                      'orbits': int(len(np.unique(orbit))), 'counts': record['counts']}, indent=2))


if __name__ == '__main__':
    main()
