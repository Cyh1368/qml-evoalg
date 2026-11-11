"""Did the search find the symmetry of each task?

transfer_sn : label is exactly an S_8 graph invariant. An S_8-equivariant block
              treats all 8 wires alike (one shared single-qubit parameter) and
              uses pair-sets closed under node relabelling, ideally all 28 pairs
              with one shared parameter.
transfer_su2: every state is a spin singlet. The SU(2)-invariant two-body
              coupling is Heisenberg, XX+YY+ZZ on a pair with ONE shared
              parameter. The schema offers XX/YY/ZZ separately, so tying them is
              a deliberate, score-driven choice.
"""
import ast
import json
import sqlite3
from collections import defaultdict
from itertools import combinations
from pathlib import Path

DBS = Path("/tmp/sym_dbs")
N = 8
ALL_PAIRS = {frozenset(p) for p in combinations(range(N), 2)}


def spec_of(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "ANSATZ_SPEC":
                    try:
                        return ast.literal_eval(node.value)
                    except ValueError:
                        return None
    return None


def sn_metrics(spec):
    """How permutation-equivariant is this block?"""
    single = defaultdict(set)      # param -> wires it acts on
    two = defaultdict(set)         # param -> pairs it acts on
    fixed_pairs = set()
    for it in spec or []:
        if not isinstance(it, dict):
            continue
        g = str(it.get("gate", "")).upper()
        if g in ("RX", "RY", "RZ") and "wire" in it:
            single[it.get("param")].add(int(it["wire"]))
        elif g in ("CRX", "CRY", "CRZ") and "wires" in it:
            two[it.get("param")].add(frozenset(int(w) for w in it["wires"]))
        elif g in ("CNOT", "CZ") and "wires" in it:
            fixed_pairs.add(frozenset(int(w) for w in it["wires"]))
    # a fully equivariant single-qubit layer = one param covering all 8 wires
    best_single = max((len(w) for w in single.values()), default=0)
    # a fully equivariant coupling layer = one param covering all 28 pairs
    best_two = max((len(p) for p in two.values()), default=0)
    used_pairs = set().union(*two.values()) if two else set()
    used_pairs |= fixed_pairs
    # degree sequence of the interaction graph; equivariant => all degrees equal
    deg = defaultdict(int)
    for p in used_pairs:
        for q in p:
            deg[q] += 1
    degs = [deg.get(q, 0) for q in range(N)]
    n_params = len(set(list(single) + list(two)) - {None})
    return {
        "n_params": n_params,
        "max_wires_per_single_param": best_single,
        "max_pairs_per_two_param": best_two,
        "n_pairs_used": len(used_pairs),
        "pair_coverage": len(used_pairs) / 28,
        "degree_uniform": len(set(degs)) == 1,
        "degrees": degs,
    }


def su2_metrics(spec):
    """Does the block use Heisenberg (SU(2)-invariant) couplings?"""
    by_pair = defaultdict(dict)   # pair -> {axis: param}
    for it in spec or []:
        if not isinstance(it, dict):
            continue
        g = str(it.get("gate", "")).upper()
        if g in ("XX", "YY", "ZZ") and "wires" in it:
            by_pair[frozenset(int(w) for w in it["wires"])][g] = it.get("param")
    n_pairs = len(by_pair)
    complete = 0      # all three axes present
    tied = 0          # all three present AND sharing one parameter
    for axes in by_pair.values():
        if {"XX", "YY", "ZZ"} <= set(axes):
            complete += 1
            if len(set(axes[a] for a in ("XX", "YY", "ZZ"))) == 1:
                tied += 1
    return {
        "pairs_with_ising": n_pairs,
        "pairs_all_three_axes": complete,
        "pairs_heisenberg_tied": tied,
        "heisenberg_fraction": (tied / n_pairs) if n_pairs else 0.0,
    }


out = {}
for db in sorted(DBS.glob("*.sqlite")):
    task, run = db.stem.split("__")
    try:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10) as c:
            c.row_factory = sqlite3.Row
            rows = c.execute("SELECT generation, combined_score, correct, code, "
                             "public_metrics FROM programs").fetchall()
    except sqlite3.OperationalError:
        continue   # run died before writing any program
    progs = []
    for r in rows:
        if not r["correct"] or r["combined_score"] is None:
            continue
        spec = spec_of(r["code"])
        if spec is None:
            continue
        pm = json.loads(r["public_metrics"]) if r["public_metrics"] else {}
        m = sn_metrics(spec) if task == "transfer_sn" else su2_metrics(spec)
        progs.append({"gen": r["generation"], "score": r["combined_score"],
                      "val": pm.get("validation_accuracy_mean"),
                      "test": pm.get("test_accuracy_mean"),
                      "np": pm.get("n_params"), **m})
    if not progs:
        continue
    best = max(progs, key=lambda p: p["score"])
    out[f"{task}/{run}"] = {"n": len(progs), "best": best, "all": progs}

print(json.dumps({k: {"n": v["n"], "best": v["best"]} for k, v in out.items()},
                 indent=2, default=str))
Path("/tmp/sym_results.json").write_text(json.dumps(out, indent=2, default=str))
