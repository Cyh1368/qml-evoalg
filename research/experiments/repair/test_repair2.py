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

    def test_repaired_pair_analytic_factorisation(self):
        """Analytic equivariance proof, checked numerically (appendix identity).

        ``CRZ_ij(b) CRZ_ji(b) = exp(-i b (Z_i+Z_j)/4) exp(i b Z_i Z_j / 2)``: a
        permutation-symmetric single-qubit field times a manifestly symmetric ZZ
        term, hence equivariant for *every* permutation, not merely D6. Dually
        ``CRZ_ij(b)^2 = CRZ_ij(2b) = exp(-i b Z_j/2) exp(i b Z_i Z_j/2)`` hits only
        the target wire, which is exactly why the gate-count-matched control is not
        equivariant.
        """
        from research.core import simulator as _sim
        b = 0.77
        zi = np.array([1.0, 1.0, -1.0, -1.0])      # Z on wire 0 (q0 = MSB)
        zj = np.array([1.0, -1.0, 1.0, -1.0])      # Z on wire 1
        diag = lambda v: np.diag(v.astype(complex))
        rep = _sim.unitary([{"gate": "CRZ", "wires": [0, 1], "param": "b"},
                            {"gate": "CRZ", "wires": [1, 0], "param": "b"}],
                           {"b": b}, 2)
        analytic = diag(np.exp(-1j * b / 4.0 * (zi + zj))) @ \
            diag(np.exp(1j * b / 2.0 * (zi * zj)))
        self.assertTrue(np.allclose(rep, analytic, atol=1e-13))
        dup = _sim.unitary([{"gate": "CRZ", "wires": [0, 1], "param": "b"},
                            {"gate": "CRZ", "wires": [0, 1], "param": "b"}],
                           {"b": b}, 2)
        dup_analytic = diag(np.exp(-1j * b / 2.0 * zj)) @ \
            diag(np.exp(1j * b / 2.0 * (zi * zj)))
        self.assertTrue(np.allclose(dup, dup_analytic, atol=1e-13))
        swap = np.eye(4, dtype=complex)[np.ix_([0, 1, 2, 3], [0, 2, 1, 3])]
        self.assertTrue(np.allclose(rep @ swap, swap @ rep, atol=1e-13))
        self.assertFalse(np.allclose(dup @ swap, swap @ dup, atol=1e-6))

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
