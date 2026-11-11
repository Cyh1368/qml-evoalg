"""Deterministic re-fitting of candidates recorded in search run logs.

The search harness does not persist fitted parameters, but ``train.fit`` is
deterministic in ``(candidate, task, x, y, seed, steps, batch, lr)`` and the
harness always calls it as::

    train.fit(cand, task, x_tr, y_tr, seed, steps=steps, max_train=max_train)

so a logged candidate can be reproduced exactly. This module is the single
place that reconstructs a fitted predictor from a run log, and it *verifies*
the reconstruction against the ``dev_risk`` recorded in the log before any
downstream analysis (stratified evaluation, holdout evaluation) uses it.

Locked-holdout access is explicit and separate: ``evaluate_locked`` must be
called only from the one-shot frozen holdout evaluation
(``research/search/holdout_eval.py``), never from search itself.
"""
import json

import numpy as np

from research.core import tasks as _tasks
from research.core import train as _train


def load_run(path):
    with open(path) as fh:
        return json.load(fh)


def best_candidate(run_log):
    return run_log["best"]["candidate"]


def refit_best(run_log, task=None, dev=True):
    """Refit the run's dev-selected candidate; verify against the logged risk.

    Returns ``(fit, task, x_dev, y_dev, check)`` where ``check`` reports the
    absolute difference between the reproduced and logged dev risk.
    """
    family = run_log["family"]
    if task is None:
        task = _tasks.load_family(family, development=True, locked=False)
    splits = task.splits
    train_mask = np.asarray(splits["train"], bool)
    val_mask = np.asarray(splits["validation"], bool)
    x = np.asarray(task.x)
    key = run_log.get("target") or task.primary_target
    y = np.asarray(task.targets[key])
    cand = best_candidate(run_log)
    fit = _train.fit(cand, task, x[train_mask], y[train_mask], int(run_log["seed"]),
                     steps=int(run_log["steps"]), max_train=run_log.get("max_train"))
    risk = float(_train.risk(fit, task, x[val_mask], y[val_mask]))
    logged = float(run_log["best"]["dev_risk"])
    check = {"reproduced_dev_risk": risk, "logged_dev_risk": logged,
             "abs_diff": abs(risk - logged),
             "exact": bool(abs(risk - logged) < 1e-12)}
    return fit, task, x[val_mask], y[val_mask], check


def predictions(fit, task, rows):
    return np.asarray(fit.predict(task, rows), dtype=float).reshape(-1)
