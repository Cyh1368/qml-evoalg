"""A5: the closed-form optimum must be the optimum of the exact risk, not just of the theory."""
import unittest
import numpy as np
from shotcert.core import Policy, exact_risk
from shotcert.tasks import control_task
from shotcert.theory import coefficients, w_star, thresholds, risk_theory


class TestRepaymentTheorem(unittest.TestCase):
    def setUp(self):
        self.task = control_task(regime="help")
        self.xs = self.task.x_dist(80, np.random.default_rng(11))
        self.c = coefficients(self.task, self.xs)

    def test_risk_formula_matches_exact_risk(self):
        """R_S(w) from four scalars must equal the enumerated deployed risk."""
        G = len(self.task.group.actions)
        for S in (32, 64):
            for w in (0.0, 0.25, 0.5, 0.75, 1.0):
                p = Policy("m", "mix", S=S, w=w, orbit_size=G)
                if not p.feasible():
                    continue
                self.assertLess(abs(risk_theory(self.c, w, S)
                                    - exact_risk(self.task, p, self.xs)), 2e-3,
                                "S=%d w=%.2f" % (S, w))

    def test_w_star_is_the_exact_argmin(self):
        """Grid argmin of the EXACT risk must sit within one grid step of the closed form."""
        G = len(self.task.group.actions)
        ws = np.linspace(0.0, 1.0, 51)
        for S in (64, 256):
            risks, ok = [], []
            for w in ws:
                p = Policy("m", "mix", S=S, w=float(w), orbit_size=G)
                if p.feasible():
                    risks.append(exact_risk(self.task, p, self.xs)); ok.append(float(w))
            emp = ok[int(np.argmin(risks))]
            self.assertLess(abs(emp - w_star(self.c, S)), 0.05,
                            "S=%d exact argmin %.2f vs theory %.2f" % (S, emp, w_star(self.c, S)))

    def test_convexity_in_the_coefficients(self):
        self.assertGreater(self.c["A"], 0.0)

    def test_luxury_good_monotonicity(self):
        """dw*/dS has the sign of V: if symmetrisation costs shot variance, weight rises with budget."""
        c = dict(self.c); c["V"] = 0.05
        w_small, w_big = w_star(c, 32), w_star(c, 4096)
        self.assertLessEqual(w_small, w_big + 1e-12)
        c["V"] = -0.05
        self.assertGreaterEqual(w_star(c, 32), w_star(c, 4096) - 1e-12)

    def test_thresholds_are_the_boundaries_they_claim(self):
        c = dict(self.c); c["A"], c["V"], c["dD"] = 0.02, 0.08, 0.01
        s_on, s_full = thresholds(c)
        self.assertGreater(s_on, 0.0)
        self.assertLess(w_star(c, s_on * 0.5), 1e-12)      # below S_on: buy no symmetry
        self.assertGreater(w_star(c, s_on * 2.0), 0.0)

    def test_partial_beats_both_extremes_when_dd_negative(self):
        """The non-obvious case: symmetrisation hurts the ideal predictor, yet some symmetry is best."""
        # Coefficients must satisfy the identity dD = -2B - A, or the closed form and the risk
        # formula disagree; the first version of this test set B=0 with an independent dD and failed.
        A, dD, V = 0.00822, -0.00213, 0.00551
        c = {"A": A, "B": -(dD + A) / 2.0, "dD": dD, "V": V, "D0": 0.02, "sigma0": 0.5}
        S = 256
        w = w_star(c, S)
        self.assertTrue(0.0 < w < 1.0, "expected interior optimum, got %.3f" % w)
        self.assertLess(risk_theory(c, w, S), risk_theory(c, 0.0, S))
        self.assertLess(risk_theory(c, w, S), risk_theory(c, 1.0, S))


if __name__ == "__main__":
    unittest.main()
