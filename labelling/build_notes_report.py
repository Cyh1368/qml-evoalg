"""Assemble labelling/patch_notes_report.html from note_stats.json + examples."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, "labelling/note_stats.json")))
rows = [r for r in json.load(open(os.path.join(ROOT, "labelling/note_labels.json")))
        if r["own"] and r["parsed"] and len(r["note"]["patch_description"].strip()) >= 20]
idx = {(r["run_id"], r["generation"]): r for r in rows}

# hand audit
A = json.load(open(os.path.join(ROOT, "labelling/audit_notes.json")))["sample"]
S["audit"] = {"n": len(A), "n_pos": sum(h["build"] for h in A)}

PICKS = [
    ("sn-transfer-or_frontier_r1", 18, "frontier", "says it and builds it"),
    ("sn-transfer-or_weak_r5", 2, "weak", "says it, builds 15 of 28 pairs"),
    ("sn-transfer-frw3_mid_r5", 7, "mid", "says all-to-all, builds a 12-edge hypercube"),
    ("sn-transfer-or_frontier_r1", 45, "frontier", "builds it, never mentions it"),
]
ex = []
for rid, gen, arm, why in PICKS:
    r = idx[(rid, gen)]
    ex.append({"run": rid, "gen": gen, "arm": arm, "why": why,
               "score": r["score"], "pairs": r["note"]["union_pairs"],
               "name": r["note"]["patch_name"], "flags": r["note"]["flags"],
               "text": r["note"]["patch_description"][:520]})
S["examples"] = ex

blob = json.dumps(S, separators=(",", ":"))
html = open(os.path.join(ROOT, "labelling/notes_report_template.html")).read()
out = html.replace("/*__DATA__*/null", blob)
open(os.path.join(ROOT, "labelling/patch_notes_report.html"), "w").write(out)
print("wrote labelling/patch_notes_report.html", len(out), "bytes")
