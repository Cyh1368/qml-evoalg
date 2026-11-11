"""Offline tests for WP-SEARCH: no network, no real research/core required.

A stub package is injected into sys.modules so arm loops run end-to-end
before the parallel WP-CORE implementation lands. Real-core integration
tests are skipped until research.core.simulator exists.
"""
import contextlib
import importlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
import zlib

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.search import prompts  # noqa: E402
from research.search import harness  # noqa: E402

CORE_MODULES = ("research.core", "research.core.simulator",
                "research.core.candidates", "research.core.tasks",
                "research.core.train")


def _real_core_available():
    try:
        return importlib.util.find_spec("research.core.simulator") is not None
    except (ImportError, ValueError):
        return False


# --------------------------------------------------------------------- stub
def _fake_task():
    rng = np.random.default_rng(11)
    x = (rng.random((24, 15)) > 0.5).astype(float)
    train_mask = np.arange(24) < 16
    y = np.where(x.sum(axis=1) >= 7, 1.0, -1.0)
    task = types.SimpleNamespace()
    task.name = "graphs_n6"
    task.n_qubits = 6
    task.x = x
    task.orbit = np.arange(24)
    task.splits = {"train": train_mask, "validation": ~train_mask}
    task.targets = {"connected": y}
    task.generators = [[1, 0, 2, 3, 4, 5], [0, 1, 2, 4, 3, 5]]
    task.observables = [{(i,): 1.0} for i in range(6)]
    task.label_oracle = lambda X: np.where(np.asarray(X).sum(axis=1) >= 7, 1.0, -1.0)
    task.feature_map = lambda xv: []
    return task


def _fake_sample_random(rng, task, max_block=24):
    k = int(rng.integers(2, 6))
    block, names = [], ["t0", "t1"]
    for i in range(k):
        if rng.random() < 0.5:
            block.append({"gate": "RY", "wire": int(rng.integers(0, 6)),
                          "param": names[i % 2]})
        else:
            a, b = rng.choice(6, size=2, replace=False)
            block.append({"gate": "CZ", "wires": [int(a), int(b)]})
    hyp = None
    if rng.random() < 0.6:
        hyp = {"generators": [[1, 0, 2, 3, 4, 5]], "output_action": "invariant"}
    return {"id": "f%06d" % int(rng.integers(0, 10**6)), "n_qubits": 6,
            "block": block, "repeats": 2, "layers": 2, "param_names": names,
            "hypothesis": hyp, "notes": "stub proposal",
            "source": {"arm": "stub", "model": None, "parent": None}}


def _fake_validate(cand, task):
    errors = []
    if not isinstance(cand, dict):
        return ["not a dict"]
    for key in ("block", "param_names", "n_qubits"):
        if key not in cand:
            errors.append("missing %s" % key)
    for g in cand.get("block", []):
        wires = g.get("wires", [g.get("wire")] if "wire" in g else [])
        if any(not isinstance(w, int) or not 0 <= w < cand["n_qubits"]
               for w in wires):
            errors.append("bad wire")
    return errors


def _fake_expand(candidate, task, x=None):
    gates = [{"gate": "RZZ", "wires": [i, i + 1], "angle": np.pi / 2}
             for i in range(2)]
    gates += list(candidate["block"]) * int(candidate.get("repeats", 2))
    return gates, list(candidate["param_names"])


def _fake_unitary(gates, params, n):
    d = 2 ** n
    u = np.eye(d, dtype=complex)
    u[32, 32] = np.exp(0.3j)  # phase on |100000> (q0 MSB), moved by
    return u             # the swap -> channel residual > 1e-6


class _FakeFit:
    def __init__(self, dev):
        self.dev = dev
        self.params = np.zeros(2)

    def predict(self, task, x):
        return np.full(len(x), 0.5)


def _fake_fit(candidate, task, x, y, seed, **kw):
    key = json.dumps(candidate.get("block"), sort_keys=True).encode()
    dev = 0.1 + (zlib.crc32(key) % 1000) / 1000.0
    return _FakeFit(dev)


def _fake_risk(fit, task, x, y):
    return fit.dev


@contextlib.contextmanager
def fake_core():
    saved = {k: sys.modules.get(k) for k in CORE_MODULES}
    core = types.ModuleType("research.core")
    core.__path__ = []
    mods = {}
    for name in CORE_MODULES[1:]:
        m = types.ModuleType(name)
        mods[name.split(".")[-1]] = m
        setattr(core, name.split(".")[-1], m)
        sys.modules[name] = m
    mods["candidates"].sample_random = _fake_sample_random
    mods["candidates"].mutate = lambda c, rng, task: _fake_sample_random(rng, task)
    mods["candidates"].validate = _fake_validate
    mods["candidates"].expand_example = _fake_expand
    mods["candidates"].n_params = lambda c: len(c.get("param_names", []))
    mods["candidates"].count_gates = lambda c: len(c.get("block", []))
    mods["simulator"].unitary = _fake_unitary
    mods["tasks"].load_family = lambda name, development=True, locked=False: _fake_task()
    mods["train"].fit = _fake_fit
    mods["train"].risk = _fake_risk
    sys.modules["research.core"] = core
    try:
        yield core
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


class TestRedaction(unittest.TestCase):
    def test_task_descriptions_are_redacted(self):
        for family in ("graphs_n6", "ring_n6", "tictactoe_n9"):
            text = prompts.task_description(family).lower()
            for token in prompts.REDACTED_FORBIDDEN_TOKENS:
                self.assertNotIn(token.lower(), text,
                                 "%s leaks %r" % (family, token))
            self.assertEqual(prompts.audit_redaction(family), [])

    def test_full_prompt_runs_and_history_ok(self):
        history = [{"id": "c0001", "summary": "4 gates (CZ:4), 0 params",
                    "dev_risk": 0.5, "valid": True}]
        system, user = prompts.build_prompt("graphs_n6", history)
        self.assertIn("15", user)
        self.assertIn("c0001", user)
        _, user2 = prompts.build_prompt(
            "graphs_n6", history,
            {"status": "ok", "group_order": 720, "parameter_samples": 3,
             "mean_channel_residual": 1e-3, "max_channel_residual": 9e-3,
             "tolerance": 1e-10, "sampled_pass": False,
             "label_mean_abs_discrepancy": 0.0, "label_max_discrepancy": 0.0,
             "label_violated_fraction": 0.0})
        self.assertIn("VERIFIER REPORT", user2)
        self.assertNotIn("true group", user2.lower())


class TestJsonExtraction(unittest.TestCase):
    CAND = {"block": [{"gate": "RY", "wire": 0, "param": "t0"}],
            "param_names": ["t0"], "hypothesis": None, "notes": "n"}

    def test_plain(self):
        cand, note, errs = prompts.extract_candidate(json.dumps(self.CAND))
        self.assertIsNotNone(cand)
        self.assertEqual(cand["param_names"], ["t0"])

    def test_markdown_fence_and_trailing_text(self):
        text = ("Here is my proposal:\n```json\n%s\n```\n"
                "This block ties all wires together." % json.dumps(self.CAND))
        cand, note, errs = prompts.extract_candidate(text)
        self.assertIsNotNone(cand)

    def test_trailing_comma_and_prose(self):
        bad = json.dumps(self.CAND)[:-1] + ",}"
        cand, note, errs = prompts.extract_candidate(bad + " Hope this helps!")
        self.assertIsNotNone(cand)

    def test_invalid_gate_falls_back(self):
        bad = dict(self.CAND, block=[{"gate": "TELEPORT", "wire": 0}])
        cand, note, errs = prompts.extract_candidate(json.dumps(bad))
        self.assertIsNone(cand)
        self.assertTrue(errs)

    def test_garbage(self):
        cand, note, errs = prompts.extract_candidate("I cannot help with that.")
        self.assertIsNone(cand)
        self.assertTrue(errs)


class TestLockedGuard(unittest.TestCase):
    def test_locked_path_refused(self):
        for out in ("/tmp/locked_holdout", "/x/Locked_data", "datasets/LOCKED"):
            with self.assertRaises(harness.LockedError):
                harness.run_search("random", "graphs_n6", 0, 2, out)
        with self.assertRaises(harness.LockedError):
            harness.check_locked_path(family="graphs_n6_locked")

    def test_locked_forbidden_constant_present(self):
        self.assertEqual(harness.LOCKED_FORBIDDEN_IN, ("research/search",))


class TestArmsWithFakeCore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="wpsearch_test_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_budget_accounting_and_shared_population(self):
        with fake_core():
            log1 = harness.run_search("random", "graphs_n6", 7, 5,
                                      os.path.join(self.tmp, "a"),
                                      write_log=True)
            self.assertEqual(log1["evaluated_valid"], 5)
            self.assertGreaterEqual(log1["proposals_total"], 5)
            self.assertEqual(log1["invalid_total"],
                             log1["proposals_total"] - log1["evaluated_valid"])
            self.assertTrue(os.path.exists(log1["log_path"]))
            log2 = harness.run_search("mutation-ea", "graphs_n6", 7, 5,
                                      os.path.join(self.tmp, "b"),
                                      write_log=False)
            init1 = [json.dumps(p["candidate"]["block"], sort_keys=True)
                     for p in log1["proposals"][:4]]
            init2 = [json.dumps(p["candidate"]["block"], sort_keys=True)
                     for p in log2["proposals"][:4]]
            self.assertEqual(init1, init2)  # identical seed-derived start
            for key in ("arm", "family", "seed", "budget", "metadata",
                        "proposals", "best", "wall_time"):
                self.assertIn(key, log1)
            for key in ("python", "numpy", "host", "git_commit"):
                self.assertIn(key, log1["metadata"])

    def test_llm_mock_end_to_end(self):
        with fake_core():
            for arm in ("llm-fitness", "llm-verify", "llm-verify-repair"):
                log = harness.run_search(arm, "graphs_n6", 3, 6,
                                         os.path.join(self.tmp, arm),
                                         mock_llm=True, write_log=True)
                self.assertEqual(log["evaluated_valid"], 6, arm)
                self.assertGreaterEqual(log["tokens"]["calls"], 2, arm)
                llm_props = [p for p in log["proposals"]
                             if p["source"]["arm"] == arm]
                self.assertTrue(llm_props)
                if arm in ("llm-verify", "llm-verify-repair"):
                    self.assertTrue(any(p["verify"] is not None
                                        for p in llm_props), arm)
                if arm == "llm-verify-repair":
                    self.assertIn("repaired", log["best"]["repair"])
                self.assertTrue(os.path.exists(log["log_path"]))

    def test_invalid_proposals_counted_separately(self):
        with fake_core():
            import research.search.llmclient as llmclient
            n = {"i": 0}

            def flaky_client_fn(rng):
                n["i"] += 1
                if n["i"] % 2 == 0:  # every other proposal is garbage
                    return {"notes": "oops"}
                return _fake_sample_random(rng, _fake_task())

            client = llmclient.LLMClient(mock=True, seed=5,
                                         mock_candidate_fn=flaky_client_fn)
            log = harness.run_search("llm-fitness", "graphs_n6", 2, 8,
                                     os.path.join(self.tmp, "flaky"),
                                     mock_llm=True, client=client,
                                     write_log=False)
            self.assertEqual(log["evaluated_valid"], 8)
            self.assertGreaterEqual(log["invalid_total"], 3)
            self.assertEqual(log["proposals_total"],
                             log["evaluated_valid"] + log["invalid_total"])


class TestVerifierBridge(unittest.TestCase):
    def test_verify_and_label_preservation(self):
        with fake_core():
            from research.search import verifier_bridge
            task = _fake_task()
            cand = _fake_sample_random(np.random.default_rng(0), task)
            cand["hypothesis"] = {"generators": [[1, 0, 2, 3, 4, 5]],
                                  "output_action": "invariant"}
            samples = verifier_bridge.sample_param_dicts(cand,
                                                         np.random.default_rng(1))
            rep = verifier_bridge.verify_candidate(cand, task, samples,
                                                   group="hypothesis")
            self.assertEqual(rep["group_order"], 2)  # closure of one swap
            self.assertGreater(rep["mean_channel_residual"], 1e-6)
            # label oracle of the stub task is NOT invariant under swaps of
            # the edge vector -> violated fraction must be detectable, and an
            # identity hypothesis must be perfectly preserved.
            ident = verifier_bridge.label_preservation(
                task, {"generators": [[0, 1, 2, 3, 4, 5]]}, 8)
            self.assertEqual(ident["violated_fraction"], 0.0)
            self.assertEqual(ident["mean_abs_discrepancy"], 0.0)
            swap = verifier_bridge.label_preservation(
                task, cand["hypothesis"], 8)
            self.assertIn("max_discrepancy", swap)
            self.assertIn("violated_fraction", swap)


@unittest.skipUnless(_real_core_available(),
                     "research.core not implemented yet (parallel WP-CORE)")
class TestRealCoreIntegration(unittest.TestCase):
    def test_bridge_on_real_task(self):
        from research.core import tasks
        from research.search import verifier_bridge
        task = tasks.load_family("graphs_n6", development=True, locked=False)
        cand = {"id": "i0", "n_qubits": 6, "block": [], "repeats": 1,
                "layers": 1, "param_names": [],
                "hypothesis": {"generators": [task.generators[0]],
                               "output_action": "invariant"},
                "notes": "", "source": {}}
        rep = verifier_bridge.verify_candidate(cand, task, [{}],
                                               group="hypothesis")
        self.assertGreaterEqual(rep["group_order"], 2)
        lp = verifier_bridge.label_preservation(
            task, {"generators": [list(p) for p in task.generators]}, 16)
        self.assertEqual(lp["violated_fraction"], 0.0)  # true group preserves


if __name__ == "__main__":
    unittest.main(verbosity=2)
