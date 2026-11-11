"""Dense state-vector simulator with reverse-mode gradients (see INTERFACES.md).

Gate-entry format and conventions match research/metrics/symmetry.py:
RX/RY/RZ(t) = exp(-i t P/2); CR*(t) = controlled rotation with control
wires[0] (exp[-i t (I-Z_c) Z_t/4]); CNOT/CZ control = wires[0];
RZZ(t) = exp(-i t Z (x) Z / 2). Bit order: q0 is the most significant bit.
Fixed angles use {"gate": G, "wires": [...], "angle": t}; trainable angles use
"param": name. Forward.grad interprets dloss_dpsi as the conjugate (Wirtinger)
gradient dL/dpsi* (JAX convention); for a real loss that is conj(dL/dpsi).
"""
import numpy as np

_I2 = np.eye(2, dtype=complex)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
_Z = np.diag([1, -1]).astype(complex)
_PAULI = {'X': _X, 'Y': _Y, 'Z': _Z}
_FIXED1 = {'H': np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2.0),
           'X': _X, 'Y': _Y,
           'S': np.diag([1.0, 1j]).astype(complex),
           'T': np.diag([1.0, np.exp(1j * np.pi / 4)]).astype(complex)}
_ROT = ('RX', 'RY', 'RZ')
_CROT = ('CRX', 'CRY', 'CRZ')
_ZZ_SIGN = np.array([1.0, -1.0, -1.0, 1.0])


def _wires(entry):
    if 'wires' in entry:
        return [int(w) for w in entry['wires']]
    return [int(entry['wire'])]


def _rot(pauli, angle):
    p = _PAULI[pauli]
    m = np.cos(angle / 2.0) * _I2 - 1j * np.sin(angle / 2.0) * p
    return m, -0.5j * (p @ m)


def _gate(entry, params):
    """Return (matrix, wires, dmatrix_or_None) for one gate entry."""
    name, wires = entry['gate'], _wires(entry)
    if 'param' in entry:
        angle, trainable = float(params[entry['param']]), True
    elif 'angle' in entry:
        angle, trainable = float(entry['angle']), False
    else:
        angle, trainable = 0.0, False
    if name in _FIXED1 or name in _ROT:
        if len(wires) != 1:
            raise ValueError('%s needs one wire' % name)
        if name in _FIXED1:
            return _FIXED1[name], wires, None
        m, dm = _rot(name[-1], angle)
        return m, wires, dm if trainable else None
    if len(wires) != 2:
        raise ValueError('%s needs two wires' % name)
    if name in ('CNOT', 'CZ'):
        m = np.eye(4, dtype=complex)
        m[2:, 2:] = _X if name == 'CNOT' else _Z
        return m, wires, None
    if name in _CROT:
        rot, drot = _rot(name[-1], angle)
        z = np.zeros((2, 2), dtype=complex)
        full = np.block([[_I2, z], [z, rot]])
        dfull = np.block([[z, z], [z, drot]])
        return full, wires, dfull if trainable else None
    if name == 'RZZ':
        d = np.exp(-0.5j * angle * _ZZ_SIGN)
        dm = -0.5j * _ZZ_SIGN * d
        return np.diag(d), wires, np.diag(dm) if trainable else None
    raise ValueError('Unsupported gate: %s' % name)


def _apply(psi, mat, wires, n):
    """Apply a 1- or 2-qubit matrix to batched states psi (m, 2**n)."""
    k, m = len(wires), psi.shape[0]
    t = np.tensordot(mat.reshape((2,) * (2 * k)), psi.reshape((m,) + (2,) * n),
                     axes=(list(range(k, 2 * k)), [w + 1 for w in wires]))
    return np.moveaxis(t, range(k), [w + 1 for w in wires]).reshape(m, 2 ** n)


def apply_gate_vectorized(gates, params, n, states0):
    psi = np.array(states0, dtype=complex, copy=True).reshape(-1, 2 ** n)
    for entry in gates:
        mat, wires, _ = _gate(entry, params)
        psi = _apply(psi, mat, wires, n)
    return psi


def unitary(gates, params, n):
    """Dense circuit unitary; agrees with metrics.symmetry.unitary.

    apply_gate_vectorized maps each row r of the identity to U @ e_r, i.e. to
    column r of U, so the batched result is U transposed (not conjugated).
    """
    return apply_gate_vectorized(gates, params, n, np.eye(2 ** n, dtype=complex)).T


def _terms(observable):
    return list(observable.items()) if isinstance(observable, dict) else list(observable)


class Forward:
    """Compiled circuit: forward run, reverse-mode grad, diagonal expectations."""

    def __init__(self, gates, param_names, n):
        self.gates = list(gates)
        self.param_names = list(param_names)
        self.n = int(n)

    def _dict(self, params_vec):
        return dict(zip(self.param_names, np.asarray(params_vec, dtype=float).ravel()))

    def run(self, params_vec, states0):
        pd = self._dict(params_vec)
        psi = np.array(states0, dtype=complex, copy=True).reshape(-1, 2 ** self.n)
        cache = [psi]
        for entry in self.gates:
            mat, wires, _ = _gate(entry, pd)
            psi = _apply(psi, mat, wires, self.n)
            cache.append(psi)
        return psi, cache

    def grad(self, params_vec, cache, dloss_dpsi):
        """dL/dparam_j for every trainable parameter, given dL/dpsi* (m, 2**n)."""
        pd = self._dict(params_vec)
        grads = np.zeros(len(self.param_names))
        bar = np.array(dloss_dpsi, dtype=complex, copy=True).reshape(cache[-1].shape)
        for k in range(len(self.gates), 0, -1):
            entry = self.gates[k - 1]
            mat, wires, dmat = _gate(entry, pd)
            if dmat is not None and entry['param'] in self.param_names:
                j = self.param_names.index(entry['param'])
                dots = np.sum(np.conj(bar) * _apply(cache[k - 1], dmat, wires, self.n), axis=1)
                grads[j] += float(np.sum(2.0 * np.real(dots)))
            bar = _apply(bar, mat.conj().T, wires, self.n)
        return grads

    def _eigenvalues(self, observables):
        d = 2 ** self.n
        bits = ((np.arange(d)[:, None] >> (self.n - 1 - np.arange(self.n))) & 1)
        out = []
        for obs in observables:
            v = np.zeros(d)
            for index, coeff in _terms(obs):
                sign = np.ones(d)
                for i in index:
                    sign *= 1.0 - 2.0 * bits[:, int(i)]
                v += float(np.real(coeff)) * sign
            out.append(v)
        return np.array(out).reshape(len(observables), d)

    def _expect_psi(self, psi, observables):
        return (np.abs(psi) ** 2) @ self._eigenvalues(observables).T

    def expect(self, params_vec, states0, observables):
        psi, _ = self.run(params_vec, states0)
        return self._expect_psi(psi, observables)

    def grad_expect(self, params_vec, cache, observables, dloss_dexpect):
        """dL/dparam_j for L = sum_k w_k <O_k>, with w = dloss_dexpect (m, k)."""
        e = self._eigenvalues(observables)
        psi = cache[-1]
        w = np.asarray(dloss_dexpect, dtype=float).reshape(-1, len(observables))
        if w.shape[0] == 1 and psi.shape[0] > 1:
            w = np.broadcast_to(w, (psi.shape[0], w.shape[1]))
        return self.grad(params_vec, cache, psi * (w @ e))


def compile_circuit(gates, param_names, n):
    return Forward(gates, param_names, n)
