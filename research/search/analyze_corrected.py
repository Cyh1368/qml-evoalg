"""A6.7 analysis: matched search runs under the corrected label semantics.

The referee's point is that post-processing frozen candidates cannot recover the search
trajectories corrected feedback would have produced, so any behavioural claim about feedback
needs new matched runs. Those runs are ``logs/runs_corrected/`` (``label_mode="corrected"`` in
every run JSON, so they cannot be confused with the frozen confirmatory runs in
``logs/runs_confirm/``).

Frozen design (Addendum A6.7, committed before these runs were analysed):

* arms ``llm-fitness``, ``llm-verify``, ``llm-verify-repair`` under corrected semantics, on
  both families, 12 paired seeds, and the budget/optimiser settings of the frozen record itself
  (``budget=12``, ``steps=120``, ``max_train=256``, ``reasoning_effort=none`` — read from the 120
  confirmatory run JSONs, not from the job template's 32/200 defaults, which would not have been
  matched);
* the frozen defective-semantics runs of the same arms and seeds are the matched comparator
  for "what did correcting the feedback change";
* primary contrast ``llm-verify-corrected - llm-fitness-corrected`` on development-selected
  risk, Holm within family;
* prespecified practically meaningful threshold ``0.002`` absolute risk. A contrast is called
  *detected at the prespecified threshold* only if the bootstrap CI excludes 0 **and** the
  absolute mean reaches the threshold. Otherwise the wording stays "difference not detected",
  which is not "no effect".

Inference unit is the paired seed (12 vectors), never a proposal or a candidate: proposals
inside a run are adaptively related. Cost is reported per arm (LLM calls, tokens, wall time)
because a feedback channel that costs more than it saves is not a finding.

Run: ``python3 -m research.search.analyze_corrected --out research/search/corrected_search.json``
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics

import numpy as np

from research.core import paired as P

THRESHOLD = 0.002
ARMS = ("llm-fitness", "llm-verify", "llm-verify-repair")
FAMILIES = ("ring_n6", "graphs_n6")
CONTRASTS = {
    "ring_n6": [("llm-verify", "llm-fitness"), ("llm-verify-repair", "llm-fitness"),
                ("llm-verify-repair", "llm-verify")],
    "graphs_n6": [("llm-verify", "llm-fitness"), ("llm-verify-repair", "llm-fitness"),
                  ("llm-verify-repair", "llm-verify")],
}


MATCH = {"budget": 12, "steps": 120, "max_train": 256}


def load(pattern, label_mode, matched=True):
    """Read run logs, keeping only the protocol-matched configuration.

    Three earlier A6.7 arrays were submitted with the job template's budget 32 / steps 200
    instead of the frozen study's 12 / 120 and were cancelled; a cancelled task can still
    finish and write its log, so the filter is applied here rather than trusted to the
    submission. Skipped records are counted and reported, never silently dropped.
    """
    out = {}
    skipped = {"wrong_mode": 0, "wrong_config": 0, "mock": 0, "arm": 0}
    for path in sorted(glob.glob(pattern)):
        with open(path) as fh:
            d = json.load(fh)
        if d.get("arm") not in ARMS:
            skipped["arm"] += 1
            continue
        if d.get("mock_llm"):
            skipped["mock"] += 1
            continue
        if d.get("label_mode", "implemented") != label_mode:
            skipped["wrong_mode"] += 1
            continue
        if matched and any(d.get(k) != v for k, v in MATCH.items()):
            skipped["wrong_config"] += 1
            continue
        out[(d["family"], d["arm"], int(d["seed"]))] = d
    load.last_skipped = skipped
    return out


def series(runs, family, arm, mode_tag):
    """Paired-by-seed vectors of development-selected risk plus per-seed metadata."""
    seeds = sorted({k[2] for k in runs if k[0] == family and k[1] == arm})
    risk, fired, calls, tokens, invalid, valid = [], [], [], [], [], []
    for s in seeds:
        d = runs.get((family, arm, s))
        if d is None:
            continue
        risk.append(float(d["best"]["dev_risk"]))
        fired.append(bool((d.get("repair") or {}).get("repaired", False)))
        calls.append(int((d.get("tokens") or {}).get("calls", 0)))
        tokens.append(int((d.get("tokens") or {}).get("total_tokens", 0)))
        invalid.append(int(d.get("invalid_total", 0)))
        valid.append(int(d.get("evaluated_valid", 0)))
    if not risk:
        return None
    return {"mode": mode_tag, "family": family, "arm": arm, "n_seeds": len(risk),
            "seeds": seeds, "risk": risk, "repaired": fired, "llm_calls": calls,
            "tokens": tokens, "invalid": invalid, "valid": valid,
            "risk_mean": statistics.fmean(risk)}


def contrast(a, b, family):
    """Paired a - b on shared seeds, seed-vector bootstrap and sign-flip test."""
    sa = {(s, r) for s, r in zip(a["seeds"], a["risk"])}
    sb = dict(zip(b["seeds"], b["risk"]))
    shared = sorted({s for s, _ in sa} & set(sb))
    ra = dict(zip(a["seeds"], a["risk"]))
    diffs = np.array([ra[s] - sb[s] for s in shared])
    ci = P.bootstrap_ci(diffs, n_boot=20000, seed=20261112)
    flip = P.signflip_p(diffs, n_boot=200000, seed=20261112)
    flip = float(flip["p"]) if isinstance(flip, dict) else float(flip)
    mean = float(diffs.mean())
    detected = (ci["ci95_low"] > 0 or ci["ci95_high"] < 0)
    meaningful = abs(mean) >= THRESHOLD
    if detected and meaningful:
        verdict = ("lower" if mean < 0 else "higher") + " at the prespecified threshold"
    elif detected:
        verdict = "detected but smaller than the prespecified threshold"
    else:
        verdict = "difference not detected"
    return {"family": family, "a": a["arm"] + "/" + a["mode"],
            "b": b["arm"] + "/" + b["mode"], "n_pairs": len(shared),
            "mean_diff": mean, "ci95_low": ci["ci95_low"], "ci95_high": ci["ci95_high"],
            "sign_flip_p": flip, "sd_pairs": float(diffs.std(ddof=1)) if len(shared) > 1
            else None, "a_better_fraction": float((diffs < 0).mean()),
            "threshold": THRESHOLD, "verdict": verdict,
            "per_seed": [[int(s), float(ra[s] - sb[s])] for s in shared]}


def holm(rows):
    ps = [(i, r["sign_flip_p"]) for i, r in enumerate(rows)]
    order = sorted(ps, key=lambda t: t[1])
    m = len(order)
    adj = {}
    running = 0.0
    for rank, (i, p) in enumerate(order):
        running = max(running, (m - rank) * p)
        adj[i] = min(1.0, running)
    for i, v in adj.items():
        rows[i]["holm_p"] = v
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(prog="research/search/analyze_corrected.py")
    ap.add_argument("--corrected", default="logs/runs_corrected/*.json")
    ap.add_argument("--frozen", default="logs/runs_confirm/*.json")
    ap.add_argument("--out", default="research/search/corrected_search.json")
    ap.add_argument("--allow-unmatched", action="store_true",
                    help="accept corrected-mode runs at budgets other than the frozen 12/120 "
                         "(off by default: unmatched runs are not the matched study A6.7 asks for)")
    a = ap.parse_args(argv)

    corr = load(a.corrected, "corrected", matched=not a.allow_unmatched)
    froz = load(a.frozen, "implemented", matched=False)
    if not corr:
        raise SystemExit("no corrected runs found at %s" % a.corrected)

    arms_present = sorted({k[1] for k in corr})
    n_by = {}
    for fam in FAMILIES:
        for arm in ARMS:
            n_by["%s/%s" % (fam, arm)] = len([k for k in corr if k[0] == fam and k[1] == arm])

    arms_rows, rows = [], []
    for fam in FAMILIES:
        got = {}
        for arm in ARMS:
            s = series(corr, fam, arm, "corrected")
            if s:
                got[arm] = s
        for (x, y) in CONTRASTS[fam]:
            if x in got and y in got:
                rows.append(contrast(got[x], got[y], fam))
        for arm, s in got.items():
            arms_rows.append({k: v for k, v in s.items() if k != "risk"} |
                             {"risk_mean": s["risk_mean"]})
        # what did correcting the feedback change? same arm, two modes
        for arm in ARMS:
            c = series(corr, fam, arm, "corrected")
            f = series(froz, fam, arm, "implemented")
            if c and f:
                rows.append(contrast(c, f, fam))

    for fam in FAMILIES:
        fam_rows = [r for r in rows if r["family"] == fam]
        holm(fam_rows)

    out = {"protocol": "Addendum A6.7 (frozen before analysis)",
           "threshold_abs_risk": THRESHOLD,
           "matched_configuration": MATCH,
           "skipped_records": {"corrected": getattr(load, "last_skipped", {}),
                               "frozen": getattr(load, "last_skipped", {})},
           "arms_present_in_corrected_runs": arms_present,
           "runs_per_cell": n_by, "arms": arms_rows, "contrasts": rows,
           "note": ("Unit is the paired seed. 'difference not detected' means the interval "
                    "covers 0; it is not a claim of no effect. Corrected and frozen runs are "
                    "separate LLM draws, so the corrected-vs-frozen contrast mixes the "
                    "semantics change with run-to-run LLM variation and is labelled as such.")}
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote %s: %d contrasts, %d corrected runs" % (a.out, len(rows), len(corr)))
    for r in rows:
        print("  %-11s %-24s - %-24s %+.5f [%+.5f,%+.5f] %s"
              % (r["family"], r["a"], r["b"], r["mean_diff"], r["ci95_low"],
                 r["ci95_high"], r["verdict"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
