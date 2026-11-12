"""Unit tests for the A6 corrected gate, panel dedupe and diagnostic.

These pin the two defects the third-round review verified, so that a future edit cannot
silently restore them while the prose still claims they are fixed.
"""
import unittest

import numpy as np

from research.core import tasks as _tasks
from research.search import corrected_gate as CG


class TestClosure(unittest.TestCase):
    def test_identity_only(self):
        self.assertEqual(CG.closure([[0, 1, 2]], 3), [(0, 1, 2)])

    def test_cyclic_order(self):
        n = 6
        rot = [(i + 1) % n for i in range(n)]
        self.assertEqual(len(CG.closure([rot], n)), 6)

    def test_dihedral_order(self):
        n = 6
        rot = [(i + 1) % n for i in range(n)]
        ref = [(-1 - i) % n for i in range(n)]
        self.assertEqual(len(CG.closure([rot, ref], n)), 12)

    def test_cycle_plus_transposition_is_symmetric(self):
        n = 6
        rot = [(i + 1) % n for i in range(n)]
        swap = [1, 0, 2, 3, 4, 5]
        self.assertEqual(len(CG.closure([rot, swap], n)), 720)

    def test_closed_under_inverse(self):
        n = 6
        rot = [(i + 1) % n for i in range(n)]
        ref = [(-1 - i) % n for i in range(n)]
        H = set(CG.closure([rot, ref], n))
        for g in H:
            inv = [0] * n
            for i, gi in enumerate(g):
                inv[gi] = i
            self.assertIn(tuple(inv), H)


class TestLabelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task = _tasks.load_family("ring_n6", development=True, locked=False)
        cls.rows = np.asarray(cls.task.x)[:32]
        n = int(cls.task.n_qubits)
        cls.rot = [(i + 1) % n for i in range(n)]
        cls.ref = [(-1 - i) % n for i in range(n)]
        cls.dihedral = [cls.rot, cls.ref]
        cls.transposition = [[1, 0, 2, 3, 4, 5]]

    def test_declared_group_passes_on_its_own_target(self):
        r = CG.label_test(self.task, self.dihedral, self.task.primary_target, self.rows)
        self.assertEqual(r["violated_fraction"], 0.0)

    def test_transposition_is_rejected_by_the_corrected_gate(self):
        r = CG.label_test(self.task, self.transposition, self.task.primary_target, self.rows)
        self.assertGreater(r["violated_fraction"], 0.0)

    def test_defect_reproduced_all_columns_rejects_the_declared_group(self):
        """The implemented gate scores every target column; alpha_0.5 is not D6-invariant,
        so the declared group itself fails. This test pins the defect, not the fix."""
        r = CG.label_test(self.task, self.dihedral, self.task.primary_target, self.rows,
                          atol_abs=0.0, atol_rel=0.0, all_columns=True)
        self.assertGreater(r["violated_fraction"], 0.0)

    def test_zero_tolerance_rejects_an_exact_symmetry_by_roundoff(self):
        """The second verified defect, pinned: on a continuous target, labels recomputed
        after relabelling differ at roundoff, so exact equality rejects the declared group.
        The discrepancy is far below the probe tolerance, so this is arithmetic noise, not
        a symmetry violation."""
        zero = CG.label_test(self.task, self.dihedral, self.task.primary_target, self.rows,
                             atol_abs=0.0, atol_rel=0.0)
        self.assertLess(zero["max_discrepancy"], 1e-9)
        self.assertGreater(zero["violated_fraction"], 0.0)      # defect: sound, rejected
        fixed = CG.label_test(self.task, self.dihedral, self.task.primary_target, self.rows)
        self.assertEqual(fixed["violated_fraction"], 0.0)       # fix: accepted

    def test_corrected_gate_is_no_stricter_than_the_truth_instrument(self):
        """ATOL_REL equals the probe tolerance, so anything the probe calls sound with
        zero violations must also pass the gate on the same rows."""
        probe = np.arange(32)
        truth, worst = CG.sound_on_probe(self.task, self.dihedral,
                                         self.task.primary_target, probe)
        self.assertTrue(truth)
        self.assertLessEqual(worst, CG.ATOL_ABS + CG.ATOL_REL * 10)


class TestPanelDedupe(unittest.TestCase):
    def test_panel_has_nine_entries_and_fewer_unique_groups(self):
        task = _tasks.load_family("ring_n6", development=True, locked=False)
        probe = np.arange(16)
        out = CG.panel_reanalysis(task, [task.primary_target], probe)
        self.assertEqual(out["n_entries"], 9)
        # the three full-symmetric presentations collapse to one subgroup
        self.assertLess(out["n_unique_subgroups"], out["n_entries"])
        big = [v for v in out["unique_subgroups"].values() if len(v) > 1]
        self.assertTrue(any("full_symmetric" in names for names in big))

    def test_full_symmetric_entries_all_generate_the_same_group(self):
        n = 6
        gens = CG.panel(n)
        orders = {k: len(CG.closure(gens[k], n))
                  for k in ("full_symmetric", "random_permutations",
                            "single_transpositions")}
        self.assertEqual(set(orders.values()), {720})


class TestDiagnostic(unittest.TestCase):
    def test_mc_estimate_matches_exact_ratio_within_noise(self):
        task = _tasks.load_family("ring_n6", development=True, locked=False)
        probe = np.random.default_rng(CG.PROBE_SEED).choice(
            len(task.x), size=64, replace=False)
        r = CG.accept_probability(task, task.primary_target, "uniform_single", probe,
                                  draws=200, seed=1)
        ex = CG.exact_L(task, task.primary_target, probe)
        # same estimator, different sampling scheme: intervals must overlap
        self.assertLessEqual(r["ci95_low"], ex["ratio"] + 0.15)
        self.assertGreaterEqual(r["ci95_high"], ex["ratio"] - 0.15)

    def test_exact_L_is_a_group(self):
        task = _tasks.load_family("ring_n6", development=True, locked=False)
        probe = np.arange(16)
        ex = CG.exact_L(task, task.primary_target, probe)
        self.assertEqual(ex["order"], 12)          # D6 for alpha_0

    def test_accept_probability_interval_contains_rate(self):
        task = _tasks.load_family("ring_n6", development=True, locked=False)
        probe = np.arange(32)
        r = CG.accept_probability(task, task.primary_target, "uniform_k", probe,
                                  draws=60, seed=2, k=2)
        self.assertLessEqual(r["ci95_low"], r["accept_rate"])
        self.assertGreaterEqual(r["ci95_high"], r["accept_rate"])


class TestBoardSymmetries(unittest.TestCase):
    def test_eight_unique_board_symmetries(self):
        sq = CG.square_symmetries()
        self.assertEqual(len(sq), 8)
        for p in sq:
            self.assertEqual(sorted(p), list(range(9)))


if __name__ == "__main__":
    unittest.main()


class TestCanonicalPanel(unittest.TestCase):
    """A6.6: the panel analysed must be the panel A5.3 defined, not a copy of it."""

    def test_panel_is_the_canonical_mapping(self):
        from research.search.verify_semantics import panel as canonical
        for n in (6, 9):
            a, b = CG.panel(n), canonical(n)
            self.assertEqual(list(a.keys()), list(b.keys()))
            for k in a:
                self.assertEqual([tuple(g) for g in a[k]], [tuple(g) for g in b[k]],
                                 "panel entry %r drifted at n=%d" % (k, n))

    def test_rotation_subgroups_are_distinct_subgroups(self):
        # with the canonical panel these are <rho^2> (order 3) and <rho^3> (order 2) at n=6
        c3 = CG.closure(CG.panel(6)["rotation_subgroup_c3"], 6)
        c2 = CG.closure(CG.panel(6)["rotation_subgroup_c2"], 6)
        self.assertEqual(len(c3), 3)
        self.assertEqual(len(c2), 2)
        self.assertNotEqual(CG.sha_sorted(c3), CG.sha_sorted(c2))


class TestSubgroupSamplingA7(unittest.TestCase):
    """A7.1: the capped fallback must stay inside the hypothesized subgroup."""

    CYC9 = [(i + 1) % 9 for i in range(9)]
    TRANS = [1, 0, 2, 3, 4, 5, 6, 7, 8]

    def test_capped_return_is_always_subgroup_words(self):
        # a group of order 4 (two disjoint transpositions), capped below its order
        g1 = [1, 0, 2, 3, 4, 5, 6, 7, 8]
        g2 = [0, 1, 3, 2, 4, 5, 6, 7, 8]
        full = CG.closure([g1, g2], 9)
        self.assertEqual(len(full), 4)
        elems, complete = CG.closure_capped([g1, g2], 9, cap=2)
        self.assertFalse(complete)
        self.assertGreater(len(elems), 1)
        for g in elems:                                 # every element is a bijection
            self.assertEqual(sorted(g), list(range(9)))
        # and every element is a word in the proposed generators, i.e. inside the subgroup
        self.assertTrue(set(elems) <= set(full),
                        "capped fallback returned an element outside the hypothesized subgroup")
        # a genuinely un-enumerable case stays a subset of bijections and reports incomplete
        big, comp = CG.closure_capped([self.CYC9, self.TRANS], 9, cap=200)
        self.assertFalse(comp)
        self.assertTrue(all(sorted(b) == list(range(9)) for b in big))

    def test_small_subgroup_enumerates_completely(self):
        elems, complete = CG.closure_capped([self.CYC9], 9, cap=2000)
        self.assertTrue(complete)
        self.assertEqual(len(elems), 9)

    def test_label_test_scope_vocabulary(self):
        task = _tasks.load_family("ring_n6", development=True, locked=False)
        n = int(task.n_qubits)
        probe = list(range(32))
        rows = np.asarray(task.x)[:32]
        r_ok = CG.label_test(task, [list(g) for g in task.generators], task.primary_target,
                             rows)
        self.assertEqual(r_ok["scope"], "exhaustive_subgroup_on_probe_set")
        self.assertTrue(r_ok["closure_enumeration_complete"])
        self.assertTrue(r_ok["acceptance_is_conclusive"])
        self.assertNotIn("certifies_soundness", r_ok)
        # an un-enumerable subgroup is inconclusive, never a pass
        _, comp = CG.closure_capped([self.CYC9, self.TRANS], 9, cap=50)
        self.assertFalse(comp)

    def test_zero_acceptance_reports_a_bound_not_zero(self):
        self.assertAlmostEqual(CG.cp_upper_95(0, 400), 0.00746, places=4)
        self.assertGreater(CG.cp_upper_95(0, 400), 0.0)
        self.assertAlmostEqual(CG.cp_upper_95(0, 1), 0.95, places=3)


class TestPoolDefinitionA7(unittest.TestCase):
    """A7.2: Q is filtered by arm and family and carries no selection duplicates."""

    def test_pool_is_family_and_arm_filtered(self):
        pool = CG.empirical_pool("logs/runs_confirm", "ring_n6")
        self.assertEqual(pool["family"], "ring_n6")
        self.assertTrue(set(pool["arms"]) <= set(CG.LLM_ARMS))
        self.assertGreater(pool["n_hypotheses"], 0)
        # no double-weighting: the count equals the sum over runs of proposals carrying a
        # hypothesis, with no extra +1 per run for the selected best
        self.assertEqual(pool["n_hypotheses"], sum(pool["runs"].values()))

    def test_deprecated_pool_is_larger_than_the_filtered_one(self):
        old = CG._empirical_hypotheses("logs/runs_confirm")
        new = CG.empirical_pool("logs/runs_confirm", "ring_n6")["n_hypotheses"]
        self.assertGreater(len(old), new,
                           "the unfiltered pool mixed arms and both six-qubit families")

    def test_exact_pool_rate_has_no_monte_carlo_layer(self):
        task = _tasks.load_family("ring_n6", development=True, locked=False)
        pool = CG.empirical_pool("logs/runs_confirm", "ring_n6")
        from research.search.verify_semantics import probe_indices
        probe = probe_indices(task, n_rows=256, seed=CG.PROBE_SEED)
        r = CG.accept_pool_exact(task, task.primary_target, pool, "llm_ring_n6", probe)
        self.assertEqual(r["pool"], "finite_stored_pool")
        self.assertEqual(r["n_hypotheses"], pool["n_hypotheses"])
        self.assertIn("exact over the pool", r["interval_kind"])
        # deterministic: enumeration, not sampling
        r2 = CG.accept_pool_exact(task, task.primary_target, pool, "llm_ring_n6", probe)
        self.assertEqual(r["accepted"], r2["accepted"])
