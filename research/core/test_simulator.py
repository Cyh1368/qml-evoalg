"""Unit tests for research/core/simulator.py."""
import os
import sys
import unittest

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir))
sys.path.insert(0, _HERE)
sys.path.insert(0, _ROOT)

import simulator as sim  # noqa: E402
from research.metrics import symmetry  # noqa: E402

_I2 = np.eye(2, dtype=complex)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
_Z = np.diag([1, -1]).astype(complex)
_H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2.0)
_SHARED1 = ('RX', 'RY', 'RZ')
_SHARED2 = ('CNOT', 'CZ', 'CRX', 'CRY', 'CRZ')
_ALL1 = ('RX', 'RY', 'RZ', 'H', 'X', 'Y', 'S', 'T')
_ALL2 = ('CNOT', 'CZ', 'CRX', 'CRY', 'CRZ', 'RZZ')


def _pair(rng, n):
    a = int(rng.integers(n))
    b = int(rng.integers(n))
    while b == a:
        b = int(rng.integers(n))
    return a, b


def _add_angle(entry, gate, rng, pool, allow_angle):
    if gate in ('RX', 'RY', 'RZ', 'CRX', 'CRY', 'CRZ', 'RZZ'):
        if allow_angle and rng.random() < 0.4:
            entry['angle'] = float(rng.uniform(-np.pi, np.pi))
        else:
            name = pool[int(rng.integers(len(pool)))] if pool else 'p%d' % len(pool)
            entry['param'] = name
    return entry


def random_circuit(rng, n, ngates, pool=None, allow_angle=True,
                   one=_ALL1, two=_ALL2):
    """Random gate list; `pool` is the reusable parameter-name list."""
    pool = list(pool or ['t0', 't1', 't2', 't3'])
    gates = []
    for _ in range(ngates):
        if rng.random() < 0.5:
            g = str(rng.choice(one))
            e = {'gate': g, 'wire': int(rng.integers(n))}
        else:
            g = str(rng.choice(two))
            a, b = _pair(rng, n)
            e = {'gate': g, 'wires': [a, b]}
        gates.append(_add_angle(e, g, rng, pool, allow_angle))
    return gates, pool


def full_circuit(rng, n, pool):
    """Circuit containing every supported gate type at least once."""
    gates = []
    for g in _ALL1:
        e = {'gate': g, 'wire': int(rng.integers(n))}
        gates.append(_add_angle(e, g, rng, pool, allow_angle=True))
    for g in _ALL2:
        a, b = _pair(rng, n)
        e = {'gate': g, 'wires': [a, b]}
        gates.append(_add_angle(e, g, rng, pool, allow_angle=True))
    extra, _ = random_circuit(rng, n, 12, pool=pool)
    return gates + extra, pool


def observables(n, k=4, rng=None):
    obs = []
    for _ in range(k):
        terms = []
        for _ in range(int(rng.integers(1, 4))):
            ns = int(rng.integers(1, 3))
            idx = tuple(sorted(int(x) for x in rng.choice(n, size=ns, replace=False)))
            terms.append((idx, float(rng.choice([1.0, -1.0, 0.5]))))
        obs.append(terms)
    return obs


def obs_eigenvalues(obs, n):
    d = 2 ** n
    out = np.zeros(d)
    for index, coeff in obs:
        ops = {int(i): _Z for i in index}
        m = np.array([1.0 + 0j])
        for q in range(n):
            m = np.kron(m, ops.get(q, _I2))
        out += coeff * np.real(np.diag(m))
    return out


class TestSymmetryAgreement(unittest.TestCase):
    def test_unitary_matches_symmetry(self):
        for seed in (0, 1, 2):
            rng = np.random.default_rng(seed)
            n = 4
            gates, names = random_circuit(rng, n, 30, allow_angle=False,
                                          one=_SHARED1, two=_SHARED2)
            params = {nm: float(rng.uniform(-np.pi, np.pi)) for nm in names}
            got = sim.unitary(gates, params, n)
            want = symmetry.unitary(gates, params, n)
            self.assertEqual(got.shape, (2 ** n, 2 ** n))
            self.assertLess(np.max(np.abs(got - want)), 1e-12)
            self.assertLess(np.max(np.abs(got.conj().T @ got - np.eye(2 ** n))), 1e-12)


class TestExplicitGates(unittest.TestCase):
    def test_rzz_two_wires(self):
        for t in (0.0, 0.3, -1.1, np.pi):
            want = np.diag(np.exp(-0.5j * t * np.array([1.0, -1.0, -1.0, 1.0])))
            got = sim.unitary([{'gate': 'RZZ', 'wires': [0, 1], 'angle': t}], {}, 2)
            self.assertLess(np.max(np.abs(got - want)), 1e-14)

    def test_rzz_nonadjacent_matches_kron(self):
        t = 0.77
        zz = np.kron(np.kron(_Z, _I2), _Z)
        d, v = np.linalg.eigh(zz)
        want = (v * np.exp(-0.5j * t * d)) @ v.conj().T
        got = sim.unitary([{'gate': 'RZZ', 'wires': [0, 2], 'angle': t}], {}, 3)
        self.assertLess(np.max(np.abs(got - want)), 1e-13)

    def test_h_and_x_bit_order(self):
        got = sim.unitary([{'gate': 'H', 'wire': 0}], {}, 2)
        self.assertLess(np.max(np.abs(got - np.kron(_H, _I2))), 1e-14)
        got = sim.unitary([{'gate': 'H', 'wire': 1}], {}, 2)
        self.assertLess(np.max(np.abs(got - np.kron(_I2, _H))), 1e-14)
        got = sim.unitary([{'gate': 'X', 'wire': 0}], {}, 3)
        self.assertLess(np.max(np.abs(got - np.kron(np.kron(_X, _I2), _I2))), 1e-14)
        got = sim.unitary([{'gate': 'X', 'wire': 2}], {}, 3)
        self.assertLess(np.max(np.abs(got - np.kron(np.kron(_I2, _I2), _X))), 1e-14)
        s_gate = np.diag([1.0, 1j]).astype(complex)
        t_gate = np.diag([1.0, np.exp(1j * np.pi / 4)]).astype(complex)
        got = sim.unitary([{'gate': 'S', 'wire': 0}], {}, 2)
        self.assertLess(np.max(np.abs(got - np.kron(s_gate, _I2))), 1e-14)
        got = sim.unitary([{'gate': 'T', 'wire': 1}], {}, 2)
        self.assertLess(np.max(np.abs(got - np.kron(_I2, t_gate))), 1e-14)
        # q0 most significant: X on wire 0 maps |000> -> |100> = index 4.
        psi = sim.apply_gate_vectorized([{'gate': 'X', 'wire': 0}], {}, 3,
                                        np.eye(8)[:, :1])
        self.assertEqual(int(np.argmax(np.abs(psi[0]))), 4)

    def test_cnot_control_is_wire_zero(self):
        got = sim.unitary([{'gate': 'CNOT', 'wires': [0, 1]}], {}, 2)
        want = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
                        dtype=complex)
        self.assertLess(np.max(np.abs(got - want)), 1e-14)


class TestVectorization(unittest.TestCase):
    def test_run_and_expect_match_per_row_unitary(self):
        rng = np.random.default_rng(11)
        n, m = 4, 5
        gates, names = full_circuit(rng, n, pool=['t0', 't1', 't2'])
        vec = rng.uniform(-np.pi, np.pi, len(names))
        pd = dict(zip(names, vec))
        states0 = rng.normal(size=(m, 2 ** n)) + 1j * rng.normal(size=(m, 2 ** n))
        states0 /= np.linalg.norm(states0, axis=1, keepdims=True)
        fwd = sim.compile_circuit(gates, names, n)
        psi, cache = fwd.run(vec, states0)
        self.assertEqual(len(cache), len(gates) + 1)
        u = sim.unitary(gates, pd, n)
        want = np.stack([u @ row for row in states0])
        self.assertLess(np.max(np.abs(psi - want)), 1e-12)
        self.assertLess(np.max(np.abs(sim.apply_gate_vectorized(gates, pd, n, states0)
                                      - want)), 1e-12)
        obs = observables(n, k=4, rng=rng)
        got = fwd.expect(vec, states0, obs)
        self.assertEqual(got.shape, (m, len(obs)))
        evals = np.stack([obs_eigenvalues(o, n) for o in obs])
        want_e = (np.abs(want) ** 2) @ evals.T
        self.assertLess(np.max(np.abs(got - want_e)), 1e-12)
        # dict-style observables (INTERFACES format) agree with term lists.
        dict_obs = [{(0,): 1.0}, {(1, 3): 1.0}, {(2,): -0.5, (0,): 0.25}]
        got_d = fwd.expect(vec, states0, dict_obs)
        want_d = (np.abs(want) ** 2) @ np.stack(
            [obs_eigenvalues(list(o.items()), n) for o in dict_obs]).T
        self.assertLess(np.max(np.abs(got_d - want_d)), 1e-12)


class TestGradients(unittest.TestCase):
    def _setup(self, seed):
        rng = np.random.default_rng(seed)
        n, m = 4, 3
        gates, names = full_circuit(rng, n, pool=['t0', 't1', 't2', 't3'])
        vec = rng.uniform(-np.pi, np.pi, len(names))
        states0 = rng.normal(size=(m, 2 ** n)) + 1j * rng.normal(size=(m, 2 ** n))
        states0 /= np.linalg.norm(states0, axis=1, keepdims=True)
        return rng, sim.compile_circuit(gates, names, n), vec, states0, n, m

    def test_grad_matches_central_differences(self):
        for seed in (21, 22):
            rng, fwd, vec, states0, n, m = self._setup(seed)
            d = 2 ** n
            a = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
            herm = a + a.conj().T
            v = rng.normal(size=d) + 1j * rng.normal(size=d)

            def loss_herm(p):
                psi, _ = fwd.run(p, states0)
                return float(np.sum(np.real(np.einsum('ij,jk,ik->', psi.conj(), herm, psi))))

            def loss_ovl(p):
                psi, _ = fwd.run(p, states0)
                return float(np.sum(np.abs(psi @ v.conj()) ** 2))

            for loss, dloss in ((loss_herm, lambda psi: psi @ herm.T),
                                (loss_ovl, lambda psi: np.outer(psi @ v.conj(), v))):
                psi, cache = fwd.run(vec, states0)
                got = fwd.grad(vec, cache, dloss(psi))
                self.assertEqual(got.shape, vec.shape)
                for j in range(len(vec)):
                    vp, vm = vec.copy(), vec.copy()
                    vp[j] += 1e-5
                    vm[j] -= 1e-5
                    fd = (loss(vp) - loss(vm)) / 2e-5
                    self.assertLess(abs(got[j] - fd), 1e-6)

    def test_grad_expect_matches_central_differences(self):
        for seed in (31, 32):
            rng, fwd, vec, states0, n, m = self._setup(seed)
            obs = observables(n, k=5, rng=rng)
            w = rng.normal(size=(m, len(obs)))

            def loss(p):
                return float(np.sum(w * fwd.expect(p, states0, obs)))

            psi, cache = fwd.run(vec, states0)
            got = fwd.grad_expect(vec, cache, obs, w)
            got_row0 = fwd.grad_expect(vec, cache, obs, w[:1])
            for j in range(len(vec)):
                vp, vm = vec.copy(), vec.copy()
                vp[j] += 1e-5
                vm[j] -= 1e-5
                self.assertLess(abs(got[j] - (loss(vp) - loss(vm)) / 2e-5), 1e-6)
            # Shared (1, k) weights broadcast to every row of the batch.
            def loss0(p):
                return float(np.sum(w[:1] * fwd.expect(p, states0, obs)))
            for j in range(len(vec)):
                vp, vm = vec.copy(), vec.copy()
                vp[j] += 1e-5
                vm[j] -= 1e-5
                self.assertLess(abs(got_row0[j] - (loss0(vp) - loss0(vm)) / 2e-5), 1e-6)

    def test_norm_is_stationary_and_finite(self):
        # dloss_dpsi = psi is the loss sum_b |psi_b|^2, constant under unitaries.
        rng, fwd, vec, states0, n, m = self._setup(41)
        psi, cache = fwd.run(vec, states0)
        got = fwd.grad(vec, cache, psi)
        self.assertTrue(np.all(np.isfinite(got)))
        self.assertLess(np.max(np.abs(got)), 1e-10)
        self.assertEqual(got.shape, vec.shape)


class TestDeterminism(unittest.TestCase):
    def test_bitwise_identical(self):
        rng = np.random.default_rng(7)
        n, m = 4, 4
        gates, names = full_circuit(rng, n, pool=['t0', 't1', 't2'])
        vec = rng.uniform(-np.pi, np.pi, len(names))
        states0 = rng.normal(size=(m, 2 ** n)) + 1j * rng.normal(size=(m, 2 ** n))
        obs = observables(n, k=3, rng=rng)
        w = rng.normal(size=(m, len(obs)))
        outs = []
        for _ in range(2):
            fwd = sim.compile_circuit(gates, names, n)
            psi, cache = fwd.run(vec, states0)
            outs.append((psi.tobytes(), fwd.grad(vec, cache, psi).tobytes(),
                         fwd.expect(vec, states0, obs).tobytes(),
                         fwd.grad_expect(vec, cache, obs, w).tobytes(),
                         sim.unitary(gates, dict(zip(names, vec)), n).tobytes()))
        self.assertEqual(outs[0], outs[1])


if __name__ == '__main__':
    unittest.main()
