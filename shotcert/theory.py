"""A5: when do symmetry measurements repay their cost? Closed-form answer for the mixture family.

The exact deployed risk of this study's policies is
    R_S(a) = D_a + Sigma_a / S
with D the integrated squared discrepancy and Sigma the shot-variance coefficient, verified against an
independent enumeration of the predictor to <1e-12. For the mixture family that is enough to solve the
allocation problem in closed form, which is what this module does.

Write the mixture-w predictor's mean as mu_0 + w*(mubar - mu_0), where mu_0 is the raw response and
mubar the orbit average. Define, all expectations over the input distribution,
    A   = E[(mubar - mu_0)^2]                    > 0 unless symmetrisation is a no-op
    B   = E[(mu_0 - y)(mubar - mu_0)]
    dD  = D_0 - D_G = -2B - A                    the ideal-predictor gain from symmetrisation
    V   = sigmabar^2 - sigma_0^2                 the shot-variance COST of symmetrisation
where sigmabar^2 is the orbit-mean shot variance and sigma_0^2 the raw one.

The mixture at weight w spends wS shots split over the G orbit points and (1-w)S shots on raw, so its
estimator variance is  [w*sigmabar^2 + (1-w)*sigma_0^2] / S  -- linear in w -- and its discrepancy is
D_0 + 2wB + w^2 A, a convex quadratic. Hence

    R_S(w) = D_0 + sigma_0^2/S + 2wB + w^2 A + wV/S,           R''(w) = 2A > 0,

strictly convex with unique unconstrained minimiser

    w*(S) = (dD + A)/(2A)  -  V/(2 A S).

Consequences, each of which is checked numerically in test_theory.py and on the physical tasks:
  * Symmetry is a LUXURY GOOD when V > 0: dw*/dS = V/(2 A S^2) > 0, and below the critical budget
        S_on = V / (dD + A)
    the optimal weight is zero -- no symmetry measurement is worth buying at all.
  * Full symmetrisation is optimal only above
        S_full = V / (dD - A)      (requires dD > A and V > 0),
    so partial symmetrisation occupies an explicit intermediate band, which is what the physical-task
    risk tables showed empirically before this derivation existed.
  * When V <= 0 symmetrisation also reduces shot variance, and w* > 0 at every budget: the repayment
    question has no threshold, and w* decreases toward its ideal-predictor limit (dD+A)/(2A) as S grows.
"""
from __future__ import annotations

import math

import numpy as np

from shotcert.core import orbit_expectations, shot_var_from_mu


def coefficients(task, xs):
    """(A, B, dD, V, D0, sig0) measured on an input set -- all estimable from calibration shots."""
    A = B = D0 = DG = s0 = sbar = 0.0
    n = 0
    for x in np.atleast_2d(np.asarray(xs, dtype=float)):
        mu = np.asarray(orbit_expectations(task, x), dtype=float)
        y = float(np.asarray(task.label(x), dtype=float).reshape(-1)[0])
        sv = np.asarray(shot_var_from_mu(mu), dtype=float)
        m0, mb = float(mu[0]), float(mu.mean())
        A += (mb - m0) ** 2
        B += (m0 - y) * (mb - m0)
        D0 += (m0 - y) ** 2
        DG += (mb - y) ** 2
        s0 += float(sv[0])
        sbar += float(sv.mean())
        n += 1
    A, B, D0, DG, s0, sbar = A / n, B / n, D0 / n, DG / n, s0 / n, sbar / n
    return {"A": A, "B": B, "dD": D0 - DG, "V": sbar - s0, "D0": D0, "sigma0": s0,
            "sigmabar": sbar, "DG": DG}


def w_star(c, S):
    """Optimal symmetrisation weight at total shot budget S, clipped to [0, 1]."""
    A, V = c["A"], c["V"]
    if A <= 0.0:
        return 0.0
    return min(max((c["dD"] + A) / (2.0 * A) - V / (2.0 * A * S), 0.0), 1.0)


def thresholds(c):
    """(S_on, S_full): the budgets at which symmetry starts paying and pays fully. inf = never."""
    A, V, dD = c["A"], c["V"], c["dD"]
    if A <= 0.0:
        return (math.inf, math.inf)
    s_on = V / (dD + A) if (V > 0.0 and dD + A > 0.0) else 0.0
    s_full = V / (dD - A) if (V > 0.0 and dD - A > 0.0) else (0.0 if V <= 0.0 else math.inf)
    return (max(s_on, 0.0), max(s_full, 0.0))


def risk_theory(c, w, S):
    """Closed-form deployed risk of the w-mixture at budget S."""
    return (c["D0"] + c["sigma0"] / S + 2.0 * w * c["B"] + (w ** 2) * c["A"] + w * c["V"] / S)


# ---- A6.5: the orbit variance profile sets how much symmetrisation can recover -------------------

def sigma_profile(task, xs):
    """(G,) array of per-orbit-point shot standard deviations, averaged over instances.

    sigma_g^2 = 1 - mu_g^2 for a +-1 shot, so this is a property of the orbit's response functions and
    is estimable from the same shots that estimate the means.
    """
    acc = None
    for x in np.atleast_2d(np.asarray(xs, dtype=float)):
        mu = np.asarray(orbit_expectations(task, x), dtype=float)
        sv = np.asarray(shot_var_from_mu(mu), dtype=float)
        acc = sv if acc is None else acc + sv
    return np.sqrt(acc / len(np.atleast_2d(xs)))


def neyman_alloc(sigmas, S):
    """Integer shot allocation over the orbit minimising the averaged estimator's variance.

    Minimising sum_g sigma_g^2 / n_g subject to sum_g n_g = S gives n_g proportional to sigma_g, and
    the resulting variance coefficient is (mean_g sigma_g)^2 instead of mean_g sigma_g^2. Every point
    must receive at least one shot, so at small S the allocation is clipped and the bound is not
    attained exactly; the shortfall is reported rather than smoothed away.
    """
    sig = np.asarray(sigmas, dtype=float)
    G = len(sig)
    if S < G:
        return None
    raw = sig / sig.sum() * S
    n = np.maximum(np.floor(raw).astype(int), 1)
    while n.sum() > S:                                  # never exceed the budget
        n[int(np.argmax(n))] -= 1
    while n.sum() < S:                                  # spend the whole budget
        n[int(np.argmin(raw - n))] += 1
    return tuple(int(v) for v in n)


def dispersion(sigmas):
    """Var_g(sigma_g): exactly the shot-variance coefficient that Neyman allocation recovers."""
    sig = np.asarray(sigmas, dtype=float)
    return float(np.mean(sig ** 2) - np.mean(sig) ** 2)
