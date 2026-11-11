"""Independent validation of the `tictactoe_n9` family (WP-TTT).

Run from the repository root after generate.py:

    cd ~/qml-evoalg
    module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
    python3 research/datasets/tictactoe/validate.py

Nothing here imports generate.py. The winning lines, the D4 action, the label
oracle and the reachability closure are rebuilt from scratch (geometry, base-3
state codes, depth-first search) so that labels, orbits and legality are checked
against an independent oracle rather than against the generator's own code.
Writes validation.json next to this file and exits non-zero on any failure.
"""
from hashlib import sha256
from pathlib import Path
import json
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
NAME = 'tictactoe_n9'
SAMPLE_PAIRS = 4000
SAMPLE_SEED = 20261110
EXPECTED_DESIGNATED = {'winner': None, 'winner_designated': 4, 'winner_designated_corner': 0}
checks = {}


def record(name, ok, **detail):
    checks[name] = dict(detail, status='PASS' if ok else 'FAIL')


def cell(row, col):
    return 3 * row + col


# --- independent geometry -----------------------------------------------------

def build_lines():
    """The 8 winning lines, derived from the 3x3 grid rather than hard-coded."""
    grid = np.arange(9).reshape(3, 3)
    lines = [tuple(grid[i, :]) for i in range(3)] + [tuple(grid[:, j]) for j in range(3)]
    lines += [tuple(np.diag(grid)), tuple(np.diag(grid[:, ::-1]))]
    return [frozenset(line) for line in lines]


LINES = build_lines()


def build_d4():
    """The 8 square symmetries as cell-index permutations, built from coordinate maps.

    Convention matches the dataset: (g.x)[i] = x[perm[i]].
    """
    coordinate_maps = [lambda r, c: (r, c), lambda r, c: (c, 2 - r), lambda r, c: (2 - r, 2 - c),
                       lambda r, c: (2 - c, r), lambda r, c: (r, 2 - c), lambda r, c: (2 - r, c),
                       lambda r, c: (c, r), lambda r, c: (2 - c, 2 - r)]
    perms = set()
    for mapping in coordinate_maps:
        perm = [None] * 9
        for r in range(3):
            for c in range(3):
                nr, nc = mapping(r, c)
                perm[cell(nr, nc)] = cell(r, c)
        perms.add(tuple(perm))
    assert len(perms) == 8, 'coordinate maps collapsed to %d permutations' % len(perms)
    return sorted(perms)


D4 = build_d4()


def oracle_labels(board):
    """Recompute every target label for one board from scratch."""
    occupied = {int(mark): {i for i, value in enumerate(board) if int(value) == int(mark)}
                for mark in (-1, 0, 1)}
    x_lines = [line for line in LINES if line <= occupied[1]]
    o_lines = [line for line in LINES if line <= occupied[-1]]
    winner = 1 if x_lines else (-1 if o_lines else 0)
    labels = {'winner': winner}
    for task, designated in EXPECTED_DESIGNATED.items():
        if task == 'winner':
            continue
        if winner == 0:
            labels[task] = 0
            continue
        owns = x_lines if winner == 1 else o_lines
        labels[task] = -winner if any(designated in line for line in owns) else winner
    return labels


def is_terminal(board):
    occupied = {int(mark): {i for i, value in enumerate(board) if int(value) == int(mark)}
                for mark in (-1, 0, 1)}
    return (any(line <= occupied[1] for line in LINES) or any(line <= occupied[-1] for line in LINES)
            or len(occupied[0]) == 0)


def move_count_valid(board):
    n_x = sum(1 for value in board if int(value) == 1)
    n_o = sum(1 for value in board if int(value) == -1)
    return n_x == n_o or n_x == n_o + 1


def encode(board):
    """Base-3 state code: digit 0 empty, 1 X, 2 O."""
    code = 0
    for value in reversed(board):
        code = code * 3 + (0 if int(value) == 0 else (1 if int(value) == 1 else 2))
    return code


def decode(code):
    digits = []
    for _ in range(9):
        code, digit = divmod(code, 3)
        digits.append(0 if digit == 0 else (1 if digit == 1 else -1))
    return tuple(digits)


def reachable_closure():
    """Depth-first closure over move sequences from the empty board, X first."""
    seen = {encode((0,) * 9)}
    stack = [(encode((0,) * 9), 1)]
    while stack:
        code, player = stack.pop()
        board = decode(code)
        digit = 1 if player == 1 else 2
        for index, value in enumerate(board):
            if value != 0:
                continue
            moved = code + digit * 3 ** index
            if moved not in seen:
                seen.add(moved)
                stack.append((moved, -player))
    return {decode(code) for code in seen}


def canonical(board):
    return min(tuple(board[perm[i]] for i in range(9)) for perm in D4)


def transform(board, perm):
    return tuple(board[perm[i]] for i in range(9))


# --- load artifacts -----------------------------------------------------------

manifest = json.loads((HERE / 'manifest.json').read_text())
family = manifest['families'][NAME]
dev = np.load(HERE / 'development' / f'{NAME}.npz')
test = np.load(HERE / 'locked_holdout' / f'{NAME}.npz')
SPLITS = {'train': dev, 'validation': dev, 'test': test}
TASKS = family['tasks']

rows, orbits, labels, origin = {}, {}, {}, []
for split in ('train', 'validation', 'test'):
    data = SPLITS[split]
    rows[split] = data['x_' + split]
    orbits[split] = data['orbit_' + split]
    labels[split] = {task: data[f'y_{task}_' + split] for task in TASKS}
ALL_X = np.concatenate([rows[s] for s in ('train', 'validation', 'test')])
ALL_ORBIT = np.concatenate([orbits[s] for s in ('train', 'validation', 'test')])
ALL_Y = {task: np.concatenate([labels[s][task] for s in ('train', 'validation', 'test')]) for task in TASKS}

# 1. file hashes
hashes = {path: sha256((HERE / path).read_bytes()).hexdigest() for path in family['files']}
record('file_hashes', hashes == family['files'], sha256=hashes)

# 2. key layout / sealed holdout separation
def expected_keys(split):
    return {'x_' + split, 'orbit_' + split} | {f'y_{t}_' + split for t in TASKS}
layout_ok = (set(dev.files) == expected_keys('train') | expected_keys('validation')
             and set(test.files) == expected_keys('test')
             and not any('test' in key for key in dev.files))
record('key_layout', layout_ok,
       development_keys=sorted(dev.files), locked_holdout_keys=sorted(test.files),
       note='development must hold train+validation only; locked_holdout holds test only')

# 3. board format
format_ok = all(arr.dtype == np.float64 and arr.ndim == 2 and arr.shape[1] == 9
                and set(np.unique(arr).tolist()) <= {-1.0, 0.0, 1.0} for arr in rows.values())
record('board_format', format_ok,
       rows={s: list(rows[s].shape) for s in rows},
       note='float64 shape (rows, 9) with values in {-1, 0, 1}')

# 4. legality, terminality, completeness (independent closure)
reachable = reachable_closure()
stored = [tuple(int(v) for v in row) for row in ALL_X]
stored_set = set(stored)
count_valid = all(move_count_valid(b) for b in stored)
in_closure = all(b in reachable for b in stored)
terminal_all = all(is_terminal(b) for b in stored)
expected_set = {b for b in reachable if is_terminal(b)}
complete = stored_set == expected_set
record('legal_terminal_and_complete', count_valid and in_closure and terminal_all and complete and len(stored) == len(stored_set),
       stored_rows=len(stored), unique_rows=len(stored_set), reachable_states=len(reachable),
       expected_terminal_boards=len(expected_set), count_valid=count_valid,
       reachable_by_independent_dfs=in_closure, all_terminal=terminal_all, completeness=complete,
       note='every stored board is count-valid, reachable by alternating play (independent DFS) and '
            'terminal; the stored set equals the full reachable-terminal set with no duplicates')

# 5. labels recomputed from scratch
label_mismatches = {}
for task in TASKS:
    recomputed = np.array([oracle_labels(b)[task] for b in stored], dtype=np.int8)
    label_mismatches[task] = int((recomputed != ALL_Y[task]).sum())
record('labels_recomputed_from_scratch', all(v == 0 for v in label_mismatches.values()),
       mismatching_rows=label_mismatches, rows=len(stored))

# 6. orbits: independent canonicalization induces the stored partition
canonical_rows = np.array([canonical(tuple(int(v) for v in row)) for row in ALL_X], dtype=np.int8)
_, independent_orbit = np.unique(canonical_rows, axis=0, return_inverse=True)
independent_orbit = independent_orbit.reshape(-1)
stored_to_independent = {}
independent_to_stored = {}
for stored_id, independent_id in zip(ALL_ORBIT.tolist(), independent_orbit.tolist()):
    stored_to_independent.setdefault(stored_id, set()).add(independent_id)
    independent_to_stored.setdefault(independent_id, set()).add(stored_id)
partition_ok = (all(len(v) == 1 for v in stored_to_independent.values())
                and all(len(v) == 1 for v in independent_to_stored.values())
                and len(stored_to_independent) == len(independent_to_stored))
record('orbit_canonicalization_independent', partition_ok,
       stored_orbits=int(len(set(ALL_ORBIT.tolist()))),
       independent_orbits=int(len(set(independent_orbit.tolist()))),
       note='lexicographic minimum over the independently constructed D4 gives a bijection with the '
            'stored orbit ids, so stored orbits are exact canonical classes')

# 7. no orbit (and no board) crosses splits
orbit_sets = {s: set(int(o) for o in orbits[s]) for s in ('train', 'validation', 'test')}
board_sets = {s: {tuple(int(v) for v in row) for row in rows[s]} for s in ('train', 'validation', 'test')}
pairs = [('train', 'validation'), ('train', 'test'), ('validation', 'test')]
record('orbit_split_disjointness',
       all(orbit_sets[a].isdisjoint(orbit_sets[b]) and board_sets[a].isdisjoint(board_sets[b]) for a, b in pairs),
       orbits_per_split={s: len(orbit_sets[s]) for s in orbit_sets},
       rows_per_split={s: int(len(rows[s])) for s in rows},
       shared_orbits={f'{a}/{b}': len(orbit_sets[a] & orbit_sets[b]) for a, b in pairs})

# 8-10. D4 behaviour of each target, via the independent oracle on transformed boards
board_index = {}
for split in ('train', 'validation', 'test'):
    for row, orbit, per_task in zip(rows[split], orbits[split], zip(*(labels[split][t] for t in TASKS))):
        board_index[tuple(int(v) for v in row)] = (split, int(orbit), {t: int(v) for t, v in zip(TASKS, per_task)})

rng = np.random.default_rng(SAMPLE_SEED)
sample = rng.integers(len(stored), size=SAMPLE_PAIRS)
sampled_pairs = [(stored[i], D4[j]) for i, j in zip(sample.tolist(), rng.integers(8, size=SAMPLE_PAIRS).tolist())]

invariance_report = {}
for task in TASKS:
    sampled_violations = sum(oracle_labels(transform(board, perm))[task] != ALL_Y[task][i]
                             for (board, perm), i in zip(sampled_pairs, sample.tolist()))
    exhaustive_violations = sum(oracle_labels(transform(board, perm))[task] != board_index[board][2][task]
                                for board in stored for perm in D4)
    present = all(transform(board, perm) in board_index for board, perm in sampled_pairs)
    same_split = all(board_index[transform(board, perm)][0] == board_index[board][0]
                     and board_index[transform(board, perm)][1] == board_index[board][1]
                     for board, perm in sampled_pairs)
    invariance_report[task] = {
        'sampled_pairs': SAMPLE_PAIRS,
        'sampled_violated_pairs': int(sampled_violations),
        'sampled_violated_fraction': float(sampled_violations / SAMPLE_PAIRS),
        'exhaustive_pairs': len(stored) * 8,
        'exhaustive_violated_pairs': int(exhaustive_violations),
        'exhaustive_violated_fraction': float(exhaustive_violations / (len(stored) * 8)),
        'transformed_boards_present_in_dataset': present,
        'transformed_boards_in_same_split_and_orbit': same_split,
    }

invariant_ok = (invariance_report['winner']['sampled_violated_fraction'] == 0.0
                and invariance_report['winner']['exhaustive_violated_fraction'] == 0.0
                and invariance_report['winner']['transformed_boards_present_in_dataset']
                and invariance_report['winner']['transformed_boards_in_same_split_and_orbit'])
record('winner_is_d4_invariant', invariant_ok, **invariance_report['winner'],
       note='independent oracle applied to transformed boards reproduces the stored label on every '
            'sampled pair and on all 8 x rows pairs; the transformed board is always present in the '
            'same split and orbit')

designated = invariance_report['winner_designated']
record('winner_designated_is_not_d4_invariant', designated['exhaustive_violated_fraction'] > 0.0,
       **designated,
       note='WP-TTT requires a genuinely D4-breaking counterfactual. The requested rule keys the sign '
            'flip on cell 4 (the centre), but the centre is fixed by all 8 elements of D4 and lines map '
            'to lines, so "the winner owns a line through cell 4" is D4-invariant and the violated-pair '
            'fraction is 0.0. The specification is self-contradictory: this target cannot serve as the '
            'symmetry-breaking control. winner_designated_corner (designated cell 0, a corner, which is '
            'not fixed by D4) is the working counterfactual.')

corner = invariance_report['winner_designated_corner']
record('winner_designated_corner_is_not_d4_invariant',
       corner['exhaustive_violated_fraction'] > 0.0 and corner['sampled_violated_fraction'] > 0.0,
       **corner,
       note='sign flip keyed on a corner cell is genuinely D4-breaking, as required of a counterfactual '
            'target')

# 11. metadata consistency with the arrays
recomputed_counts = {s: {'rows': int(len(rows[s])), 'orbits': int(len(orbit_sets[s])),
                         'target_means': {t: float(labels[s][t].mean()) for t in TASKS}}
                     for s in ('train', 'validation', 'test')}
counts_ok = recomputed_counts == json.loads(json.dumps(family['counts']))
invariance_meta_ok = all(abs(family['invariance'][task]['measured_violation_fraction']
                             - invariance_report[task]['exhaustive_violated_fraction']) < 1e-12 for task in TASKS)
def documents_rule(task):
    text, designated = family['targets'][task], EXPECTED_DESIGNATED[task]
    if designated is None:
        return 'D4-invariant' in text
    return f'cell {designated}' in text and 'flip' in text.lower()


designated_meta_ok = (all(family['invariance'][task]['designated_cell'] == EXPECTED_DESIGNATED[task]
                          for task in TASKS) and all(documents_rule(task) for task in TASKS))
generators = family['generators']


def compose(p, q):
    return tuple(p[q[i]] for i in range(9))


closure = {tuple(range(9))}
frontier = [tuple(range(9))]
while frontier:
    p = frontier.pop()
    for g in (tuple(generators['rotation']), tuple(generators['reflection'])):
        for h in (compose(p, g), compose(g, p)):
            if h not in closure:
                closure.add(h)
                frontier.append(h)
group_ok = (family['group'] == 'D4' and closure == set(D4)
            and sorted(tuple(line) for line in family['lines']) == sorted(tuple(sorted(l)) for l in LINES))
record('metadata_consistent_with_arrays',
       counts_ok and invariance_meta_ok and designated_meta_ok and group_ok
       and TASKS == sorted(TASKS) and set(TASKS) == set(EXPECTED_DESIGNATED),
       counts_match=counts_ok, invariance_fractions_match=invariance_meta_ok,
       designated_cells_match=designated_meta_ok,
       group_and_lines_match=group_ok,
       manifest_generator_closure_equals_independent_d4=closure == set(D4),
       declared_group=family['group'], declared_tasks=TASKS,
       declared_designated_cells={t: family['invariance'][t]['designated_cell'] for t in TASKS},
       recomputed_counts=recomputed_counts)

# 12. quadratic-free metadata: discrete classification family, no alpha control / no quadratic defect law
def walk_keys(node, path=''):
    if isinstance(node, dict):
        for key, value in node.items():
            yield path + '/' + key
            yield from walk_keys(value, path + '/' + key + '/')
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk_keys(value, f'{path}/{index}/')


declared_keys = sorted(set(walk_keys(family)))
forbidden_keys = [key for key in declared_keys
                  if any(token in key.lower() for token in ('alpha', 'quadratic', 'defect', 'power'))]
continuous_targets = [task for task in TASKS if not np.isin(ALL_Y[task], [-1, 0, 1]).all()]
record('quadratic_free_metadata_consistent',
       not forbidden_keys and not continuous_targets and 'alphas' not in family
       and family['n'] == 9 and len(D4) == 8 and set(TASKS) == set(EXPECTED_DESIGNATED),
       forbidden_metadata_keys=forbidden_keys, continuous_valued_targets=continuous_targets,
       declares_alphas_list='alphas' not in family,
       target_value_sets={t: sorted(set(int(value) for value in ALL_Y[t])) for t in TASKS},
       note='unlike ring_n6 this family declares no alphas list and no alpha-squared target-defect law; '
            'it is discrete classification, every target takes values in {-1, 0, 1}, and the group has '
            'exactly 8 elements acting on n=9 cells')

# 13. parent manifest untouched by WP-TTT
parent = Path(HERE).parent / 'manifest.json'
parent_ok = 'tictactoe' not in parent.read_text().lower()
record('parent_manifest_untouched', parent_ok, parent_manifest=str(parent.relative_to(Path(HERE).parents[2])),
       note='WP-TTT writes its own self-contained manifest; the parent datasets manifest must not mention it')

failures = [name for name, result in checks.items() if result['status'] == 'FAIL']
report = {'family': NAME, 'seed': manifest['seed'], 'status': 'PASS' if not failures else 'FAIL',
          'failed_checks': failures, 'checks': checks}
(HERE / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
sys.exit(1 if failures else 0)
