"""Aggregate circuit labels into run-level and program-level statistics."""
import json, os, itertools
from collections import defaultdict, Counter
import numpy as np
from scipy import stats as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = [r for r in json.load(open(os.path.join(ROOT, "labelling/labels.json")))]
parsed = [r for r in rows if r["parsed"]]
own = [r for r in parsed if r["own"]]

LABELS = ["all-double", "all-double-exact", "all-double-tied", "all-singular", "all-singular-tied",
          "ring", "linear-chain", "mirror", "cyclic", "none"]
GROUPS = [("scratch", "weak"), ("scratch", "mid"), ("scratch", "frontier"),
          ("continue", "weak"), ("continue", "mid"), ("continue", "frontier"),
          ("continue", "frontier-no-gpt")]
RNG = np.random.default_rng(20260824)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def boot_mean(x, n=20000):
    x = np.asarray(x, float)
    if len(x) == 0:
        return (float("nan"),) * 3
    if len(x) == 1:
        return (x[0], float("nan"), float("nan"))
    bs = RNG.choice(x, (n, len(x)), replace=True).mean(1)
    return float(x.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def cluster_boot_rate(units, n=20000):
    """units: list of (k, m) per run -> program-level rate, resampling runs."""
    if not units:
        return (float("nan"),) * 3
    k = np.array([u[0] for u in units], float)
    m = np.array([u[1] for u in units], float)
    pt = k.sum() / m.sum() if m.sum() else float("nan")
    idx = RNG.integers(0, len(units), (n, len(units)))
    bs = k[idx].sum(1) / np.maximum(m[idx].sum(1), 1e-9)
    return float(pt), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


out = {}

# ---- coverage / bookkeeping
out["coverage"] = {
    "n_programs_total": len(rows),
    "n_parsed": len(parsed),
    "n_unparsed": len(rows) - len(parsed),
    "n_own": len(own),
    "n_runs": len({r["run_id"] for r in rows}),
}

by_run = defaultdict(list)
for r in own:
    by_run[r["run_id"]].append(r)
run_meta = {rid: (v[0]["setting"], v[0]["arm"], v[0]["budget"]) for rid, v in by_run.items()}

# ---- group table
groups = []
for setting, arm in GROUPS:
    runs = [rid for rid, m in run_meta.items() if m[0] == setting and m[1] == arm]
    progs = [r for rid in runs for r in by_run[rid]]
    g = {"setting": setting, "arm": arm, "n_runs": len(runs), "n_programs": len(progs),
         "gens_per_run": sorted({run_meta[rid][2] for rid in runs}), "labels": {}}
    best = [max(r["score"] for r in by_run[rid]) for rid in runs]
    g["best_score"] = dict(zip(("mean", "lo", "hi"), boot_mean(best)))
    g["best_scores"] = best
    for lab in LABELS:
        k = sum(1 for rid in runs if any(lab in r["circuit"]["labels"] for r in by_run[rid]))
        p, lo, hi = wilson(k, len(runs))
        units = [(sum(1 for r in by_run[rid] if lab in r["circuit"]["labels"]), len(by_run[rid]))
                 for rid in runs]
        pp, plo, phi = cluster_boot_rate(units)
        g["labels"][lab] = {"run_k": k, "run_n": len(runs), "run_p": p, "run_lo": lo, "run_hi": hi,
                            "prog_k": sum(u[0] for u in units), "prog_n": sum(u[1] for u in units),
                            "prog_p": pp, "prog_lo": plo, "prog_hi": phi}
    groups.append(g)
out["groups"] = groups

# ---- pairwise arm comparisons on the all-double run-level rate (Fisher exact)
def gget(setting, arm):
    return next(g for g in groups if g["setting"] == setting and g["arm"] == arm)

comps = []
for setting in ("scratch", "continue"):
    arms = [a for s, a in GROUPS if s == setting]
    for a, b in itertools.combinations(arms, 2):
        for lab in ("all-double", "all-singular-tied"):
            ga, gb = gget(setting, a)["labels"][lab], gget(setting, b)["labels"][lab]
            tbl = [[ga["run_k"], ga["run_n"] - ga["run_k"]],
                   [gb["run_k"], gb["run_n"] - gb["run_k"]]]
            comps.append({"setting": setting, "label": lab, "a": a, "b": b,
                          "ka": ga["run_k"], "na": ga["run_n"], "kb": gb["run_k"], "nb": gb["run_n"],
                          "p": float(st.fisher_exact(tbl)[1])})
out["comparisons"] = comps

# ---- score by label (program level, all in-scope own programs)
score_by_label = {}
for lab in LABELS:
    a = [r["score"] for r in own if lab in r["circuit"]["labels"]]
    b = [r["score"] for r in own if lab not in r["circuit"]["labels"]]
    m, lo, hi = boot_mean(a)
    entry = {"n_with": len(a), "n_without": len(b), "mean": m, "lo": lo, "hi": hi,
             "median": float(np.median(a)) if a else float("nan"),
             "mean_without": float(np.mean(b)) if b else float("nan")}
    if len(a) >= 2 and len(b) >= 2:
        u = st.mannwhitneyu(a, b, alternative="two-sided")
        entry["mw_p"] = float(u.pvalue)
        entry["cliffs_delta"] = float(2 * u.statistic / (len(a) * len(b)) - 1)
    score_by_label[lab] = entry
out["score_by_label"] = score_by_label

# ---- within-arm: does all-double co-occur with a better score?
within = []
for setting, arm in GROUPS:
    runs = [rid for rid, m in run_meta.items() if m[0] == setting and m[1] == arm]
    progs = [r for rid in runs for r in by_run[rid]]
    a = [r["score"] for r in progs if "all-double" in r["circuit"]["labels"]]
    b = [r["score"] for r in progs if "all-double" not in r["circuit"]["labels"]]
    e = {"setting": setting, "arm": arm, "n_with": len(a), "n_without": len(b)}
    e["with"] = dict(zip(("mean", "lo", "hi"), boot_mean(a)))
    e["without"] = dict(zip(("mean", "lo", "hi"), boot_mean(b)))
    if len(a) >= 2 and len(b) >= 2:
        e["mw_p"] = float(st.mannwhitneyu(a, b, alternative="two-sided").pvalue)
    within.append(e)
out["within_arm_all_double"] = within

# ---- frontier only: all-double vs not, matched within the frontier scratch arm
# ---- budget-matched sensitivity: scratch runs truncated to generation <= 20
matched = []
for arm in ("weak", "mid", "frontier"):
    runs = [rid for rid, m in run_meta.items() if m[0] == "scratch" and m[1] == arm]
    k = 0
    for rid in runs:
        if any("all-double" in r["circuit"]["labels"] for r in by_run[rid] if r["generation"] <= 20):
            k += 1
    p, lo, hi = wilson(k, len(runs))
    matched.append({"arm": arm, "k": k, "n": len(runs), "p": p, "lo": lo, "hi": hi})
out["budget_matched_scratch"] = matched

# ---- pair coverage distribution
cov = []
for setting, arm in GROUPS:
    runs = [rid for rid, m in run_meta.items() if m[0] == setting and m[1] == arm]
    v = [max(r["circuit"]["max_pair_coverage"] for r in by_run[rid]) for rid in runs]
    m, lo, hi = boot_mean(v)
    cov.append({"setting": setting, "arm": arm, "mean": m, "lo": lo, "hi": hi, "values": v})
out["pair_coverage"] = cov

# ---- layer counts
out["layer_stats"] = {
    "mean_layers": float(np.mean([r["circuit"]["n_layers"] for r in parsed])),
    "median_layers": float(np.median([r["circuit"]["n_layers"] for r in parsed])),
    "hist": dict(Counter(r["circuit"]["n_layers"] for r in parsed).most_common()),
    "n_layers_total": sum(r["circuit"]["n_layers"] for r in parsed),
}

json.dump(out, open(os.path.join(ROOT, "labelling/stats.json"), "w"), indent=1)
for g in groups:
    d = g["labels"]["all-double"]
    print(f'{g["setting"]:9s} {g["arm"]:16s} runs={g["n_runs"]:2d} progs={g["n_programs"]:3d} '
          f'all-double runs {d["run_k"]}/{d["run_n"]} = {d["run_p"]:.2f} [{d["run_lo"]:.2f},{d["run_hi"]:.2f}]  '
          f'best={g["best_score"]["mean"]:.3f}')
