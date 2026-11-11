"""Unit tests for research/core/candidates.py and research/core/tasks.py.

Run from the repository root::

    cd ~/qml-evoalg
    module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
    OPENBLAS_NUM_THREADS=1 python3 research/core/test_tasks_candidates.py

Also runs under pytest. Every draw is seeded, so failures are reproducible.
"""
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from research.core import candidates, tasks  # noqa: E402

FAMILIES = ("graphs_n6", "ring_n6", "tictactoe_n9")
DRAW_SEED = 20240517
N_DRAWS = 200


def _d4_closure():
    """All 8 D4 elements from the two generators: (p*q)[i] = p[q[i]]."""
    def compose(p, q):
        return tuple(p[q[i]] for i in range(9))
    identity = tuple(range(9))
    elements = {identity}
    frontier = [identity]
    while frontier:
        p = frontier.pop()
        for g in (tasks.TTT_ROTATION, tasks.TTT_REFLECTION):
            for h in (compose(p, g), compose(g, p)):
                if h not in elements:
                    elements.add(h)
                    frontier.append(h)
    return sorted(elements)


D4 = _d4_closure()


def _transform_rows(rows, perm):
    return np.asarray(rows)[:, list(perm)]


def _valid_candidate(task, **overrides):
    """A hand-written valid candidate for any family, for corruption tests."""
    n = task.n_qubits
    candidate = {"id": "t0001", "n_qubits": n,
                 "block": [{"gate": "RY", "wire": 0, "param": "t0"},
                           {"gate": "CNOT", "wires": [0, 1]},
                           {"gate": "CRZ", "wires": [1, 2], "param": "t1"},
                           {"gate": "RZ", "wire": 2, "param": "t2"},
                           {"gate": "CZ", "wires": [2, 3]},
                           {"gate": "RX", "wire": 3, "param": "t3"}],
                 "repeats": 2, "layers": 2,
                 "param_names": ["t0", "t1", "t2", "t3"],
                 "hypothesis": {"generators": [list(range(n))[1:] + [0]],
                                "output_action": "invariant"},
                 "notes": "hand-written fixture", "source": {}}
    candidate.update(overrides)
    return candidate


class TestGeneration(unittest.TestCase):
    def test_sample_random_always_valid(self):
        for family in FAMILIES:
            task = tasks.load_family(family)
            rng = np.random.default_rng(DRAW_SEED)
            sizes, params = set(), set()
            for _ in range(N_DRAWS):
                candidate = candidates.sample_random(rng, task)
                self.assertEqual(candidates.validate(candidate, task), [],
                                 "%s: invalid sample %r" % (family, candidate))
                sizes.add(candidates.count_gates(candidate))
                params.add(candidates.n_params(candidate))
            self.assertLessEqual(max(sizes), 24)
            self.assertTrue(all(4 <= p <= 8 for p in params))

    def test_mutate_always_valid(self):
        for family in FAMILIES:
            task = tasks.load_family(family)
            rng = np.random.default_rng(DRAW_SEED + 1)
            candidate = candidates.sample_random(rng, task)
            lineage = []
            for _ in range(N_DRAWS):
                candidate = candidates.mutate(candidate, rng, task)
                self.assertEqual(candidates.validate(candidate, task), [],
                                 "%s: invalid mutant %r" % (family, candidate))
                lineage.append(candidates.count_gates(candidate))
            self.assertLessEqual(max(lineage), candidates.MAX_BLOCK_GATES)

    def test_mutate_applies_structural_changes(self):
        task = tasks.load_family("graphs_n6")
        rng = np.random.default_rng(DRAW_SEED + 2)
        parent = candidates.sample_random(rng, task, max_block=8)
        changed = 0
        for _ in range(40):
            child = candidates.mutate(parent, rng, task)
            self.assertEqual(child["source"]["parent"], parent["id"])
            if child["block"] != parent["block"]:
                changed += 1
        self.assertGreater(changed, 30)

    def test_param_vector_dict_roundtrip(self):
        task = tasks.load_family("ring_n6")
        candidate = candidates.sample_random(np.random.default_rng(7), task)
        vec = np.linspace(-1.0, 1.0, candidates.n_params(candidate))
        pdict = candidates.param_dict(candidate, vec)
        self.assertEqual(sorted(pdict), sorted(candidate["param_names"]))
        np.testing.assert_allclose(candidates.param_vector(candidate, pdict), vec)
        with self.assertRaises(ValueError):
            candidates.param_dict(candidate, vec[:-1])


class TestExpansion(unittest.TestCase):
    def test_expand_example_gate_counts_graphs(self):
        task = tasks.load_family("graphs_n6")
        rng = np.random.default_rng(DRAW_SEED + 3)
        for row in task.x[[0, 1, 7, 12345, 19738]]:
            candidate = candidates.sample_random(rng, task, max_block=12)
            gates, names = candidates.expand_example(candidate, task, row)
            edges_with_one = int(np.count_nonzero(row))
            expected = int(candidate["layers"]) * (
                edges_with_one + int(candidate["repeats"]) * len(candidate["block"]))
            self.assertEqual(len(gates), expected)
            self.assertEqual(names, list(candidate["param_names"]))
            feature = [g for g in gates if "angle" in g]
            block = [g for g in gates if "angle" not in g]
            self.assertEqual(len(feature),
                             int(candidate["layers"]) * edges_with_one)
            self.assertTrue(all(g["gate"] == "RZZ" and g["angle"] == np.pi / 2
                                for g in feature))
            self.assertEqual(len(block),
                             int(candidate["layers"]) * int(candidate["repeats"])
                             * len(candidate["block"]))
            self.assertTrue(all("param" in g for g in block
                                if g["gate"] in candidates.PARAM_GATES))

    def test_expand_example_other_families(self):
        for family, width in (("ring_n6", 6), ("tictactoe_n9", 9)):
            task = tasks.load_family(family)
            candidate = candidates.sample_random(np.random.default_rng(5), task,
                                                 max_block=6)
            row = task.x[3]
            gates, _ = candidates.expand_example(candidate, task, row)
            self.assertEqual(len(gates), int(candidate["layers"]) * (
                width + int(candidate["repeats"]) * len(candidate["block"])))


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.task = tasks.load_family("graphs_n6")
        self.candidates = candidates

    def test_fixture_is_valid(self):
        fixture = _valid_candidate(self.task)
        self.assertEqual(candidates.validate(fixture, self.task), [])

    def test_rejects_bad_gate_name(self):
        bad = _valid_candidate(self.task)
        bad["block"][0]["gate"] = "MEASUREMENT"
        self.assertTrue(any("unknown gate" in e for e in
                            candidates.validate(bad, self.task)))

    def test_rejects_wire_out_of_range(self):
        bad = _valid_candidate(self.task)
        bad["block"][0]["wire"] = self.task.n_qubits
        self.assertTrue(any("outside" in e for e in
                            candidates.validate(bad, self.task)))
        bad = _valid_candidate(self.task)
        bad["block"][1]["wires"] = [1, 1]
        self.assertTrue(any("repeats wire" in e for e in
                            candidates.validate(bad, self.task)))

    def test_rejects_undeclared_and_unused_params(self):
        bad = _valid_candidate(self.task)
        bad["param_names"] = ["t0", "t1", "t2"]          # t3 used but undeclared
        self.assertTrue(any("not declared" in e for e in
                            candidates.validate(bad, self.task)))
        bad = _valid_candidate(self.task)
        bad["param_names"] = ["t0", "t1", "t2", "t3", "t9"]  # t9 never used
        self.assertTrue(any("no block gate" in e for e in
                            candidates.validate(bad, self.task)))
        bad = _valid_candidate(self.task)
        bad["block"][1]["param"] = "t0"                  # CNOT is a fixed gate
        self.assertTrue(any("fixed gate" in e for e in
                            candidates.validate(bad, self.task)))

    def test_rejects_bad_hypothesis(self):
        bad = _valid_candidate(self.task)
        bad["hypothesis"] = {"generators": [[1, 0, 2, 3, 4, 4]],
                             "output_action": "invariant"}
        self.assertTrue(any("not a permutation" in e for e in
                            candidates.validate(bad, self.task)))
        bad = _valid_candidate(self.task)
        bad["hypothesis"] = {"generators": [[1, 0, 2, 3]],
                             "output_action": "invariant"}
        self.assertTrue(any("length" in e for e in
                            candidates.validate(bad, self.task)))
        bad = _valid_candidate(self.task)
        bad["hypothesis"] = {"generators": [[1, 0, 2, 3, 4, 5]],
                             "output_action": "equivariant"}
        self.assertTrue(any("output_action" in e for e in
                            candidates.validate(bad, self.task)))
        bad = _valid_candidate(self.task)
        bad["hypothesis"] = {"generators": [], "output_action": "invariant"}
        self.assertTrue(any("non-empty" in e for e in
                            candidates.validate(bad, self.task)))
        self.assertEqual(candidates.validate(
            _valid_candidate(self.task, hypothesis=None), self.task), [])

    def test_rejects_bad_structure(self):
        bad = _valid_candidate(self.task)
        bad["layers"] = 0
        self.assertTrue(any("layers" in e for e in
                            candidates.validate(bad, self.task)))
        bad = _valid_candidate(self.task)
        bad["repeats"] = 0
        self.assertTrue(any("repeats" in e for e in
                            candidates.validate(bad, self.task)))
        bad = _valid_candidate(self.task)
        bad["block"] = bad["block"] * 12                  # 72 > cap of 64
        bad["param_names"] = ["t%d" % i for i in range(4)]
        self.assertTrue(any("cap" in e for e in
                            candidates.validate(bad, self.task)))
        bad = _valid_candidate(self.task, n_qubits=8)
        self.assertTrue(any("n_qubits" in e for e in
                            candidates.validate(bad, self.task)))
        self.assertEqual(candidates.validate("not a candidate", self.task),
                         ["candidate: not a JSON object (got str)"])


class TestLabelOracles(unittest.TestCase):
    def test_graphs_connected_matches_stored_labels(self):
        task = tasks.load_family("graphs_n6")
        with np.load(tasks.dataset_path("graphs_n6")) as data:
            x = data["x_train"][:200]
            y = data["y_connected_train"][:200]
        np.testing.assert_array_equal(task.label_oracle(x, target="connected"), y)
        np.testing.assert_array_equal(task.label_oracle(x)[:, 0], y)
        self.assertEqual(set(np.unique(y)), {-1, 1})

    def test_graphs_triangle_matches_stored_labels(self):
        task = tasks.load_family("graphs_n6")
        with np.load(tasks.dataset_path("graphs_n6")) as data:
            x = data["x_train"][:200]
            y = data["y_triangle_train"][:200]
        np.testing.assert_array_equal(task.label_oracle(x, target="triangle"), y)

    def test_ring_alpha_matches_stored_labels(self):
        task = tasks.load_family("ring_n6")
        with np.load(tasks.dataset_path("ring_n6")) as data:
            x = data["x_train"][:200]
            stored = {key[2:-len("_train")]: data[key][:200] for key in data.keys()
                      if key.startswith("y_") and key.endswith("_train")}
        np.testing.assert_allclose(task.label_oracle(x, target="alpha_0"),
                                   stored["alpha_0"], atol=1e-12, rtol=0)
        for key, y in stored.items():
            np.testing.assert_allclose(task.label_oracle(x, target=key), y,
                                       atol=1e-12, rtol=0)

    def test_tictactoe_targets_match_stored_labels(self):
        task = tasks.load_family("tictactoe_n9")
        mask = task.splits["train"]
        with np.load(tasks.dataset_path("tictactoe_n9")) as data:
            x = data["x_train"]
            for target in ("winner", "winner_designated",
                           "winner_designated_corner"):
                with self.subTest(target=target):
                    stored = data["y_%s_train" % target]
                    self.assertEqual(len(stored), int(mask.sum()))
                    np.testing.assert_array_equal(
                        task.label_oracle(x, target=target), stored)
        np.testing.assert_array_equal(task.label_oracle(x),
                                      np.stack([task.targets[k][mask] for k in
                                                task.target_keys], axis=1))

    def test_graphs_true_group_preserves_labels(self):
        """Sanity: the S6 generators really do preserve both graph labels."""
        task = tasks.load_family("graphs_n6")
        rows = task.x[task.splits["train"]][:200]
        y = task.label_oracle(rows)
        index = {pair: i for i, pair in enumerate(tasks.GRAPH_PAIRS)}
        for perm in task.generators:
            moved = np.stack([rows[:, index[tuple(sorted((perm[a], perm[b])))]]
                              for a, b in tasks.GRAPH_PAIRS], axis=1)
            np.testing.assert_array_equal(task.label_oracle(moved), y)

    def test_tictactoe_winner_invariant_corner_broken(self):
        task = tasks.load_family("tictactoe_n9")
        rows = task.x[task.splits["train"]]
        self.assertEqual(len(D4), 8)
        y_winner = task.label_oracle(rows, target="winner")
        y_corner = task.label_oracle(rows, target="winner_designated_corner")
        winner_violations = 0
        corner_violations = 0
        for perm in D4:
            moved = _transform_rows(rows, perm)
            winner_violations += np.sum(
                task.label_oracle(moved, target="winner") != y_winner)
            corner_violations += np.sum(
                task.label_oracle(moved, target="winner_designated_corner") != y_corner)
        total = len(rows) * len(D4)
        winner_fraction = winner_violations / total
        corner_fraction = corner_violations / total
        self.assertEqual(winner_fraction, 0.0)
        self.assertGreater(corner_fraction, 0.1)
        # the D4-fixed centre-cell rule is a sham control: also invariant
        centre = task.label_oracle(rows, target="winner_designated")
        centre_violations = sum(
            int(np.sum(task.label_oracle(_transform_rows(rows, perm),
                                         target="winner_designated") != centre))
            for perm in D4)
        self.assertEqual(centre_violations / total, 0.0)


class TestTaskSpec(unittest.TestCase):
    def test_frozen_fields_and_shapes(self):
        expected = {"graphs_n6": (6, "S6", 21, 5, "connected"),
                    "ring_n6": (6, "D6", 21, 2, "alpha_0"),
                    "tictactoe_n9": (9, "D4", 45, 2, "winner")}
        for family, (n, group, n_obs, n_gen, primary) in expected.items():
            task = tasks.load_family(family)
            self.assertEqual(task.n_qubits, n)
            self.assertEqual(task.group_name, group)
            self.assertEqual(len(task.observables), n_obs)
            self.assertEqual(len(task.generators), n_gen)
            self.assertEqual(task.primary_target, primary)
            self.assertEqual(task.x.shape[0], task.orbit.shape[0])
            self.assertEqual(set(task.splits), {"train", "validation"})
            self.assertEqual(
                int(task.splits["train"].sum()) + int(task.splits["validation"].sum()),
                len(task.x))
            self.assertFalse(np.any(task.splits["train"] & task.splits["validation"]))
            for values in task.targets.values():
                self.assertEqual(len(values), len(task.x))
            self.assertEqual(task.observables[0], {(0,): 1.0})
            self.assertEqual(task.observables[-1], {(n - 2, n - 1): 1.0})

    def test_locked_load_warns_and_exposes_test_split_only(self):
        import io
        import contextlib
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            task = tasks.load_family("graphs_n6", locked=True)
        self.assertIn("LOCKED HOLDOUT", stdout.getvalue())
        self.assertIn("LOCKED HOLDOUT", stderr.getvalue())
        self.assertEqual(set(task.splits), {"test"})
        self.assertTrue(task.splits["test"].all())


if __name__ == "__main__":
    unittest.main(verbosity=2)
