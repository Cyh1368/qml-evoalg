"""Reference interface for proposed permutation hypotheses; no LLM API required."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'metrics'))
from symmetry import unitary, defects, permutation_indices


def closure(generators, n, limit=40320):
    """Exact finite permutation closure, with an explicit resource limit."""
    if n < 1 or not generators:
        raise ValueError('Positive n and at least one generator required')
    generators = [tuple(p) for p in generators]
    if any(sorted(p) != list(range(n)) for p in generators):
        raise ValueError('Each generator must permute range(n)')
    identity = tuple(range(n))
    seen, pending = {identity}, [identity]
    while pending:
        p = pending.pop()
        for q in generators:
            r = tuple(p[q[i]] for i in range(n))
            if r not in seen:
                if len(seen) >= limit:
                    raise ValueError('Group closure exceeds limit; no partial certification returned')
                seen.add(r)
                pending.append(r)
    return sorted(seen)


def verify(hypothesis, candidate, parameter_samples, tolerance=1e-10):
    """Numerical channel verification at supplied parameters, not symbolic proof."""
    if hypothesis.get('output_action') != 'invariant':
        raise ValueError('This version supports invariant scalar outputs only')
    n = hypothesis['n_qubits']
    if n > 10:
        raise ValueError('Dense reference verifier limited to 10 qubits')
    if not parameter_samples or not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError('Require samples and a finite nonnegative tolerance')
    group = closure(hypothesis['generators'], n)
    rows = []
    for params in parameter_samples:
        u = unitary(candidate, params, n)
        if not np.all(np.isfinite(u)):
            raise ValueError('Nonfinite circuit matrix')
        rows.append(defects(u, group))
    worst = max(row['channel_max'] for row in rows)
    return {'group_order': len(group), 'parameter_samples': len(rows),
            'sampled_channel_equivariance_pass': worst <= tolerance,
            'worst_channel_residual': worst, 'tolerance': tolerance,
            'samples': rows, 'scope': 'supplied parameter points, full generated permutation group',
            'task_symmetry_validated': False,
            'all_parameter_proof': False}


def repair_generator(h, generators):
    """Project a Hermitian generator into the supplied group's commutant.

    This repairs a Hamiltonian, not a gate list. Exponentiating this result is
    equivariant; replacing the exponential with arbitrary ordered gates is not.
    """
    h = np.asarray(h, dtype=complex)
    if h.ndim != 2 or h.shape[0] != h.shape[1]:
        raise ValueError('Expected square matrix')
    n = int(np.log2(len(h)))
    if 2**n != len(h) or not np.all(np.isfinite(h)) or not np.allclose(h, h.conj().T):
        raise ValueError('Expected finite Hermitian qubit operator')
    group = closure(generators, n)
    repaired = np.zeros_like(h)
    for p in group:
        ix = permutation_indices(p)
        repaired += h[np.ix_(ix, ix)] / len(group)
    return repaired


def invariant_prediction(predict, x, generators):
    """Exact group averaging of a scalar predictor on n-site arrays.

    This is known-group inference repair, with |G| predictor calls. It does not
    imply the circuit itself is equivariant or that labels have this symmetry.
    """
    x = np.asarray(x)
    group = closure(generators, len(x))
    return float(np.mean([predict(x[list(p)]) for p in group]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    result = verify(payload['hypothesis'], payload['candidate'], payload['parameter_samples'])
    output = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(output + '\n')
    else:
        print(output)

if __name__ == '__main__':
    main()


def graph_edge_action(edges, permutation):
    """Relabel upper-triangular undirected edge vectors in lexicographic order.

    Convention agrees with the backend tensor transpose: output site i reads
    input site permutation[i]. This is a pullback action on edge features.
    """
    import itertools
    p = tuple(permutation)
    n = len(p)
    if sorted(p) != list(range(n)):
        raise ValueError('Invalid vertex permutation')
    pairs = list(itertools.combinations(range(n), 2))
    edges = np.asarray(edges)
    if edges.shape != (len(pairs),):
        raise ValueError('Expected one value per unordered vertex pair')
    index = {pair: i for i, pair in enumerate(pairs)}
    return np.array([edges[index[tuple(sorted((p[a], p[b])))]] for a, b in pairs])


def validate_task_pairs(labels, transformed_labels, *, provenance,
                        output_action='invariant', tolerance=0.0):
    """Check independent scalar labels for explicit input/transformed-input pairs.

    Caller must compute transformed labels with an independent label oracle,
    never by copying original labels or using the candidate predictor. Rows are
    input probes; columns are tested transformations. Provenance is an explicit
    caller declaration, not something this function can independently verify.
    """
    if output_action != 'invariant':
        raise ValueError('Only scalar invariant label action is supported')
    if provenance not in ('heldout', 'exploratory'):
        raise ValueError('Declare heldout or exploratory provenance')
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError('Require finite nonnegative tolerance')
    y = np.asarray(labels, dtype=float)
    transformed = np.asarray(transformed_labels, dtype=float)
    if y.ndim != 1 or not len(y) or transformed.ndim != 2:
        raise ValueError('Expected nonempty labels and a paired label matrix')
    if transformed.shape[0] != len(y) or transformed.shape[1] == 0:
        raise ValueError('Pair dimensions do not match')
    if not np.all(np.isfinite(y)) or not np.all(np.isfinite(transformed)):
        raise ValueError('Labels must be finite')
    delta = transformed - y[:, None]
    return {'paired_label_mse': float(np.mean(delta**2)),
            'maximum_absolute_label_difference': float(np.max(np.abs(delta))),
            'fraction_pairs_exceeding_tolerance': float(np.mean(np.abs(delta) > tolerance)),
            'tested_label_invariance_pass': bool(np.all(np.abs(delta) <= tolerance)),
            'input_probes': len(y), 'transformations_per_probe': transformed.shape[1],
            'provenance_declared_by_caller': provenance,
            'scope': 'explicit input-transformation pairs only',
            'population_symmetry_proof': False,
            'adaptive_reuse_warning': provenance == 'exploratory'}


def validate_task_oracle(inputs, label_oracle, transform, generators, n,
                         *, provenance, tolerance=0.0):
    """Enumerate a proposed group and recompute labels on transformed probes.

    Used for deterministic task rules. For noisy labels, raw paired disagreement
    includes label noise and needs a separate statistical model.
    """
    group = closure(generators, n)
    inputs = list(inputs)
    labels = [label_oracle(x) for x in inputs]
    paired = [[label_oracle(transform(x, p)) for p in group] for x in inputs]
    report = validate_task_pairs(labels, paired, provenance=provenance,
                                 tolerance=tolerance)
    report['group_order'] = len(group)
    return report
