"""Dense reference implementation: fixed-parameter, ordered-circuit symmetry."""
import numpy as np


def unitary(gates, params, n):
    u = np.eye(2**n, dtype=complex)
    paulis = {'X': np.array([[0, 1], [1, 0]]),
              'Y': np.array([[0, -1j], [1j, 0]]),
              'Z': np.diag([1, -1])}
    for entry in gates:
        name = entry['gate']
        wires = entry.get('wires', [entry.get('wire')])
        if name in ('CZ', 'CNOT'):
            gate = np.eye(4, dtype=complex)
            gate[2:, 2:] = paulis['Z' if name == 'CZ' else 'X']
        elif name in ('RX', 'RY', 'RZ', 'CRX', 'CRY', 'CRZ'):
            angle = params[entry['param']]
            rot = np.cos(angle/2)*np.eye(2)-1j*np.sin(angle/2)*paulis[name[-1]]
            gate = rot if len(wires) == 1 else np.block([[np.eye(2), np.zeros((2,2))], [np.zeros((2,2)), rot]])
        else:
            raise ValueError('Unsupported gate: '+name)
        axes = wires + [i for i in range(n) if i not in wires] + [n]
        tensor = u.reshape([2]*n+[2**n]).transpose(axes)
        tensor = (gate @ tensor.reshape(2**len(wires), -1)).reshape([2]*n+[2**n])
        u = tensor.transpose(np.argsort(axes)).reshape(2**n, 2**n)
    return u


def permutation_indices(permutation):
    n = len(permutation)
    return np.arange(2**n).reshape([2]*n).transpose(permutation).reshape(-1)


def defects(u, permutations):
    """Returns means/maxima over the supplied finite list, NOT a full-group claim."""
    d = len(u)
    strict, channel = [], []
    for p in permutations:
        ix = permutation_indices(p)
        v = u[np.ix_(ix, ix)]
        overlap = np.vdot(u, v)/d
        strict.append(float(np.linalg.norm(u-v, 'fro')**2/(2*d)))
        channel.append(float(np.clip(1-abs(overlap)**2, 0, 1)))
    return {'unitary_mean': float(np.mean(strict)), 'unitary_max': float(max(strict)),
            'channel_mean': float(np.mean(channel)), 'channel_max': float(max(channel))}


def adjacent_swaps(n):
    result = []
    for i in range(n-1):
        p = list(range(n)); p[i], p[i+1] = p[i+1], p[i]; result.append(p)
    return result


def output_defect(predictions):
    """Rows are examples; columns are complete or sampled group orbits."""
    f = np.asarray(predictions)
    return float(np.mean((f-f.mean(axis=1, keepdims=True))**2))
