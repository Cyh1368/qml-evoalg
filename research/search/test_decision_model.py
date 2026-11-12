"""Unit tests for the A7 decision model: the threshold algebra and the insufficiency claim."""

import unittest

from research.search import decision_model as DM


def _recs(deltas, valid):
    """Synthetic candidate records: one regime, given deltas and whether the group is a symmetry."""
    return [{"regimes": {"r": {"delta": d, "group_is_label_symmetry": v,
                               "label_corrected_accepts": v}}}
            for d, v in zip(deltas, valid)]


class TestThresholdRule(unittest.TestCase):
    def test_threshold_is_the_harm_share(self):
        # B = 0.00345 benefit, H = 0.00399 harm (the measured ring magnitudes, to be checked
        # against the A7 record): q* = H / (B + H)
        q = DM.threshold_rule(0.00345, 0.00399)
        self.assertAlmostEqual(q, 0.00399 / (0.00345 + 0.00399), places=12)
        self.assertGreater(q, 0.5)          # harm outweighs benefit, so the bar is above a half

    def test_repair_cost_raises_the_bar(self):
        base = DM.threshold_rule(0.00345, 0.00399, w=0.0, c_repair=0.0)
        paid = DM.threshold_rule(0.00345, 0.00399, w=1.0, c_repair=0.001)
        self.assertGreater(paid, base)

    def test_benefit_rise_lowers_the_bar(self):
        self.assertLess(DM.threshold_rule(0.010, 0.00399),
                        DM.threshold_rule(0.00345, 0.00399))

    def test_degenerate_case_is_undefined_not_zero(self):
        self.assertIsNone(DM.threshold_rule(0.0, 0.0))


class TestPosterior(unittest.TestCase):
    def test_perfect_specificity_gives_posterior_one(self):
        self.assertAlmostEqual(DM.posterior(0.3, 0.5, 1.0), 1.0)

    def test_useless_screen_returns_the_prior(self):
        # sensitivity 1 and specificity 0 means "always accept": the posterior is the prior
        self.assertAlmostEqual(DM.posterior(0.4, 1.0, 0.0), 0.4)

    def test_zero_prior_gives_zero_posterior(self):
        self.assertEqual(DM.posterior(0.0, 0.9, 0.9), 0.0)

    def test_imperfect_screen_lies_between_prior_and_one(self):
        q = DM.posterior(0.5, 0.9, 0.8)
        self.assertGreater(q, 0.5)
        self.assertLess(q, 1.0)


class TestTwoProbabilitiesAreInsufficient(unittest.TestCase):
    """The withdrawn claim, tested as a claim: matched probabilities, opposite policies."""

    @staticmethod
    def _world(benefit, harm):
        """Five valid and five invalid candidates; the SAME screen in both worlds.

        Screen behaviour is identical across worlds: it accepts 4 of 5 valid entries
        (sensitivity 0.8) and 2 of 5 invalid ones (specificity 0.6), so P(valid) = 0.5 and the
        posterior it induces are the same numbers in both worlds. Only the conditional effect
        magnitudes differ.
        """
        valid = [True] * 5 + [False] * 5
        accepts = [True] * 4 + [False] + [True] * 2 + [False] * 3
        deltas = [-benefit] * 5 + [harm] * 5
        return [{"regimes": {"r": {"delta": d, "group_is_label_symmetry": v,
                                   "label_corrected_accepts": a}}}
                for d, v, a in zip(deltas, valid, accepts)]

    def test_matched_probabilities_different_optima(self):
        mild = self._world(benefit=0.0001, harm=0.00005)
        harsh = self._world(benefit=0.0010, harm=0.0040)
        e_mild, e_harsh = DM.screen_errors(mild, "r"), DM.screen_errors(harsh, "r")
        # the two probabilities of the withdrawn claim, and the screen's errors, are identical
        self.assertEqual(e_mild["sensitivity"], e_harsh["sensitivity"])
        self.assertEqual(e_mild["specificity"], e_harsh["specificity"])
        m_mild, m_harsh = DM.magnitudes(mild, "r"), DM.magnitudes(harsh, "r")
        self.assertNotAlmostEqual(m_mild["q_star"], m_harsh["q_star"], places=3)
        # the posterior the screen induces, identical in both worlds
        q_mild = DM.posterior(0.5, e_mild["sensitivity"], e_mild["specificity"])
        q_harsh = DM.posterior(0.5, e_harsh["sensitivity"], e_harsh["specificity"])
        self.assertAlmostEqual(q_mild, q_harsh)
        dec_mild = q_mild > m_mild["q_star"]
        dec_harsh = q_harsh > m_harsh["q_star"]
        self.assertNotEqual(dec_mild, dec_harsh)
        self.assertTrue(dec_mild)
        self.assertFalse(dec_harsh)

    def test_screen_errors_measured_not_assumed(self):
        recs = [{"regimes": {"r": {"delta": d, "group_is_label_symmetry": v,
                                   "label_corrected_accepts": v}}}
                for d, v in zip([-0.001, -0.002, 0.001, 0.002], [True, True, False, False])]
        err = DM.screen_errors(recs, "r")
        self.assertEqual(err["sensitivity"], 1.0)
        self.assertEqual(err["specificity"], 1.0)
        self.assertEqual(err["fp"], 0)
        self.assertEqual(err["fn"], 0)


class TestMagnitudes(unittest.TestCase):
    def test_benefit_and_harm_are_signed_magnitudes(self):
        recs = _recs([-0.002, -0.004, 0.001, 0.003], [True, True, False, False])
        m = DM.magnitudes(recs, "r")
        self.assertAlmostEqual(m["benefit_B"], 0.003)
        self.assertAlmostEqual(m["harm_H"], 0.002)
        self.assertEqual(m["n_beneficial"], 2)
        self.assertEqual(m["n_harmful"], 2)
        self.assertIn("q_star_ci95", m)
        lo, hi = m["q_star_ci95"]
        self.assertLessEqual(lo, m["q_star"] + 1e-12)
        self.assertGreaterEqual(hi, m["q_star"] - 1e-12)


if __name__ == "__main__":
    unittest.main()
