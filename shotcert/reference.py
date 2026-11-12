"""A2.4: an independently implemented reference risk, by explicit enumeration.

Why this file exists. `exact_risk()` and `components()` both obtain their estimator moments from
`_estimator_moments()`, so their agreement to 1e-17 shows that two related code paths implement the
same algebra. It does not show that the algebra describes the predictor. The manuscript called that
agreement a "brute-force enumeration"; it was not one.

This file enumerates the predictor itself. For each input it walks every group-draw sequence (through
its multinomial count vector) and, for each, every combination of binomial success counts across the
orbit points, and sums P(path) * (Z(path) - y)^2 with `scipy.stats.binom.pmf`. It shares only the
task's orbit expectations with the tested code; no moment formula from `core.py` is used. It is
therefore slow and restricted to small (S, k), which is the right trade for a verification test.
"""
from __future__ import annotations

import itertools

import numpy as np
from scipy.stats import binom

from shotcert.core import label_vector, orbit_expectations


def _compositions(total, parts):
    """All tuples of `parts` nonnegative integers summing to `total`."""
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in _compositions(total - first, parts - 1):
            yield (first,) + rest


def _mean_grid(shots_per_group):
    """(sample mean, probability) for every combination of shot outcomes, one axis per group.

    The readout is +-1 with mean mu, NOT a 0/1 indicator: a count of j "+1" outcomes out of s shots
    has sample mean (2j - s)/s and j ~ Binom(s, (1+mu)/2). Passing mu straight to binom.pmf as a
    probability was the first bug in this file and produced nan for any |mu| near 1.
    """
    axes = []
    for s, mu in shots_per_group:
        if s == 0:
            axes.append([(0.0, 1.0)])          # no shots: contributes nothing, weight handled outside
            continue
        p = min(max(0.5 * (1.0 + float(mu)), 0.0), 1.0)
        k = np.arange(s + 1)
        axes.append(list(zip(((2.0 * k - s) / s).tolist(), binom.pmf(k, s, p).tolist())))
    for combo in itertools.product(*axes):
        yield [c[0] for c in combo], float(np.prod([c[1] for c in combo]))


def reference_risk_x(task, x, pol):
    """E[(Z_a(x) - y)^2] by enumeration over group draws and binomial shot outcomes."""
    mu = np.asarray(orbit_expectations(task, x), dtype=float)
    y = float(np.asarray(task.label(x), dtype=float).reshape(-1)[0])
    G = len(mu)
    tot = 0.0

    if pol.mode == "shrink" and pol.base == "strat":
        # A6.3: shrinkage applied to the ORBIT average rather than to the raw estimate. Enumerated
        # from first principles -- equal averaging of G independent per-circuit means, S/G shots each,
        # then scaled. The audit failed loudly when this branch was missing, which is the point.
        scale = 1.0 - float(pol.gamma)
        per = pol.S // G
        for means, pr in _mean_grid([(per, mu[g]) for g in range(G)]):
            tot += pr * (scale * float(np.mean(means)) - y) ** 2
        return tot

    if pol.mode in ("raw", "shrink"):
        # shrink is raw scaled by (1 - gamma) toward the declared constant 0.0; the enumeration is
        # the same, with the scale applied to the sample mean. Without this branch a shrink policy
        # fell through to the orbit_k path below and returned an unrelated number, which is how the
        # first run of this test caught it.
        scale = 1.0 - float(pol.gamma) if pol.mode == "shrink" else 1.0
        for means, pr in _mean_grid([(pol.S, mu[0])]):
            tot += pr * (scale * means[0] - y) ** 2
        return tot

    if pol.mode == "alloc":
        # A6.5: unequal per-circuit shot counts, equal averaging weights.
        n = [int(v) for v in pol.alloc]
        for means, pr in _mean_grid([(n[g], mu[g]) for g in range(G)]):
            tot += pr * (float(np.mean(means)) - y) ** 2
        return tot

    if pol.mode == "stratified":
        per = pol.S // G
        for means, pr in _mean_grid([(per, mu[g]) for g in range(G)]):
            z = float(np.mean(means))
            tot += pr * (z - y) ** 2
        return tot

    if pol.mode == "mix":
        S_a = max(int(round(pol.w * pol.S)), 0)
        S_0 = max(pol.S - S_a, 0)
        per = S_a // G
        # A branch with no shots contributes no randomness; its weight is carried but its sample
        # mean is degenerate at 0 only when the policy is infeasible, which the caller filters.
        grid = [(per if pol.w > 0.0 else 0, mu[g]) for g in range(G)] + [(S_0, mu[0])]
        for means, pr in _mean_grid(grid):
            orbit_mean = float(np.mean(means[:G])) if pol.w > 0.0 else 0.0
            raw_mean = means[G] if pol.w < 1.0 else 0.0
            z = pol.w * orbit_mean + (1.0 - pol.w) * raw_mean
            tot += pr * (z - y) ** 2
        return tot

    # orbit_k: k draws with replacement from the orbit, S//k shots per draw, equal weights.
    # Z depends on the draw sequence only through the count vector n_1..n_G, so the multinomial
    # over count vectors is the exact draw distribution; per-draw shot counts are per * n_g.
    per = pol.S // pol.k
    from math import factorial as fact
    for counts in _compositions(pol.k, G):
        mult = fact(pol.k)
        for c in counts:
            mult //= fact(c)
        p_draw = mult * (1.0 / G) ** pol.k
        grid = [(per * c, mu[g]) for g, c in enumerate(counts)]
        for means, pr in _mean_grid(grid):
            z = sum((counts[g] / pol.k) * means[g] for g in range(G))
            tot += p_draw * pr * (z - y) ** 2
    return tot


def reference_risk(task, pol, xs):
    """Mean over inputs of the enumerated risk. xs is an input set, as for exact_risk."""
    xs = np.atleast_2d(np.asarray(xs, dtype=float))
    return float(np.mean([reference_risk_x(task, x, pol) for x in xs]))
