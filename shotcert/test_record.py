"""A6.2 stop gate (a): the calibration record's expected contrast must BE the deployed-risk difference.

The third review's principal defect was that the group arm scored Delta_{2s} while its record held s
identity shots, so it estimated R_{2s}(strat) - R_s(raw). These tests pin the repaired invariant for
every policy in both arms at several small budgets, against an enumerator written independently of
core._estimator_moments, and pin the ledger cost the repair requires.
"""
import unittest
import numpy as np
from shotcert.core import Policy, exact_risk
from shotcert.record import (audit, common_record, identity_block_expected_loss,
                             record_expected_loss, record_losses, record_shape,
                             raw_mean_from_record)
from shotcert.reference import reference_risk_x
from shotcert.tasks import control_task
from shotcert.physics import heisenberg_task, cluster_task


def menu(S, G):
    return ([Policy("a0", "raw", S=S, orbit_size=G),
             Policy("strat", "stratified", S=S, orbit_size=G)]
            + [Policy("gshr", "shrink", S=S, gamma=0.3, orbit_size=G, base="strat")]
            + [Policy("shr", "shrink", S=S, gamma=0.3, orbit_size=G, base="raw")])


class TestCommonEstimand(unittest.TestCase):
    tasks = [("control", control_task(regime="help")),
             ("heis", heisenberg_task(n=6, a_odd=1.0, c_rect=0.18)),
             ("cluster", cluster_task(n=7, a_odd=0.0))]

    def test_record_expected_loss_matches_enumeration(self):
        for _, task in self.tasks:
            G = len(task.group.actions)
            xs = task.x_dist(10, np.random.default_rng(3))
            for S in (4, 8, 16, 64):
                if S < G:
                    continue
                for name, v in audit(task, menu(S, G), xs, S).items():
                    self.assertTrue(v["pass"], "%s S=%d %s diff=%.2e"
                                    % (task.__class__, S, name, v["abs_diff"]))

    def test_ledger_cost_is_two_minus_one_over_G(self):
        """A6.1: the group arm's record must cost S(2 - 1/G) per instance, no less."""
        task = control_task(regime="help")
        G = len(task.group.actions)
        for S in (8, 16, 64):
            rec = common_record(task, task.x_dist(5, np.random.default_rng(1)), S,
                                np.random.default_rng(2))
            self.assertEqual(rec["cost_per_instance"], int(S * (2.0 - 1.0 / G)))
            per, extra = record_shape(S, G)
            self.assertEqual(per + extra, S, "raw baseline must receive exactly S identity shots")

    def test_raw_baseline_is_the_S_shot_mean(self):
        """The reused identity block must not make the baseline cheaper or noisier than S shots."""
        task = control_task(regime="help")
        G = len(task.group.actions)
        S, n = 16, 4000
        xs = task.x_dist(n, np.random.default_rng(7))
        rec = common_record(task, xs, S, np.random.default_rng(8))
        z = raw_mean_from_record(rec)
        from shotcert.core import orbit_expectations as _oe
        self.assertLess(abs(float(np.mean(z)) - float(np.mean([_oe(task, x)[0] for x in xs]))), 0.05)
        # The noise part of the variance must match S iid shots, not the S/G the orbit block alone
        # supplies. Var(z) also carries the between-instance variance of mu_0(X), so the comparison is
        # made on the residual z - mu_0(X); comparing raw variances conflates the two terms.
        from shotcert.core import orbit_expectations, shot_var_from_mu
        mu0 = np.array([float(orbit_expectations(task, x)[0]) for x in xs])
        sv = float(np.mean([shot_var_from_mu(np.asarray(orbit_expectations(task, x)))[0]
                            for x in xs]))
        self.assertLess(abs(float(np.var(z - mu0)) - sv / S), 0.05 * sv / S)
        # The orbit block alone would leave the baseline with S/G shots, i.e. G times the noise.
        self.assertLess(float(np.var(z - mu0)), sv / (S / G) * 0.6)

    def test_no_policy_is_scored_from_shots_it_does_not_pay_for(self):
        """alloc needs unequal blocks, so the equal-block common record must refuse it."""
        task = control_task(regime="help")
        G = len(task.group.actions)
        S = 16
        xs = task.x_dist(4, np.random.default_rng(1))
        rec = common_record(task, xs, S, np.random.default_rng(2))
        y = np.array([float(np.asarray(task.label(x)).reshape(-1)[0]) for x in xs])
        with self.assertRaises(AssertionError):
            record_losses(task, [Policy("a", "alloc", S=S, orbit_size=G, alloc=(12, 4))], rec, y)

    def test_repaired_contrast_targets_the_deployed_difference(self):
        """The exact regression: E[D_cal] must equal R_S(strat) - R_S(raw), not the s-shot version."""
        task = heisenberg_task(n=6, a_odd=1.0, c_rect=0.18)
        G = len(task.group.actions)
        S = 16
        xs = task.x_dist(300, np.random.default_rng(5))
        strat, a0 = Policy("strat", "stratified", S=S, orbit_size=G), Policy("a0", "raw", S=S, orbit_size=G)
        target = exact_risk(task, strat, xs) - exact_risk(task, a0, xs)
        got = (record_expected_loss(task, strat, xs, S)
               - record_expected_loss(task, a0, xs, S))
        self.assertLess(abs(got - target), 1e-12)
        # and the OLD construction must differ from the target by the predicted offset
        weak = Policy("a0w", "raw", S=S // G, orbit_size=G)
        offset = (record_expected_loss(task, strat, xs, S)
                  - identity_block_expected_loss(task, weak, xs, S // G)) - target
        from shotcert.core import orbit_expectations, shot_var_from_mu
        sv = np.mean([shot_var_from_mu(np.asarray(orbit_expectations(task, x)))[0] for x in xs])
        self.assertLess(abs(offset + sv / (2.0 * (S // G))), 1e-12,
                        "the s-shot baseline must be off by exactly sigma_0^2/(2s)")


if __name__ == "__main__":
    unittest.main()
