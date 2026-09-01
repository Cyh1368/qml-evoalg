"""Did GPT-5.6-sol place gates on the REMEMBERED lines rather than the true ones?

It stated it was targeting "the eight winning lines of a 3x3 board". Under the
secret permutation those remembered lines are wrong. If this is recall, its
gates should match a naive unpermuted layout, not the true permuted lines.
"""
import json
from pathlib import Path

SP = Path(__file__).resolve().parent
runs = json.loads((SP / "rundata.json").read_text())

TRUE = {frozenset(t) for t in runs["gpt56sol"]["win"]}

# Candidate layouts a model might assume if it thinks "3x3 board".
ROWMAJOR = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
RING     = [(0,1,2),(7,8,3),(6,5,4),(0,7,6),(1,8,5),(2,3,4),(0,8,4),(2,8,6)]
CANDS = {"true permuted lines": TRUE,
         "row-major 3x3 (naive recall)": {frozenset(t) for t in ROWMAJOR},
         "ring+centre (benchmark layout)": {frozenset(t) for t in RING}}


def triples(spec):
    return [frozenset(int(w) for w in it["wires"])
            for it in (spec or [])
            if isinstance(it, dict)
            and str(it.get("gate", "")).upper() in ("ZZZ", "CCRZ")
            and isinstance(it.get("wires"), (list, tuple)) and len(it["wires"]) == 3]


progs = {p["gen"]: p for p in runs["gpt56sol"]["programs"]}
print("GPT-5.6-sol, the generations where it claimed to target winning lines\n")
hdr = f"{'gen':>4} {'score':>7} {'gates':>6} " + " ".join(f"{k:>30}" for k in CANDS)
print(hdr)
print("-" * len(hdr))
for g in (3, 7, 8, 9, 10):
    p = progs.get(g)
    if not p:
        continue
    tr = triples(p["spec"])
    row = f"{g:>4} {p['score']:>7.4f} {len(tr):>6} "
    for name, ref in CANDS.items():
        hit = sum(1 for t in tr if t in ref)
        row += f"{hit:>21}/{len(tr):<8}"
    print(row)

print("\nBest circuit (gen 20) for comparison:")
tr = triples(progs[20]["spec"])
for name, ref in CANDS.items():
    print(f"  {name:<32}: {sum(1 for t in tr if t in ref)}/{len(tr)}")

print("\nActual triples placed at gen 9 ('winning_line_iqp'):")
print(" ", sorted(tuple(sorted(t)) for t in triples(progs[9]["spec"])))
print("true permuted lines:", sorted(tuple(sorted(t)) for t in TRUE))
print("row-major lines    :", sorted(tuple(sorted(t)) for t in ROWMAJOR))
