"""Join patch-note labels with circuit labels and answer three questions:

  Q1 identify  -- does the note refer to the all-pairs / permutation structure?
  Q2 say->do   -- when a note claims the structure, does the circuit have it?
  Q3 do->say   -- when a circuit has it, did the note mention it at all?

Rates are reported per arm with run-clustered bootstrap CIs; arm contrasts use
Fisher's exact test on run-level counts and on program counts.
"""
import json, os, itertools
from collections import defaultdict
import numpy as np
from scipy import stats as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_all = [r for r in json.load(open(os.path.join(ROOT, "labelling/note_labels.json")))
        if r["own"] and r["parsed"]]
# 37 programs carry no patch note at all (empty patch_description); they cannot
# be scored on what the model said, so they are dropped from every rate below.
rows = [r for r in _all if len(r["note"]["patch_description"].strip()) >= 20]
N_EMPTY = len(_all) - len(rows)
ARMS = ["weak", "mid", "frontier"]
RNG = np.random.default_rng(20260825)

for r in rows:
    lab = set(r["circuit"]["labels"])
    n = r["note"]
    r["built"] = n["union_pairs"] == 28               # block covers all 28 pairs
    r["built_layer"] = "all-double" in lab            # one layer covers all 28
    r["built_exact"] = "all-double-exact" in lab
    r["said_build"] = bool(n["build_claim"])
    r["said_any"] = bool(n["claims"] or "task_pairs" in n["flags"])
    r["collective"] = "collective" in n["flags"]
    r["partial"] = "partial_sym" in n["flags"]
    r["breaks"] = "breaks_sym" in n["flags"]
    r["silent_build"] = r["built"] and not r["said_any"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def cluster_rate(units, n=20000):
    """units: (k, m) per run.  Program-level rate, runs resampled."""
    units = [u for u in units if u[1] > 0]
    if not units:
        return {"p": float("nan"), "lo": float("nan"), "hi": float("nan"), "k": 0, "n": 0}
    k = np.array([u[0] for u in units], float)
    m = np.array([u[1] for u in units], float)
    idx = RNG.integers(0, len(units), (n, len(units)))
    bs = k[idx].sum(1) / np.maximum(m[idx].sum(1), 1e-9)
    return {"p": float(k.sum() / m.sum()), "lo": float(np.percentile(bs, 2.5)),
            "hi": float(np.percentile(bs, 97.5)), "k": int(k.sum()), "n": int(m.sum()),
            "runs": len(units)}


by_run = defaultdict(list)
for r in rows:
    by_run[r["run_id"]].append(r)
arm_of = {rid: v[0]["arm"] for rid, v in by_run.items()}
set_of = {rid: v[0]["setting"] for rid, v in by_run.items()}


def runs_of(arm, setting=None):
    return [rid for rid in by_run
            if arm_of[rid] == arm and (setting is None or set_of[rid] == setting)]


def rate(arm, num, den=lambda r: True, setting=None):
    return cluster_rate([(sum(1 for r in by_run[rid] if den(r) and num(r)),
                          sum(1 for r in by_run[rid] if den(r))) for rid in runs_of(arm, setting)])


def run_level(arm, pred, setting=None):
    rs = runs_of(arm, setting)
    k = sum(1 for rid in rs if any(pred(r) for r in by_run[rid]))
    p, lo, hi = wilson(k, len(rs))
    return {"k": k, "n": len(rs), "p": p, "lo": lo, "hi": hi}


out = {"n_empty_notes": N_EMPTY, "n_programs": len(rows), "n_runs": len(by_run),
       "arms": {a: {"runs": len(runs_of(a)), "programs": sum(len(by_run[r]) for r in runs_of(a))}
                for a in ARMS}}

# ---------- Q1: identification
out["q1"] = {a: {
    "said_any": rate(a, lambda r: r["said_any"]),
    "said_build": rate(a, lambda r: r["said_build"]),
    "collective": rate(a, lambda r: r["collective"]),
    "partial": rate(a, lambda r: r["partial"]),
    "silent": rate(a, lambda r: not (r["said_any"] or r["collective"] or r["partial"])),
    "run_said_any": run_level(a, lambda r: r["said_any"]),
    "run_said_build": run_level(a, lambda r: r["said_build"]),
    "run_built": run_level(a, lambda r: r["built"]),
    "run_built_layer": run_level(a, lambda r: r["built_layer"]),
    "built": rate(a, lambda r: r["built"]),
    "built_layer": rate(a, lambda r: r["built_layer"]),
} for a in ARMS}

# ---------- Q2: say -> do, and Q3: do -> say
out["q2"] = {a: {
    "build_given_say": rate(a, lambda r: r["built"], lambda r: r["said_build"]),
    "build_given_nosay": rate(a, lambda r: r["built"], lambda r: not r["said_build"]),
    "exact_given_say": rate(a, lambda r: r["built_exact"], lambda r: r["said_build"]),
    "layer_given_say": rate(a, lambda r: r["built_layer"], lambda r: r["said_build"]),
    "say_given_build": rate(a, lambda r: r["said_build"], lambda r: r["built"]),
    "any_given_build": rate(a, lambda r: r["said_any"], lambda r: r["built"]),
    "silent_given_build": rate(a, lambda r: not r["said_any"], lambda r: r["built"]),
} for a in ARMS}

# ---------- 2x2 contingency per arm + overall, with kappa
def table(sub):
    a = sum(1 for r in sub if r["said_build"] and r["built"])
    b = sum(1 for r in sub if r["said_build"] and not r["built"])
    c = sum(1 for r in sub if not r["said_build"] and r["built"])
    d = sum(1 for r in sub if not r["said_build"] and not r["built"])
    n = a + b + c + d
    po = (a + d) / n
    pe = ((a + b) * (a + c) + (c + d) * (b + d)) / n ** 2
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    odds, p = st.fisher_exact([[a, b], [c, d]])
    mc = st.binomtest(b, b + c, 0.5).pvalue if b + c else float("nan")
    return {"say_build": a, "say_nobuild": b, "nosay_build": c, "nosay_nobuild": d,
            "n": n, "kappa": float(kappa), "fisher_p": float(p),
            "odds": float(odds) if np.isfinite(odds) else None, "mcnemar_p": float(mc)}


out["contingency"] = {a: table([r for r in rows if r["arm"] == a]) for a in ARMS}
out["contingency"]["all"] = table(rows)

# ---------- arm contrasts (run-level Fisher)
comps = []
for a, b in itertools.combinations(ARMS, 2):
    for name, key in (("identify", "run_said_any"), ("claim", "run_said_build"), ("build", "run_built")):
        ga, gb = out["q1"][a][key], out["q1"][b][key]
        p = st.fisher_exact([[ga["k"], ga["n"] - ga["k"]], [gb["k"], gb["n"] - gb["k"]]])[1]
        comps.append({"a": a, "b": b, "what": name, "ka": ga["k"], "na": ga["n"],
                      "kb": gb["k"], "nb": gb["n"], "p": float(p)})
# program-level identify contrast (runs as clusters -> bootstrap difference)
for a, b in itertools.combinations(ARMS, 2):
    for key, num in (("identify", lambda r: r["said_any"]), ("build", lambda r: r["built"])):
        ra, rb = rate(a, num), rate(b, num)
        comps.append({"a": a, "b": b, "what": key + "_prog", "pa": ra["p"], "pb": rb["p"],
                      "ci_a": [ra["lo"], ra["hi"]], "ci_b": [rb["lo"], rb["hi"]]})
out["comparisons"] = comps

# ---------- does talk lead building?  first mention vs first build generation
lead = []
for rid, progs in by_run.items():
    ps = sorted(progs, key=lambda r: r["generation"])
    fs = next((r["generation"] for r in ps if r["said_build"]), None)
    fb = next((r["generation"] for r in ps if r["built"]), None)
    lead.append({"run": rid, "arm": arm_of[rid], "setting": set_of[rid],
                 "first_say": fs, "first_build": fb})
out["lead"] = lead
out["lead_summary"] = {}
for a in ARMS:
    both = [l for l in lead if l["arm"] == a and l["first_say"] is not None and l["first_build"] is not None]
    d = [l["first_build"] - l["first_say"] for l in both]
    out["lead_summary"][a] = {
        "n_both": len(both), "median_delta": float(np.median(d)) if d else float("nan"),
        "say_first": sum(1 for x in d if x > 0), "same_gen": sum(1 for x in d if x == 0),
        "build_first": sum(1 for x in d if x < 0),
        "n_say_only": sum(1 for l in lead if l["arm"] == a and l["first_say"] is not None and l["first_build"] is None),
        "n_build_only": sum(1 for l in lead if l["arm"] == a and l["first_say"] is None and l["first_build"] is not None),
        "n_neither": sum(1 for l in lead if l["arm"] == a and l["first_say"] is None and l["first_build"] is None),
    }

# ---------- silent builders: did the parent already have it?
parent = {}
import glob as _glob
from label_circuits import load_run as _lr, classify as _cl
for f in sorted(_glob.glob(os.path.join(ROOT, "viz/data/run_sn-transfer-*.js"))):
    rid = os.path.basename(f)[4:-3]
    if not _cl(rid):
        continue
    for p in _lr(f)["programs"]:
        parent[(rid, p["id"])] = p.get("parent_id")
built_of = {(r["run_id"], r["program_id"]): r["built"] for r in rows}
inh = {"silent_total": 0, "silent_parent_built": 0, "stated_total": 0, "stated_parent_built": 0,
       "silent_examples": []}
for r in rows:
    if not r["built"]:
        continue
    pb = built_of.get((r["run_id"], parent.get((r["run_id"], r["program_id"]))))
    key = "silent" if not r["said_any"] else "stated"
    inh[key + "_total"] += 1
    inh[key + "_parent_built"] += bool(pb)
    if key == "silent":
        inh["silent_examples"].append({"run": r["run_id"], "gen": r["generation"],
                                       "score": r["score"], "parent_built": bool(pb),
                                       "patch_name": r["note"]["patch_name"],
                                       "flags": r["note"]["flags"]})
out["inheritance"] = inh

# ---------- score by cell
def boot(x, n=20000):
    x = np.asarray(x, float)
    if len(x) < 2:
        return {"mean": float(x[0]) if len(x) else float("nan"), "lo": float("nan"),
                "hi": float("nan"), "n": len(x)}
    bs = RNG.choice(x, (n, len(x)), replace=True).mean(1)
    return {"mean": float(x.mean()), "lo": float(np.percentile(bs, 2.5)),
            "hi": float(np.percentile(bs, 97.5)), "n": len(x)}


cells = {}
for s in (True, False):
    for b in (True, False):
        v = [r["score"] for r in rows if r["said_build"] == s and r["built"] == b]
        cells[f"say{int(s)}_build{int(b)}"] = boot(v)
out["score_cells"] = cells
sb = [r["score"] for r in rows if r["said_build"] and r["built"]]
nb = [r["score"] for r in rows if not r["said_build"] and r["built"]]
out["score_silent_vs_stated_build"] = {
    "stated": boot(sb), "silent": boot(nb),
    "mw_p": float(st.mannwhitneyu(sb, nb).pvalue) if len(sb) > 1 and len(nb) > 1 else float("nan")}

# ---------- vocabulary tallies
flags = ["names_perm", "all_pairs", "collective", "task_pairs", "partial_sym", "breaks_sym", "none"]
out["flag_rates"] = {a: {f: rate(a, lambda r, f=f: f in r["note"]["flags"]) for f in flags} for a in ARMS}

json.dump(out, open(os.path.join(ROOT, "labelling/note_stats.json"), "w"), indent=1)
for a in ARMS:
    q1, q2 = out["q1"][a], out["q2"][a]
    print(f'{a:9s} identify {q1["said_any"]["p"]:.2f}  claim-build {q1["said_build"]["p"]:.2f}  '
          f'built {run_level(a, lambda r: r["built"])["p"]:.2f}  '
          f'P(build|say) {q2["build_given_say"]["p"]:.2f} ({q2["build_given_say"]["n"]})  '
          f'P(say|build) {q2["say_given_build"]["p"]:.2f} ({q2["say_given_build"]["n"]})  '
          f'kappa {out["contingency"][a]["kappa"]:.2f}')
