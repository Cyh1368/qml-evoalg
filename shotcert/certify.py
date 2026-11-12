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

# Squared losses lie in [0,4], but the CALIBRATION QUANTITY is a difference of two squared losses,
# so it lies in [-4,+4]: the interval width entering the range term is 8, not 4. Conflating the
# loss range with the contrast range was one of two errors in the original bound.
CONTRAST_LO, CONTRAST_HI = -4.0, 4.0
CONTRAST_WIDTH = CONTRAST_HI - CONTRAST_LO      # 8.0
LOSS_RANGE = 4.0        # kept for the (unused) single-loss range


def mp_bound(D, delta, menu_size=1):
    """One-sided simultaneous Maurer-Pontil bound (Corollary 5) for contrasts in [a, b].

    For D_1..D_n i.i.d. in [a,b], with V the sample variance, with probability >= 1-delta
    simultaneously over all `menu_size` candidates:

        E[D] <= mean + sqrt(2 V ln / n) + 7 (b-a) ln / (3 (n-1)),   ln = log(2 m / delta).

    Two things the first version of this file got wrong, both found by review. (i) The logarithm
    must GROW with the number of candidates and must not contain 1/n: the old log(RANGE/(delta*n))
    shrank with n and went negative past n > RANGE/delta, producing a negative "range term", which
    is not a confidence radius at all. (ii) The range is the CONTRAST width 8, not the loss width 4.
    Scaling from the [0,1] statement: the sqrt term picks up no (b-a) factor because (b-a)^2 cancels
    against the rescaled variance, while the linear term picks up exactly one.
    """
    D = np.asarray(D, dtype=float)
    n = len(D)
    if n < 3:
        return float("inf")
    m = max(int(menu_size), 1)
    ln = math.log(2.0 * m / delta) if delta > 0 else float("inf")
    mean = float(np.mean(D))
    var = max(float(np.var(D, ddof=1)), 0.0)
    return mean + math.sqrt(2.0 * var * ln / n)         + 7.0 * CONTRAST_WIDTH * ln / (3.0 * (n - 1))


def eb_bound_broken(D, delta):
    """The original, invalid bound. Retained ONLY so the withdrawal is reproducible.

    log(LOSS_RANGE/(delta*n)) is not a confidence radius: it decreases with n, can be negative, and
    uses the loss width where the contrast width belongs. Do not use it for any claim.
    """
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


BOUND = {"mp": mp_bound, "normal": normal_bound, "eb_broken": eb_bound_broken}


@dataclass
class Decision:
    status: str            # "selected" | "fallback" | "unsupported"
    chosen: object
    bounds: dict
    reason: str = ""


def certify(cal_losses, menu, a0_name, eps, delta, min_support=0, bound="mp"):
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
        # mp_bound takes the FULL delta and the menu size, and pays for multiplicity inside the
        # logarithm as log(2m/delta). The old call passed delta/m to a bound whose log already
        # divided by n, so multiplicity was charged twice in the wrong direction.
        bounds[name] = (fn(D, delta, menu_size=m) if bound == "mp" else fn(D, delta / m))
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


def calib_ledger(menu, n_instances, n_switches=None):
    """A2.2: what a calibration run actually costs, per unit of the five-part ledger.

    The first version labelled n*S the calibration budget while calibration_losses() evaluated the
    whole menu on every instance, which is n * sum_p shots_used(p) = n*S*m shots. The frontier was
    therefore not at a matched total budget. Preparations are counted per shot-batch executed, since
    every repeated shot needs a fresh physical state copy even when the classical input is shared.

    A3.2 corrections. (i) Preparations equal shots: the access model is scalar single-copy
    measurement, so every destructive shot consumes a freshly prepared state; counting one
    preparation per policy *batch* (400 preparations for 3,200 shots) contradicted this function's own
    docstring. (ii) Compilations are the DISTINCT circuits across the menu, not the sum over
    policies: a two-element group compiles two circuits, not twelve. (iii) Switches come from the
    schedule actually executed, which for a shared-record calibration pass is one circuit change per
    additional distinct circuit per instance.
    """
    circuits = set()
    for p in menu:
        circuits |= set(p.circuit_ids)
    n_circ = max(len(circuits), 1)
    shots_per_instance = sum(p.shots_used for p in menu)
    shared_shots_per_instance = n_circ * max((p.shots_used for p in menu), default=0)
    return {"instances": int(n_instances),
            "distinct_circuits": int(n_circ),
            "shots_per_instance_all_policies": int(shots_per_instance),
            "shots_total": int(shots_per_instance) * int(n_instances),
            "preparations_total": int(shots_per_instance) * int(n_instances),
            "shared_shots_total": int(shared_shots_per_instance) * int(n_instances),
            "shared_preparations_total": int(shared_shots_per_instance) * int(n_instances),
            "switches_total": int(max(n_circ - 1, 0)) * int(n_instances),
            "policies": len(menu),
            "compilations": int(n_circ),
            "preparation_convention": "one physical state copy per destructive single-copy shot"}


def wilson(k, n, z=1.96):
    """Wilson interval for a rate estimated over n Monte-Carlo repetitions.

    Coverage and power are themselves estimates; quoting 0.000 without an interval over 400 reps is
    how the first version overstated a null.
    """
    if n == 0:
        return (float("nan"), float("nan"))
    p = min(max(k / n, 0.0), 1.0)
    d = 1.0 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


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


def calibration_losses_fast(task, menu, xs, rng):
    """Same contract as calibration_losses(), vectorised over instances.

    The paired structure is preserved exactly: every policy sees the same instances and labels, and
    each policy's shots are drawn independently. Only the loop order changed. This exists because the
    A2.6 sweep needs ~1e5 calibration trials, and the per-instance loop made that a day-long job.
    """
    from shotcert.core import born_prob
    P = born_prob(np.stack([np.asarray(task.model(a(xs)), dtype=float).reshape(-1)
                            for a in task.group.actions], axis=1))   # (n, G)
    y = label_vector(task, xs)
    n, G = P.shape
    out = {}
    for pol in menu:
        if pol.mode == "raw":
            z = 2.0 * (rng.binomial(pol.S, P[:, 0]) / pol.S) - 1.0
        elif pol.mode == "shrink":
            z = (1.0 - pol.gamma) * (2.0 * (rng.binomial(pol.S, P[:, 0]) / pol.S) - 1.0)
        elif pol.mode == "stratified":
            per = pol.S // G
            acc = np.zeros(n)
            for g in range(G):
                acc += 2.0 * (rng.binomial(per, P[:, g]) / per) - 1.0
            z = acc / G
        elif pol.mode == "mix":
            S_a = max(int(round(pol.w * pol.S)), 0)
            S_0 = max(pol.S - S_a, 0)
            per = S_a // G
            if pol.w == 0.0:
                z = 2.0 * (rng.binomial(pol.S, P[:, 0]) / pol.S) - 1.0
            else:
                acc = np.zeros(n)
                for g in range(G):
                    acc += 2.0 * (rng.binomial(per, P[:, g]) / per) - 1.0
                z_a = acc / G
                if pol.w >= 1.0:
                    z = z_a
                else:
                    z = pol.w * z_a + (1 - pol.w) * (
                        2.0 * (rng.binomial(S_0, P[:, 0]) / S_0) - 1.0)
        else:                                          # orbit_k
            per = pol.S // pol.k
            idx = rng.integers(0, G, size=(n, pol.k))
            acc = np.zeros(n)
            for j in range(pol.k):
                pg = P[np.arange(n), idx[:, j]]
                acc += 2.0 * (rng.binomial(per, pg) / per) - 1.0
            z = acc / pol.k
        out[pol.name] = (z - y) ** 2
    return out


def n_required_mp(gap, menu_size, delta=0.05, tol=1e-4, var_hint=0.01):
    """Smallest n at which the corrected simultaneous MP bound can close a gap of this size.

    Closed form, because simulating the answer would be slow and would obscure the point: the range
    term 7(b-a)ln/(3(n-1)) with b-a = 8 and ln = log(2m/delta) decays as 1/n, so certifying a gap of
    0.008 needs tens of thousands of labelled preparations no matter how the shots are allocated.
    var_hint is the contrast variance used in the sqrt term; the result is dominated by the range
    term and is insensitive to it here, which is itself the finding.
    """
    ln = math.log(2.0 * max(int(menu_size), 1) / delta)
    n = 2
    while n < 10 ** 9:
        r = math.sqrt(2.0 * var_hint * ln / n) + 7.0 * CONTRAST_WIDTH * ln / (3.0 * (n - 1))
        if r <= abs(gap) + tol:
            return n
        n = int(n * 1.15) + 1
    return None


def true_delta(task, menu, xs, a0_name):
    """Ground-truth R_S(a) - R_S(a0) on the evaluation inputs, used only to score decisions."""
    from shotcert.core import exact_risk
    base = exact_risk(task, [p for p in menu if p.name == a0_name][0], xs)
    return {p.name: exact_risk(task, p, xs) - base for p in menu if p.name != a0_name}
