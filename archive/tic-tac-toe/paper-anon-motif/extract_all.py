"""Dump every run (leaky + three anonymized arms) to one JSON for local analysis."""
import ast
import json
import sqlite3
from pathlib import Path

DBS = Path("/tmp/anon_dbs")
META = json.loads(
    Path("/home/ch2499/project/motif_anon_haiku/permutation_meta.json").read_text())

# Leaky run used the Meyer ring+center labelling, with these constants sitting
# verbatim in the seed program the proposer model was shown.
LEAKY_WIN = [(0,1,2),(7,8,3),(6,5,4),(0,7,6),(1,8,5),(2,3,4),(0,8,4),(2,8,6)]
LEAKY_EDGES = [(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,0),(1,8),(3,8),(5,8),(7,8)]

RUNS = {
    "leaky":    {"db": "leaky.sqlite",    "win": LEAKY_WIN, "edges": LEAKY_EDGES,
                 "model": "haiku-4.5 / gpt-5-mini / gemini-3-flash (bandit)"},
    "haiku":    {"db": "haiku.sqlite",    "win": META["permuted_win_lines"],
                 "edges": META["permuted_hardware_edges"], "model": "claude-haiku-4.5"},
    "sonnet":   {"db": "sonnet.sqlite",   "win": META["permuted_win_lines"],
                 "edges": META["permuted_hardware_edges"], "model": "claude-sonnet-5"},
    "gpt56sol": {"db": "gpt56sol.sqlite", "win": META["permuted_win_lines"],
                 "edges": META["permuted_hardware_edges"], "model": "gpt-5.6-sol"},
}


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


out = {}
for tag, cfg in RUNS.items():
    db = DBS / cfg["db"]
    if not db.exists():
        continue
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute("SELECT id, code, generation, combined_score, correct, "
                         "public_metrics FROM programs").fetchall()
    progs = []
    for r in rows:
        spec = spec_of(r["code"])
        pm = json.loads(r["public_metrics"]) if r["public_metrics"] else {}
        progs.append({
            "gen": r["generation"], "score": r["combined_score"],
            "correct": bool(r["correct"]),
            "spec": spec,
            "val": pm.get("validation_accuracy_mean"),
            "test": pm.get("test_accuracy_mean"),
            "train": pm.get("train_accuracy_mean"),
            "gap": pm.get("generalization_gap_mean"),
            "n_params": pm.get("n_params"),
            "depth": pm.get("depth_mean"),
        })
    out[tag] = {"model": cfg["model"], "win": [list(t) for t in cfg["win"]],
                "edges": [list(e) for e in cfg["edges"]], "programs": progs}

print(json.dumps(out))
