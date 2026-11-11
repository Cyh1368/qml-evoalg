"""WP-SEARCH analysis: paired run-level contrasts with bootstrap CIs and Holm
correction (statistics conventions in research/core/INTERFACES.md).

Reads run JSON logs from a directory and compares arms at matched budget,
paired by seed (and, for LLM-vs-LLM contrasts, by model treatment). The primary
endpoint is ``llm-verify`` minus ``llm-fitness`` dev risk per (family, treatment,
seed); negative => the verifier helps. Secondary contrasts are Holm-corrected
within each family.

Usage::

    python3 -m research.search.analyze --dir logs/runs_pilot \
        --out research/search/pilot_analysis.json
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

PRIMARY = ("llm-verify", "llm-fitness")
SECONDARY = [("llm-verify-repair", "llm-verify"),
             ("llm-fitness", "mutation-ea"),
             ("mutation-ea", "random"),
             ("llm-verify", "random")]
REF_TREATMENT = ("ycrc-local", "none")  # for LLM-vs-nonLLM pairing


def load_runs(directory):
    runs = []
    for path in sorted(glob.glob(os.path.join(directory, "run_*.json"))):
        with open(path) as fh:
            d = json.load(fh)
        runs.append({"arm": d["arm"], "family": d["family"],
                     "model": d.get("model"),
                     "effort": d.get("reasoning_effort"),
                     "seed": int(d["seed"]), "budget": d["budget"],
                     "steps": d.get("steps"), "dev_risk": d["best"]["dev_risk"],
                     "invalid": d["invalid_total"],
                     "tokens": d["tokens"]["total_tokens"],
                     "repaired": d["best"]["repair"].get("repaired", False)})
    return runs


def _index(runs, arm, family, model, effort):
    out = {}
    for r in runs:
        if r["arm"] != arm or r["family"] != family:
            continue
        if arm in ("llm-fitness", "llm-verify", "llm-verify-repair"):
            if model is not None and (r["model"], r["effort"]) != (model, effort):
                continue
        else:
            # non-LLM arms carry model=None; match only those
            if r["model"] is not None:
                continue
        out.setdefault(r["seed"], []).append(r["dev_risk"])
    return {s: float(np.mean(v)) for s, v in out.items()}


def paired(runs, a, b, family, ma=None, ea=None, mb=None, eb=None):
    ia = _index(runs, a, family, ma, ea)
    ib = _index(runs, b, family, mb, eb)
    seeds = sorted(set(ia) & set(ib))
    diffs = [ia[s] - ib[s] for s in seeds]  # a - b; negative => a better
    return {"a": a, "b": b, "family": family,
            "model": ma if a in ("llm-fitness", "llm-verify", "llm-verify-repair")
            else mb, "effort": ea if a in ("llm-fitness", "llm-verify",
            "llm-verify-repair") else eb,
            "n_pairs": len(diffs), "seeds": seeds,
            "mean_diff_a_minus_b": float(np.mean(diffs)) if diffs else None,
            "frac_a_better": float(np.mean([d < 0 for d in diffs])) if diffs else None,
            "diffs": diffs}


def bootstrap(diffs, n_boot=10000, seed=0):
    if not diffs:
        return {"mean": None, "ci95_low": None, "ci95_high": None, "p_two_sided": None}
    rng = np.random.default_rng(seed)
    d = np.asarray(diffs, float)
    means = np.array([np.mean(rng.choice(d, size=len(d), replace=True))
                      for _ in range(n_boot)])
    p = 2.0 * min((means <= 0).mean(), (means >= 0).mean())
    return {"mean": float(np.mean(d)),
            "ci95_low": float(np.percentile(means, 2.5)),
            "ci95_high": float(np.percentile(means, 97.5)),
            "p_two_sided": float(min(1.0, p))}


def holm(pvals):
    """Holm-Bonferroni adjusted p-values (same order as input)."""
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.zeros(m)
    running = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * pvals[idx]
        running = max(running, val)
        adj[idx] = min(1.0, running)
    return adj


def analyze(directory):
    runs = load_runs(directory)
    families = sorted({r["family"] for r in runs})
    treatments = sorted({(r["model"], r["effort"]) for r in runs
                         if r["arm"] in ("llm-fitness", "llm-verify",
                                         "llm-verify-repair")})
    result = {"directory": directory, "n_runs": len(runs),
              "families": families, "treatments": [list(t) for t in treatments],
              "primary": [], "secondary": [], "arm_summary": []}
    for fam in families:
        for arm in sorted({r["arm"] for r in runs if r["family"] == fam}):
            sub = [r for r in runs if r["family"] == fam and r["arm"] == arm]
            result["arm_summary"].append(
                {"family": fam, "arm": arm, "n_runs": len(sub),
                 "mean_dev_risk": float(np.mean([r["dev_risk"] for r in sub])),
                 "mean_invalid": float(np.mean([r["invalid"] for r in sub])),
                 "mean_tokens": float(np.mean([r["tokens"] for r in sub]))})
        # primary: paired by (treatment, seed)
        for (model, effort) in treatments:
            p = paired(runs, PRIMARY[0], PRIMARY[1], fam, model, effort,
                       model, effort)
            p["bootstrap"] = bootstrap(p["diffs"])
            result["primary"].append(p)
        # secondary: Holm-corrected within family
        sec = []
        for (a, b) in SECONDARY:
            llm = ("llm-fitness", "llm-verify", "llm-verify-repair")
            ma, ea = REF_TREATMENT if a in llm else (None, None)
            mb, eb = REF_TREATMENT if b in llm else (None, None)
            c = paired(runs, a, b, fam, ma, ea, mb, eb)
            c["bootstrap"] = bootstrap(c["diffs"])
            sec.append(c)
        pv = [c["bootstrap"]["p_two_sided"] if c["n_pairs"] else 1.0 for c in sec]
        adj = holm(pv)
        for c, pa in zip(sec, adj):
            c["p_holm"] = float(pa)
        result["secondary"].extend(sec)
    return result


def main(argv=None):
    p = argparse.ArgumentParser(prog="research/search/analyze.py")
    p.add_argument("--dir", required=True)
    p.add_argument("--out", default=None)
    args = p.parse_args(argv)
    res = analyze(args.dir)
    if args.out:
        with open(args.out, "w") as fh:
            json.dump(res, fh, indent=1, default=str)
    print("runs=%d families=%s" % (res["n_runs"], res["families"]))
    print("\n=== PRIMARY (llm-verify - llm-fitness; negative => verifier helps) ===")
    for c in res["primary"]:
        b = c["bootstrap"]
        print("%-14s %-18s n=%d mean=%+.5f ci=[%+.5f,%+.5f] p=%.3f frac_verify_better=%.2f"
              % (c["family"], "%s/%s" % (c["model"], c["effort"]), c["n_pairs"],
                 b["mean"] or 0, b["ci95_low"] or 0, b["ci95_high"] or 0,
                 b["p_two_sided"] or 1, c["frac_a_better"] or 0))
    print("\n=== SECONDARY (Holm-adjusted; negative => first arm better) ===")
    for c in res["secondary"]:
        b = c["bootstrap"]
        print("%-14s %-18s vs %-18s n=%d mean=%+.5f p_holm=%.3f"
              % (c["family"], c["a"], c["b"], c["n_pairs"], b["mean"] or 0,
                 c["p_holm"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
