"""Unit tests for WP-REPAIR correctness (no cluster, small budgets)."""
import unittest

import numpy as np

from research.core import tasks as _tasks
from research.core import candidates as _cand
from research.core import train as _train
from research.experiments.repair import repair_experiment as R


class TestGroup(unittest.TestCase):
    def test_d6_closure_order(self):
        task = _tasks.load_family("ring_n6")
        closure = R.group_closure(task.generators)
        self.assertEqual(len(closure), 12)  # |D6| = 12
        # closure is closed under composition
        genset = set(closure)
        for p in closure[:4]:
            for q in closure[:4]:
                comp = tuple(p[q[i]] for i in range(len(p)))
                self.assertIn(comp, genset)


class TestArms(unittest.TestCase):
    def setUp(self):
        self.task = _tasks.load_family("ring_n6")
        self.n = int(self.task.n_qubits)
        self.closure = R.group_closure(self.task.generators)

    def test_equal_param_count(self):
        for arm in R.ARMS:
            self.assertEqual(_cand.n_params(R.make_candidate(arm, self.n)), 3)

    def test_control_operator_family_equals_original(self):
        """Two same-direction CRZs sharing the angle == one CRZ at double the
        angle, so control is operator-FAMILY-equivalent to original (the learner
        rescales b) and has repair's gate count but original's asymmetry."""
        theta = np.array([0.7, 1.1, -0.4])
        theta_double = np.array([0.7, 2.2, -0.4])  # b -> 2b
        rows = self.task.x[self.task.splits["train"]][:16]
        f_c = _train.batched_expectations(
            R.make_candidate("control", self.n), self.task, rows, theta)
        f_o = _train.batched_expectations(
            R.make_candidate("original", self.n), self.task, rows, theta_double)
        np.testing.assert_allclose(f_c, f_o, atol=1e-10)

    def test_repaired_is_equivariant_original_is_not(self):
        theta = np.array([0.9, 1.3, -0.6])
        rep = R.block_channel_residual("repaired", self.n, theta, self.closure)
        orig = R.block_channel_residual("original", self.n, theta, self.closure)
        ctrl = R.block_channel_residual("control", self.n, theta, self.closure)
        self.assertLess(rep["channel_mean"], 1e-12)   # exactly equivariant
        self.assertGreater(orig["channel_mean"], 1e-6)  # asymmetric
        # control's asymmetry equals original's at the double-angle parameterisation
        orig_double = R.block_channel_residual(
            "original", self.n, np.array([0.9, 2.6, -0.6]), self.closure)
        self.assertAlmostEqual(ctrl["channel_mean"], orig_double["channel_mean"],
                               places=9)


class TestFloor(unittest.TestCase):
    def test_analytic_matches_empirical_floor(self):
        task = _tasks.load_family("ring_n6")
        targets, _ = R.build_targets(task, 101, (0.0, 0.5, 1.0))
        for eta, tg in targets.items():
            self.assertAlmostEqual(tg["floor_analytic"], tg["floor_empirical"],
                                   places=6,
                                   msg="floor identity failed at eta=%s" % eta)

    def test_eta0_target_is_invariant(self):
        task = _tasks.load_family("ring_n6")
        targets, _ = R.build_targets(task, 101, (0.0,))
        y = targets[0.0]["y_dev"]
        # eta=0 target is the orbit-averaged teacher -> zero invariant floor
        self.assertLess(targets[0.0]["floor_analytic"], 1e-20)


if __name__ == "__main__":
    unittest.main()
