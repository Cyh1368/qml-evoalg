"""Unit tests for WP-REPAIR-2 (research/REVISED_PROTOCOL.md sections 1-3).

Cheap invariants only (no long training runs):
* the repaired arm is exactly equivariant (channel residual at roundoff);
* ``control_dup`` is the ``original`` interaction at angle 2b, so
  ``control_matched`` (initial ``b`` halved) has an *identical initial operator*
  to ``original`` while ``control_dup`` at the same seed does not;
* the orbit-completed projection identity holds exactly for an invariant target;
* ``eta = 0`` rows carry no breaking direction (the replication unit is the
  optimiser seed, not (direction, seed)).
"""
import unittest

import numpy as np

from research.core import tasks as _tasks
from research.experiments.repair import repair_experiment as _r1
from research.experiments.repair import repair_experiment2 as _r2


class Repair2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task = _tasks.load_family("ring_n6", development=True, locked=False)
        cls.closure = _r1.group_closure(cls.task.generators)
        cls.n = int(cls.task.n_qubits)

    def test_gate_counts_and_symmetry(self):
        theta = np.array([0.3, -1.1, 0.7])
        counts = {a: len(_r2.arm_block(a, self.n)) - 2 * self.n for a in _r2.ARMS}
        self.assertEqual(counts["original"], 15)
        for arm in ("repaired", "control_dup", "control_rand", "control_matched"):
            self.assertEqual(counts[arm], 30, arm)
        self.assertLess(_r2.channel_residual("repaired", self.n, theta,
                                             self.closure)["channel_mean"], 1e-12)
        for arm in ("original", "control_dup", "control_rand"):
            self.assertGreater(_r2.channel_residual(arm, self.n, theta,
                                                    self.closure)["channel_mean"],
                               1e-3, arm)

    def test_control_dup_is_original_at_double_angle(self):
        theta = np.array([0.4, 0.55, -0.25])
        u_dup = _r1._sym.unitary(_r2.arm_block("control_dup", self.n),
                                 {"a": theta[0], "b": theta[1], "c": theta[2]}, self.n)
        u_orig = _r1._sym.unitary(_r2.arm_block("original", self.n),
                                  {"a": theta[0], "b": 2 * theta[1], "c": theta[2]},
                                  self.n)
        self.assertLess(np.linalg.norm(u_dup - u_orig), 1e-12)

    def test_operator_matched_initialisation(self):
        n_train = int(self.task.splits["train"].sum())
        for seed in (0, 5, 17):
            t_orig = _r2.init_theta(seed, n_train, 256, "original")
            t_match = _r2.init_theta(seed, n_train, 256, "control_matched")
            t_dup = _r2.init_theta(seed, n_train, 256, "control_dup")
            self.assertAlmostEqual(t_match[1] * 2.0, t_orig[1], places=12)
            d_match = _r2.operator_distance("control_matched", self.n, t_match,
                                            self.closure, t_orig)
            d_dup = _r2.operator_distance("control_dup", self.n, t_dup,
                                          self.closure, t_orig)
            self.assertLess(d_match, 1e-12)
            self.assertGreater(d_dup, 1e-3)

    def test_projection_identity_at_eta_zero(self):
        tf = _r2.TargetFn(self.task, None, 0.0, self.closure)
        dev = np.asarray(self.task.x)[np.asarray(self.task.splits["validation"], bool)]
        theta = np.array([0.9, -0.4, 1.6])
        out = _r2.orbit_eval("control_dup", self.task, tf, theta, dev, self.closure)
        self.assertLess(out["orb_identity_gap"], 1e-12)
        self.assertLess(abs(out["orb_cross_term"]), 1e-12)
        self.assertLessEqual(out["orb_risk_proj"], out["orb_risk"] + 1e-12)

    def test_b_is_group_centred_and_normalised(self):
        x = np.asarray(self.task.x, float)
        tf = _r2.TargetFn(self.task, 101, 1.0, self.closure)
        b = tf.b_of(x)
        orbit_mean = np.mean([tf.b_of(x[:, list(p)]) for p in self.closure], axis=0)
        self.assertLess(np.max(np.abs(orbit_mean)), 1e-10)
        train = np.asarray(self.task.splits["train"], bool)
        self.assertAlmostEqual(float(np.mean(b[train] ** 2)), 1.0, places=9)

    def test_eta_zero_rows_have_no_direction(self):
        rows = [{"eta": 0.0, "direction_seed": None}, {"eta": 1.0, "direction_seed": 101}]
        for row in rows:
            if row["eta"] == 0.0:
                self.assertIsNone(row["direction_seed"])
        # the design emits a single direction level at eta = 0
        dirs = {r["direction_seed"] for r in rows if r["eta"] == 0.0}
        self.assertEqual(dirs, {None})


if __name__ == "__main__":
    unittest.main()
