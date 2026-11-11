"""Compute the paper's zero-context numbers from zcdata.json.

Metric definitions are taken unchanged from the existing scripts so the new
arms are directly comparable to the ones already in the paper:
  motif counting        -> stats.py
  S_n equivariance      -> equivariance_test.py (exact + partial, canonical form)
  SU(2) Heisenberg tie  -> sym_analysis.py
  game vocabulary       -> reasoning.py
"""
import json
import math
import random
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

SP = Path(__file__).resolve().parent
D = json.loads((SP / "zcdata.json").read_text())
RUNS, KEYS = D["runs"], D["keys"]

SYM_GATES = {"CZ", "ZZ", "XX", "YY"}
LEAK = re.compile(r"tic.?tac|noughts|board|row|column|diagonal|corner|"
                  r"centre|center|win(ning)?\s*line|three.in.a.row", re.I)
SYM_WORD = re.compile(r"symmetr|invarian|equivarian|permut|relabel|exchange|"
                      r"isotropic|heisenberg|spin|su\(2\)|s_?8", re.I)


def binom_sf(k, n, p):
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))


def ok_progs(run):
    return [p for p in run["programs"]
            if p["correct"] and p["score"] is not None and p["spec"] is not None]


# ---------------------------------------------------------------- tic-tac-toe

def ttt_stats(run):
    win = {frozenset(t) for t in KEYS["ttt"]["win"]}
    edges = {frozenset(e) for e in KEYS["ttt"]["edges"]}

    def deg(t):
        return sum(1 for pr in combinations(sorted(t), 2) if frozenset(pr) in edges)

    all_t = [frozenset(t) for t in combinations(range(9), 3)]
    hidden = {t for t in win if deg(t) == 0}
    p_uni = len(win) / len(all_t)
    s2 = [t for t in all_t if deg(t) == 2]
    p_e2 = sum(1 for t in s2 if t in win) / len(s2)

    progs = []
    for p in ok_progs(run):
        tr = [frozenset(int(w) for w in it["wires"])
              for it in (p["spec"] or [])
              if isinstance(it, dict)
              and str(it.get("gate", "")).upper() in ("ZZZ", "CCRZ")
              and isinstance(it.get("wires"), (list, tuple)) and len(it["wires"]) == 3]
        progs.append({**p, "tr": tr, "n_tr": len(tr),
                      "n_win": sum(1 for t in tr if t in win)})

    best, traj = None, []
    for p in sorted(progs, key=lambda q: (q["gen"], q["score"])):
        if best is None or p["score"] > best["score"]:
            best = p
            traj.append({"gen": p["gen"], "score": p["score"], "val": p["val"],
                         "test": p["test"], "n_tr": p["n_tr"], "n_win": p["n_win"],
                         "covered": len(set(p["tr"]) & win),
                         "hidden": len(set(p["tr"]) & hidden)})

    pop = [t for p in progs for t in p["tr"]]
    pop_w = sum(1 for t in pop if t in win)
    lines_any = set()
    hidden_any = set()
    for p in progs:
        lines_any |= set(p["tr"]) & win
        hidden_any |= set(p["tr"]) & hidden

    return {
        "n_progs": len(progs),
        "n_using_triples": sum(1 for p in progs if p["n_tr"] > 0),
        "max_gen": max((p["gen"] for p in run["programs"]), default=-1) + 1,
        "p_uni": p_uni, "p_e2": p_e2,
        "population": {
            "n": len(pop), "n_win": pop_w,
            "frac": (pop_w / len(pop)) if pop else None,
            "by_deg": {d: sum(1 for t in pop if deg(t) == d) for d in (0, 1, 2, 3)},
            "p_uni": binom_sf(pop_w, len(pop), p_uni) if pop else None,
            "p_e2": binom_sf(pop_w, len(pop), p_e2) if pop else None,
        },
        "lines_found_anywhere": len(lines_any),
        "hidden_found_anywhere": len(hidden_any),
        "first_hit_gen": next((t["gen"] for t in traj if t["n_win"] > 0), None),
        "best": {k: best[k] for k in
                 ("gen", "score", "val", "test", "train", "gap", "n_params",
                  "n_tr", "n_win")} | {
            "covered": len(set(best["tr"]) & win),
            "hidden": len(set(best["tr"]) & hidden),
            "triples": sorted(tuple(sorted(t)) for t in best["tr"]),
        },
        "trajectory": traj,
    }


# ------------------------------------------------------------------ S_n graph

def canon(spec, perm=None, n=8):
    p = perm or list(range(n))
    out = []
    for it in spec or []:
        if not isinstance(it, dict):
            continue
        g = str(it.get("gate", "")).upper()
        par = it.get("param")
        if "wire" in it:
            w = (p[int(it["wire"])],)
        elif "wires" in it:
            w = tuple(p[int(x)] for x in it["wires"])
            if g in SYM_GATES:
                w = tuple(sorted(w))
        else:
            continue
        out.append((g, w, par))
    return Counter(out)


def equivariance(spec, trials=200, seed=0):
    """(fraction of relabellings leaving the block identical, mean preserved share)."""
    base = canon(spec)
    if not base:
        return 0.0, 0.0
    rng = random.Random(seed)
    ok, frac = 0, []
    total = sum(base.values())
    for _ in range(trials):
        p = list(range(8))
        rng.shuffle(p)
        c = canon(spec, p)
        ok += (c == base)
        frac.append(sum((base & c).values()) / total)
    return ok / trials, sum(frac) / len(frac)


def sn_stats(run):
    progs = []
    for p in ok_progs(run):
        exact, partial = equivariance(p["spec"])
        progs.append({**{k: p[k] for k in
                         ("gen", "score", "val", "test", "n_params", "name")},
                      "exact": exact, "partial": partial,
                      "n_gates": len(p["spec"] or [])})
    if not progs:
        return None
    best = max(progs, key=lambda q: q["score"])
    return {
        "n_progs": len(progs),
        "max_gen": max((p["gen"] for p in run["programs"]), default=-1) + 1,
        "first_exact_gen": min((p["gen"] for p in progs if p["exact"] == 1.0),
                               default=None),
        "n_exact": sum(1 for p in progs if p["exact"] == 1.0),
        "mean_partial": sum(p["partial"] for p in progs) / len(progs),
        "max_partial": max(p["partial"] for p in progs),
        "best": best,
        "trajectory": sorted(progs, key=lambda q: q["gen"]),
    }


# ----------------------------------------------------------------- SU(2) ring

def su2_stats(run):
    progs = []
    for p in ok_progs(run):
        by_pair = defaultdict(dict)
        for it in p["spec"] or []:
            if not isinstance(it, dict):
                continue
            g = str(it.get("gate", "")).upper()
            if g in ("XX", "YY", "ZZ") and "wires" in it:
                by_pair[frozenset(int(w) for w in it["wires"])][g] = it.get("param")
        tied = sum(1 for ax in by_pair.values()
                   if {"XX", "YY", "ZZ"} <= set(ax)
                   and len({ax[a] for a in ("XX", "YY", "ZZ")}) == 1)
        progs.append({**{k: p[k] for k in
                         ("gen", "score", "val", "test", "n_params", "name")},
                      "n_gates": len(p["spec"] or []),
                      "pairs_ising": len(by_pair), "pairs_tied": tied})
    if not progs:
        return None
    best = max(progs, key=lambda q: q["score"])
    return {
        "n_progs": len(progs),
        "max_gen": max((p["gen"] for p in run["programs"]), default=-1) + 1,
        "n_with_tied": sum(1 for p in progs if p["pairs_tied"] > 0),
        "n_empty": sum(1 for p in progs if p["n_gates"] == 0),
        "best": best,
        "trajectory": sorted(progs, key=lambda q: q["gen"]),
    }


# ------------------------------------------------------------------ narration

def vocab(run, pattern):
    items = [p for p in run["programs"] if (p.get("desc") or "").strip()]
    hits = [p for p in items if pattern.search(p["desc"])]
    return {"n_desc": len(items), "n_hits": len(hits),
            "frac": (len(hits) / len(items)) if items else None,
            "gens": [p["gen"] for p in hits]}


out = {}
for tag, run in RUNS.items():
    task = run["task"]
    rec = {"task": task, "model": run["model"], "context": run["context"]}
    if task == "ttt":
        rec["motif"] = ttt_stats(run)
        rec["vocab"] = vocab(run, LEAK)
    elif task == "sn":
        rec["sym"] = sn_stats(run)
        rec["vocab"] = vocab(run, SYM_WORD)
    else:
        rec["sym"] = su2_stats(run)
        rec["vocab"] = vocab(run, SYM_WORD)
    rec["cost"] = round(sum(p.get("cost") or 0 for p in run["programs"]), 2)
    out[tag] = rec

(SP / "zcstats.json").write_text(json.dumps(out, indent=2, default=str))

# ------------------------------------------------------------------- printout
print("=" * 78)
print("ZERO-CONTEXT TIC-TAC-TOE (80 generations, no task name, secret permutation)")
print("=" * 78)
for tag in ("zc_ttt_haiku", "zc_ttt_sonnet", "zc_ttt_gpt56sol"):
    r = out[tag]; m = r["motif"]; b = m["best"]; pop = m["population"]
    print(f"\n--- {tag}  ({m['max_gen']} gens, ${r['cost']})")
    print(f"  programs {m['n_progs']}, using triples {m['n_using_triples']}")
    frac_txt = f" = {pop['frac']:.3f}" if pop["n"] else ""
    print(f"  POPULATION on lines: {pop['n_win']}/{pop['n']}{frac_txt}"
          f"   (uniform null {m['p_uni']:.3f}, connectivity null {m['p_e2']:.3f})")
    if pop["n"]:
        print(f"    p_uni={pop['p_uni']:.3g}  p_conn={pop['p_e2']:.3g}"
              f"   by edge-degree {pop['by_deg']}")
    print(f"  distinct lines found anywhere: {m['lines_found_anywhere']}/8")
    print(f"  HIDDEN lines found anywhere:   {m['hidden_found_anywhere']}/2")
    print(f"  first line in best lineage: gen {m['first_hit_gen']}")
    print(f"  BEST gen{b['gen']}: score {b['score']:.4f}  val {b['val']}  "
          f"test {b['test']}  params {b['n_params']}  "
          f"triples {b['n_win']}/{b['n_tr']} on lines")
    v = r["vocab"]
    print(f"  game vocabulary in {v['n_hits']}/{v['n_desc']} descriptions "
          f"({(v['frac'] or 0)*100:.0f}%)")

print()
print("=" * 78)
print("GRAPH TASK: S_8 equivariance, hinted vs zero-context")
print("=" * 78)
print(f"{'run':<24}{'gens':>5}{'best gen':>9}{'score':>8}{'test':>7}{'prm':>5}"
      f"{'exact':>7}{'partial':>9}{'1st-eq':>8}{'#exact':>7}")
for tag in sorted(out):
    r = out[tag]
    if r["task"] != "sn" or not r.get("sym"):
        continue
    s = r["sym"]; b = s["best"]
    print(f"{tag:<24}{s['max_gen']:>5}{b['gen']:>9}{b['score']:>8.4f}"
          f"{(b['test'] or 0):>7.3f}{b['n_params']:>5}{b['exact']:>7.2f}"
          f"{b['partial']:>9.3f}{str(s['first_exact_gen']):>8}{s['n_exact']:>7}")

print()
print("=" * 78)
print("SPIN TASK: Heisenberg tying, hinted vs zero-context")
print("=" * 78)
print(f"{'run':<24}{'gens':>5}{'best gen':>9}{'score':>8}{'test':>7}{'prm':>5}"
      f"{'gates':>7}{'tied':>6}{'#tied':>7}{'#empty':>8}")
for tag in sorted(out):
    r = out[tag]
    if r["task"] != "su2" or not r.get("sym"):
        continue
    s = r["sym"]; b = s["best"]
    print(f"{tag:<24}{s['max_gen']:>5}{b['gen']:>9}{b['score']:>8.4f}"
          f"{(b['test'] or 0):>7.3f}{b['n_params']:>5}{b['n_gates']:>7}"
          f"{b['pairs_tied']:>6}{s['n_with_tied']:>7}{s['n_empty']:>8}")

print(f"\nwrote {SP / 'zcstats.json'}")
