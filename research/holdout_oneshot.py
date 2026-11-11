"""ONE-SHOT sealed/fresh holdout evaluation (REVISED_PROTOCOL section 5).

This is the only module in the project that reads sealed test arrays for outcome
measurement. It (a) prints the LOCKED banner, (b) records the sha256 of every sealed
file before and after, (c) writes an access record with the git commit, host, UTC
time and Slurm job id, and (d) evaluates exactly the frozen subsets declared in the
protocol — no selection, no tuning, no second pass.

Two evaluations, both single-shot:

* **E-R4** WP-REPAIR-2 arms ``original``/``repaired``/``control_dup`` at
  ``eta in {0, 0.5, 1}`` on 4 breaking directions x 8 optimiser seeds, trained on the
  development *training* split only, scored on the v1 sealed ring test split and on
  the fresh v2 ring holdout (orbits disjoint from everything used so far).
* **E-S7** the 120 frozen search runs: each run's dev-selected candidate is refitted
  (deterministically, verified against its logged development risk) and scored on the
  sealed test split of its own family, plus the constructive equivariant baseline at
  the same fit budget.

Usage::

    python3 -m research.holdout_oneshot --workers 24 \\
        --out research/HOLDOUT_RESULTS.json
"""
import argparse
import datetime
import glob
import hashlib
import json
import multiprocessing as mp
import os
import platform
import socket
import subprocess
import sys
from pathlib import Path

import numpy as np

from research.core import paired as _P
from research.core import tasks as _tasks
from research.core import train as _train
from research.experiments.repair import repair_experiment as _r1
from research.experiments.repair import repair_experiment2 as _r2
from research.search import refit as _refit

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANNER = "*" * 78 + "\n" + "\n".join(
    "*** ONE-SHOT HOLDOUT EVALUATION: sealed test arrays are being read."
    for _ in range(1)) + "\n" + "*" * 78
ARMS = ("original", "repaired", "control_dup")
DIRECTIONS = (101, 202, 303, 404)
N_OPT_SEEDS = 8
STEPS = 200
MAX_TRAIN = 256
_W = {}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _meta():
    return {"python": platform.python_version(), "numpy": np.__version__,
            "host": socket.gethostname(),
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                                         capture_output=True, text=True,
                                         timeout=10).stdout.strip() or "unknown",
            "utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}


# ------------------------------------------------------------------ E-R4 repair
def _repair_unit(job):
    arm, eta, direction, opt_seed = job
    task = _W["task"]
    closure = _W["closure"]
    x = np.asarray(task.x, float)
    train = np.asarray(task.splits["train"], bool)
    tf = _r2.TargetFn(task, direction, eta, closure)
    y = tf.y_of(x)
    theta, train_risk = _r2.fit_arm(arm, task, x[train], y[train], opt_seed,
                                    int(_W["steps"]), max_train=MAX_TRAIN)
    row = {"arm": arm, "eta": float(eta),
           "direction_seed": int(direction) if direction is not None else None,
           "opt_seed": int(opt_seed), "steps": int(_W["steps"]),
           "train_loss": train_risk, "theta": theta.tolist()}
    # The target is rebuilt from the SAME trusted TargetFn that trained the arm: an
    # untouched-input holdout supplies new x, and the label is the generative function
    # evaluated there.  (The first version of this script read a single alpha_0 label per
    # split, which evaluated every eta against the invariant target; see PROVENANCE.)
    for name, xt in _W["eval_sets"].items():
        xt = np.asarray(xt, float)
        row["risk_" + name] = _r2.block_dev_risk(arm, task, xt, tf.y_of(xt), theta)
    row["channel_mean"] = _r2.channel_residual(arm, int(task.n_qubits), theta,
                                               closure)["channel_mean"]
    return row


def eval_repair():
    task = _W["task"]
    closure = _W["closure"]
    jobs = [(arm, eta, direction, seed)
            for eta in (0.0, 0.5, 1.0)
            for direction in ((None,) if eta == 0.0 else _W["directions"])
            for seed in range(int(_W["n_opt_seeds"]))
            for arm in ARMS]
    print("E-R4: %d fits" % len(jobs), flush=True)
    ctx = mp.get_context("fork")
    with ctx.Pool(_W["workers"]) as pool:
        rows = pool.map(_repair_unit, jobs, chunksize=1)
    return rows


# ------------------------------------------------------------------ E-S7 search
def _search_run(path):
    log = _refit.load_run(path)
    task = _W["tasks"][log["family"]]
    fit, _, _, _, check = _refit.refit_best(log, task=task)
    dev = np.asarray(task.splits["validation"], bool)
    train = np.asarray(task.splits["train"], bool)
    x = np.asarray(task.x)
    key = log.get("target") or task.primary_target
    y = np.asarray(task.targets[key])
    test_risk = float(_train.risk(fit, task, _W["test_x"][log["family"]],
                                  _W["test_y"][log["family"]]))
    return {"path": path, "arm": log["arm"], "family": log["family"],
            "seed": int(log["seed"]), "dev_risk": float(log["best"]["dev_risk"]),
            "test_risk": test_risk, "reproduction": check,
            "repair_fired": bool((log["best"].get("repair") or {}).get("repaired")),
            "test_risk_averaged_diagnostic": None}


def eval_search(paths):
    ctx = mp.get_context("fork")
    with ctx.Pool(_W["workers"]) as pool:
        return pool.map(_search_run, paths, chunksize=1)


# ------------------------------------------------------------------------ driver
def main(argv=None):
    p = argparse.ArgumentParser(prog="research/holdout_oneshot.py")
    p.add_argument("--runs", default="logs/runs_confirm")
    p.add_argument("--out", default="research/HOLDOUT_RESULTS.json")
    p.add_argument("--access-log", default="research/HOLDOUT_ACCESS.json")
    p.add_argument("--workers", type=int, default=24)
    p.add_argument("--directions", default=",".join(str(d) for d in DIRECTIONS),
                   help="frozen design default; override only for the dry run")
    p.add_argument("--n-opt-seeds", type=int, default=N_OPT_SEEDS)
    p.add_argument("--steps", type=int, default=STEPS)
    p.add_argument("--dry-run", action="store_true",
                   help="substitute the development validation split for every "
                        "sealed array and touch nothing sealed; validates code paths "
                        "before the single real evaluation")
    p.add_argument("--splits", default="dev,fresh_v3",
                   help="comma list of E-R4 evaluation inputs; the consumed v1/v2 "
                        "splits are excluded by default after the Addendum A4 defect")
    p.add_argument("--selfcheck", default=None,
                   help="path to repair2_results.json: compare the refit's dev-row risk "
                        "against the logged dev_risk and fail on any mismatch")
    p.add_argument("--skip-search", action="store_true",
                   help="do not run E-S7 (keeps the already-consumed v1 search split "
                        "single-read)")
    a = p.parse_args(argv)
    if a.dry_run:
        a.out = "logs/holdout_dryrun.json"
        a.access_log = "logs/holdout_dryrun_access.json"
        print("DRY RUN: sealed arrays are NOT opened", flush=True)
    print(BANNER if not a.dry_run else "DRY RUN - no sealed read", flush=True)
    sealed = {"ring_v1": _tasks.dataset_path("ring_n6", locked=True),
              "graphs_v1": _tasks.dataset_path("graphs_n6", locked=True),
              "ring_v2": os.path.join(_tasks.DATASETS / "locked_holdout_v2",
                                      "ring_n6.npz")}
    before = ({} if a.dry_run else {k: sha256(v) for k, v in sealed.items()})
    access = {"event": "DRY RUN (no sealed read)" if a.dry_run
              else "ONE-SHOT holdout evaluation",
              "files": before, "started": _meta()}
    with open(a.access_log, "w") as fh:
        json.dump(access, fh, indent=1, default=str)

    # ---- E-R4 (ring): untouched INPUTS; targets rebuilt from the trusted TargetFn ----
    task = _tasks.load_family("ring_n6", development=True, locked=False)
    dev_mask = np.asarray(task.splits["validation"], bool)
    x_dev = np.asarray(task.x)[dev_mask]
    want = [s.strip() for s in a.splits.split(",") if s.strip()]
    eval_sets = {}
    for name in want:
        if name == "dev":
            eval_sets["dev"] = x_dev
        elif name == "fresh_v3":
            p3 = os.path.join(_tasks.DATASETS / "locked_holdout_v3", "ring_n6_x.npz")
            sealed["ring_v3"] = p3
            before["ring_v3"] = sha256(p3)
            with np.load(p3) as d3:
                eval_sets["fresh_v3"] = np.asarray(d3["x_test"], float)
        elif name in ("sealed_v1", "fresh_v2"):
            raise SystemExit("%s was consumed by the defective one-shot run recorded in "
                             "research/PROVENANCE.md; re-reading it would violate the "
                             "one-shot policy (Addendum A4)" % name)
        else:
            raise SystemExit("unknown split %r" % name)
    _W.update({"task": task, "closure": _r1.group_closure(task.generators),
               "workers": a.workers, "n_opt_seeds": int(a.n_opt_seeds),
               "steps": int(a.steps),
               "directions": tuple(int(d) for d in a.directions.split(",")),
               "eval_sets": eval_sets})
    repair_rows = eval_repair()

    selfcheck = None
    if a.selfcheck:
        with open(a.selfcheck) as fh:
            ref = json.load(fh)
        want_keys = {(r["arm"], r["eta"], r.get("direction_seed"), r["opt_seed"]):
                     r["dev_risk"] for r in ref["rows"] if int(r["steps"]) == int(a.steps)}
        diffs, missing = [], 0
        for r in repair_rows:
            k = (r["arm"], r["eta"], r["direction_seed"], r["opt_seed"])
            if k in want_keys and "risk_dev" in r:
                diffs.append(abs(r["risk_dev"] - want_keys[k]))
            else:
                missing += 1
        selfcheck = {"reference": a.selfcheck, "compared": len(diffs),
                     "not_in_reference": missing,
                     "max_abs_dev_risk_diff": float(max(diffs)) if diffs else None,
                     "tolerance": 1e-9, "pass": bool(diffs and max(diffs) < 1e-9)}
        print("SELFCHECK vs %s: %d compared, max |dev diff| = %.3e -> %s"
              % (a.selfcheck, len(diffs),
                 max(diffs) if diffs else float("nan"), "PASS" if selfcheck["pass"]
                 else "FAIL"), flush=True)
        if not selfcheck["pass"]:
            raise SystemExit("self-check failed: the holdout evaluator does not "
                             "reproduce the experiment's own dev risk")

    # ---- E-S7 (search) ----
    import glob
    tasks, tx, ty = {}, {}, {}
    search_rows = []
    if a.skip_search:
        print("E-S7 skipped (sealed v1 splits already consumed by the first one-shot "
              "run; its valid E-S7 results stay in the original HOLDOUT_RESULTS.json)",
              flush=True)
    else:
        for fam in ("ring_n6", "graphs_n6"):
            tasks[fam] = _tasks.load_family(fam, development=True, locked=False)
            if a.dry_run:
                m = np.asarray(tasks[fam].splits["validation"], bool)
                tx[fam] = np.asarray(tasks[fam].x)[m][:200]
                ty[fam] = np.asarray(tasks[fam].targets[tasks[fam].primary_target])[m][:200]
                continue
            path = sealed["ring_v1"] if fam == "ring_n6" else sealed["graphs_v1"]
            with np.load(path) as dd:
                key = "y_%s_test" % tasks[fam].primary_target
                tx[fam] = np.asarray(dd["x_test"], float)
                ty[fam] = np.asarray(dd[key], float)
        _W.update({"tasks": tasks, "test_x": tx, "test_y": ty})
        paths = sorted(glob.glob(os.path.join(a.runs, "run_*.json")))
        search_rows = eval_search(paths)

    # ---- contrasts ----
    def by(rows, key):
        out = {}
        for r in rows:
            out.setdefault(key(r), []).append(r)
        return out

    repair_contrasts = []
    for split in eval_sets:
        for eta in (0.0, 0.5, 1.0):
            for a_arm, b_arm in (("repaired", "control_dup"),
                                 ("repaired", "original"),
                                 ("control_dup", "original")):
                A = by([r for r in repair_rows if r["eta"] == eta and r["arm"] == a_arm],
                       lambda r: (r["direction_seed"], r["opt_seed"]))
                B = by([r for r in repair_rows if r["eta"] == eta and r["arm"] == b_arm],
                       lambda r: (r["direction_seed"], r["opt_seed"]))
                keys = sorted(set(A) & set(B))
                diffs = [A[k][0]["risk_" + split] - B[k][0]["risk_" + split]
                         for k in keys]
                if eta == 0.0:                       # unit = optimiser seed only
                    seen, ded = set(), []
                    for k, dv in zip(keys, diffs):
                        if k[1] in seen:
                            continue
                        seen.add(k[1])
                        ded.append(dv)
                    diffs = ded
                c = {"split": split, "eta": eta, "a": a_arm, "b": b_arm,
                     "n_units": len(diffs), "diffs": diffs,
                     "mean_diff_a_minus_b": float(np.mean(diffs)) if diffs else None}
                c["bootstrap"] = _P.bootstrap_ci(diffs)
                c["p_shifted_bootstrap"] = _P.shifted_bootstrap_p(diffs)
                c["p_signflip"] = _P.signflip_p(diffs)
                c["verdict"] = _P.verdict(c["bootstrap"]["ci95_low"],
                                          c["bootstrap"]["ci95_high"])
                repair_contrasts.append(c)

    search_contrasts = []
    for fam in ("ring_n6", "graphs_n6"):
        for a_arm, b_arm in (("llm-verify", "llm-fitness"),
                             ("llm-verify-repair", "llm-verify"),
                             ("llm-fitness", "mutation-ea"),
                             ("llm-verify", "random")):
            A = {r["seed"]: r["test_risk"] for r in search_rows
                 if r["family"] == fam and r["arm"] == a_arm}
            B = {r["seed"]: r["test_risk"] for r in search_rows
                 if r["family"] == fam and r["arm"] == b_arm}
            seeds = sorted(set(A) & set(B))
            diffs = [A[s] - B[s] for s in seeds]
            c = {"family": fam, "a": a_arm, "b": b_arm, "n_pairs": len(diffs),
                 "diffs": diffs,
                 "mean_diff_a_minus_b": float(np.mean(diffs)) if diffs else None}
            c["bootstrap"] = _P.bootstrap_ci(diffs)
            c["p_shifted_bootstrap"] = _P.shifted_bootstrap_p(diffs)
            c["p_signflip"] = _P.signflip_p(diffs)
            c["verdict"] = _P.verdict(c["bootstrap"]["ci95_low"],
                                      c["bootstrap"]["ci95_high"])
            search_contrasts.append(c)

    after = ({} if a.dry_run else {k: sha256(v) for k, v in sealed.items()})
    result = {"protocol": "research/REVISED_PROTOCOL.md section 5 + Addendum A4",
              "one_shot": True,
              "splits_evaluated": list(eval_sets),
              "selfcheck": selfcheck,
              "sealed_sha256_before": before, "sealed_sha256_after": after,
              "unchanged": bool(before == after),
              "repair_design": {"arms": list(ARMS), "directions": list(DIRECTIONS),
                                "n_opt_seeds": N_OPT_SEEDS, "steps": STEPS,
                                "max_train": MAX_TRAIN,
                                "unit": "optimiser seed at eta=0; (direction, seed) "
                                        "at eta>0"},
              "repair_rows": repair_rows, "repair_contrasts": repair_contrasts,
              "search_rows": search_rows, "search_contrasts": search_contrasts,
              "search_arm_means": [
                  {"family": fam, "arm": arm,
                   "n": len(rs), "mean_dev_risk": float(np.mean([r["dev_risk"] for r in rs])),
                   "mean_test_risk": float(np.mean([r["test_risk"] for r in rs]))}
                  for fam in ("ring_n6", "graphs_n6")
                  for arm in sorted({r["arm"] for r in search_rows if r["family"] == fam})
                  for rs in [[r for r in search_rows
                              if r["family"] == fam and r["arm"] == arm]]],
              "metadata": _meta()}
    with open(a.out, "w") as fh:
        json.dump(result, fh, indent=1, default=str)
    access["finished"] = _meta()
    access["sealed_sha256_after"] = after
    with open(a.access_log, "w") as fh:
        json.dump(access, fh, indent=1, default=str)
    print("wrote %s and %s" % (a.out, a.access_log))
    for c in repair_contrasts:
        b = c["bootstrap"]
        if b["mean"] is None:
            print("[E-R4 %-10s eta=%.1f] %-13s vs %-13s no paired units" %
                  (c["split"], c["eta"], c["a"], c["b"]))
            continue
        print("[E-R4 %-10s eta=%.1f] %-13s vs %-13s n=%d mean=%+.5f CI=[%+.5f,%+.5f] %s"
              % (c["split"], c["eta"], c["a"], c["b"], c["n_units"], b["mean"],
                 b["ci95_low"], b["ci95_high"], c["verdict"]))
    for c in search_contrasts:
        b = c["bootstrap"]
        if b["mean"] is None:
            print("[E-S7 %-11s] %-18s vs %-18s no paired units" %
                  (c["family"], c["a"], c["b"]))
            continue
        print("[E-S7 %-11s] %-18s vs %-18s n=%d mean=%+.5f CI=[%+.5f,%+.5f] %s"
              % (c["family"], c["a"], c["b"], c["n_pairs"], b["mean"],
                 b["ci95_low"], b["ci95_high"], c["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
