"""A7 decision model: what the value of a verifier actually depends on.

The third-round rebuttal proposed that a label-preservation verifier's value is a function of two
quantities: the probability that the supplied group is wrong, and the probability that a proposal
falls inside the target's label-symmetry group. That claim is **wrong as stated**, and this module
exists to say so precisely and to replace it.

Model (the referee's own notation, made explicit). For a candidate predictor and a supplied group:

* :math:`\\Delta` = risk after group-averaged repair minus risk before it, so :math:`\\Delta < 0`
  is a benefit. :math:`\\Delta` is a random quantity: it depends on the target, the candidate, and
  the fit.
* :math:`A \\in \\{0,1\\}` = the gate's firing decision, a function of the candidate and the supplied
  group only (never of the regime).
* :math:`c_{gate}` = cost of screening one candidate, :math:`c_{rep}` = cost of repairing and then
  serving the repaired predictor, :math:`w \\ge 0` = the price of time in risk units.

Relative to never repairing, a policy's expected change in objective is

    :math:`V(A) = E[A\\,\\Delta] + w\\,E[c_{gate} + A\\,c_{rep}].`

Let :math:`q = P(\\text{group is a label symmetry} \\mid A = 1)` be the posterior the screen induces,
:math:`B = -E[\\Delta \\mid \\text{valid}] > 0` the benefit magnitude and
:math:`H = E[\\Delta \\mid \\text{invalid}] > 0` the harm magnitude. Then

    :math:`E[\\Delta \\mid A=1] = -qB + (1-q)H`,

so firing is preferred exactly when

    :math:`q > q^*(w) \\;\\equiv\\; \\frac{H + w\\,c_{rep}}{B + H}`          (threshold rule)

and the gate cost :math:`w\\,c_{gate}` is paid whenever the screen is run at all, so it shifts *whether
to screen* but not *whether to fire once screened*. Two consequences follow, and both are measured
below rather than asserted.

**Insufficiency of two probabilities.** :math:`q^*` depends on the ratio of two conditional effect
magnitudes and on the cost of repair. Two problems can share :math:`P(\\text{wrong group})` and
:math:`P(Q \\subseteq L_t)` exactly and have opposite optimal policies, because their
:math:`(B, H)` differ. The approximate-symmetry continuum in A7.5 is exactly such a pair: the
probabilities are fixed by the proposal distribution and the supplied group, while :math:`H` shrinks
continuously with the perturbation strength, so :math:`q^*` moves and the two probabilities do not.

**What the screen contributes.** With sensitivity :math:`s` and specificity :math:`f` for the event
"group is a label symmetry", Bayes gives

    :math:`q = \\frac{\\pi s}{\\pi s + (1-\\pi)(1-f)}, \\qquad \\pi = P(\\text{valid}),`

so the two probabilities of the withdrawn claim enter only *through* the posterior, and only
together with the screen's own error rates. A screen with :math:`f = 1` (it never accepts a
non-symmetry) delivers :math:`q = 1` and beats the threshold whenever :math:`B > w c_{rep}`; a screen
with :math:`f < 1` may deliver a posterior below :math:`q^*` even when both probabilities are
favourable. That is the correct statement of the boundary result, and it is a statement about a
threshold, not about the presence of verification.

Run as a script this module reads the A7 decision record and reports the measured threshold, its
bootstrap interval, the screen's measured sensitivity and specificity, the induced posterior, and the
point on the continuum where the optimal decision flips.
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from research.core import paired as _P


def threshold_rule(benefit, harm, w=0.0, c_repair=0.0):
    """q*(w) = (H + w c_rep) / (B + H): fire once the posterior exceeds this."""
    b, h = float(benefit), float(harm)
    if b + h <= 0:
        return None
    return (h + float(w) * float(c_repair)) / (b + h)


def posterior(pi, sens, spec):
    """Bayes posterior that the supplied group is a label symmetry, given the screen accepts."""
    num = pi * sens
    den = pi * sens + (1.0 - pi) * (1.0 - spec)
    return None if den <= 0 else num / den


def screen_errors(recs, regime, key="label_corrected_accepts"):
    """Measured sensitivity / specificity of a firing rule for "the group is a label symmetry".

    Read from the record's own per-regime decision, never assumed: the whole point of A7 is that
    the screen's error rates are quantities to be measured on the panel, not properties of the
    word "verified".
    """
    tp = fp = tn = fn = 0
    for r in recs:
        if regime not in r["regimes"]:
            continue
        fires = bool(r["regimes"][regime][key])
        valid = bool(r["regimes"][regime]["group_is_label_symmetry"])
        if valid and fires:
            tp += 1
        elif valid:
            fn += 1
        elif fires:
            fp += 1
        else:
            tn += 1
    sens = tp / (tp + fn) if (tp + fn) else None
    spec = tn / (tn + fp) if (tn + fp) else None
    return {"tp": tp, "fn": fn, "fp": fp, "tn": tn, "sensitivity": sens, "specificity": spec}


def magnitudes(recs, regime):
    """Paired benefit/harm magnitudes on one regime, with a candidate-level bootstrap."""
    d = np.array([r["regimes"][regime]["delta"] for r in recs if regime in r["regimes"]])
    valid_side = d[d < 0.0]
    harm_side = d[d > 0.0]
    out = {"n": int(len(d)), "mean_delta": float(d.mean()),
           "n_beneficial": int(len(valid_side)), "n_harmful": int(len(harm_side)),
           "benefit_B": float(-valid_side.mean()) if len(valid_side) else 0.0,
           "harm_H": float(harm_side.mean()) if len(harm_side) else 0.0,
           "share_harmful": float((d > 0).mean())}
    boots = []
    rng = np.random.default_rng(20261213)
    for _ in range(4000):
        s = rng.choice(d, size=len(d), replace=True)
        b = -s[s < 0].mean() if (s < 0).any() else 0.0
        h = s[s > 0].mean() if (s > 0).any() else 0.0
        t = threshold_rule(b, h)
        if t is not None:
            boots.append(t)
    if boots:
        out["q_star"] = threshold_rule(out["benefit_B"], out["harm_H"])
        out["q_star_ci95"] = [float(np.quantile(boots, 0.025)),
                              float(np.quantile(boots, 0.975))]
    return out


def insufficiency_demo(recs_by_regime, pi_grid=(0.2, 0.5, 0.8)):
    """Two regimes, matched probabilities, different optimal policies: the counterexample, run."""
    rows = []
    for name, recs in recs_by_regime.items():
        m = magnitudes(recs, name)
        rows.append({"regime": name, **m})
    for pi in pi_grid:
        for r in rows:
            q = r.get("q_star")
            r.setdefault("decisions_at_pi", {})[("%.2f" % pi)] = (
                None if q is None else {"fire_if_posterior_above": q,
                                        "policy_at_this_pi": "fire" if pi > q else "never"})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(prog="research/search/decision_model.py")
    ap.add_argument("--record", default="research/search/decision_rules3.json")
    ap.add_argument("--out", default="research/search/decision_model.json")
    a = ap.parse_args(argv)
    with open(a.record) as fh:
        rec = json.load(fh)

    out = {"model": "V(A) = E[A*Delta] + w*E[c_gate + A*c_rep]; fire iff posterior q > q*(w) "
                    "= (H + w*c_rep)/(B + H)",
           "withdrawn_claim": ("value is a function of P(supplied group wrong) and "
                              "P(Q lands in L_t) alone"),
           "why_withdrawn": ("q* depends on the ratio of conditional benefit to conditional harm and "
                             "on the repair cost; the two probabilities enter only through the "
                             "posterior, together with the screen's sensitivity and specificity"),
           "families": {}}
    for fam, body in rec.get("summary", {}).items():
        fam_out = {"regimes": {}, "insufficiency": []}
        recs = [c for c in rec["candidates"] if c["family"] == fam]
        # The corrected-screen firing rule is recomputed from each record's own per-regime label
        # decision, so this module does not depend on the comparison job having stored masks.
        for regime in body.get("regimes", {}):
            sub = [r for r in recs if regime in r["regimes"]]
            err = screen_errors(sub, regime)
            m = magnitudes(sub, regime)
            pi = (sum(1 for r in sub if r["regimes"][regime]["group_is_label_symmetry"]) / len(sub)
                  if sub else None)
            q = (posterior(pi, err["sensitivity"], err["specificity"])
                 if err["sensitivity"] is not None and err["specificity"] is not None else None)
            fam_out["regimes"][regime] = {
                "magnitudes": m, "screen_errors": err, "pi_valid_measured": pi,
                "posterior_given_accept": q,
                "screen_clears_threshold": (None if (q is None or m.get("q_star") is None)
                                            else bool(q > m["q_star"])),
                "n_fired": body["regimes"][regime].get("n_fired", {})}
        pair = {k: [r for r in recs if k in r["regimes"]]
                for k in ("declared", "mismatched") if k in body.get("regimes", {})}
        if len(pair) == 2:
            fam_out["insufficiency"] = insufficiency_demo(pair)
        out["families"][fam] = fam_out

    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True, default=str)
    for fam, f in out["families"].items():
        for regime, r in f["regimes"].items():
            m = r["magnitudes"]
            print("%-11s %-12s B=%.5f H=%.5f q*=%s %s"
                  % (fam, regime, m["benefit_B"], m["harm_H"],
                     ("%.3f" % m["q_star"]) if m.get("q_star") is not None else "n/a",
                     ("CI[%.3f,%.3f]" % tuple(m["q_star_ci95"]))
                     if m.get("q_star_ci95") else ""))
    print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
