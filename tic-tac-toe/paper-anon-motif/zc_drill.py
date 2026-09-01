"""Drill-downs the summary table cannot show.

1. The GPT-5.6-sol zero-context tic-tac-toe arm shows on-line enrichment. Is it
   score-driven, or another episode of recalled geometry?
2. Did any zero-context graph arm even propose permutation symmetry in words?
3. What did the hinted graph arm say at the generation it became equivariant?
"""
import json
import re
from itertools import combinations
from pathlib import Path

SP = Path(__file__).resolve().parent
D = json.loads((SP / "zcdata.json").read_text())
RUNS, KEYS = D["runs"], D["keys"]

WIN = {frozenset(t) for t in KEYS["ttt"]["win"]}
EDGES = {frozenset(e) for e in KEYS["ttt"]["edges"]}
# the unpermuted row-major board, which is what a recalling model would target
INV = json.loads(Path("/dev/stdin").read_text()) if False else None
LEAK = re.compile(r"tic.?tac|noughts|board|row|column|diagonal|corner|"
                  r"centre|center|win(ning)?\s*line|three.in.a.row", re.I)
SYM_WORD = re.compile(r"symmetr|invarian|equivarian|permut|relabel|exchange|"
                      r"isotropic|heisenberg|spin|su\(2\)|s_?8", re.I)


def triples(spec):
    return [frozenset(int(w) for w in it["wires"])
            for it in (spec or [])
            if isinstance(it, dict)
            and str(it.get("gate", "")).upper() in ("ZZZ", "CCRZ")
            and isinstance(it.get("wires"), (list, tuple)) and len(it["wires"]) == 3]


def deg(t):
    return sum(1 for pr in combinations(sorted(t), 2) if frozenset(pr) in EDGES)


print("=" * 78)
print("1. Every triple-gate placed by the zero-context GPT-5.6-sol tic-tac-toe arm")
print("=" * 78)
run = RUNS["zc_ttt_gpt56sol"]
for p in sorted(run["programs"], key=lambda q: q["gen"]):
    tr = triples(p["spec"])
    if not tr:
        continue
    marks = ", ".join(
        f"{tuple(sorted(t))}{'  <-LINE' if t in WIN else ''}[deg{deg(t)}]" for t in tr)
    sc = f"{p['score']:.4f}" if p["score"] is not None else "  n/a "
    flag = " GAME-WORDS" if p.get("desc") and LEAK.search(p["desc"]) else ""
    print(f"  gen {p['gen']:>2} score {sc} ok={int(p['correct'])} "
          f"{(p['name'] or '')[:30]:<30}{flag}")
    print(f"          {marks}")

print()
print("=" * 78)
print("2. Zero-context graph arms: did anything even mention symmetry?")
print("=" * 78)
for tag in ("zc_sn_haiku", "zc_sn_sonnet", "zc_sn_gpt56sol"):
    run = RUNS[tag]
    hits = [p for p in run["programs"]
            if (p.get("desc") or "") and SYM_WORD.search(p["desc"])]
    print(f"\n--- {tag}: {len(hits)} of "
          f"{sum(1 for p in run['programs'] if p.get('desc'))} descriptions")
    for p in sorted(hits, key=lambda q: q["gen"])[:8]:
        words = sorted({w.group(0).lower() for w in SYM_WORD.finditer(p["desc"])})
        sc = f"{p['score']:.4f}" if p["score"] is not None else "  n/a "
        print(f"  gen {p['gen']:>2} {sc} {(p['name'] or '')[:32]:<32} {words}")

print()
print("=" * 78)
print("3. The hinted graph arm at the generation it became equivariant")
print("=" * 78)
run = RUNS["hint_sn_gpt56sol_r2"]
for p in sorted(run["programs"], key=lambda q: q["gen"]):
    if 30 <= p["gen"] <= 35 and p.get("desc"):
        print(f"\n  gen {p['gen']} score "
              f"{p['score'] if p['score'] is None else round(p['score'], 4)} "
              f"name={p['name']}")
        print("   ", " ".join(p["desc"].split())[:520])

print()
print("=" * 78)
print("4. Best zero-context graph proposals, for contrast")
print("=" * 78)
for tag in ("zc_sn_gpt56sol", "zc_sn_haiku"):
    run = RUNS[tag]
    ok = [p for p in run["programs"] if p["correct"] and p["score"] is not None]
    best = max(ok, key=lambda q: q["score"])
    print(f"\n--- {tag}: best gen {best['gen']} score {best['score']:.4f} "
          f"test {best['test']} params {best['n_params']}  name={best['name']}")
    print("   ", " ".join((best["desc"] or "").split())[:520])

print()
print("=" * 78)
print("5. The empty-circuit winner on the spin task")
print("=" * 78)
run = RUNS["zc_su2_sonnet"]
ok = [p for p in run["programs"] if p["correct"] and p["score"] is not None]
best = max(ok, key=lambda q: q["score"])
print(f"  best gen {best['gen']} score {best['score']:.4f} gates "
      f"{len(best['spec'] or [])} params {best['n_params']} "
      f"val {best['val']} test {best['test']}")
print(f"  name={best['name']}")
print("   ", " ".join((best["desc"] or "").split())[:600])
empties = [p for p in ok if not (p["spec"] or [])]
print(f"\n  programs with an empty ansatz block: {len(empties)} of {len(ok)}")
print(f"  their scores: {sorted({round(p['score'], 4) for p in empties})}")
print(f"  seed (gen 0) score: "
      f"{[round(p['score'], 4) for p in ok if p['gen'] == 0]}")
