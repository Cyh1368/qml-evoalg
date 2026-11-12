"""Did the proposers reason about symmetry, or just build dense circuits?"""
import json
import re
import sqlite3
from pathlib import Path

DBS = Path("/tmp/sym_dbs")

# vocabulary that would indicate explicit symmetry reasoning
SYM = re.compile(r"permut|symmetr|equivar|invaria|exchange|interchange|"
                 r"relabel|isomorph|orbit|S_?8|全排列|graph invariant|"
                 r"node label|vertex label|all pairs|complete graph|"
                 r"singlet|spin|SU\(2\)|heisenberg|rotation.?invariant", re.I)
# narrower: only true symmetry claims, not "all pairs"
STRICT = re.compile(r"permut|symmetr|equivar|invaria|relabel|isomorph|orbit|"
                    r"exchange|singlet|SU\(2\)|heisenberg", re.I)

out = {}
for db in sorted(DBS.glob("*.sqlite")):
    task, run = db.stem.split("__")
    try:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10) as c:
            c.row_factory = sqlite3.Row
            rows = c.execute("SELECT generation, combined_score, correct, metadata "
                             "FROM programs ORDER BY generation").fetchall()
    except sqlite3.OperationalError:
        continue
    items = []
    for r in rows:
        m = json.loads(r["metadata"]) if r["metadata"] else {}
        d = (m.get("patch_description") or "").strip()
        if not d:
            continue
        items.append({"gen": r["generation"], "score": r["combined_score"],
                      "name": (m.get("patch_name") or "").strip(),
                      "desc": d,
                      "hits": sorted({w.group(0).lower() for w in STRICT.finditer(d)})})
    if items:
        out[f"{task}/{run}"] = items

Path("/tmp/sym_reasoning.json").write_text(json.dumps(out, indent=2))

for key, items in out.items():
    n = sum(1 for i in items if i["hits"])
    first = next((i["gen"] for i in items if i["hits"]), None)
    print(f"\n##### {key}: {n}/{len(items)} proposals use symmetry vocabulary"
          f"  (first at gen {first})")
    for i in items:
        if i["hits"]:
            sc = f"{i['score']:.4f}" if i["score"] is not None else " n/a  "
            print(f"   gen {i['gen']:>3} {sc}  {i['name'][:38]:<38} {','.join(i['hits'])[:60]}")
