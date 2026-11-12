"""Deployed-endpoint evaluation on newly reserved inputs (Addendum A5.5).

`holdout_oneshot._search_run` computed `test_risk` from the refitted *candidate* and left
`test_risk_averaged_diagnostic = None`, so E-S7 says nothing about the pipeline the
`llm-verify-repair` arm deploys. This module measures both endpoints, per frozen run:

``test_risk_candidate``  the refitted selected candidate, as before.
``test_risk_deployed``   the predictor the pipeline would actually ship: the candidate
                         averaged over the group its **development-frozen** repair decision
                         selected (``best.repair.repaired`` and the candidate's hypothesis
                         generators). Runs whose frozen decision is "do not repair" have
                         deployed == candidate.
``test_risk_declared_twirl``
                         the same averaging tool applied to **every** arm with the task's
                         declared group: the non-LLM comparator on the same distribution.
                         Monte-Carlo twirling is recorded per run (``twirl_exact``).

Baselines are fitted on development **training** rows only and scored on the same
evaluation rows as the arms (the E-S7 caption's comparison against the edge-count rule's
*development* risk was not a matched comparison):

``edge_count_rule``  one threshold on edge count (graphs) / degree analogue,
``constructive_equivariant`` the hand-built exactly equivariant block at the search
                         protocol's per-fit budget (reported as per-fit, not total, budget),
``best_constant``    mean of training labels,
``oracle_reference`` the target-defining oracle: a **reference value**, not a learned
                     competitor, because it is the function the synthetic target is.

Data policy, stated before the run:
* ``ring_n6``  fresh inputs-only v5 (seed 20261205, orbit-disjoint from development and
  holdouts v1-v4): a genuinely untouched distribution.
* ``graphs_n6`` **no fresh class-disjoint data exists** (`generate_holdout_v5` found 0
  unseen isomorphism classes: development plus v1/v2 exhaust all 2**15 labeled graphs).
  The graphs deployed endpoint is therefore a *second, post hoc read* of the v1 sealed
  split, labelled as such everywhere, with digests recorded.

The development self-check runs **before** any sealed or v5 array is opened (the Addendum
A4 lesson): every run must reproduce its logged development risk exactly, or this module
aborts without reading anything.
"""
import argparse
import glob
import hashlib
from pathlib import Path
import itertools
import json
import multiprocessing as mp
import os
import time

import numpy as np

from research.core import paired as _P
from research.core import tasks as _tasks
from research.core import train as _train
from research.search import refit as _refit
from research.search import verifier_bridge as _vb

MC_TWIRL_ELEMENTS = 24
EVAL_ROWS_MAX = 1024      # paired subsample: every endpoint uses these rows
EVAL_ROW_SEED = 5150
_W = {"eval_x": {}, "eval_y": {}}
BANNER = ("*** ONE-SHOT HOLDOUT EVALUATION: sealed test arrays and the v5 fresh inputs "
          "are being read. This module is the only reader. ***")


def sha256(path):
    """Digest of a path given as str or pathlib.Path.

    Read the bytes explicitly: hashlib accepts no Path object, and
    hasattr(path, 'read_bytes') is True for pathlib.Path, so a hasattr-based
    shortcut silently hands hashlib a Path and raises TypeError.  That bug cost
    one aborted one-shot attempt (it fired before any sealed array was opened,
    so no held-out data was read).
    """
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ------------------------------------------------------------------ evaluation
def _set_eval_rows(fam, x, y, source):
    """Fix ONE paired subsample per family: every endpoint is scored on the same rows."""
    n = len(x)
    if n > EVAL_ROWS_MAX:
        rng = np.random.default_rng(EVAL_ROW_SEED)
        idx = np.sort(rng.choice(n, size=EVAL_ROWS_MAX, replace=False))
        x, y = x[idx], y[idx]
    _W["eval_x"][fam], _W["eval_y"][fam] = np.asarray(x), np.asarray(y, float)
    _W["row_accounting"][fam] = {"rows_total": int(n), "rows_used": int(len(x)),
                                 "seed": EVAL_ROW_SEED, "source": source}


def _average(fit, task, rows, elems):
    acc = None
    for perm in elems:
        v = np.asarray(_refit.predictions(fit, task, _vb.transform_rows(task, rows, perm)),
                       dtype=float).reshape(-1)
        acc = v if acc is None else acc + v
    return acc / len(elems)


def _twirl_set(closure, rng):
    if len(closure) <= MC_TWIRL_ELEMENTS:
        return list(closure), True
    idx = rng.choice(len(closure), size=MC_TWIRL_ELEMENTS, replace=False)
    return [closure[i] for i in idx], False


def evaluate_run(path):
    log = _refit.load_run(path)
    fam = log["family"]
    task = _W["tasks"][fam]
    ev_x, ev_y = _W["eval_x"][fam], _W["eval_y"][fam]
    fit, _, _, _, check = _refit.refit_best(log, task=task)
    # NOTE: evaluation rows (and their labels) are fixed once, subsampled and paired, by
    # _set_eval_rows(); evaluate_run must not re-derive them or the endpoints would be
    # scored on different row counts.
    key = log.get("target") or task.primary_target

    candidate_risk = float(np.mean((_refit.predictions(fit, task, ev_x) - ev_y) ** 2))
    rep = log["best"].get("repair") or {}
    hyp = (log["best"]["candidate"] or {}).get("hypothesis") or {}
    deployed_risk, dep_group, dep_exact = candidate_risk, None, None
    if rep.get("repaired") and hyp.get("generators"):
        from verify import closure as _closure
        H = _closure([list(g) for g in hyp["generators"]], int(task.n_qubits))
        elems, exact = _twirl_set(H, np.random.default_rng(4242 + int(log["seed"])))
        deployed_risk = float(np.mean((_average(fit, task, ev_x, elems) - ev_y) ** 2))
        dep_group, dep_exact = len(H), bool(exact)
    rng = np.random.default_rng(777 + int(log["seed"]))
    elems, exact = _twirl_set(_W["closures"][fam], rng)
    declared_risk = float(np.mean((_average(fit, task, ev_x, elems) - ev_y) ** 2))
    return {"path": path, "family": fam, "arm": log["arm"], "seed": int(log["seed"]),
            "target": key, "reproduction": check,
            "dev_risk": float(log["best"]["dev_risk"]),
            "test_risk_candidate": candidate_risk,
            "test_risk_deployed": deployed_risk,
            "deployed_repair_frozen": bool(rep.get("repaired")),
            "deployed_group_order": dep_group, "deployed_twirl_exact": dep_exact,
            "test_risk_declared_twirl": declared_risk,
            "declared_twirl_exact": bool(exact),
            "declared_group_order": len(_W["closures"][fam])}


def baselines(fam, steps, max_train, seeds):
    """Fitted on development TRAIN rows only, scored on the evaluation rows."""
    task = _W["tasks"][fam]
    train = np.asarray(task.splits["train"], bool)
    x, ev_x, ev_y = np.asarray(task.x), _W["eval_x"][fam], _W["eval_y"][fam]
    key = task.primary_target
    y = np.asarray(task.targets[key], float)
    ytr = y[train]
    out = {"family": fam, "target": key, "endpoint": "same rows as the arms"}
    out["best_constant"] = {"fitted_on": "train", "risk": float(np.mean(
        (ev_y - ytr.mean()) ** 2))}
    if fam.startswith("graphs"):
        e_tr, e_ev = x[train].sum(axis=1), np.asarray(ev_x, float).sum(axis=1)
        best = min(((float(np.mean((np.where(e_tr >= k, 1.0, -1.0) - ytr) ** 2)), k)
                    for k in range(16)))
        out["edge_count_rule"] = {"threshold": int(best[1]), "train_risk": best[0],
                                  "risk": float(np.mean(
                                      (np.where(e_ev >= best[1], 1.0, -1.0) - ev_y) ** 2))}
    n = int(task.n_qubits)
    block = [{"gate": "RY", "wire": i, "param": "a"} for i in range(n)]
    for i, j in itertools.combinations(range(n), 2):
        block.append({"gate": "CRZ", "wires": [i, j], "param": "b"})
        block.append({"gate": "CRZ", "wires": [j, i], "param": "b"})
    block += [{"gate": "RY", "wire": i, "param": "c"} for i in range(n)]
    cand = {"id": "constructive", "n_qubits": n, "block": block, "repeats": 1,
            "layers": 1, "param_names": ["a", "b", "c"], "hypothesis": None,
            "notes": "constructive equivariant baseline", "source": {"arm": "baseline"}}
    risks = []
    for s in seeds:
        fit = _train.fit(cand, task, x[train], ytr, int(s), steps=int(steps),
                         max_train=max_train)
        risks.append(float(np.mean((_refit.predictions(fit, task, ev_x) - ev_y) ** 2)))
    out["constructive_equivariant"] = {
        "risk_mean": float(np.mean(risks)), "risks": risks, "steps": int(steps),
        "max_train": max_train,
        "budget_note": "per-fit budget equals the search protocol's; total search budget "
                       "is not equal (the arms also spend proposals)"}
    out["oracle_reference"] = {
        "risk": float(np.mean((np.asarray(task.label_oracle(ev_x, target=key), float)
                               - ev_y) ** 2)),
        "status": "reference value, not a learned baseline: this is the function the "
                  "synthetic target is"}
    return out


def _init(tasks, closures):
    _W["tasks"], _W["closures"] = tasks, closures


def selfcheck(paths):
    """Refit every run on development rows; require exact reproduction, no sealed read."""
    ctx = mp.get_context("fork")
    with ctx.Pool(_W["workers"], initializer=_init,
                  initargs=(_W["tasks"], _W["closures"])) as pool:
        out = pool.map(_selfcheck_one, paths, chunksize=1)
    bad = [o for o in out if not o["exact"]]
    return {"n": len(out), "n_exact": len(out) - len(bad),
            "max_abs_dev_risk_diff": float(max(o["abs_diff"] for o in out)),
            "pass": not bad, "failures": bad[:5]}


def _selfcheck_one(path):
    log = _refit.load_run(path)
    task = _W["tasks"][log["family"]]
    _, _, _, _, check = _refit.refit_best(log, task=task)
    return {"path": path, "exact": check["exact"], "abs_diff": check["abs_diff"]}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="research/holdout_deployed.py")
    ap.add_argument("--runs", default="logs/runs_confirm")
    ap.add_argument("--out", default="research/HOLDOUT_DEPLOYED.json")
    ap.add_argument("--access-log", default="research/HOLDOUT_DEPLOYED_ACCESS.json")
    ap.add_argument("--ledger", default="research/HOLDOUT_ACCESS.json",
                    help="shared one-shot consumption ledger; splits recorded here are "
                         "refused unless listed in --allow-reread, with the reason logged")
    ap.add_argument("--allow-reread", nargs="*", default=[], metavar="SPLIT",
                    help="explicitly authorise a second read of an already-consumed split "
                         "(recorded, with --reread-reason, in the ledger)")
    ap.add_argument("--reread-reason", default="")
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--dry-run", action="store_true",
                    help="score development validation rows; open nothing sealed or fresh")
    ap.add_argument("--baseline-steps", type=int, default=120)
    a = ap.parse_args(argv)
    _W["workers"] = a.workers
    paths = sorted(glob.glob(os.path.join(a.runs, "run_*.json")))
    families = sorted({_refit.load_run(p)["family"] for p in paths})
    from verify import closure as _closure
    tasks, closures = {}, {}
    for fam in families:
        tasks[fam] = _tasks.load_family(fam, development=True, locked=False)
        closures[fam] = _closure([list(g) for g in tasks[fam].generators],
                                 int(tasks[fam].n_qubits))
    _W["tasks"], _W["closures"] = tasks, closures
    _W["dry_run"] = a.dry_run

    # ---- evaluation rows -------------------------------------------------------
    sources = {}
    _W["row_accounting"] = {}
    if a.dry_run:
        for fam in families:
            t = tasks[fam]
            dev = np.asarray(t.splits["validation"], bool)
            key = t.primary_target
            _set_eval_rows(fam, np.asarray(t.x)[dev],
                           np.asarray(t.targets[key], float)[dev],
                           "development validation (DRY RUN)")
            sources[fam] = "development validation (DRY RUN)"
    else:
        print(BANNER, flush=True)
        # ring_v1 is deliberately NOT opened: it is consumed and unused here, and a
        # digest read would still touch a spent split.
        sealed = {"graphs_v1": _tasks.dataset_path("graphs_n6", locked=True)}
        v5 = os.path.join(str(_tasks.DATASETS), "locked_holdout_v5", "ring_n6_x.npz")
        sealed["ring_v5"] = v5
        # --- one-shot policy enforcement (Addendum A4): refuse consumed splits -----
        ledger = {}
        if os.path.exists(a.ledger):
            with open(a.ledger) as fh:
                ledger = json.load(fh)
        consumed = set(ledger.get("files", {}))
        for rec in ledger.get("reads", []):
            consumed |= set(rec.get("files", []))
        blocked = sorted(k for k in sealed if k in consumed and k not in set(a.allow_reread))
        if blocked:
            print("REFUSING to read consumed split(s): %s\n"
                  "The one-shot policy allows one read per split. Re-run with "
                  "--allow-reread %s --reread-reason '...' only for a deliberate, "
                  "labelled post-hoc second read."
                  % (", ".join(blocked), " ".join(blocked)), flush=True)
            return 2
        if a.allow_reread:
            print("SECOND READ authorised for: %s\nreason: %s"
                  % (", ".join(a.allow_reread), a.reread_reason or "(none given)"),
                  flush=True)
        before = {k: sha256(v) for k, v in sealed.items()}
        with np.load(sealed["graphs_v1"]) as d:
            gx = np.asarray(d["x_test"])
        t = tasks["graphs_n6"]
        sources["graphs_n6"] = ("v1 sealed split, SECOND READ (post hoc): no fresh "
                                "class-disjoint graphs data exists (0 unseen isomorphism "
                                "classes)")
        _set_eval_rows("graphs_n6", gx,
                       np.asarray(t.label_oracle(gx, target=t.primary_target), float),
                       sources["graphs_n6"])
        with np.load(v5) as d:
            rx = np.asarray(d["x_test"])
        t = tasks["ring_n6"]
        sources["ring_n6"] = "v5 fresh inputs-only holdout (seed 20261205), first read"
        _set_eval_rows("ring_n6", rx,
                       np.asarray(t.label_oracle(rx, target="alpha_0"), float),
                       sources["ring_n6"])
        _W["sealed_before"] = before

    # ---- self-check BEFORE any outcome is computed on evaluation rows ----------
    gate = selfcheck(paths)
    print("self-check: %d/%d exact, max |dev diff| %.2e"
          % (gate["n_exact"], gate["n"], gate["max_abs_dev_risk_diff"]), flush=True)
    if not gate["pass"]:
        raise SystemExit("self-check failed; evaluation rows not scored")

    ctx = mp.get_context("fork")
    with ctx.Pool(a.workers, initializer=_init, initargs=(tasks, closures)) as pool:
        runs = pool.map(evaluate_run, paths, chunksize=1)
    base = {fam: baselines(fam, a.baseline_steps,
                           _refit.load_run(paths[0]).get("max_train"),
                           [20261110 + i for i in range(4)]) for fam in families}

    out = {"protocol": "REVISED_PROTOCOL Addendum A5.5", "dry_run": a.dry_run,
            "selfcheck": gate, "sources": sources, "row_accounting": _W["row_accounting"],
            "runs": runs, "baselines": base,
            "contrasts": contrasts(runs)}
    if not a.dry_run:
        after = {k: sha256(v) for k, v in sealed.items()}
        out["sealed_digests_before"] = before
        out["sealed_digests_after"] = after
        out["unchanged"] = all(before[k] == after[k] for k in before)
        access = {"event": "deployed-endpoint one-shot (A5.5)",
                  "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                  "files": list(sealed), "unchanged": out["unchanged"],
                  "digests": after}
        with open(a.access_log, "w") as fh:
            json.dump(access, fh, indent=1)
        # append to the shared ledger so no later module can re-read these silently
        ledger.setdefault("reads", []).append(dict(access,
                                                   authorised_reread=list(a.allow_reread),
                                                   reread_reason=a.reread_reason,
                                                   out=a.out))
        ledger.setdefault("read_files", {}).update(after)
        with open(a.ledger, "w") as fh:
            json.dump(ledger, fh, indent=1)
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    print(json.dumps({"sources": sources, "contrasts": out["contrasts"],
                      "baselines": {f: {k: (v["risk"] if isinstance(v, dict) and "risk" in v
                                            else v.get("risk_mean", v))
                                        for k, v in d.items() if k in
                                        ("best_constant", "edge_count_rule",
                                         "constructive_equivariant", "oracle_reference")}
                                    for f, d in base.items()}}, indent=1)[:3000])
    print("wrote", a.out)
    return 0


def contrasts(runs):
    """Paired run-level contrasts between endpoints, by family and arm."""
    out = []
    for fam in sorted({r["family"] for r in runs}):
        for arm in sorted({r["arm"] for r in runs if r["family"] == fam}):
            rs = [r for r in runs if r["family"] == fam and r["arm"] == arm]
            for name, ka, kb in (("deployed - candidate", "test_risk_deployed",
                                  "test_risk_candidate"),
                                 ("declared twirl - candidate", "test_risk_declared_twirl",
                                  "test_risk_candidate")):
                d = [r[ka] - r[kb] for r in rs]
                boot = _P.bootstrap_ci(d)
                out.append({"family": fam, "arm": arm, "contrast": name,
                            "n_runs": len(rs), "mean_diff": float(np.mean(d)),
                            "bootstrap": boot,
                            "verdict": _P.verdict(boot["ci95_low"], boot["ci95_high"])})
    return out


if __name__ == "__main__":
    raise SystemExit(main())
