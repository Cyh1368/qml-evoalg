"""A2.4: the closed-form risk must agree with an enumeration of the predictor itself."""
from __future__ import annotations
import unittest

import numpy as np

from shotcert.core import Policy, exact_risk
from shotcert.reference import reference_risk
from shotcert.tasks import control_task


class TestReferenceEnumeration(unittest.TestCase):
    """exact_risk vs a from-scratch enumeration of draws AND binomial shot outcomes.

    Sizes are deliberately tiny: the reference enumerates every outcome combination, so this is a
    correctness check, not a scaling one. Small S is also where the integer-division factors in
    per = S // k actually bite, which is where a closed form is most likely to be wrong.
    """

    def setUp(self):
        self.task = control_task(regime="help")
        self.xs = self.task.x_dist(24, np.random.default_rng(99))

    def _pols(self, S, k):
        G = len(self.task.group.actions)
        out = [Policy("a0", "raw", S=S, orbit_size=G),
               Policy("strat", "stratified", S=S, orbit_size=G),
               Policy("orbit_k", "orbit_k", k=k, S=S, orbit_size=G)]
        for w in (0.25, 0.75):
            out.append(Policy("mix%d" % int(w * 100), "mix", S=S, w=w, orbit_size=G))
        return [p for p in out if p.feasible()]

    def test_agrees_for_small_budgets(self):
        worst = 0.0
        for S in (2, 4, 6, 8):
            for k in (1, 2, 3, 4):
                if S // k < 1:
                    continue
                for p in self._pols(S, k):
                    a = exact_risk(self.task, p, self.xs)
                    b = reference_risk(self.task, p, self.xs)
                    worst = max(worst, abs(a - b))
                    self.assertLess(abs(a - b), 1e-12,
                                    "S=%d k=%d %s: closed %.12f enumerated %.12f"
                                    % (S, k, p.name, a, b))
        self.assertLess(worst, 1e-12)

    def test_reference_is_not_the_same_code_path(self):
        """A guard against 'fixing' the reference by importing the thing it verifies."""
        import shotcert.reference as ref
        # Checked against the module namespace and its imports, not its prose: the docstring names
        # _estimator_moments to explain what this file replaces, and a substring check on the source
        # flags that explanation. What must be absent is the symbol itself.
        self.assertFalse(hasattr(ref, "_estimator_moments"))
        self.assertFalse(hasattr(ref, "components"))
        imported = [n for n in dir(ref) if n.startswith("_") and callable(getattr(ref, n))]
        self.assertNotIn("_estimator_moments", imported)

    def test_circuits_are_bounded_by_the_orbit(self):
        """A2.3: a two-element group cannot compile eight distinct circuits."""
        G = len(self.task.group.actions)
        for k in (1, 2, 4, 8, 64):
            p = Policy("orbit_k", "orbit_k", k=k, S=64, orbit_size=G)
            self.assertLessEqual(p.circuits, G)
        self.assertEqual(Policy("o", "orbit_k", k=64, S=64, orbit_size=G).circuits, G)

    def test_switches_are_counted_from_the_schedule(self):
        G = len(self.task.group.actions)
        p = Policy("o", "orbit_k", k=64, S=64, orbit_size=G)
        self.assertEqual(p.max_switches, G - 1)
        self.assertEqual(Policy("r", "raw", S=8, orbit_size=G).max_switches, 0)


if __name__ == "__main__":
    unittest.main()
