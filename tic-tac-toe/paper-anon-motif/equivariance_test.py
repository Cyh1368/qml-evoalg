"""Rigorous test: is the evolved block literally invariant under relabelling?

Proxy metrics (shared params, uniform degree) can be produced by the score's
parameter-economy term alone. The exact test is whether permuting the eight wire
labels maps the gate multiset onto itself, parameter identities included. Only a
genuinely S_8-equivariant block passes that.
"""
import ast
import json
import random
import sqlite3
from collections import Counter
from itertools import combinations
from pathlib import Path

DBS = Path("/tmp/sym_dbs")
SYM = {"CZ", "ZZ", "XX", "YY"}          # gates whose wire order does not matter


def spec_of(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == "ANSATZ_SPEC":
                    try:
                        return ast.literal_eval(n.value)
                    except ValueError:
                        return None
    return None


def canon(spec, perm=None):
    """Multiset of gates, wires relabelled by perm, parameters kept as identities."""
    p = perm or list(range(8))
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
            if g in SYM:
                w = tuple(sorted(w))
        else:
            continue
        out.append((g, w, par))
    return Counter(out)


def equivariance(spec, trials=200, seed=0):
    """Fraction of random relabellings that leave the block unchanged."""
    base = canon(spec)
    if not base:
        return 0.0, 0.0
    rng = random.Random(seed)
    ok = 0
    frac = []
    for _ in range(trials):
        p = list(range(8))
        rng.shuffle(p)
        c = canon(spec, p)
        ok += (c == base)
        # how much of the block is preserved, for partial credit
        inter = sum((base & c).values())
        frac.append(inter / sum(base.values()))
    return ok / trials, sum(frac) / len(frac)


def transposition_orbit(spec):
    """Invariance under adjacent transpositions generates S_8; report each."""
    base = canon(spec)
    res = []
    for i, j in combinations(range(8), 2):
        p = list(range(8))
        p[i], p[j] = p[j], p[i]
        res.append(canon(spec, p) == base)
    return sum(res), len(res)


rows_out = []
for db in sorted(DBS.glob("transfer_sn__*.sqlite")):
    run = db.stem.split("__")[1]
    try:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10) as c:
            c.row_factory = sqlite3.Row
            rows = c.execute("SELECT generation, combined_score, correct, code, "
                             "public_metrics FROM programs").fetchall()
    except sqlite3.OperationalError:
        continue
    progs = []
    for r in rows:
        if not r["correct"] or r["combined_score"] is None:
            continue
        s = spec_of(r["code"])
        if s is None:
            continue
        pm = json.loads(r["public_metrics"]) if r["public_metrics"] else {}
        exact, partial = equivariance(s)
        t_ok, t_tot = transposition_orbit(s)
        progs.append({"gen": r["generation"], "score": r["combined_score"],
                      "test": pm.get("test_accuracy_mean"), "np": pm.get("n_params"),
                      "exact": exact, "partial": partial,
                      "transpositions": f"{t_ok}/{t_tot}", "spec": s})
    if not progs:
        continue
    best = max(progs, key=lambda p: p["score"])
    first_eq = min((p["gen"] for p in progs if p["exact"] == 1.0), default=None)
    rows_out.append((run, best, first_eq, progs))

print("%-28s %5s %7s %6s %8s %9s %14s" %
      ("run", "gen", "test", "prms", "exact-eq", "partial", "transpositions"))
print("-" * 86)
for run, b, first_eq, _ in rows_out:
    print("%-28s %5d %7.3f %6s %8.2f %9.3f %14s" %
          (run, b["gen"], b["test"] or 0, b["np"], b["exact"], b["partial"],
           b["transpositions"]))
    if first_eq is not None:
        print("%-28s   first exactly-equivariant program at generation %d" % ("", first_eq))

Path("/tmp/equivariance.json").write_text(json.dumps(
    {r: {"best": {k: v for k, v in b.items() if k != "spec"},
         "first_equivariant_gen": fe,
         "trajectory": [{k: v for k, v in p.items() if k != "spec"} for p in ps]}
     for r, b, fe, ps in rows_out}, indent=2, default=str))

# show the winning block
best_run = max(rows_out, key=lambda t: t[1]["score"])
print("\nBest overall: %s, generation %d" % (best_run[0], best_run[1]["gen"]))
for g in best_run[1]["spec"]:
    print("   ", g)
