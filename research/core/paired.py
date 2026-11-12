"""Paired-inference helpers required by ``research/REVISED_PROTOCOL.md`` section 4.

Every contrast in the revised analyses goes through here so that the same
conventions apply everywhere:

* ``bootstrap_ci``           percentile bootstrap CI of the mean paired difference,
                             resampling *units* (never duplicated rows).
* ``shifted_bootstrap_p``    null-centred ("shifted") bootstrap: resample
                             ``d - mean(d)`` and compare the resampled mean to 0.
                             This is a genuine null-distribution procedure, unlike
                             counting which side of zero ordinary bootstrap means
                             fall on (which the first analysis did and which is not
                             a calibrated test).
* ``signflip_p``             sign-flip test under the explicit assumption that the
                             null distribution of the paired differences is
                             symmetric about 0 (exact for ``n <= 12``, randomised
                             otherwise). Simulated p-values are reported with a
                             floor, never as 0.
* ``cluster_bootstrap_*``    resamples whole clusters (e.g. breaking directions)
                             when the population statement is about clusters.
* ``holm``                   Holm-Bonferroni within a declared family.
* ``loo_range``              leave-one-unit-out range of the mean: the small-sample
                             sensitivity check the protocol requires for primaries.
* ``equivalence``            a CI containing 0 means "not detected"; equivalence is
                             claimed only when the whole CI lies inside the
                             prespecified margin.
"""
import itertools

import numpy as np

P_FLOOR_NOTE = "simulated p-value; report as '< 1/(2 n_flip)', never 0"


def collapse_units(pairs):
    """Drop exact duplicate observations of the same experimental unit.

    ``pairs`` is a sequence of ``(unit_key, value)`` where ``unit_key`` names every
    covariate that defines the unit (the covariates that actually determine the
    target and the fit). Repeats with identical values are collapsed to one; if a
    key appears with *different* values that is a design error and raises.
    """
    out = {}
    for key, value in pairs:
        if key in out:
            if abs(float(out[key]) - float(value)) > 1e-15:
                raise ValueError("unit %r appears with different values (%r, %r); "
                                 "the unit key does not identify the unit"
                                 % (key, out[key], value))
            continue
        out[key] = float(value)
    return out


def bootstrap_ci(diffs, n_boot=20000, seed=0):
    d = np.asarray(diffs, float)
    if d.size == 0:
        return {"n": 0, "mean": None, "ci95_low": None, "ci95_high": None}
    rng = np.random.default_rng(int(seed))
    means = np.empty(int(n_boot))
    for i in range(int(n_boot)):
        means[i] = d[rng.integers(0, d.size, d.size)].mean()
    return {"n": int(d.size), "mean": float(d.mean()),
            "ci95_low": float(np.percentile(means, 2.5)),
            "ci95_high": float(np.percentile(means, 97.5)),
            "n_boot": int(n_boot), "boot_seed": int(seed)}


def shifted_bootstrap_p(diffs, n_boot=20000, seed=0):
    """Two-sided p-value from the null-centred bootstrap."""
    d = np.asarray(diffs, float)
    if d.size < 2 or not np.any(d):
        return {"p": 1.0, "p_floor": None, "n_boot": int(n_boot),
                "method": "shifted bootstrap (degenerate input)"}
    rng = np.random.default_rng(int(seed))
    null = d - d.mean()
    count = 0
    for _ in range(int(n_boot)):
        if abs(null[rng.integers(0, d.size, d.size)].mean()) >= abs(d.mean()):
            count += 1
    p_raw = (count + 1.0) / (int(n_boot) + 1.0)
    floor = 1.0 / (int(n_boot) + 1.0)
    return {"p": float(min(1.0, p_raw)), "p_floor": float(floor),
            "p_reported": ("< %.4g" % floor) if p_raw <= floor else None,
            "n_boot": int(n_boot), "method": "null-centred (shifted) bootstrap"}


def signflip_p(diffs, n_boot=200000, seed=0):
    """Sign-flip test; assumes symmetry of the null distribution about 0."""
    d = np.asarray(diffs, float)
    n = d.size
    if n == 0 or not np.any(d):
        return {"p": 1.0, "exact": False, "n_flip": 0,
                "assumption": "null distribution of paired differences symmetric about 0"}
    observed = abs(d.mean())
    if n <= 12:
        count = 0
        total = 0
        for signs in itertools.product((1.0, -1.0), repeat=n):
            total += 1
            if abs(np.dot(signs, d) / n) >= observed - 1e-15:
                count += 1
        return {"p": float(min(1.0, count / total)), "exact": True, "n_flip": total,
                "assumption": "null distribution of paired differences symmetric about 0"}
    rng = np.random.default_rng(int(seed))
    count = 0
    for _ in range(int(n_boot)):
        signs = np.where(rng.integers(0, 2, n) == 0, 1.0, -1.0)
        if abs(np.dot(signs, d) / n) >= observed - 1e-15:
            count += 1
    floor = 1.0 / (int(n_boot) + 1.0)
    p_raw = (count + 1.0) / (int(n_boot) + 1.0)
    return {"p": float(min(1.0, p_raw)), "p_floor": float(floor),
            "p_reported": ("< %.4g" % floor) if p_raw <= floor else None,
            "exact": False, "n_flip": int(n_boot), "seed": int(seed),
            "assumption": "null distribution of paired differences symmetric about 0"}


def cluster_bootstrap_ci(values_by_cluster, n_boot=20000, seed=0):
    """Resample whole clusters (e.g. breaking directions) for cluster-level claims."""
    keys = sorted(values_by_cluster)
    arrs = [np.asarray(values_by_cluster[k], float) for k in keys]
    if not keys:
        return {"n_clusters": 0, "mean": None}
    rng = np.random.default_rng(int(seed))
    overall = float(np.concatenate(arrs).mean())
    means = np.empty(int(n_boot))
    for i in range(int(n_boot)):
        pick = rng.integers(0, len(keys), len(keys))
        means[i] = np.concatenate([arrs[j] for j in pick]).mean()
    return {"n_clusters": len(keys), "mean": overall,
            "ci95_low": float(np.percentile(means, 2.5)),
            "ci95_high": float(np.percentile(means, 97.5)),
            "caveat": "cluster bootstrap over %d clusters supports only a "
                      "within-benchmark statement about these clusters" % len(keys)}


def holm(pvals):
    p = np.asarray(pvals, float)
    m = p.size
    order = np.argsort(p)
    adj = np.zeros(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * p[idx])
        adj[idx] = min(1.0, running)
    return [float(a) for a in adj]


def loo_range(diffs):
    d = np.asarray(diffs, float)
    if d.size < 2:
        return {"loo_min": None, "loo_max": None}
    m = (d.sum() - d) / (d.size - 1)
    return {"loo_min": float(m.min()), "loo_max": float(m.max())}


def equivalence(ci_low, ci_high, margin):
    """Only a CI entirely inside +/-margin supports practical equivalence."""
    if ci_low is None or margin is None:
        return {"equivalent": None, "margin": margin}
    inside = (ci_low > -margin) and (ci_high < margin)
    return {"equivalent": bool(inside), "margin": float(margin),
            "wording": "practically equivalent within +/-%.5g" % margin if inside
            else "not detected (CI includes 0)" if ci_low <= 0 <= ci_high
            else "detected difference"}


def verdict(ci_low, ci_high, margin=None, p_adjusted=None, alpha=0.05,
            lower_is_better=True):
    """Protocol verdicts with the metric direction and the adjusted test attached.

    The contrast is always ``a - b``.  For a *lower-is-better* metric (risk) a wholly
    positive interval means **a is worse**; the earlier wording said "b worse", which
    reversed the reading of every positive repair contrast (REVIEW_ROUND2 6).

    A raw-CI direction is not a protocol verdict when a multiplicity-adjusted p-value is
    supplied and does not clear ``alpha``: that case is reported as a downgraded verdict so
    a generated table cannot print a discovery the adjusted test does not support.
    """
    if ci_low is None:
        return "no data"
    inside_margin = (margin is not None and ci_low > -margin and ci_high < margin)
    if inside_margin:
        # Equivalence is supported by the CI sitting inside the prespecified margin; a
        # significant difference test is not required for it and would be contradictory.
        return "practically equivalent within +/-%.5g" % margin
    if ci_low > 0 or ci_high < 0:
        if p_adjusted is not None and p_adjusted > alpha:
            return ("difference not detected after multiplicity adjustment "
                    "(adjusted p > %.2g; raw CI excludes 0 but is not a protocol verdict)"
                    % alpha)
        if ci_low > 0:
            return "%s worse (raw CI excludes 0 on the positive side)" % (
                "a" if lower_is_better else "b")
        return "%s better (raw CI excludes 0 on the negative side)" % (
            "a" if lower_is_better else "b")
    return "difference not detected (CI includes 0; NOT evidence of no effect)"


def crossed_bootstrap_ci(cell_matrix, n_boot=20000, seed=0):
    """Estimand E-C: resample seeds outside *and* directions inside.

    ``cell_matrix`` is ``(n_seeds, n_directions)``.  Both replication sources are treated as
    random, which is the only interval that exposes the joint dependence.

    It is **not** wider by construction: no ordering between a crossed-resampling interval
    and a single-cluster interval holds for arbitrary data, and an earlier docstring here
    asserted one.  In this design the crossed interval happened to be the widest, and that
    observed ordering is reported as a sensitivity result (Addendum A5.1, corrected by the
    third-round review), never as a theorem.
    """
    m = np.atleast_2d(np.asarray(cell_matrix, float))
    n_seed, n_dir = m.shape
    rng = np.random.default_rng(int(seed))
    means = np.empty(int(n_boot))
    for i in range(int(n_boot)):
        rows = rng.integers(0, n_seed, n_seed)
        cols = rng.integers(0, n_dir, n_dir)
        means[i] = m[np.ix_(rows, cols)].mean()
    return {"n_seeds": int(n_seed), "n_directions": int(n_dir),
            "mean": float(m.mean()),
            "ci95_low": float(np.percentile(means, 2.5)),
            "ci95_high": float(np.percentile(means, 97.5)),
            "estimand": "E-C: generalise over directions and optimiser seeds jointly",
            "caveat": "conditions on one dataset and one task family"}


def seed_vector_bootstrap_ci(cell_matrix, n_boot=20000, seed=0):
    """Estimand E-A: average directions within each seed, then resample seed vectors.

    Correct when the direction set is fixed (it is: the 8 frozen breaking directions) and the
    claim is about optimiser randomness.  Units are seeds, not cells.
    """
    m = np.atleast_2d(np.asarray(cell_matrix, float))
    v = m.mean(axis=1)
    return bootstrap_ci(v, n_boot=n_boot, seed=seed) | {
        "estimand": "E-A: fixed direction set, generalise over optimiser seeds",
        "n_units": int(v.size)}


def wilson_ci(k, n, z=1.959963984540054):
    """Wilson 95% interval for a rate with an explicit denominator."""
    n = int(n)
    if n == 0:
        return {"k": int(k), "n": 0, "rate": None, "ci95_low": None, "ci95_high": None}
    p = float(k) / n
    d = 1.0 + z * z / n
    c = p + z * z / (2 * n)
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return {"k": int(k), "n": n, "rate": p,
            "ci95_low": float((c - h) / d), "ci95_high": float((c + h) / d)}
