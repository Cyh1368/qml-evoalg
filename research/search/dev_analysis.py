"""WP-SEARCH development-side analyses that need the fitted predictor (E-S4b, E-S5,
E-S6 of ``research/REVISED_PROTOCOL.md``).

Everything here is **development-split only**; the sealed splits are never opened
(this module refuses locked paths). It re-fits each run's dev-selected candidate
with the harness's own deterministic call (``research.search.refit``), verifies the
reproduction against the risk recorded in the run log, and then measures:

* **E-S4b** executable-validity / nonconstant-output checks on the deployed
  predictor (the reliability claim the first manuscript made without an endpoint);
* **E-S4c** verifier selectivity: how often a *wrong* hypothesis group passes the
  label-preservation gate (the verifier's own error rate, trusted-side);
* **E-S5** the density-shortcut intervention: risk of every arm's selected
  predictor inside edge-count bands of ``graphs_n6``, which is what the "a density
  shortcut explains the graphs null" claim needs;
* **E-S5b** the same inference-time Reynolds average that ``llm-verify-repair``
  deploys, applied to *every* arm's selected candidate with the task's **declared**
  group (a non-LLM pipeline given the same repair tool; Monte-Carlo twirl where the
  group is too large to enumerate);
* **E-S6** matched-budget tool baselines: the constructive equivariant
  architecture, the edge-count-threshold classical rule, the invariant oracle and
  the best constant predictor.

Usage::

    python3 -m research.search.dev_analysis --dir logs/runs_confirm \\
        --out research/search/dev_analysis.json [--workers 24]
"""
import argparse
import glob
import json
import multiprocessing as mp
import os
import sys

import numpy as np

from research.core import candidates as _cand
from research.core import paired as _P
from research.core import tasks as _tasks
from research.core import train as _train
from research.search import refit as _refit
from research.search import verifier_bridge as _vb

MC_TWIRL_ELEMENTS = 24          # Monte-Carlo twirl when |G| is large
DEV_ROWS_MC = 256
BANDS = ((0, 5), (6, 7), (8, 9), (10, 11), (12, 15))
_W = {}


def _task_group_closure(task):
    from verify import closure
    return closure([list(g) for g in task.generators], int(task.n_qubits))


def _hyp_closure(task, generators):
    from verify import closure
    return closure([list(g) for g in generators], int(task.n_qubits))


# --------------------------------------------------------------------- per run
def analyse_run(path):
    log = _refit.load_run(path)
    family = log["family"]
    task = _W["tasks"][family]
    dev = np.asarray(task.splits["validation"], bool)
    x = np.asarray(task.x)
    key = log.get("target") or task.primary_target
    y = np.asarray(task.targets[key])[dev]
    x_dev = x[dev]
    fit, _, _, _, check = _refit.refit_best(log, task=task)
    pred = _refit.predictions(fit, task, x_dev)
    out = {"path": path, "arm": log["arm"], "family": family, "seed": int(log["seed"]),
           "steps": log["steps"], "max_train": log.get("max_train"),
           "reproduction": check,
           "dev_risk": float(np.mean((pred - y) ** 2)),
           "pred_std": float(np.std(pred)),
           "nonconstant": bool(np.std(pred) > 1e-8),
           "accuracy": float(np.mean(np.sign(pred) == np.sign(y)))
           if set(np.unique(y)) <= {-1.0, 1.0} else None}
    # E-S5: risk inside density (edge-count) bands, graphs only
    if family.startswith("graphs"):
        edges = np.asarray(x_dev, float).sum(axis=1).astype(int)
        bands = {}
        for lo, hi in BANDS:
            m = (edges >= lo) & (edges <= hi)
            if m.sum():
                bands["%d-%d" % (lo, hi)] = {
                    "n": int(m.sum()),
                    "risk": float(np.mean((pred[m] - y[m]) ** 2)),
                    "pos_rate": float(np.mean(y[m] > 0))}
        out["bands"] = bands
    # E-S5b: declared-group Reynolds average applied to this arm's predictor
    closure = _W["closures"][family]
    rng = np.random.default_rng(1234 + int(log["seed"]))
    idx = rng.choice(len(x_dev), size=min(DEV_ROWS_MC, len(x_dev)), replace=False) \
        if len(x_dev) > DEV_ROWS_MC else np.arange(len(x_dev))
    rows = x_dev[idx]
    yy = y[idx]
    elems = closure if len(closure) <= MC_TWIRL_ELEMENTS else \
        [closure[i] for i in rng.choice(len(closure), size=MC_TWIRL_ELEMENTS,
                                        replace=False)]
    acc = np.zeros(len(rows))
    for perm in elems:
        acc += _refit.predictions(fit, task, _vb.transform_rows(task, rows, perm))
    avg = acc / len(elems)
    out["twirl"] = {"n_rows": int(len(rows)), "n_elements": len(elems),
                    "exact": len(elems) == len(closure),
                    "group_order": len(closure),
                    "risk_before": float(np.mean((np.asarray(
                        _refit.predictions(fit, task, rows)) - yy) ** 2)),
                    "risk_after": float(np.mean((avg - yy) ** 2))}
    out["twirl"]["diff_after_minus_before"] = (out["twirl"]["risk_after"]
                                               - out["twirl"]["risk_before"])
    # E-S4c: verifier selectivity on this run's proposals (trusted side)
    if log["arm"] in ("llm-fitness", "llm-verify", "llm-verify-repair"):
        stats = {"proposals_with_hypothesis": 0, "hyp_group_equals_task": 0,
                 "hyp_label_preserving": 0, "wrong_group_but_label_preserving": 0,
                 "hyp_order_mean": None}
        orders = []
        for p in log.get("proposals") or []:
            cand = p.get("candidate") or {}
            hyp = cand.get("hypothesis") or {}
            gens = hyp.get("generators")
            if not gens or not p.get("valid"):
                continue
            stats["proposals_with_hypothesis"] += 1
            try:
                cl = _hyp_closure(task, gens)
            except Exception:
                continue
            orders.append(len(cl))
            same = (len(cl) == len(closure) and set(map(tuple, cl))
                    == set(map(tuple, closure)))
            stats["hyp_group_equals_task"] += int(same)
            try:
                lp = _vb.label_preservation(task, hyp, 64)
                ok = lp["violated_fraction"] == 0.0
            except Exception:
                ok = False
            stats["hyp_label_preserving"] += int(ok)
            stats["wrong_group_but_label_preserving"] += int(ok and not same)
        stats["hyp_order_mean"] = float(np.mean(orders)) if orders else None
        out["verifier_selectivity"] = stats
    return out


# ------------------------------------------------------------------- baselines
def constructive_equivariant(family, seeds, steps, max_train):
    """Hand-built exactly equivariant block at the search protocol's fit budget."""
    task = _W["tasks"][family]
    n = int(task.n_qubits)
    import itertools
    block = [{"gate": "RY", "wire": i, "param": "a"} for i in range(n)]
    for i, j in itertools.combinations(range(n), 2):
        block.append({"gate": "CRZ", "wires": [i, j], "param": "b"})
        block.append({"gate": "CRZ", "wires": [j, i], "param": "b"})
    block += [{"gate": "RY", "wire": i, "param": "c"} for i in range(n)]
    cand = {"id": "constructive", "n_qubits": n, "block": block, "repeats": 1,
            "layers": 1, "param_names": ["a", "b", "c"], "hypothesis": None,
            "notes": "constructive equivariant baseline", "source": {"arm": "baseline"}}
    dev = np.asarray(task.splits["validation"], bool)
    train = np.asarray(task.splits["train"], bool)
    x = np.asarray(task.x)
    key = task.primary_target
    y = np.asarray(task.targets[key])
    closure = _W["closures"][family]
    from research.metrics import symmetry as _sym
    resid = _sym.defects(_sym.unitary(block, {"a": 0.3, "b": 0.4, "c": 0.5}, n),
                         closure)["channel_mean"]
    risks = []
    for s in seeds:
        fit = _train.fit(cand, task, x[train], y[train], int(s), steps=int(steps),
                         max_train=max_train)
        risks.append(float(_train.risk(fit, task, x[dev], y[dev])))
    return {"family": family, "arm": "constructive-equivariant", "steps": int(steps),
            "max_train": max_train, "channel_residual": float(resid),
            "seeds": list(map(int, seeds)), "dev_risks": risks,
            "mean_dev_risk": float(np.mean(risks))}


def classical_baselines(family):
    """Task-aware classical rules fitted on TRAIN rows only, scored on dev."""
    task = _W["tasks"][family]
    dev = np.asarray(task.splits["validation"], bool)
    train = np.asarray(task.splits["train"], bool)
    x = np.asarray(task.x)
    key = task.primary_target
    y = np.asarray(task.targets[key], float)
    out = {"family": family, "target": key}
    ytr, ydev = y[train], y[dev]
    out["best_constant"] = {"threshold": "mean(train)",
                            "dev_risk": float(np.mean((ydev - ytr.mean()) ** 2))}
    if family.startswith("graphs"):
        edges_tr = x[train].sum(axis=1)
        edges_dev = x[dev].sum(axis=1)
        best = None
        for k in range(0, 16):
            pred = np.where(edges_tr >= k, 1.0, -1.0)
            risk = float(np.mean((pred - ytr) ** 2))
            if best is None or risk < best[1]:
                best = (k, risk)
        k = best[0]
        pred = np.where(edges_dev >= k, 1.0, -1.0)
        out["edge_count_threshold"] = {
            "threshold": int(k), "fitted_on": "train only",
            "dev_risk": float(np.mean((pred - ydev) ** 2)),
            "dev_accuracy": float(np.mean(pred == ydev)),
            "train_accuracy": float(np.mean(np.where(edges_tr >= k, 1.0, -1.0) == ytr))}
        bands = {}
        for lo, hi in BANDS:
            m = (edges_dev >= lo) & (edges_dev <= hi)
            if m.sum():
                bands["%d-%d" % (lo, hi)] = {
                    "n": int(m.sum()),
                    "dev_risk": float(np.mean((pred[m] - ydev[m]) ** 2)),
                    "majority_accuracy": float(max(np.mean(ydev[m] > 0),
                                                   np.mean(ydev[m] < 0)))}
        out["edge_count_threshold"]["bands"] = bands
    else:
        h = np.asarray(task.targets["alpha_0"], float)
        out["invariant_oracle"] = {"dev_risk": float(np.mean((h[dev] - ydev) ** 2)),
                                   "note": "h is the ground-truth invariant target "
                                           "for alpha_0, so this is 0 by construction"}
    return out


# ----------------------------------------------------------------------- driver
def _init(tasks, closures):
    _W["tasks"] = tasks
    _W["closures"] = closures


def main(argv=None):
    p = argparse.ArgumentParser(prog="research/search/dev_analysis.py")
    p.add_argument("--dir", default="logs/runs_confirm")
    p.add_argument("--out", default="research/search/dev_analysis.json")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--baseline-steps", type=int, default=120)
    a = p.parse_args(argv)
    if "locked" in a.dir.lower():
        raise SystemExit("dev_analysis is development-only")
    paths = sorted(glob.glob(os.path.join(a.dir, "run_*.json")))
    families = sorted({_refit.load_run(p)["family"] for p in paths})
    tasks, closures = {}, {}
    for fam in families:
        tasks[fam] = _tasks.load_family(fam, development=True, locked=False)
        closures[fam] = _task_group_closure(tasks[fam])
        print("%s declared group order %d" % (fam, len(closures[fam])), flush=True)
    runs = []
    _W["tasks"] = tasks
    _W["closures"] = closures
    ctx = mp.get_context("fork")
    with ctx.Pool(a.workers, initializer=_init, initargs=(tasks, closures)) as pool:
        for i, row in enumerate(pool.imap_unordered(analyse_run, paths), 1):
            runs.append(row)
            if i % 10 == 0 or i == len(paths):
                print("  %d/%d runs analysed" % (i, len(paths)), flush=True)
    bad = [r for r in runs if not r["reproduction"]["exact"]]
    print("refit reproduction: %d/%d exact, max abs diff %.2e"
          % (len(runs) - len(bad), len(runs),
             max(r["reproduction"]["abs_diff"] for r in runs)))
    seeds = sorted({r["seed"] for r in runs})
    baselines = {"per_run": None,
                 "constructive": [constructive_equivariant(f, seeds, a.baseline_steps,
                                                           256) for f in families],
                 "classical": [classical_baselines(f) for f in families]}
    # paired comparisons: constructive baseline vs each arm's selected risk
    comp = []
    for fam in families:
        con = [c for c in baselines["constructive"] if c["family"] == fam][0]
        con_by_seed = dict(zip(con["seeds"], con["dev_risks"]))
        for arm in sorted({r["arm"] for r in runs if r["family"] == fam}):
            diffs, used = [], []
            for r in runs:
                if r["family"] != fam or r["arm"] != arm:
                    continue
                if r["seed"] in con_by_seed:
                    diffs.append(r["dev_risk"] - con_by_seed[r["seed"]])
                    used.append(r["seed"])
            c = {"family": fam, "a": arm, "b": "constructive-equivariant",
                 "unit": "paired seed", "n_pairs": len(diffs), "seeds": used,
                 "diffs": diffs,
                 "mean_diff_a_minus_b": float(np.mean(diffs)) if diffs else None}
            c["bootstrap"] = _P.bootstrap_ci(diffs)
            c["p_shifted_bootstrap"] = _P.shifted_bootstrap_p(diffs)
            c["verdict"] = _P.verdict(c["bootstrap"]["ci95_low"],
                                      c["bootstrap"]["ci95_high"])
            comp.append(c)
    baselines["arm_vs_constructive"] = comp
    # twirl (declared-group repair tool applied to every arm) paired summary
    tw = []
    for fam in families:
        for arm in sorted({r["arm"] for r in runs if r["family"] == fam}):
            diffs = [r["twirl"]["diff_after_minus_before"] for r in runs
                     if r["family"] == fam and r["arm"] == arm]
            c = {"family": fam, "arm": arm, "estimand": "E-S5b declared-group twirl "
                   "applied to the arm's selected predictor",
                 "n": len(diffs), "diffs": diffs,
                 "mean_diff_after_minus_before": float(np.mean(diffs)) if diffs else None}
            c["bootstrap"] = _P.bootstrap_ci(diffs)
            c["p_shifted_bootstrap"] = _P.shifted_bootstrap_p(diffs)
            c["verdict"] = _P.verdict(c["bootstrap"]["ci95_low"],
                                      c["bootstrap"]["ci95_high"])
            tw.append(c)
    # E-S5c (protocol Addendum A2): density-MATCHED arm comparisons.  All arms share
    # seeds and therefore datasets, so a paired arm contrast restricted to the rows of
    # one edge-count band is density-matched by construction.
    band_contrasts = []
    band_keys = ["%d-%d" % b for b in BANDS]
    for fam in families:
        if not fam.startswith("graphs"):
            continue
        by_key = {}
        for r in runs:
            ds_name = os.path.basename(r["path"]).split("__")[0]
            by_key.setdefault((ds_name, r["seed"]), {})[r["arm"]] = r.get("bands", {})
        for a_arm, b_arm in (("llm-verify", "llm-fitness"),
                             ("llm-verify-repair", "llm-verify")):
            for bk in band_keys:
                diffs = []
                for _k, per_arm in by_key.items():
                    A, B = per_arm.get(a_arm, {}), per_arm.get(b_arm, {})
                    if bk in A and bk in B and A[bk]["n"] == B[bk]["n"]:
                        diffs.append(A[bk]["risk"] - B[bk]["risk"])
                if not diffs:
                    continue
                c = {"family": fam, "band_edges": bk, "a": a_arm, "b": b_arm,
                     "n_pairs": len(diffs), "diffs": diffs,
                     "mean_diff_a_minus_b": float(np.mean(diffs))}
                c["bootstrap"] = _P.bootstrap_ci(diffs)
                c["p_shifted_bootstrap"] = _P.shifted_bootstrap_p(diffs)
                c["verdict"] = _P.verdict(c["bootstrap"]["ci95_low"],
                                          c["bootstrap"]["ci95_high"])
                band_contrasts.append(c)

    result = {"directory": a.dir, "scope": "development only; locked splits never read",
              "n_runs": len(runs), "families": families,
              "refit_reproduction": {
                  "exact": int(len(runs) - len(bad)), "n": len(runs),
                  "max_abs_diff": float(max(r["reproduction"]["abs_diff"]
                                            for r in runs))},
              "bands_definition": ["%d-%d" % b for b in BANDS],
              "mc_twirl": {"elements": MC_TWIRL_ELEMENTS, "rows": DEV_ROWS_MC,
                           "note": "exact when the declared group order <= %d"
                                   % MC_TWIRL_ELEMENTS},
              "runs": runs, "twirl_summary": tw, "baselines": baselines,
              "E-S5c_density_matched_arm_contrasts": band_contrasts}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(result, fh, indent=1, default=str)
    print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
