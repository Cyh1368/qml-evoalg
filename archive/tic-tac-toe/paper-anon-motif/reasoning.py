"""Pull each proposer's own description of every edit it made."""
import json
import re
import sqlite3
from pathlib import Path

DBS = Path("/tmp/anon_dbs")
OUT = {}

# words that would betray knowledge of the underlying game
LEAK = re.compile(r"tic.?tac|noughts|board|row|column|diagonal|corner|"
                  r"centre|center|win(ning)?\s*line|three.in.a.row", re.I)

for tag in ("leaky", "haiku", "sonnet", "gpt56sol"):
    db = DBS / f"{tag}.sqlite"
    if not db.exists():
        continue
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute("SELECT generation, combined_score, correct, metadata "
                         "FROM programs ORDER BY generation").fetchall()
    items = []
    for r in rows:
        m = json.loads(r["metadata"]) if r["metadata"] else {}
        desc = (m.get("patch_description") or "").strip()
        items.append({
            "gen": r["generation"],
            "score": r["combined_score"],
            "correct": bool(r["correct"]),
            "name": (m.get("patch_name") or "").strip(),
            "desc": desc,
            "model": m.get("model_name"),
            "leak_hits": sorted({w.group(0).lower()
                                 for w in LEAK.finditer(desc)}),
        })
    OUT[tag] = items

Path("/tmp/reasoning.json").write_text(json.dumps(OUT, indent=2))

for tag, items in OUT.items():
    n_leak = sum(1 for i in items if i["leak_hits"])
    print(f"\n########## {tag}: {len(items)} generations, "
          f"{n_leak} descriptions containing game vocabulary")
    for i in items:
        if i["desc"]:
            flag = " [GAME-WORDS: %s]" % ",".join(i["leak_hits"]) if i["leak_hits"] else ""
            sc = f"{i['score']:.4f}" if i["score"] is not None else "  n/a "
            print(f"  gen {i['gen']:>2} {sc} {i['name'][:34]:<34}{flag}")
