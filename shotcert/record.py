"""A6.1: one stochastic predictor per policy -- a calibration record whose expected contrast IS the
deployed-risk difference.

The third review's principal defect, reproduced before repair: the group arm scored
Delta_{2s} = R_{2s}(strat) - R_{2s}(raw) but its record held s identity shots, so the raw baseline was
an s-shot mean and the contrast estimated R_{2s}(strat) - R_s(raw), inflated by sigma_0^2/(2s)
(0.05258 measured on heisenberg_raw_n6 at s=8 against a reported gain of 0.00160).

The repair defines every candidate at a common total S and buys the raw baseline the shots it needs.
The orbit block holds S/G shots at each of the G orbit points, which is exactly what the stratified
policy deploys. The identity circuit appears in that block with only S/G shots, so an additional
block of S - S/G identity shots is collected and combined with it, giving the raw baseline S identity
shots in total. Cost per calibration instance is therefore S(2 - 1/G), which is 3s for G = 2 with
s = S/2 -- the reviewer's bound. The reuse of the first S/G identity outcomes inside the raw baseline
creates within-instance dependence between the two terms of the paired difference; that is permitted
because the Maurer-Pontil certificate needs only boundedness of the paired difference, and it is
stated rather than hidden.

Nothing here may give a policy more shots than its own ledger charges, and audit() checks that claim
against an enumerator written independently of core._estimator_moments.
"""
from __future__ import annotations

import numpy as np

from shotcert.core import born_prob, label_vector, orbit_expectations, shot_var_from_mu
from shotcert.reference import reference_risk_x


def orbit_probs(task, xs):
    return born_prob(np.stack([np.asarray(task.model(a(xs)), dtype=float).reshape(-1)
                               for a in task.group.actions], axis=1))


def record_shape(S, G):
    """(shots per orbit point, extra identity shots) for a common total S."""
    per = S // G
    if per < 1:
        raise ValueError("S=%d cannot fund |G|=%d orbit points" % (S, G))
    return per, S - per


def common_record(task, xs, S, rng):
    """One common-estimand record per instance. Returns a dict of shot means and their sizes."""
    xs = np.atleast_2d(np.asarray(xs, dtype=float))
    P = orbit_probs(task, xs)
    G = P.shape[1]
    per, extra = record_shape(S, G)
    orbit = 2.0 * (rng.binomial(per, P) / float(per)) - 1.0        # (n, G)
    ident_extra = (2.0 * (rng.binomial(extra, P[:, 0]) / float(extra)) - 1.0
                   if extra > 0 else np.zeros(len(xs)))
    return {"orbit": orbit, "per": per, "extra": extra, "ident_extra": ident_extra,
            "S": S, "G": G,
            "cost_per_instance": per * G + extra,
            "shots": int(len(xs) * (per * G + extra))}


def raw_mean_from_record(rec):
    """The S-shot identity mean: the orbit block's identity shots reweighted with the extra block.

    Both blocks are independent +-1 shot means at the same circuit, so their size-weighted sum is the
    mean of S shots, which is what Policy("a0", "raw", S=S) deploys.
    """
    per, extra = rec["per"], rec["extra"]
    tot = per + extra
    if extra == 0:
        return rec["orbit"][:, 0]
    return (per * rec["orbit"][:, 0] + extra * rec["ident_extra"]) / float(tot)


def record_losses(task, menu, rec, y):
    """Loss of every menu policy scored from the common record; each uses exactly its own shots."""
    out = {}
    for pol in menu:
        if pol.mode == "raw":
            z = raw_mean_from_record(rec)
        elif pol.mode == "shrink":
            src = (raw_mean_from_record(rec) if pol.base == "raw"
                   else rec["orbit"][:, :pol.orbit_size].mean(axis=1))
            z = (1.0 - pol.gamma) * src
        elif pol.mode == "stratified":
            z = rec["orbit"][:, :pol.orbit_size].mean(axis=1)
        elif pol.mode == "alloc":
            # The common record holds equal blocks per orbit point, so it cannot supply the unequal
            # per-circuit counts an alloc policy pays for; scoring it from this record would silently
            # hand it a different allocation than its ledger charges.
            raise AssertionError("alloc policies need a per-circuit record, not the common one")
        else:
            raise AssertionError("policy %s (%s) is not common-record compatible"
                                 % (pol.name, pol.mode))
        out[pol.name] = (z - np.asarray(y, dtype=float)) ** 2
    return out


def identity_block_expected_loss(task, pol, xs, shots):
    """E[(mean of `shots` identity shots - y)^2], for auditing a record that under-funds the baseline.

    This is the defective construction the third review identified: scoring the raw baseline from the
    orbit block's S/G identity shots. It is kept so the regression can be asserted numerically instead
    of described.
    """
    xs = np.atleast_2d(np.asarray(xs, dtype=float))
    tot = 0.0
    for x in xs:
        mu = np.asarray(orbit_expectations(task, x), dtype=float)
        sv = np.asarray(shot_var_from_mu(mu), dtype=float)
        y = float(np.asarray(task.label(x), dtype=float).reshape(-1)[0])
        scale = (1.0 - float(pol.gamma)) if pol.mode == "shrink" else 1.0
        tot += (scale * mu[0] - y) ** 2 + (scale ** 2) * float(sv[0]) / float(shots)
    return tot / len(xs)


def record_expected_loss(task, pol, xs, S):
    """E[loss] of the record-based estimator, derived from the record's own linear-combination form.

    Deliberately does not call core._estimator_moments: the audit is worth nothing if both sides read
    the same helper. Mean and variance are built here from block sizes and exact orbit probabilities.
    """
    xs = np.atleast_2d(np.asarray(xs, dtype=float))
    per, extra = record_shape(S, len(task.group.actions))
    if pol.S != S:
        # The record is built for one total. A policy at a different total cannot be scored from it
        # without either under- or over-funding it, which is the defect this module exists to prevent.
        raise ValueError("policy budget %d does not match record budget %d" % (pol.S, S))
    tot = 0.0
    for x in xs:
        mu = np.asarray(orbit_expectations(task, x), dtype=float)
        sv = np.asarray(shot_var_from_mu(mu), dtype=float)
        if pol.mode == "raw":
            m = mu[0]
            v = sv[0] / float(per + extra)                    # S iid shots at the identity circuit
        elif pol.mode == "shrink":
            g = float(pol.gamma)
            if pol.base == "strat":
                m = (1.0 - g) * mu[:pol.orbit_size].mean()
                v = ((1.0 - g) ** 2) * float(np.sum(sv[:pol.orbit_size])) \
                    / (pol.orbit_size ** 2 * per)
            else:
                m = (1.0 - g) * mu[0]
                v = ((1.0 - g) ** 2) * sv[0] / float(per + extra)
        elif pol.mode == "stratified":
            G = pol.orbit_size
            m = mu[:G].mean()
            v = float(np.sum(sv[:G])) / (G * G * per)
        else:
            raise AssertionError("no record form for mode %s" % pol.mode)
        y = float(np.asarray(task.label(x), dtype=float).reshape(-1)[0])
        tot += (m - y) ** 2 + v
    return tot / len(xs)


def audit(task, menu, xs, S, tol=1e-10):
    """Stop gate (a): record expected loss == independent enumeration, per policy.

    Returns per-policy disagreement against reference_risk_x, which enumerates draw sequences and
    binomial outcomes without using the closed-form moments.
    """
    out = {}
    for pol in menu:
        mine = record_expected_loss(task, pol, xs, S)
        ref = float(np.mean([reference_risk_x(task, x, pol) for x in np.atleast_2d(xs)]))
        out[pol.name] = {"record_expected": mine, "enumerated": ref,
                         "abs_diff": abs(mine - ref), "pass": bool(abs(mine - ref) < tol)}
    return out
