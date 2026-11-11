"""Compile every corrected result into ``research/results_summary2.md``.

No number in the manuscript or the rebuttal is hand-typed: it is transcribed from
this file, which is generated from the result JSONs by

    python3 -m research.compile_results2 --out research/results_summary2.md

Endpoints are labelled exactly as ``research/REVISED_PROTOCOL.md`` section 0 defines
them: development risk (validation split, used by selection and feedback), sealed
test risk (one shot), fresh holdout risk (ring v2, one shot).
"""
import argparse
import json
import os

import numpy as np


def load(path):
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        return json.load(fh)


def fmt(x, spec="%+.5f"):
    if x is None:
        return "n/a"
    try:
        return spec % x
    except TypeError:
        return str(x)


def ci(b):
    if not b or b.get("mean") is None:
        return "n/a"
    return "[%+.5f, %+.5f]" % (b["ci95_low"], b["ci95_high"])


def pstr(entry):
    if not entry:
        return "n/a"
    p = entry.get("p")
    if p is None:
        return "n/a"
    rep = entry.get("p_reported")
    return ("%.4g" % p) + (" (floor %s)" % rep if rep else "")


def pfloat(p):
    return "n/a" if p is None else "%.4g" % p


def repair_section(path, title, out):
    d = load(path)
    if d is None:
        out.append("_(%s missing)_" % path)
        return
    out.append("## %s\n" % title)
    out.append("- input: `%s`  units rule: %s" % (path, d.get("protocol")))
    out.append("- units per eta (rows vs units after collapsing exact repeats): %s\n"
               % json.dumps(d.get("unit_counts")))
    out.append("| eta | steps | contrast | rows | units | mean diff (a-b) | 95% CI | "
               "frac a better | p_shift-boot | p_signflip | p_holm | verdict |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in d.get("contrasts", []):
        out.append("| %.1f | %s | %s vs %s | %d | %d | %s | %s | %.2f | %s | %s | %.3f | %s |"
                   % (c["eta"], c["steps"], c["a"], c["b"], c["n_rows"], c["n_units"],
                      fmt(c["mean_diff_a_minus_b"]), ci(c["bootstrap"]),
                      c["frac_a_better"], pstr(c["p_shifted_bootstrap"]),
                      pstr(c["p_signflip"]), c["p_holm_within_eta"], c["verdict"]))
    out.append("")
    out.append("### Floor accounting (population / MC / exact finite-orbit)\n")
    out.append("| eta | arm | units | dev risk | floor (rep MC) | floor (exact orbit) | "
               "orb risk | orb risk after projection | excess over orbit floor | channel residual |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for eta, rows in (d.get("floor_accounting") or {}).items():
        for e in rows:
            out.append("| %s | %s | %d | %.5f | %s | %s | %s | %s | %s | %.2e |"
                       % (eta, e["arm"], e["n_units"], e["mean_dev_risk"],
                          fmt(e.get("floor_representative_mc"), "%.5f"),
                          fmt(e.get("floor_exact_finite_orbit"), "%.5f"),
                          fmt(e.get("orb_risk"), "%.5f"),
                          fmt(e.get("orb_risk_reynolds_projection"), "%.5f"),
                          fmt(e.get("excess_over_floor")),
                          e["mean_channel_residual"]))
    out.append("")
    out.append("### E-R1 function-space contrast (same fitted predictor)\n")
    out.append("| eta | arm | units | R_orb(f) - R_orb(P f) | E[(f-P f)^2] | cross term | identity gap |")
    out.append("|---|---|---|---|---|---|---|")
    for eta, rows in (d.get("er1_function_space") or {}).items():
        for e in rows:
            out.append("| %s | %s | %d | %s | %.6f | %+.3e | %.1e |"
                       % (eta, e["arm"], e["n_units"], fmt(e["mean_risk_minus_proj"]),
                          e["mean_asymmetry"], e["mean_cross_term"], e["identity_gap_max"]))
    out.append("")
    if d.get("budget_sensitivity"):
        out.append("### Optimiser-budget sensitivity\n")
        out.append("| eta | steps | contrast | units | mean diff | 95% CI | verdict |")
        out.append("|---|---|---|---|---|---|---|")
        for c in d["budget_sensitivity"]:
            out.append("| %.1f | %s | %s vs %s | %d | %s | %s | %s |"
                       % (c["eta"], c["steps"], c["a"], c["b"], c["n_units"],
                          fmt(c["mean_diff_a_minus_b"]), ci(c["bootstrap"]),
                          c["verdict"]))
        out.append("")


def search_section(path, out):
    d = load(path)
    if d is None:
        out.append("_(%s missing)_" % path)
        return
    out.append("## WP-SEARCH reanalysis (frozen 120-run record, development endpoints)\n")
    out.append("- runs %d; families %s; endpoint: **development risk** (validation "
               "split used by selection and feedback)\n"
               % (d["n_runs"], ", ".join(d["families"])))
    out.append("### E-S3 primary (verify - fitness)\n")
    out.append("| family | n | mean diff | 95% CI | p_shift-boot | p_signflip | p_holm (A) | margin | verdict |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for c in d["primary"]:
        m = d["margins"][c["family"]]
        out.append("| %s | %d | %s | %s | %s | %s | %.3f | %.5f | %s |"
                   % (c["family"], c["n_pairs"], fmt(c["mean_diff_a_minus_b"]),
                      ci(c["bootstrap"]), pstr(c["p_shifted_bootstrap"]),
                      pstr(c["p_signflip"]), c["p_holm_family_A"], m["margin"],
                      c["verdict"]))
    out.append("")
    out.append("### E-S1 inference-time Reynolds averaging on the frozen candidate\n")
    out.append("| family | coverage | n fired | mean diff (averaged - candidate) | 95% CI | p_shift-boot | p_signflip | verdict |")
    out.append("|---|---|---|---|---|---|---|---|")
    for e in d["repair"]:
        out.append("| %s | %s | %d | %s | %s | %s | %s | %s |"
                   % (e["family"], json.dumps(e["coverage"]), e["n_pairs"],
                      fmt(e.get("mean_diff_averaged_minus_candidate")),
                      ci(e["bootstrap"]), pstr(e["p_shifted_bootstrap"]),
                      pstr(e["p_signflip"]), e["verdict"]))
    out.append("")
    out.append("### Secondary contrasts (candidate endpoint vs deployed endpoint)\n")
    out.append("| family | endpoint | contrast | n | mean diff | 95% CI | p_holm (D) |")
    out.append("|---|---|---|---|---|---|---|")
    for c in d["secondary"]:
        out.append("| %s | %s | %s vs %s | %d | %s | %s | %.3f |"
                   % (c["family"], c["endpoint"], c["a"], c["b"], c["n_pairs"],
                      fmt(c["mean_diff_a_minus_b"]), ci(c["bootstrap"]),
                      c["p_holm_family_D"]))
    out.append("")
    out.append("### E-S4 reliability (per arm, development record)\n")
    out.append("| family | arm | runs | invalid rate | hypothesis rate | tokens | wall s | mean dev risk |")
    out.append("|---|---|---|---|---|---|---|---|")
    for r in d["reliability"]:
        for arm, s in r["per_arm"].items():
            out.append("| %s | %s | %d | %.3f | %.3f | %.0f | %.0f | %.5f |"
                       % (r["family"], arm, s["n_runs"], s["mean_invalid_rate"],
                          s["mean_hypothesis_rate"], s["mean_tokens"],
                          s["mean_wall_time_s"], s["mean_dev_risk"]))
    out.append("")
    out.append("### E-S4 paired reliability contrasts (verify - fitness)\n")
    out.append("| family | metric | n | mean diff | 95% CI | p_shift-boot | verdict |")
    out.append("|---|---|---|---|---|---|---|")
    for r in d["reliability"]:
        for c in r["paired"]:
            out.append("| %s | %s | %d | %s | %s | %s | %s |"
                       % (r["family"], c["metric"], c["n_pairs"],
                          fmt(c["mean_diff_a_minus_b"]), ci(c["bootstrap"]),
                          pstr(c["p_shifted_bootstrap"]), c["verdict"]))
    out.append("")


def dev_section(path, out):
    d = load(path)
    if d is None:
        out.append("_(%s missing)_" % path)
        return
    out.append("## WP-DEV analyses (refit-verified, development endpoints)\n")
    rr = d["refit_reproduction"]
    out.append("- deterministic refit reproduced the logged dev risk exactly for "
               "%d/%d runs (max abs diff %.2e)\n"
               % (rr["exact"], rr["n"], rr["max_abs_diff"]))
    out.append("### E-S5b declared-group twirl applied to every arm's selected predictor\n")
    out.append("| family | arm | n | mean diff (after - before) | 95% CI | p_shift-boot | verdict |")
    out.append("|---|---|---|---|---|---|---|")
    for c in d["twirl_summary"]:
        out.append("| %s | %s | %d | %s | %s | %s | %s |"
                   % (c["family"], c["arm"], c["n"],
                      fmt(c["mean_diff_after_minus_before"]), ci(c["bootstrap"]),
                      pstr(c["p_shifted_bootstrap"]), c["verdict"]))
    out.append("")
    out.append("### E-S6 matched-budget baselines\n")
    for c in d["baselines"]["constructive"]:
        out.append("- constructive equivariant architecture, `%s`: channel residual "
                   "%.2e, mean dev risk %.5f over %d seeds"
                   % (c["family"], c["channel_residual"], c["mean_dev_risk"],
                      len(c["seeds"])))
    for c in d["baselines"]["classical"]:
        if "edge_count_threshold" in c:
            e = c["edge_count_threshold"]
            out.append("- edge-count threshold rule, `%s` (target `%s`): threshold %d "
                       "fitted on train only, dev risk %.5f, dev accuracy %.4f"
                       % (c["family"], c["target"], e["threshold"], e["dev_risk"],
                          e["dev_accuracy"]))
        if "invariant_oracle" in c:
            out.append("- invariant oracle, `%s`: dev risk %.5f (0 by construction)"
                       % (c["family"], c["invariant_oracle"]["dev_risk"]))
        out.append("- best constant predictor, `%s`: dev risk %.5f"
                   % (c["family"], c["best_constant"]["dev_risk"]))
    out.append("")
    out.append("### E-S6 arm selected predictor vs constructive equivariant baseline\n")
    out.append("| family | arm | n | mean diff (arm - constructive) | 95% CI | p_shift-boot | verdict |")
    out.append("|---|---|---|---|---|---|---|")
    for c in d["baselines"]["arm_vs_constructive"]:
        out.append("| %s | %s | %d | %s | %s | %s | %s |"
                   % (c["family"], c["a"], c["n_pairs"], fmt(c["mean_diff_a_minus_b"]),
                      ci(c["bootstrap"]), pstr(c["p_shifted_bootstrap"]), c["verdict"]))
    out.append("")
    out.append("### E-S4c verifier selectivity (wrong hypothesis group passing label preservation)\n")
    out.append("| family | arm | runs | proposals with hypothesis | group == task group | "
               "label-preserving | wrong group AND label-preserving |")
    out.append("|---|---|---|---|---|---|---|")
    agg = {}
    for r in d["runs"]:
        s = r.get("verifier_selectivity")
        if not s:
            continue
        k = (r["family"], r["arm"])
        a = agg.setdefault(k, {"n": 0, "hyp": 0, "same": 0, "lp": 0, "wrong": 0})
        a["n"] += 1
        a["hyp"] += s["proposals_with_hypothesis"]
        a["same"] += s["hyp_group_equals_task"]
        a["lp"] += s["hyp_label_preserving"]
        a["wrong"] += s["wrong_group_but_label_preserving"]
    for (fam, arm), a in sorted(agg.items()):
        out.append("| %s | %s | %d | %d | %d | %d | %d |"
                   % (fam, arm, a["n"], a["hyp"], a["same"], a["lp"], a["wrong"]))
    out.append("")
    out.append("### E-S5 density (edge-count) band risks, graphs_n6 (mean over runs per arm)\n")
    arms = sorted({r["arm"] for r in d["runs"] if r["family"] == "graphs_n6"})
    bands = d["bands_definition"]
    out.append("| arm | " + " | ".join("band %s (risk / n)" % b for b in bands) + " |")
    out.append("|---|" + "---|" * len(bands))
    for arm in arms:
        cells = []
        for b in bands:
            vals = [(r["bands"][b]["risk"], r["bands"][b]["n"])
                    for r in d["runs"]
                    if r["family"] == "graphs_n6" and r["arm"] == arm and b in r["bands"]]
            cells.append("%.4f / %d" % (np.mean([v[0] for v in vals]), vals[0][1])
                         if vals else "n/a")
        out.append("| %s | " % arm + " | ".join(cells) + " |")
    out.append("")
    out.append("### Nonconstant-output check (deployed predictor, dev rows)\n")
    out.append("| family | arm | runs | min pred std | frac nonconstant |")
    out.append("|---|---|---|---|---|")
    for fam in d["families"]:
        for arm in sorted({r["arm"] for r in d["runs"] if r["family"] == fam}):
            rs = [r for r in d["runs"] if r["family"] == fam and r["arm"] == arm]
            out.append("| %s | %s | %d | %.4f | %.2f |"
                       % (fam, arm, len(rs), min(r["pred_std"] for r in rs),
                          np.mean([r["nonconstant"] for r in rs])))
    out.append("")


def holdout_section(out_path, access_path, out):
    d = load(out_path)
    if d is None:
        out.append("_(one-shot holdout evaluation not yet run)_")
        return
    a = load(access_path) or {}
    out.append("## One-shot sealed / fresh holdout evaluation\n")
    out.append("- sealed digests unchanged across the evaluation: **%s**; access record: "
               "`%s`; started %s, finished %s\n"
               % (d.get("unchanged"), access_path,
                  (a.get("started") or {}).get("utc"), (a.get("finished") or {}).get("utc")))
    out.append("### E-R4 repair arms on untouched data\n")
    out.append("| split | eta | contrast | units | mean diff | 95% CI | p_shift-boot | p_signflip | verdict |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for c in d["repair_contrasts"]:
        out.append("| %s | %.1f | %s vs %s | %d | %s | %s | %s | %s | %s |"
                   % (c["split"], c["eta"], c["a"], c["b"], c["n_units"],
                      fmt(c["mean_diff_a_minus_b"]), ci(c["bootstrap"]),
                      pstr(c["p_shifted_bootstrap"]), pstr(c["p_signflip"]),
                      c["verdict"]))
    out.append("")
    out.append("### E-S7 search arms on the sealed test split\n")
    out.append("| family | arm | runs | mean dev risk | mean sealed-test risk |")
    out.append("|---|---|---|---|---|")
    for s in d["search_arm_means"]:
        out.append("| %s | %s | %d | %.5f | %.5f |"
                   % (s["family"], s["arm"], s["n"], s["mean_dev_risk"],
                      s["mean_test_risk"]))
    out.append("")
    out.append("| family | contrast | n | mean diff | 95% CI | p_shift-boot | p_signflip | verdict |")
    out.append("|---|---|---|---|---|---|---|---|")
    for c in d["search_contrasts"]:
        out.append("| %s | %s vs %s | %d | %s | %s | %s | %s | %s |"
                   % (c["family"], c["a"], c["b"], c["n_pairs"],
                      fmt(c["mean_diff_a_minus_b"]), ci(c["bootstrap"]),
                      pstr(c["p_shifted_bootstrap"]), pstr(c["p_signflip"]),
                      c["verdict"]))
    out.append("")


def breaking_section(path, out):
    d = load(path)
    if d is None:
        out.append("_(breaking-target selectivity test not yet run)_")
        return
    out.append("## Breaking-target selectivity test (protocol Addendum A1)\n")
    out.append("Family `%s`, target `%s` (the declared group is **not** a label symmetry "
               "here). Development risk on each run's own validation split. Declared "
               "prediction: if the verifier's benefit came from pushing toward the "
               "declared group, it must turn negative on this target.\n"
               % (d["family"], d["target"]))
    out.append("| arm | runs | mean dev risk | accuracy | nonconstant | repair fired/attempted | hyp. | hyp. pass gate | hyp. = task group |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for arm, v in d["arms"].items():
        out.append("| %s | %d | %.5f | %.3f | %d/%d | %d/%d | %d | %d | %d |"
                   % (arm, v["n"], v["dev_risk_mean"], v["accuracy_mean"],
                      v["n_nonconstant"], v["n"], v["n_repair_fired"],
                      v["n_repair_attempted"], v["proposals_with_hypothesis"],
                      v["hypotheses_passing_label_gate"],
                      v["hypotheses_equal_to_task_group"]))
    out.append("")
    out.append("| contrast | n | mean diff | 95% CI | p_shift-boot | p_signflip | p_holm (E) | verdict |")
    out.append("|---|---|---|---|---|---|---|---|")
    for c in d["contrasts"]:
        out.append("| %s vs %s | %d | %s | %s | %s | %s | %s | %s |"
                   % (c["a"], c["b"], c["n_pairs"], fmt(c["mean_diff_a_minus_b"]),
                      ci(c["bootstrap"]), pstr(c["p_shifted_bootstrap"]),
                      pstr(c["p_signflip"]), pfloat(c["holm_p_within_family_E"]),
                      c["verdict"]))
    out.append("")


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="research/results_summary2.md")
    a = p.parse_args(argv)
    out = ["# Corrected results summary (auto-compiled; do not hand-edit numbers)\n",
           "Endpoints follow `research/REVISED_PROTOCOL.md` section 0. Development risk "
           "is **not** held-out risk: the validation split is used by candidate "
           "selection, by the search feedback loop and by the verifier.\n",
           "Inference conventions: `research/core/paired.py` (percentile bootstrap over "
           "*units*, null-centred bootstrap p, sign-flip p with its symmetry assumption "
           "stated, p floors reported, Holm within declared families, equivalence only "
           "against a prespecified margin).\n"]
    repair_section("research/experiments/repair/repair_v1_reanalysis.json",
                   "WP-REPAIR v1 record, recomputed with correct replication units", out)
    repair_section("research/experiments/repair/repair2_analysis.json",
                   "WP-REPAIR-2 (corrected design)", out)
    search_section("research/search/confirm_analysis2.json", out)
    dev_section("research/search/dev_analysis.json", out)
    holdout_section("research/HOLDOUT_RESULTS.json", "research/HOLDOUT_ACCESS.json", out)
    breaking_section("research/search/breaking_target.json", out)
    with open(a.out, "w") as fh:
        fh.write("\n".join(out) + "\n")
    print("wrote %s (%d lines)" % (a.out, len(out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
