"""WP-SEARCH harness: five matched-budget arms over the frozen core interfaces.

Arms: random, mutation-ea, llm-fitness, llm-verify, llm-verify-repair.
Identical seed-derived initial population of 4 random valid candidates across
all arms; budget B counts VALID evaluated candidates, invalid proposals are
counted separately in proposals_total. Every run writes a full JSON log.

HARD LOCKED GUARD: this module refuses to run if any path-like argument
contains 'locked' (LOCKED_FORBIDDEN_IN is the grep-able constant required by
INTERFACES.md). Search receives development artifacts only.
"""
import argparse
import datetime
import importlib
import importlib.util
import json
import os
import platform
import socket
import subprocess
import sys
import time

import numpy as np

ARMS = ("random", "mutation-ea", "llm-fitness", "llm-verify", "llm-verify-repair")
LLM_ARMS = ("llm-fitness", "llm-verify", "llm-verify-repair")
LOCKED_FORBIDDEN_IN = ("research/search",)
INITIAL_POPULATION = 4
EA_POPULATION = 8
EA_TOURNAMENT = 2
LABEL_ROWS = 64
VERIFY_PARAM_SAMPLES = 3
REPAIR_RESIDUAL_FLOOR = 1e-6
DEFAULT_MAX_PROPOSALS_FACTOR = 10


class LockedError(ValueError):
    """A path argument referenced sealed locked-holdout data."""


def check_locked_path(**values):
    """Refuse any argument whose text contains 'locked' (case-insensitive)."""
    for key, val in values.items():
        items = val if isinstance(val, (list, tuple)) else [val]
        for item in items:
            if item is not None and "locked" in str(item).lower():
                raise LockedError(
                    "LOCKED GUARD: argument %r references a locked path (%r); "
                    "research/search may only receive development artifacts. "
                    "LOCKED_FORBIDDEN_IN=%s" % (key, item, LOCKED_FORBIDDEN_IN))


def _core():
    """Lazy core imports so this module loads before research/core lands."""
    from research.core import candidates, tasks, train
    return candidates, tasks, train


def _metadata():
    meta = {"python": platform.python_version(), "numpy": np.__version__,
            "host": socket.gethostname(), "platform": platform.platform()}
    try:
        import scipy
        meta["scipy"] = scipy.__version__
    except Exception:
        meta["scipy"] = None
    try:
        root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        meta["git_commit"] = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
            text=True, timeout=10).stdout.strip() or "unknown"
    except Exception:
        meta["git_commit"] = "unknown"
    return meta


def _structural_summary(candidate):
    from research.search import prompts
    return prompts.structural_summary(candidate)


def run_search(arm, family, seed, budget, out_dir, model="ycrc-local",
               reasoning_effort="none", mock_llm=False, task=None,
               target=None, label_rows=LABEL_ROWS,
               max_proposals=None, llm_timeout=None, client=None,
               write_log=True, steps=200, max_train=None):
    """Execute one search run; returns the run-log dict (also written to JSON)."""
    check_locked_path(family=family, out_dir=out_dir, model=model,
                      target=target, reasoning_effort=reasoning_effort)
    if arm not in ARMS:
        raise ValueError("unknown arm %r, expected one of %s" % (arm, ARMS))
    if budget < 1:
        raise ValueError("budget must be >= 1")
    candidates, tasks, train = _core()
    from research.search import prompts, verifier_bridge
    from research.search.llmclient import LLMClient, DEFAULT_TIMEOUT

    started = time.time()
    if task is None:
        task = tasks.load_family(family, development=True, locked=False)
    family_name = str(getattr(task, "name", family))
    splits = getattr(task, "splits", None) or {}
    train_mask = np.asarray(splits.get("train", np.ones(len(task.x), bool)),
                            dtype=bool)
    val_mask = np.asarray(splits.get("validation", ~train_mask), dtype=bool)
    x_tr, x_val = np.asarray(task.x)[train_mask], np.asarray(task.x)[val_mask]
    target_key = target or next(iter(task.targets))
    y_tr = np.asarray(task.targets[target_key])[train_mask]
    y_val = np.asarray(task.targets[target_key])[val_mask]

    # Independent, seed-derived streams: initial population identical across
    # arms for a given seed; arm/LLM/verifier randomness kept separate.
    seq = np.random.SeedSequence(int(seed))
    spawned = seq.spawn(INITIAL_POPULATION + 3)
    init_seqs = spawned[:INITIAL_POPULATION]
    arm_seq, llm_seq, verify_seq = spawned[INITIAL_POPULATION:]
    arm_rng = np.random.default_rng(arm_seq)
    verify_rng = np.random.default_rng(verify_seq)

    proposals = []          # every proposal record, valid or not
    evaluated = []          # dicts: candidate, fit, dev_risk
    counters = {"proposals_total": 0, "evaluated_valid": 0, "invalid_total": 0}
    cap = max_proposals or DEFAULT_MAX_PROPOSALS_FACTOR * int(budget) + 50
    stop_reason = "budget_exhausted"

    def evaluate(raw, source, note=""):
        """Validate + (if valid) train one proposal; returns candidate or None."""
        counters["proposals_total"] += 1
        idx = counters["proposals_total"]
        cand = raw if isinstance(raw, dict) else None
        if cand is not None:
            cand = dict(cand)
            cand.setdefault("n_qubits", int(task.n_qubits))
            cand.setdefault("repeats", prompts.DEFAULT_REPEATS)
            cand.setdefault("layers", prompts.DEFAULT_LAYERS)
            cand.setdefault("param_names", [])
            cand.setdefault("hypothesis", None)
            cand["id"] = "c%04d" % idx
            cand["source"] = dict(source)
        errors = candidates.validate(cand, task) if cand is not None else ["unparseable proposal"]
        record = {"id": "c%04d" % idx, "arm": arm, "source": dict(source),
                  "valid": not errors, "validation_errors": errors,
                  "note": note, "summary": None, "dev_risk": None,
                  "n_params": None, "n_gates": None, "candidate": cand,
                  "verify": None, "wall_time_fit": None}
        proposals.append(record)
        if errors:
            counters["invalid_total"] += 1
            return None
        t0 = time.time()
        fit = train.fit(cand, task, x_tr, y_tr, int(seed), steps=steps,
                        max_train=max_train)
        dev = float(train.risk(fit, task, x_val, y_val))
        record["dev_risk"] = dev
        record["wall_time_fit"] = time.time() - t0
        record["summary"] = _structural_summary(cand)
        record["n_params"] = candidates.n_params(cand)
        record["n_gates"] = candidates.count_gates(cand)
        counters["evaluated_valid"] += 1
        evaluated.append({"candidate": cand, "fit": fit, "dev_risk": dev,
                          "record": record})
        return cand

    def verify_report_for(cand):
        """Verifier feedback on the model's OWN hypothesis (never the true group)."""
        hyp = cand.get("hypothesis") if cand else None
        if not hyp or not hyp.get("generators"):
            return {"status": "no_hypothesis"}
        try:
            vr = verifier_bridge.verify_candidate(
                cand, task,
                verifier_bridge.sample_param_dicts(cand, verify_rng,
                                                   VERIFY_PARAM_SAMPLES),
                group="hypothesis")
            lp = verifier_bridge.label_preservation(task, hyp, label_rows)
            report = {"status": "ok", **{k: vr[k] for k in
                      ("group_order", "parameter_samples", "mean_channel_residual",
                       "max_channel_residual", "tolerance", "sampled_pass")},
                      "label_mean_abs_discrepancy": lp["mean_abs_discrepancy"],
                      "label_max_discrepancy": lp["max_discrepancy"],
                      "label_violated_fraction": lp["violated_fraction"]}
            return report
        except Exception as exc:  # malformed hypothesis etc.: report, don't crash
            return {"status": "error", "error": repr(exc)}

    # ---- identical initial population (all arms) ----
    for sq in init_seqs[:INITIAL_POPULATION]:
        evaluate(candidates.sample_random(np.random.default_rng(sq), task),
                 {"arm": "init", "model": None, "parent": None})

    if arm == "random":
        while counters["evaluated_valid"] < budget and \
                counters["proposals_total"] < cap:
            evaluate(candidates.sample_random(arm_rng, task),
                     {"arm": arm, "model": None, "parent": None})

    elif arm == "mutation-ea":
        while counters["evaluated_valid"] < budget and \
                counters["proposals_total"] < cap:
            if len(evaluated) < EA_POPULATION:
                child = candidates.sample_random(arm_rng, task)
                parent_id = None
            else:
                pool = sorted(arm_rng.choice(len(evaluated),
                                             size=min(EA_TOURNAMENT,
                                                      len(evaluated)),
                                             replace=False),
                              key=lambda i: evaluated[i]["dev_risk"])
                parent = evaluated[int(pool[0])]
                parent_id = parent["candidate"]["id"]
                child = candidates.mutate(parent["candidate"], arm_rng, task)
            got = evaluate(child, {"arm": arm, "model": None, "parent": parent_id})
            if got is not None:
                evaluated.sort(key=lambda e: e["dev_risk"])
                if len(evaluated) > EA_POPULATION:
                    evaluated.pop()  # drop worst dev risk

    elif arm in LLM_ARMS:
        if client is None:
            client = LLMClient(
                model="mock" if mock_llm else model,
                reasoning_effort=reasoning_effort, mock=mock_llm,
                seed=int(seed), timeout=llm_timeout or DEFAULT_TIMEOUT,
                mock_candidate_fn=lambda rng: candidates.sample_random(rng, task))
        history = [{"id": e["record"]["id"], "summary": e["record"]["summary"],
                    "dev_risk": e["dev_risk"], "valid": True}
                   for e in evaluated]
        report = None
        while counters["evaluated_valid"] < budget and \
                counters["proposals_total"] < cap:
            system, user = prompts.build_prompt(task, history, report)
            resp = client.chat([{"role": "system", "content": system},
                                {"role": "user", "content": user}])
            raw, note, errors = prompts.extract_candidate(resp["content"])
            got = evaluate(raw, {"arm": arm, "model": client.model,
                                 "parent": None}, note=note)
            proposals[-1]["tokens"] = {"prompt": resp["prompt_tokens"],
                                       "completion": resp["completion_tokens"],
                                       "attempts": resp["attempts"]}
            history.append({"id": proposals[-1]["id"],
                            "summary": proposals[-1]["summary"]
                            or "invalid proposal",
                            "dev_risk": proposals[-1]["dev_risk"],
                            "valid": got is not None})
            if arm in ("llm-verify", "llm-verify-repair") and got is not None:
                report = verify_report_for(got)
                proposals[-1]["verify"] = report
        stop_reason = ("budget_exhausted" if counters["evaluated_valid"] >= budget
                       else "proposal_cap_reached")

    if counters["evaluated_valid"] < budget and stop_reason == "budget_exhausted":
        stop_reason = "proposal_cap_reached"
    if not evaluated:
        raise RuntimeError("no valid candidate was ever evaluated; check core "
                           "validate/sample_random")

    # ---- dev-selected best (+ optional Reynolds repair) ----
    best = min(evaluated, key=lambda e: e["dev_risk"])
    best_cand, best_fit = best["candidate"], best["fit"]
    repair = {"attempted": False, "repaired": False}
    if arm == "llm-verify-repair":
        hyp = best_cand.get("hypothesis")
        if hyp and hyp.get("generators"):
            repair["attempted"] = True
            vr = best["record"]["verify"] or verify_report_for(best_cand)
            best["record"]["verify"] = vr
            if vr.get("status") == "ok":
                lp = {"violated_fraction": vr["label_violated_fraction"]}
                if lp["violated_fraction"] == 0.0 and \
                        vr["mean_channel_residual"] > REPAIR_RESIDUAL_FLOOR:
                    avg, order = verifier_bridge.reynolds_average_predictions(
                        lambda rows: best_fit.predict(task, rows), task, x_val,
                        hyp["generators"])
                    repair.update({
                        "repaired": True, "group_order": order,
                        "mean_channel_residual": vr["mean_channel_residual"],
                        "label_violated_fraction": 0.0,
                        "dev_risk_repaired_diagnostic":
                            float(np.mean((avg - y_val) ** 2))})
    # Per protocol the repaired predictor's official dev risk is the
    # candidate's dev risk; the averaged value is logged as a diagnostic only.
    best_risk = best["dev_risk"]

    run_log = {
        "arm": arm, "family": family_name, "model": client.model
        if arm in LLM_ARMS else None, "reasoning_effort":
        reasoning_effort if arm in LLM_ARMS else None,
        "mock_llm": bool(mock_llm), "seed": int(seed), "budget": int(budget),
        "steps": int(steps), "max_train": max_train,
        "target": target_key, "proposals_total": counters["proposals_total"],
        "evaluated_valid": counters["evaluated_valid"],
        "invalid_total": counters["invalid_total"], "stop_reason": stop_reason,
        "ea_population": EA_POPULATION if arm == "mutation-ea" else None,
        "llm_calls": client.calls if arm in LLM_ARMS else [],
        "tokens": client.tokens_total if arm in LLM_ARMS else
        {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
         "calls": 0},
        "wall_time": time.time() - started,
        "proposals": proposals,
        "best": {"id": best_cand["id"], "dev_risk": best_risk,
                 "repair": repair, "candidate": best_cand},
        "metadata": _metadata(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    if write_log:
        os.makedirs(out_dir, exist_ok=True)
        effort = run_log.get("reasoning_effort") or "none"
        tag = "%s_%s_%s-%s_seed%d" % (arm, family_name,
                                      run_log["model"] or "none", effort,
                                      int(seed))
        path = os.path.join(out_dir, "run_%s.json" % tag)
        with open(path, "w") as fh:
            json.dump(run_log, fh, indent=1, default=str)
        run_log["log_path"] = path
    return run_log


def main(argv=None):
    parser = argparse.ArgumentParser(prog="research/search/harness.py")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="run one search arm")
    run.add_argument("--arm", required=True, choices=ARMS)
    run.add_argument("--family", required=True)
    run.add_argument("--model", default="ycrc-local")
    run.add_argument("--reasoning-effort", default="none",
                     choices=("none", "medium"))
    run.add_argument("--seed", type=int, required=True)
    run.add_argument("--budget", type=int, required=True)
    run.add_argument("--out", required=True, help="per-run log directory")
    run.add_argument("--target", default=None)
    run.add_argument("--mock-llm", action="store_true",
                     help="deterministic offline LLM (tests only)")
    run.add_argument("--max-proposals", type=int, default=None)
    run.add_argument("--steps", type=int, default=200,
                     help="Adam steps per candidate (protocol default 200)")
    run.add_argument("--max-train", type=int, default=None,
                     help="cap the training pool (uniform compute control)")
    args = parser.parse_args(argv)
    check_locked_path(out=args.out, family=args.family, model=args.model)
    log = run_search(arm=args.arm, family=args.family, seed=args.seed,
                     budget=args.budget, out_dir=args.out, model=args.model,
                     reasoning_effort=args.reasoning_effort,
                     mock_llm=args.mock_llm, target=args.target,
                     max_proposals=args.max_proposals,
                     steps=args.steps, max_train=args.max_train)
    print(json.dumps({"log": log.get("log_path"),
                      "evaluated_valid": log["evaluated_valid"],
                      "proposals_total": log["proposals_total"],
                      "invalid_total": log["invalid_total"],
                      "best_dev_risk": log["best"]["dev_risk"],
                      "repaired": log["best"]["repair"].get("repaired", False),
                      "tokens": log["tokens"]["total_tokens"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
