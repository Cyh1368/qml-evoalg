"""Compile WP-REPAIR and WP-SEARCH results into a compact markdown summary for
the manuscript. Reads the result JSONs only; writes research/results_summary.md.

Usage::

    python3 -m research.compile_results \
        --repair research/experiments/repair/repair_results.json \
        --search research/search/pilot_analysis.json \
        --out research/results_summary.md
"""
import argparse
import json
import os
import sys


def _fmt(x, nd=5):
    if x is None:
        return "n/a"
    return ("%+." + str(nd) + "f") % x


def repair_section(path):
    if not path or not os.path.exists(path):
        return "_WP-REPAIR results not available yet._\n"
    d = json.load(open(path))
    L = ["## WP-REPAIR — causal symmetry repair (family `%s`)" % d.get("family"), ""]
    L.append("- group order %d; arms %s; etas %s; teacher draws %s; opt seeds %d; "
             "budgets %s" % (d.get("group_order", 12), ",".join(d["arms"]),
                             d["etas"], d["teacher_seeds"], len(d["opt_seeds"]),
                             d["budgets"]))
    L.append("- Scope: %s" % d["scope"])
    L.append("")
    L.append("| eta | steps | contrast | n | mean diff (a-b) | 95% CI | frac a better |")
    L.append("|---|---|---|---|---|---|---|")
    for c in d["contrasts"]:
        b = c.get("bootstrap") or {}
        L.append("| %.1f | %d | %s vs %s | %d | %s | [%s, %s] | %.2f |"
                 % (c["eta"], c["steps"], c["a"], c["b"], c["n_pairs"],
                    _fmt(c["mean_diff_a_minus_b"]), _fmt(b.get("ci95_low")),
                    _fmt(b.get("ci95_high")), c["frac_a_better"] or 0))
    L.append("")
    L.append("_Negative mean diff => arm `a` has lower dev risk (better). Expected: "
             "repaired beats gate-count-matched `control` at eta=0; control beats "
             "repaired at eta=1 (repaired is pinned at the invariant floor "
             "eta^2 E[b^2])._")
    return "\n".join(L)


def search_section(path):
    if not path or not os.path.exists(path):
        return "_WP-SEARCH analysis not available yet._\n"
    d = json.load(open(path))
    L = ["## WP-SEARCH — matched-budget search arms", ""]
    L.append("- runs %d; families %s; treatments %s"
             % (d["n_runs"], d["families"], d["treatments"]))
    L.append("")
    L.append("### Arm summary (mean dev risk / invalid / tokens)")
    L.append("| family | arm | n | mean dev risk | mean invalid | mean tokens |")
    L.append("|---|---|---|---|---|---|")
    for s in d["arm_summary"]:
        L.append("| %s | %s | %d | %.5f | %.1f | %.0f |"
                 % (s["family"], s["arm"], s["n_runs"], s["mean_dev_risk"],
                    s["mean_invalid"], s["mean_tokens"]))
    L.append("")
    L.append("### Primary contrast: llm-verify - llm-fitness (negative => verifier helps)")
    L.append("| family | treatment | n | mean diff | 95% CI | p | frac verify better |")
    L.append("|---|---|---|---|---|---|---|")
    for c in d["primary"]:
        b = c["bootstrap"]
        L.append("| %s | %s/%s | %d | %s | [%s, %s] | %s | %.2f |"
                 % (c["family"], c["model"], c["effort"], c["n_pairs"],
                    _fmt(b["mean"]), _fmt(b["ci95_low"]), _fmt(b["ci95_high"]),
                    ("%.3f" % b["p_two_sided"]) if b["p_two_sided"] is not None else "n/a",
                    c["frac_a_better"] or 0))
    L.append("")
    L.append("### Secondary contrasts (Holm-adjusted within family)")
    L.append("| family | a vs b | n | mean diff | p_holm |")
    L.append("|---|---|---|---|---|")
    for c in d["secondary"]:
        L.append("| %s | %s vs %s | %d | %s | %s |"
                 % (c["family"], c["a"], c["b"], c["n_pairs"],
                    _fmt(c["bootstrap"]["mean"]),
                    ("%.3f" % c["p_holm"]) if c.get("p_holm") is not None else "n/a"))
    return "\n".join(L)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--repair", default="research/experiments/repair/repair_results.json")
    p.add_argument("--search", default="research/search/pilot_analysis.json")
    p.add_argument("--out", default="research/results_summary.md")
    args = p.parse_args(argv)
    parts = ["# Results summary (auto-compiled; do not hand-edit numbers)", "",
             repair_section(args.repair), "", search_section(args.search), ""]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as fh:
        fh.write("\n".join(parts))
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
