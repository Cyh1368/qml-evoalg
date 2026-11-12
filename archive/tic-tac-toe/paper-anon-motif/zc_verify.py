"""Check whether the zero-context enrichment is discovery or the coincidence triple.

The permuted winning lines and the winning lines of an unpermuted row-major board
overlap in exactly one triple. If the enrichment is carried by that triple, it is
recall scoring a lucky hit, not search.
"""
import json
import math
from collections import Counter
from itertools import combinations
from pathlib import Path

SP = Path(__file__).resolve().parent
D = json.loads((SP / "zcdata.json").read_text())
WIN = {frozenset(t) for t in D["keys"]["ttt"]["win"]}
EDGES = {frozenset(e) for e in D["keys"]["ttt"]["edges"]}

ROWMAJOR = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
            (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
RM = {frozenset(t) for t in ROWMAJOR}

print("true permuted winning lines :", sorted(tuple(sorted(t)) for t in WIN))
print("unpermuted row-major lines  :", sorted(tuple(sorted(t)) for t in RM))
overlap = WIN & RM
print("overlap (coincidence triples):", sorted(tuple(sorted(t)) for t in overlap))


def deg(t):
    return sum(1 for pr in combinations(sorted(t), 2) if frozenset(pr) in EDGES)


def binom_sf(k, n, p):
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))


def triples(spec):
    return [frozenset(int(w) for w in it["wires"])
            for it in (spec or [])
            if isinstance(it, dict)
            and str(it.get("gate", "")).upper() in ("ZZZ", "CCRZ")
            and isinstance(it.get("wires"), (list, tuple)) and len(it["wires"]) == 3]


p_uni = len(WIN) / math.comb(9, 3)
s2 = [t for t in (frozenset(x) for x in combinations(range(9), 3)) if deg(t) == 2]
p_e2 = sum(1 for t in s2 if t in WIN) / len(s2)

for tag in ("zc_ttt_haiku", "zc_ttt_sonnet", "zc_ttt_gpt56sol"):
    run = D["runs"][tag]
    ok = [p for p in run["programs"] if p["correct"] and p["score"] is not None]
    placements = [t for p in ok for t in triples(p["spec"])]
    c = Counter(placements)
    n_win = sum(1 for t in placements if t in WIN)
    coincidence = sum(1 for t in placements if t in overlap)

    # de-duplicated view: each distinct triple counted once, which removes the
    # pseudoreplication caused by a triple being inherited down a lineage
    distinct = set(placements)
    d_win = sum(1 for t in distinct if t in WIN)

    print(f"\n=== {tag}")
    print(f"  gate placements {len(placements)}, of which on a true line {n_win}")
    print(f"  carried by the coincidence triple {sorted(tuple(sorted(t)) for t in overlap)}"
          f": {coincidence}")
    print(f"  on-line placements excluding it: {n_win - coincidence}")
    print(f"  distinct triples used: {len(distinct)}, of which lines: {d_win}")
    if distinct:
        print(f"    p_uni(distinct)  = {binom_sf(d_win, len(distinct), p_uni):.4g}")
        print(f"    p_conn(distinct) = {binom_sf(d_win, len(distinct), p_e2):.4g}")
    print("  most-used triples:")
    for t, k in c.most_common(5):
        tags = []
        if t in WIN:
            tags.append("TRUE-LINE")
        if t in RM:
            tags.append("row-major-line")
        print(f"    {tuple(sorted(t))} x{k}  deg{deg(t)}  {' '.join(tags)}")
