import unittest

import numpy as np

from research.core import paired as P


class PairedTests(unittest.TestCase):
    def test_collapse_units_drops_exact_repeats(self):
        pairs = [((0,), 1.0), ((0,), 1.0), ((1,), 2.0), ((1,), 2.0)]
        out = P.collapse_units(pairs)
        self.assertEqual(len(out), 2)                      # 4 rows, 2 units
        self.assertEqual(sorted(out.values()), [1.0, 2.0])

    def test_collapse_units_rejects_conflicting_repeats(self):
        with self.assertRaises(ValueError):
            P.collapse_units([((0,), 1.0), ((0,), 1.0001)])

    def test_shifted_bootstrap_detects_shift(self):
        rng = np.random.default_rng(0)
        null = rng.normal(0, 1, 40)
        self.assertGreater(P.shifted_bootstrap_p(null, n_boot=2000)["p"], 0.05)
        shifted = null + 0.8
        self.assertLess(P.shifted_bootstrap_p(shifted, n_boot=2000)["p"], 0.05)

    def test_shifted_bootstrap_p_is_never_zero(self):
        out = P.shifted_bootstrap_p([1.0] * 12, n_boot=1000)
        self.assertGreater(out["p"], 0.0)
        self.assertEqual(out["p_floor"], 1.0 / 1001.0)

    def test_signflip_exact_small_sample(self):
        # four identical differences: only the 2 of 2**4 all-same-sign patterns keep
        # the observed |mean| -> exact p = 2/16
        out = P.signflip_p([-0.5, -0.5, -0.5, -0.5])
        self.assertTrue(out["exact"])
        self.assertAlmostEqual(out["p"], 2.0 / 16.0, places=12)
        # mixed signs: 10 of 16 patterns give |mean| >= 0.25
        self.assertAlmostEqual(P.signflip_p([-0.5, -0.5, -0.5, 0.5])["p"],
                               10.0 / 16.0, places=12)

    def test_signflip_randomised_reports_floor(self):
        out = P.signflip_p(list(np.linspace(-1, 1, 20)), n_boot=500, seed=1)
        self.assertFalse(out["exact"])
        self.assertGreater(out["p"], 0.0)

    def test_holm_matches_textbook(self):
        adj = P.holm([0.01, 0.04, 0.03])
        self.assertAlmostEqual(adj[0], 0.03, places=12)   # 3 x 0.01
        self.assertAlmostEqual(adj[1], 0.06, places=12)   # running max of 2 x 0.03
        self.assertAlmostEqual(adj[2], 0.06, places=12)

    def test_verdict_wording(self):
        self.assertEqual(P.verdict(-0.2, -0.01), "a better (raw CI excludes 0 on the "
                                                 "negative side)")
        self.assertIn("not detected", P.verdict(-0.1, 0.1))
        self.assertIn("practically equivalent", P.verdict(-0.01, 0.02, margin=0.05))

    def test_verdict_direction_for_lower_is_better_metric(self):
        # REVIEW_ROUND2 6: a wholly positive a-minus-b *risk* interval means a is worse.
        self.assertEqual(P.verdict(0.01, 0.2),
                         "a worse (raw CI excludes 0 on the positive side)")
        # for a higher-is-better metric (accuracy) the same interval favours a's opponent
        self.assertEqual(P.verdict(0.01, 0.2, lower_is_better=False),
                         "b worse (raw CI excludes 0 on the positive side)")

    def test_verdict_cannot_outrun_the_adjusted_test(self):
        out = P.verdict(-0.002, -0.0001, p_adjusted=0.246)
        self.assertIn("not detected after multiplicity adjustment", out)
        self.assertNotIn("a better", out)
        self.assertIn("a better", P.verdict(-0.002, -0.0001, p_adjusted=0.043))
        # equivalence wording survives only when the CI really sits inside the margin
        self.assertIn("practically equivalent",
                      P.verdict(-0.001, 0.001, margin=0.01, p_adjusted=0.9))

    def test_wilson_ci_denominators(self):
        z = P.wilson_ci(0, 20)
        self.assertEqual((z["k"], z["n"]), (0, 20))
        self.assertEqual(z["rate"], 0.0)
        self.assertEqual(z["ci95_low"], 0.0)
        self.assertGreater(z["ci95_high"], 0.0)          # upper bound, not "impossible"
        half = P.wilson_ci(10, 20)
        self.assertAlmostEqual(half["rate"], 0.5)
        self.assertAlmostEqual(half["ci95_low"] + half["ci95_high"], 1.0, places=10)
        self.assertIsNone(P.wilson_ci(0, 0)["rate"])

    def test_seed_vector_units_are_seeds_not_cells(self):
        m = np.full((24, 8), -0.5)
        out = P.seed_vector_bootstrap_ci(m, n_boot=200, seed=0)
        self.assertEqual(out["n_units"], 24)             # 192 cells collapse to 24 seeds
        self.assertAlmostEqual(out["mean"], -0.5)
        self.assertAlmostEqual(out["ci95_low"], -0.5, places=12)

    def test_crossed_bootstrap_is_at_least_as_wide_as_seed_vector(self):
        rng = np.random.default_rng(3)
        m = rng.normal(0.04, 0.2, size=(24, 8))
        crossed = P.crossed_bootstrap_ci(m, n_boot=2000, seed=1)
        seed_v = P.seed_vector_bootstrap_ci(m, n_boot=2000, seed=1)
        self.assertGreaterEqual(crossed["ci95_high"] - crossed["ci95_low"],
                                seed_v["ci95_high"] - seed_v["ci95_low"])
        self.assertEqual((crossed["n_seeds"], crossed["n_directions"]), (24, 8))

    def test_cluster_bootstrap_spans_clusters(self):
        out = P.cluster_bootstrap_ci({1: [1.0, 1.2, 0.9], 2: [-1.0, -0.8],
                                      3: [0.5]}, n_boot=500, seed=0)
        self.assertEqual(out["n_clusters"], 3)
        self.assertLess(out["ci95_low"], out["mean"])
        self.assertGreater(out["ci95_high"], out["mean"])

    def test_loo_range(self):
        out = P.loo_range([1.0, 2.0, 100.0])
        self.assertLess(out["loo_min"], out["loo_max"])


if __name__ == "__main__":
    unittest.main()
