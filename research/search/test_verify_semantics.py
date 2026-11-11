"""Unit tests for the A5.2/A5.3 verifier-semantics module.

These check the *instrument*, not the finding: the vectorised group action must agree
with the harness's own row transform, the taxonomy must separate sound-but-incomplete
hypotheses from genuine false accepts, and the probe must not overlap the rows the
implemented gate reads.
"""
import unittest

import numpy as np

from research.core import tasks as _tasks
from research.search import verifier_bridge as _vb
from research.search import verify_semantics as V


class ActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ring = _tasks.load_family("ring_n6", development=True, locked=False)
        cls.graphs = _tasks.load_family("graphs_n6", development=True, locked=False)

    def test_vectorised_action_matches_harness(self):
        for task in (self.ring, self.graphs):
            rows = np.asarray(task.x)[:24]
            for perm in V.all_permutations(int(task.n_qubits))[:6]:
                got = V.action_columns(task, rows, perm)
                want = _vb.transform_rows(task, rows, perm)
                np.testing.assert_allclose(got, want,
                                           err_msg="action mismatch for %s" % task.name)

    def test_identity_is_the_only_fixed_point_of_a_random_perm_check(self):
        # sanity: a non-identity permutation really does move some ring input
        rows = np.asarray(self.ring.x)[:64]
        moved = 0
        for perm in V.all_permutations(6):
            if perm == tuple(range(6)):
                continue
            if not np.allclose(V.action_columns(self.ring, rows, perm), rows):
                moved += 1
        self.assertEqual(moved, 719)


class TaxonomyTests(unittest.TestCase):
    def test_statuses_separate_sound_incomplete_from_false_accept(self):
        # n = 4: declared G = C3 on sites {0,1,2}; the target's label-symmetry group L is
        # every permutation that fixes site 3 (order 6).  A hypothesis moving site 3 is a
        # genuine false accept; a smaller group inside G is merely incomplete.
        n = 4
        G = set(V.closure_of([(1, 2, 0, 3)], n))
        L = {p for p in V.all_permutations(n) if p[3] == 3}
        self.assertEqual(len(G), 3)
        self.assertEqual(len(L), 6)
        self.assertEqual(V.classify(G, G, L), "exact_declared")
        self.assertEqual(V.classify({(0, 1, 2, 3)}, G, L), "valid_proper_subgroup")
        self.assertEqual(V.classify(L, G, L), "valid_supergroup")
        self.assertEqual(V.classify(set(V.closure_of([(3, 1, 2, 0)], n)), G, L),
                         "invalid")

    def test_full_symmetric_target_makes_every_hypothesis_sound(self):
        # When a target's label-symmetry group is the whole symmetric group, no
        # permutation hypothesis can be a false accept: the gate is vacuous there.
        n = 3
        L = set(V.all_permutations(n))                   # vacuous gate
        G = {(0, 1, 2), (1, 2, 0), (2, 0, 1)}
        for perm in L:
            H = set(V.closure_of([perm], n))
            self.assertNotEqual(V.classify(H, G, L), "invalid")

    def test_sound_hypothesis_not_comparable_with_declared_group_is_not_invalid(self):
        # G = C3 inside S3; H = a transposition group.  H is a genuine label symmetry of a
        # target whose L is all of S3, so it must never be reported as a false accept.
        n = 3
        L = set(V.all_permutations(n))
        G = {(0, 1, 2), (1, 2, 0), (2, 0, 1)}
        H = set(V.closure_of([(1, 0, 2)], n))
        self.assertEqual(V.classify(H, G, L), "sound_noncomparable")


class ProbeTests(unittest.TestCase):
    def test_probe_excludes_the_rows_the_gate_reads(self):
        task = _tasks.load_family("ring_n6", development=True, locked=False)
        train = np.flatnonzero(np.asarray(task.splits["train"], bool))
        gate_rows = set(train[:V.GATE_ROWS].tolist())
        probe = set(V.probe_indices(task).tolist())
        self.assertEqual(gate_rows & probe, set())
        self.assertGreater(len(probe), 100)

    def test_label_symmetry_groups_are_groups_and_contain_the_declared_one(self):
        task = _tasks.load_family("ring_n6", development=True, locked=False)
        probe = V.probe_indices(task)
        res = V.label_symmetry_group(task, "alpha_0", probe)
        G = set(V.closure_of(task.generators, 6))
        self.assertTrue(G <= res["group"])               # declared group really is a symmetry
        self.assertGreaterEqual(res["order"], len(G))
        # closure under composition and inverse
        for a in list(res["group"])[:40]:
            for b in list(res["group"])[:40]:
                self.assertIn(tuple(a[b[i]] for i in range(6)), res["group"])
            self.assertIn(tuple(np.argsort(np.array(a)).tolist()), res["group"])

    def test_graphs_connected_target_is_invariant_under_the_whole_symmetric_group(self):
        # This is why the graphs label gate cannot discriminate: connectedness is a
        # property of the isomorphism class, so every vertex relabelling preserves it.
        task = _tasks.load_family("graphs_n6", development=True, locked=False)
        probe = V.probe_indices(task)
        res = V.label_symmetry_group(task, "connected", probe)
        self.assertEqual(res["order"], 720)


class PanelTests(unittest.TestCase):
    def test_panel_members_have_the_expected_closure_orders(self):
        p = V.panel(6)
        self.assertEqual(len(V.closure_of(p["identity"], 6)), 1)
        self.assertEqual(len(V.closure_of(p["cyclic_rotation"], 6)), 6)
        self.assertEqual(len(V.closure_of(p["rotation_subgroup_c3"], 6)), 3)
        self.assertEqual(len(V.closure_of(p["rotation_subgroup_c2"], 6)), 2)
        self.assertEqual(len(V.closure_of(p["dihedral_declared"], 6)), 12)
        self.assertEqual(len(V.closure_of(p["full_symmetric"], 6)), 720)
        self.assertEqual(len(p["random_permutations"]), V.N_RANDOM)
        self.assertEqual(len(p["single_transpositions"]), V.N_TRANSPOSITIONS)


if __name__ == "__main__":
    unittest.main()
