"""Assemble labelling/symmetry_report.html from stats.json + curated examples."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, "labelling/stats.json")))
rows = [r for r in json.load(open(os.path.join(ROOT, "labelling/labels.json")))
        if r["parsed"] and r["own"]]

def pick(pred, key=lambda r: r["score"]):
    return max((r for r in rows if pred(r)), key=key)

best_front = pick(lambda r: "all-double-exact" in r["circuit"]["labels"])
best_weak = pick(lambda r: r["arm"] == "weak" and r["setting"] == "scratch")

def ex(r):
    return {"run": r["run_id"], "gen": r["generation"], "score": r["score"],
            "model": (r["model"] or "").split("/")[-1],
            "layers": [{"gates": l["gates"], "n1": l["n_1q"], "n2": l["n_2q"],
                        "wires": l["n_wires"], "pairs": l["n_pairs"],
                        "params": l["n_params"], "labels": l["labels"]}
                       for l in r["circuit"]["layers"]]}

S["examples"] = {"frontier": ex(best_front), "weak": ex(best_weak)}
blob = json.dumps(S, separators=(",", ":"))
html = open(os.path.join(ROOT, "labelling/report_template.html")).read()
out = html.replace("/*__DATA__*/null", blob)
open(os.path.join(ROOT, "labelling/symmetry_report.html"), "w").write(out)
print("wrote labelling/symmetry_report.html", len(out), "bytes")
