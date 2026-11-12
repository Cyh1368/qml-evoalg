"""Unit tests: the decomposition is verified against brute force, not asserted.

Run:  python3 -m unittest discover -s shotcert -p 'test_*.py' -v
"""

from __future__ import annotations

import unittest

import numpy as np

from shotcert.core import (Group, Policy, born_prob, components, exact_risk, label_vector,
                           orbit_expectations, orbit_probs, predict_once, shot_variance)
from shotcert.tasks import control_task

REGIMES = ("help", "hurt", "interior")


def _xs(task, n=200, seed=5):
    return task.x_dist(n, np.random.default_rng(seed))


class TestGroupAndMeasurement(unittest.TestCase):
    def test_born_prob_range(self):
        e = np.linspace(-1.0, 1.0, 41)
        p = born_prob(e)
        self.assertTrue(np.all(p >= 0) and np.all(p <= 1))
        np.testing.assert_allclose(p, 0.5 * (1 + e), atol=1e-12)

    def test_shot_variance_of_scaled_bernoi(self):
        # a single shot returns 2*Bernoulli(p)-1, whose variance is 4p(1-p)
        p = 0.3
        rng = np.random.default_rng(0)
        draws = 2.0 * rng.binomial(1, p, size=400000) - 1.0
        self.assertAlmostEqual(float(np.var(draws)), float(shot_variance(p)), delta=0.01)

    def test_orbit_probs_shape(self):
        t = control_task(regime="help")
        x = np.array([0.4, 0.0])
        p = orbit_probs(t, x)
        self.assertEqual(len(p), len(t.group.actions))
        self.assertTrue(np.all(p >= 0) and np.all(p <= 1))
        # in the help regime the LABEL is invariant under the group; the MODEL is not
        mu = orbit_expectations(t, x)
        self.assertAlmostEqual(float(np.asarray(t.label(x)).reshape(-1)[0]),
                               float(np.asarray(t.label(t.group.actions[1](x))).reshape(-1)[0]),
                               places=12)
        self.assertGreater(abs(float(mu[0]) - float(mu[1])), 1e-3)


class TestDecompositionIdentity(unittest.TestCase):
    """R_S(a) = bias^2 + V_G/k + Sigma/S, exactly, for every policy mode."""

    def setUp(self):
        self.tasks = {r: control_task(regime=r) for r in REGIMES}
        self.xs = _xs(self.tasks["help"])

    def _policies(self):
        out = [Policy("a0", "raw", 1, 64),
               Policy("strat", "stratified", 2, 64),
               Policy("mix25", "mix", 2, 64, w=0.25),
               Policy("mix50", "mix", 2, 64, w=0.5),
               Policy("mix100", "mix", 2, 64, w=1.0)]
        for k in (1, 2, 4, 8, 16, 64):
            out.append(Policy("k%d" % k, "orbit_k", k, 64))
        return out

    def test_identity_holds_exactly(self):
        for reg, t in self.tasks.items():
            for pol in self._policies():
                R = exact_risk(t, pol, self.xs)
                b2, vg, sg = components(t, self.xs, pol)
                k = max(pol.k, 1)
                pred = b2 + vg / k + sg / pol.S
                self.assertAlmostEqual(R, pred, places=13,
                                       msg="%s/%s: R=%.10f pred=%.10f" % (reg, pol.name, R, pred))

    def test_mix_at_w_one_equals_stratified(self):
        """A mixture with w=1 IS the stratified orbit average; the two must agree exactly."""
        for reg, t in self.tasks.items():
            a = exact_risk(t, Policy("mix100", "mix", 2, 64, w=1.0), self.xs)
            b = exact_risk(t, Policy("strat", "stratified", 2, 64), self.xs)
            self.assertAlmostEqual(a, b, places=14, msg=reg)

    def test_F1_shot_term_independent_of_k(self):
        """At fixed total shots the shot term does not move; only the draw term does."""
        t = control_task(regime="hurt")          # nonzero orbit spread
        xs = _xs(t)
        sig = []
        vgs = []
        for k in (1, 2, 4, 8, 16, 32, 64):
            _, vg, sg = components(t, xs, Policy("k%d" % k, "orbit_k", k, 64))
            sig.append(sg)
            vgs.append(vg)
        self.assertTrue(max(sig) - min(sig) < 1e-12, "Sigma moved with k: %s" % sig)
        self.assertTrue(all(v == vgs[0] for v in vgs), "V_G moved with k: %s" % vgs)
        # and the risk itself decreases with k because V_G/k shrinks
        R = [exact_risk(t, Policy("k%d" % k, "orbit_k", k, 64), xs) for k in (1, 2, 4, 8, 16, 32, 64)]
        self.assertTrue(all(R[i] >= R[i + 1] - 1e-15 for i in range(len(R) - 1)), R)

    def test_monte_carlo_matches_exact_risk(self):
        """The deployed procedure and the analyzed formula must agree: same estimator, both ways."""
        from shotcert.core import predict_batch
        t = control_task(regime="interior")
        xs = _xs(t, n=200)
        rng = np.random.default_rng(11)
        reps = 20000
        for pol in (Policy("a0", "raw", 1, 32), Policy("k4", "orbit_k", 4, 32),
                    Policy("k16", "orbit_k", 16, 32), Policy("strat", "stratified", 2, 32),
                    Policy("mix50", "mix", 2, 32, w=0.5)):
            Z = predict_batch(t, xs, pol, rng, reps=reps)
            y = label_vector(t, xs)
            L = (Z - y) ** 2                       # (reps, n)
            mc = float(np.mean(L))
            per_input_se = np.std(L, axis=0) / np.sqrt(reps)
            se = float(np.mean(per_input_se))      # conservative: ignore cross-input averaging
            ex = exact_risk(t, pol, xs)
            self.assertLess(abs(mc - ex), 4.0 * se + 1e-9,
                            "%s: MC %.6f vs exact %.6f (se %.6f)" % (pol.name, mc, ex, se))

    def test_predict_once_agrees_with_sampling(self):
        """The scalar deployment path must be distributionally identical to the exact risk."""
        t = control_task(regime="hurt")
        xs = _xs(t, n=40)
        rng = np.random.default_rng(3)
        for pol in (Policy("a0", "raw", 1, 16), Policy("k4", "orbit_k", 4, 16),
                    Policy("strat", "stratified", 2, 16), Policy("mix50", "mix", 2, 16, w=0.5)):
            once = np.array([[predict_once(t, x, pol, rng) for x in xs] for _ in range(3000)])
            y = label_vector(t, xs)
            r_once = float(np.mean((once - y) ** 2))
            r_exact = exact_risk(t, pol, xs)
            self.assertLess(abs(r_once - r_exact), 0.004,
                            "%s once=%.5f exact=%.5f" % (pol.name, r_once, r_exact))


class TestPredeclaredRegimes(unittest.TestCase):
    """The three control regimes must behave as declared before any experiment is run."""

    def test_regimes_are_distinct_and_ordered(self):
        rows = {}
        for r in REGIMES:
            t = control_task(regime=r)
            xs = _xs(t, n=1200)
            raw = exact_risk(t, Policy("a0", "raw", 1, 64), xs)
            full = exact_risk(t, Policy("strat", "stratified", 2, 64), xs)
            ws = np.arange(0.0, 1.001, 0.05)
            curve = [exact_risk(t, Policy("mix", "mix", 2, 64, w=w), xs) for w in ws]
            best = float(ws[int(np.argmin(curve))])
            rows[r] = (raw, full, best)
        # help: full averaging strictly better than raw
        self.assertLess(rows["help"][1], rows["help"][0] - 1e-4)
        self.assertAlmostEqual(rows["help"][2], 1.0, places=6)
        # hurt: full averaging strictly worse than raw
        self.assertGreater(rows["hurt"][1], rows["hurt"][0] + 1e-4)
        self.assertAlmostEqual(rows["hurt"][2], 0.0, places=6)
        # interior: the minimiser is strictly inside (0,1) and beats both endpoints
        raw, full, best = rows["interior"]
        self.assertGreater(best, 0.05)
        self.assertLess(best, 0.95)


class TestBudgetFeasibility(unittest.TestCase):
    """Every policy that enters a comparison must spend at most its declared shots."""

    def test_feasible_only_when_k_le_S(self):
        self.assertTrue(Policy("ok", "orbit_k", 8, 32).feasible())
        self.assertTrue(Policy("ok", "orbit_k", 32, 32).feasible())
        self.assertFalse(Policy("bad", "orbit_k", 64, 32).feasible(),
                         "k=64 with S=32 spends 64 shots")
        self.assertEqual(Policy("bad", "orbit_k", 64, 32).shots_used, 64)

    def test_all_declared_menus_feasible(self):
        from shotcert.experiments.exp_control import menu
        for S in (4, 8, 16, 32, 64, 128):
            for pol in menu(S):
                self.assertTrue(pol.feasible(),
                                "S=%d policy %s uses %d shots" % (S, pol.name, pol.shots_used))


class TestPhysicsTasks(unittest.TestCase):
    """A task whose response does not vary is a bug, not a result. Both past degenerate tasks
    (a hermitised matrix exponential, a Neel initial state that is an eigenstate of the measured
    Z-string) looked perfectly complete and produced zero risk."""

    def test_heisenberg_response_varies(self):
        from shotcert.physics import HeisenbergResponse
        R = HeisenbergResponse(n=6, J_alt=1.3, c_rect=0.18)
        vals = [R.exact(t, 0.3) for t in (0.0, 0.3, 0.7, 1.1)]
        self.assertGreater(max(vals) - min(vals), 0.05, "response is constant: %s" % vals)
        self.assertGreater(abs(R.exact(0.7, 0.6) - R.device(0.7, 0.6)), 1e-6,
                           "device and exact agree exactly: the rectification error is inert")

    def test_cluster_response_varies(self):
        from shotcert.physics import ClusterIsingResponse
        R = ClusterIsingResponse(n=7, c_rect=0.15)
        vals = [R.exact(t, 0.25) for t in (0.0, 0.2, 0.5, 0.9)]
        self.assertGreater(max(vals) - min(vals), 0.01, "cluster response constant: %s" % vals)
        self.assertGreater(abs(R.exact(0.5, 0.4) - R.device(0.5, 0.4)), 1e-6)

    def test_control_regimes_give_nonzero_risk(self):
        from shotcert.core import exact_risk as er
        from shotcert.core import Policy
        for reg in REGIMES:
            t = control_task(regime=reg)
            xs = _xs(t, n=200)
            self.assertGreater(er(t, Policy("a0", "raw", 1, 32), xs), 1e-6, reg)


class TestGroupClosure(unittest.TestCase):
    def test_sign_flip_closed(self):
        g = control_task(regime="help").group
        x = np.array([0.7, -0.3])
        for a in g.actions:
            for b in g.actions:
                self.assertTrue(any(np.allclose(a(b(x)), c(x)) for c in g.actions))

    def test_identity_present(self):
        g = control_task(regime="help").group
        x = np.array([0.7, -0.3])
        self.assertTrue(any(np.allclose(a(x), x) for a in g.actions))


if __name__ == "__main__":
    unittest.main()
