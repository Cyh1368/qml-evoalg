"""Executable equivariance + label-preservation checks for search arms.

Reuses the exact permutation closure from research/verifier/verify.py (via
sys.path insertion, per INTERFACES.md) and the channel-defect convention from
research/metrics/symmetry.py. Circuit unitaries come from
research.core.simulator, imported lazily so this module loads before core
lands. The true task group is only ever computed when the caller explicitly
asks for group="true"; LLM prompts must never receive that report.
"""
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve()
_VERIFIER_DIR = _HERE.parents[1] / "verifier"
_METRICS_DIR = _HERE.parents[1] / "metrics"
for _p in (str(_VERIFIER_DIR), str(_METRICS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from verify import closure, graph_edge_action  # noqa: E402
from symmetry import defects  # noqa: E402

DEFAULT_TOLERANCE = 1e-10
DEFAULT_PARAM_SAMPLES = 3


def _simulator():
    from research.core import simulator
    return simulator


def _candidates():
    from research.core import candidates
    return candidates


def hypothesis_generators(candidate):
    hyp = (candidate or {}).get("hypothesis")
    if not hyp or not hyp.get("generators"):
        return None
    return hyp["generators"]


def resolve_generators(candidate, task, group="hypothesis"):
    if group == "true":
        gens = getattr(task, "generators", None)
        if not gens:
            raise ValueError("task exposes no true generators")
        return gens
    if isinstance(group, (list, tuple)) and group and isinstance(group[0], (list, tuple)):
        # An explicit generator list, used by the decision-rule study so that a gate can be asked
        # about the group of the *current regime* rather than only the candidate's own claim or the
        # task's true generators. Analysis-side only: nothing here reaches a prompt, and the
        # prompt-side path continues to pass group="hypothesis" exclusively.
        return [[int(i) for i in g] for g in group]
    if group != "hypothesis":
        raise ValueError("group must be 'hypothesis', 'true', or an explicit generator list")
    gens = hypothesis_generators(candidate)
    if gens is None:
        raise ValueError("candidate carries no hypothesis to verify")
    return gens


def sample_param_dicts(candidate, rng, n_samples=DEFAULT_PARAM_SAMPLES,
                       low=-np.pi, high=np.pi):
    """Random parameter draws over the candidate's own parameter names."""
    names = list(candidate.get("param_names") or [])
    return [{name: float(rng.uniform(low, high)) for name in names}
            for _ in range(n_samples)]


def transform_row(task, x, perm):
    """Pullback action of a site permutation on one input row.

    Convention matches research/verifier/verify.py: output site i reads input
    site perm[i]. Graph edge-bit rows use the induced lexicographic edge
    action; all other families are per-site feature vectors.
    """
    x = np.asarray(x)
    if str(getattr(task, "name", "")).startswith("graphs"):
        return graph_edge_action(x, perm)
    return x[list(perm)]


def transform_rows(task, rows, perm):
    return np.stack([transform_row(task, row, perm) for row in np.atleast_2d(rows)])


def verify_candidate(candidate, task, params_samples, group="hypothesis",
                     x=None, tolerance=DEFAULT_TOLERANCE):
    """Channel residual of the candidate's FULL EXPANDED circuit.

    params_samples: nonempty list of parameter dicts (values for the block's
    param_names; feature-map gates carry fixed angles). group is 'hypothesis'
    (the candidate's own claim - the only value allowed to reach a prompt) or
    'true' (logging only, never prompt material). Returns a report dict with
    group_order, mean/max channel residual over all (sample, element) pairs.
    """
    if not params_samples:
        raise ValueError("params_samples must be a nonempty list of param dicts")
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and nonnegative")
    n = int(candidate.get("n_qubits") or task.n_qubits)
    gens = resolve_generators(candidate, task, group)
    perms = closure(gens, n)
    if x is None:
        xs = getattr(task, "x", None)
        if xs is None or len(xs) == 0:
            raise ValueError("need an input row to expand the feature map")
        x = np.asarray(xs)[0]
    gates, _names = _candidates().expand_example(candidate, task, x)
    sim = _simulator()
    per_sample = []
    all_channel = []
    for params in params_samples:
        u = sim.unitary(gates, params, n)
        if not np.all(np.isfinite(u)):
            raise ValueError("nonfinite expanded-circuit unitary")
        row = defects(u, perms)
        per_sample.append(row)
        # Recompute per-element channel values for the mean over the group.
        d = u.shape[0]
        for p in perms:
            ix = _permutation_indices(p)
            v = u[np.ix_(ix, ix)]
            overlap = np.vdot(u, v) / d
            all_channel.append(float(np.clip(1 - abs(overlap) ** 2, 0.0, 1.0)))
    worst = max(r["channel_max"] for r in per_sample)
    return {"group": group, "group_order": len(perms),
            "parameter_samples": len(params_samples),
            "mean_channel_residual": float(np.mean(all_channel)),
            "max_channel_residual": float(worst),
            "per_sample_channel_max": [r["channel_max"] for r in per_sample],
            "tolerance": tolerance,
            "sampled_pass": bool(worst <= tolerance),
            "scope": "supplied parameter draws, full closure of the supplied "
                     "generators, expanded circuit on one input row",
            "all_parameter_proof": False}


def _permutation_indices(permutation):
    n = len(permutation)
    return np.arange(2 ** n).reshape([2] * n).transpose(tuple(permutation)).reshape(-1)


def label_preservation(task, hypothesis, n_rows, tolerance=0.0):
    """Recompute task.label_oracle on group-transformed training rows.

    Returns mean abs discrepancy, max discrepancy and violated fraction over
    all (row, transform, target) entries. Rows are TRAINING rows only.
    """
    gens = hypothesis.get("generators") if hypothesis else None
    if not gens:
        raise ValueError("hypothesis with generators required")
    n = int(task.n_qubits)
    perms = closure(gens, n)
    splits = getattr(task, "splits", None) or {}
    mask = splits.get("train")
    rows = np.asarray(task.x)
    if mask is not None:
        rows = rows[np.asarray(mask, dtype=bool)]
    rows = rows[: int(n_rows)]
    if len(rows) == 0:
        raise ValueError("no training rows available")
    y = np.asarray(task.label_oracle(rows), dtype=float)
    if y.ndim == 1:
        y = y[:, None]
    disc = []
    for p in perms:
        yt = np.asarray(task.label_oracle(transform_rows(task, rows, p)),
                        dtype=float)
        if yt.ndim == 1:
            yt = yt[:, None]
        disc.append(np.abs(yt - y))
    disc = np.stack(disc, axis=0)
    return {"group_order": len(perms), "n_rows": int(len(rows)),
            "tolerance": float(tolerance),
            "mean_abs_discrepancy": float(disc.mean()),
            "max_discrepancy": float(disc.max()),
            "violated_fraction": float((disc > tolerance).mean())}


def reynolds_average_predictions(predict, task, x_rows, generators):
    """Inference-time Reynolds average: one predictor call per group element.

    predict(x_rows) -> array aligned with rows. Returns (averaged, group_order).
    """
    n = int(task.n_qubits)
    perms = closure(generators, n)
    x_rows = np.atleast_2d(np.asarray(x_rows))
    acc = None
    for p in perms:
        vals = np.asarray(predict(transform_rows(task, x_rows, p)), dtype=float)
        acc = vals if acc is None else acc + vals
    return acc / len(perms), len(perms)
