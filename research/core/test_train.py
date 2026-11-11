"""Unit tests for research/core/train.py (see INTERFACES.md train contract)."""
import unittest

import numpy as np

from research.core import candidates, tasks, train
from research.core import simulator as sim


def _per_row_expectations(candidate, task, x, theta):
    """Reference path: one compiled Forward per row (no batching)."""
    n = int(candidate["n_qubits"])
    obs = train.obs_matrix(task.observables, n)
    out = np.zeros((len(x), len(task.observables)))
    for i in range(len(x)):
        gates, _ = candidates.expand_example(candidate, task, x[i])
        fwd = sim.compile_circuit(gates, list(candidate["param_names"]), n)
        psi, _ = fwd.run(theta, train._zero_state(n))
        out[i] = ((np.abs(psi) ** 2) @ obs.T).reshape(-1)
    return out


class TestBatchedExpectations(unittest.TestCase):
    def test_matches_reference_path(self):
        for family in ("ring_n6", "tictactoe_n9", "graphs_n6"):
            task = tasks.load_family(family)
            rng = np.random.default_rng(7)
            cand = candidates.sample_random(rng, task)
            theta = rng.uniform(-np.pi, np.pi, size=candidates.n_params(cand))
            rows = task.x[task.splits["validation"]][:40]
            ref = _per_row_expectations(cand, task, rows, theta)
            bat = train.batched_expectations(cand, task, rows, theta)
            np.testing.assert_allclose(bat, ref, atol=1e-10,
                                       err_msg=family)

    def test_batching_groups_mixed_structures(self):
        # graphs have per-example edge counts -> many structure groups at once
        task = tasks.load_family("graphs_n6")
        rng = np.random.default_rng(11)
        cand = candidates.sample_random(rng, task)
        theta = rng.uniform(-np.pi, np.pi, size=candidates.n_params(cand))
        rows = task.x[task.splits["validation"]][:60]
        ref = _per_row_expectations(cand, task, rows, theta)
        bat = train.batched_expectations(cand, task, rows, theta)
        np.testing.assert_allclose(bat, ref, atol=1e-10)


class TestGradient(unittest.TestCase):
    def test_fit_gradient_matches_finite_differences(self):
        task = tasks.load_family("ring_n6")
        rng = np.random.default_rng(3)
        cand = candidates.sample_random(rng, task)
        tr = task.splits["train"]
        x = task.x[tr][:8]
        y = task.targets["alpha_0"][tr][:8]
        names = cand["param_names"]
        n = cand["n_qubits"]
        obs = train.obs_matrix(task.observables, n)
        th = np.linspace(-1, 1, len(names))
        w = np.linspace(-0.3, 0.3, len(task.observables))
        b = 0.1
        plans = [train._compile_plan(cand, task, x[i]) for i in range(len(x))]

        def loss(vec):
            tot = 0.0
            for i in range(len(x)):
                psi, _ = plans[i].run(vec, train._zero_state(n))
                e = ((np.abs(psi) ** 2) @ obs.T).reshape(-1)
                tot += (float(e @ w + b) - y[i]) ** 2
            return tot / len(x)

        g = np.zeros(len(names))
        for i in range(len(x)):
            psi, cache = plans[i].run(th, train._zero_state(n))
            e = ((np.abs(psi) ** 2) @ obs.T).reshape(-1)
            coef = (2.0 / len(x)) * (float(e @ w + b) - y[i])
            g += plans[i].grad(th, cache, psi * ((coef * w) @ obs))
        num = np.zeros(len(names))
        h = 1e-5
        for j in range(len(names)):
            tp = th.copy(); tp[j] += h
            tm = th.copy(); tm[j] -= h
            num[j] = (loss(tp) - loss(tm)) / (2 * h)
        np.testing.assert_allclose(g, num, atol=1e-6)


class TestFit(unittest.TestCase):
    def test_determinism_and_progress(self):
        task = tasks.load_family("ring_n6")
        tr = task.splits["train"]
        x, y = task.x[tr][:80], task.targets["alpha_0"][tr][:80]
        cand = candidates.sample_random(np.random.default_rng(5), task)
        f1 = train.fit(cand, task, x, y, 0, steps=40, batch=16)
        f2 = train.fit(cand, task, x, y, 0, steps=40, batch=16)
        np.testing.assert_array_equal(f1.theta, f2.theta)
        np.testing.assert_array_equal(f1.w, f2.w)
        self.assertEqual(f1.b, f2.b)
        self.assertLess(f1.loss_history[-1], f1.loss_history[0])

    def test_predict_matches_risk(self):
        task = tasks.load_family("ring_n6")
        tr = task.splits["train"]
        x, y = task.x[tr][:60], task.targets["alpha_0"][tr][:60]
        cand = candidates.sample_random(np.random.default_rng(9), task)
        f = train.fit(cand, task, x, y, 1, steps=20, batch=16)
        pred = f.predict(task, x)
        self.assertAlmostEqual(float(np.mean((pred - y) ** 2)), f.train_loss,
                               places=8)

    def test_rejects_invalid_candidate(self):
        task = tasks.load_family("ring_n6")
        with self.assertRaises(ValueError):
            train.fit({"block": []}, task, task.x[:2], task.targets["alpha_0"][:2], 0)


if __name__ == "__main__":
    unittest.main()
