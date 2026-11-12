"""Paired finite-shot certification of a symmetry-spending policy.

Setting: n independent labeled preparations. For each calibration instance we deploy the candidate
policy and the raw baseline a0 on the *same* instance with paired shots and record
D = (Z_a - Y)^2 - (Z_a0 - Y)^2. Both Z are random, so D carries the deployment noise of both
predictors: that noise is not an estimation nuisance to be averaged away by taking more shots, it is
part of what makes certification expensive, and symmetry reduces it.

The certificate is an empirical-Bernstein upper bound on E[D] (variance-adaptive, explicit range),
which is deliberately ordinary: the contribution of this study is not a new concentration
inequality. What is specific is *what* is being bounded — a difference of two allocation-dependent
risks of stochastic deployed predictors, selected with the same finite-shot data that defines them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from shotcert.core import Policy, born_prob, label_vector, orbit_prob_matrix, predict_batch

LOSS_RANGE = 4.0        # outcomes and labels both lie in [-1, 1], so squared loss lies in [0, 4]


def eb_bound(D, delta):
    """One-sided empirical-Bernstein upper bound on E[D] (Maurer-Pontil form).

    Returns ub with Pr[E[D] > ub] >= 1 - delta for a fixed contrast. The multiplicity correction over
    the policy menu is applied by the caller, which splits delta across candidates.
    """
    D = np.asarray(D, dtype=float)
    n = len(D)
    if n < 2:
        return float("inf")
    m = float(np.mean(D))
    v = float(np.var(D, ddof=1))
    ln = math.log(LOSS_RANGE / (delta * n)) if delta * n > 0 else float("inf")
    # (b-a)/2 * sqrt(2 v ln / n) + 7(b-a) ln / (3(n-1))  with b-a = LOSS_RANGE
    return m + (LOSS_RANGE / 2.0) * math.sqrt(max(2.0 * v * ln / n, 0.0)) \
        + 7.0 * LOSS_RANGE * ln / (3.0 * (n - 1))


def normal_bound(D, delta):
    """One-sided Studentised upper bound on E[D].

    NOT distribution-free: its validity at a given n is an empirical question, which is exactly why
    this study measures its violation rate instead of trusting it. It is included because the
    empirical-Bernstein range term 7(b-a)ln/(3(n-1)) is enormous at small n, so a frontier located
    with EB alone could be a property of the inequality rather than of the problem.
    """
    import math
    D = np.asarray(D, dtype=float)
    n = len(D)
    if n < 3:
        return float("inf")
    m = float(np.mean(D))
    se = math.sqrt(max(float(np.var(D, ddof=1)), 0.0) / n)
    z = {0.10: 1.2816, 0.05: 1.6449, 0.025: 1.9600, 0.01: 2.3263, 0.005: 2.5758}.get(
        round(delta, 4), math.sqrt(2.0) * _erfcinv(2.0 * delta))
    return m + z * se


def _erfcinv(p):
    from scipy.special import erfcinv          # type: ignore
    return float(erfcinv(p))


BOUND = {"eb": eb_bound, "normal": normal_bound}


@dataclass
class Decision:
    status: str            # "selected" | "fallback" | "unsupported"
    chosen: object
    bounds: dict
    reason: str = ""


def certify(cal_losses, menu, a0_name, eps, delta, min_support=0, bound="eb"):
    """Pick the best policy whose risk difference against a0 is certified within eps.

    cal_losses[policy] is an array over calibration instances of (Z_policy - Y)^2. Paired against
    a0 by construction (same instances, same order). A policy is *certified within eps* when the
    one-sided upper bound on E[D] is <= eps; eps > 0 is declared in advance, so clearing it with
    eps <= 0 would be a claim of strict improvement rather than of non-degradation.

    min_support implements protocol rule 1: when fewer than min_support instances contributed a
    nonzero contrast the answer is "unsupported", never "no admissible policy". Empty evidence and
    evidence of failure are different statements.
    """
    base = cal_losses[a0_name]
    n = len(base)
    names = [k for k in cal_losses if k != a0_name]
    m = max(len(names), 1)
    fn = BOUND[bound]
    bounds = {}
    for name in names:
        D = np.asarray(cal_losses[name], dtype=float) - np.asarray(base, dtype=float)
        bounds[name] = fn(D, delta / m)
    if min_support > 0:
        nz = sum(1 for name, L in cal_losses.items()
                 if name != a0_name and np.any(np.abs(np.asarray(L) - np.asarray(base)) > 0))
        if nz < min_support:
            return Decision("unsupported", a0_name, bounds,
                            "only %d/%d candidates produced any contrast on %d instances"
                            % (nz, m, n))
    ok = {k: v for k, v in bounds.items() if v <= eps}
    if not ok:
        return Decision("fallback", a0_name, bounds,
                        "no candidate certified within eps=%.4g; best bound %.4g"
                        % (eps, min(bounds.values()) if bounds else float("nan")))
    chosen = min(sorted(ok), key=lambda k: ok[k])
    return Decision("selected", chosen, bounds, "certified within eps=%.4g" % eps)


def calibration_losses(task, menu, xs, rng):
    """Paired deployed losses on calibration instances: {policy_name: (n,) squared losses}.

    One deployment per policy per instance. Shots are drawn independently across policies (they are
    different circuits) but the instance and label are shared, which is what makes the contrast
    paired and is the reason the bound is variance-adaptive rather than range-based.
    """
    y = label_vector(task, xs)
    out = {}
    for pol in menu:
        Z = predict_batch(task, xs, pol, rng, reps=1)[0]
        out[pol.name] = (Z - y) ** 2
    return out


def true_delta(task, menu, xs, a0_name):
    """Ground-truth R_S(a) - R_S(a0) on the evaluation inputs, used only to score decisions."""
    from shotcert.core import exact_risk
    base = exact_risk(task, [p for p in menu if p.name == a0_name][0], xs)
    return {p.name: exact_risk(task, p, xs) - base for p in menu if p.name != a0_name}
