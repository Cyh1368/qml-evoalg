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
    out.append("Headline columns use the **primary estimand** of Addendum A5.1: at "
               "`eta = 0` the 24 optimiser seeds; at `eta > 0` the 24 seed vectors after "
               "averaging the 8 frozen breaking directions within each seed (E-A). The "
               "cell-level interval is listed separately as sensitivity E-D.\n")
    out.append("| eta | steps | contrast | rows | units (estimand) | mean diff (a-b) | "
               "95% CI (primary) | frac a better | p_shift-boot | p_signflip | p_holm | "
               "verdict |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in d.get("contrasts", []):
        prim = c.get("primary") or {"bootstrap": c["bootstrap"],
                                    "n_units": c["n_units"],
                                    "estimand": "cell-level (pre-A5)"}
        out.append("| %.1f | %s | %s vs %s | %d | %d (%s) | %s | %s | %.2f | %s | %s | "
                   "%.3g | %s |"
                   % (c["eta"], c["steps"], c["a"], c["b"], c["n_rows"],
                      prim["n_units"], prim.get("estimand", "?"),
                      fmt(c["mean_diff_a_minus_b"]), ci(prim["bootstrap"]),
                      c["frac_a_better"], pstr(c["p_shifted_bootstrap"]),
                      pstr(c["p_signflip"]), c["p_holm_within_eta"], c["verdict"]))
    out.append("")
    crossed = [c for c in d.get("contrasts", []) if c.get("estimand_EA_seed_vector")]
    if crossed:
        out.append("### Estimand sensitivity at eta > 0 (A5.1)\n")
        out.append("| eta | contrast | E-A seeds (primary) | E-B directions | E-C crossed "
                   "| E-D cells (legacy) | direction-specific means |")
        out.append("|---|---|---|---|---|---|---|")
        for c in crossed:
            ea, eb, ec = (c["estimand_EA_seed_vector"], c["estimand_EB_direction_cluster"],
                          c["estimand_EC_crossed"])
            spread = sorted(v["mean"] for v in c["by_direction"].values())
            out.append("| %.1f | %s vs %s | %s | %s | %s | %s | %+.5f … %+.5f |"
                       % (c["eta"], c["a"], c["b"], ci(ea), ci(eb), ci(ec),
                          ci(c["bootstrap"]), spread[0], spread[-1]))
        out.append("")
        out.append("*All four intervals condition on one dataset and one task family; "
                   "none quantifies newly sampled training datasets or task families.*\n")
    out.append("### Floor accounting (population / MC / exact finite-orbit)\n")
    out.append("| eta | arm | units | dev risk | floor (rep MC) | floor (exact orbit) | "
               "orb risk | orb risk after projection | excess over orbit floor | "
               "excess over rep-MC floor | channel residual |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for eta, rows in (d.get("floor_accounting") or {}).items():
        for e in rows:
            out.append("| %s | %s | %d | %.5f | %s | %s | %s | %s | %s | %s | %.2e |"
                       % (eta, e["arm"], e["n_units"], e["mean_dev_risk"],
                          fmt(e.get("floor_representative_mc"), "%.5f"),
                          fmt(e.get("floor_exact_finite_orbit"), "%.5f"),
                          fmt(e.get("orb_risk"), "%.5f"),
                          fmt(e.get("orb_risk_reynolds_projection"), "%.5f"),
                          fmt(e.get("excess_over_floor")),
                          fmt(e.get("excess_over_rep_floor")),
                          e["mean_channel_residual"]))
    out.append("")
    out.append("### E-R1 function-space contrast (same fitted predictor)\n")
    out.append("| eta | arm | units | R_orb(f) - R_orb(P f) | E[(f-P f)^2] | cross term | "
               "no-cross-term gap | full A3 gap |")
    out.append("|---|---|---|---|---|---|---|---|")
    for eta, rows in (d.get("er1_function_space") or {}).items():
        for e in rows:
            out.append("| %s | %s | %d | %s | %.6f | %+.3e | %.1e | %.1e |"
                       % (eta, e["arm"], e["n_units"], fmt(e["mean_risk_minus_proj"]),
                          e["mean_asymmetry"], e["mean_cross_term"],
                          e["identity_gap_max"],
                          e.get("full_identity_gap_max", float("nan"))))
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
        out.append("| %s | %d | %s | %s | %s | %s | %.3g | %.5f | %s |"
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
        out.append("| %s | %s | %s vs %s | %d | %s | %s | %.3g |"
                   % (c["family"], c["endpoint"], c["a"], c["b"], c["n_pairs"],
                      fmt(c["mean_diff_a_minus_b"]), ci(c["bootstrap"]),
                      c["p_holm_family_D"]))
    out.append("")
    out.append("### E-S4 reliability (per arm, development record)\n")
    out.append("| family | arm | runs | invalid rate | hypothesis rate | tokens | wall s | mean dev risk |")
    out.append("|---|---|---|---|---|---|---|---|")
    for fam, r in zip(d["families"], d["reliability"]):
        for arm, s in r["per_arm"].items():
            out.append("| %s | %s | %d | %.3f | %.3f | %.0f | %.0f | %.5f |"
                       % (fam, arm, s["n_runs"], s["mean_invalid_rate"],
                          s["mean_hypothesis_rate"], s["mean_tokens"],
                          s["mean_wall_time_s"], s["mean_dev_risk"]))
    out.append("")
    out.append("### E-S4 paired reliability contrasts (verify - fitness)\n")
    out.append("| family | metric | n | mean diff | 95% CI | p_shift-boot | verdict |")
    out.append("|---|---|---|---|---|---|---|")
    for r in d["reliability"]:
        for c in r["paired"]:
            out.append("| %s | %s | %d | %s | %s | %s | %s |"
                       % (c["family"], c["metric"], c["n_pairs"],
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


def holdout_section(out_path, access_path, out, er4_path=None, er4_access=None):
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
    e4 = load(er4_path) if er4_path else None
    if e4 is not None:
        out.append("- **E-R4' supersedes the E-R4 table of the first one-shot run**, whose "
                   "`eta > 0` rows scored every arm against a single invariant label "
                   "(REVISED_PROTOCOL Addendum A4). Self-check: %s (%s units compared, max "
                   "|dev diff| %s); digests unchanged: %s; access record: `%s`\n"
                   % ("PASS" if (e4.get("selfcheck") or {}).get("pass") else "FAIL",
                      (e4.get("selfcheck") or {}).get("compared"),
                      (e4.get("selfcheck") or {}).get("max_abs_dev_risk_diff"),
                      e4.get("unchanged"), er4_access))
    out.append("### E-S7 sealed-test risk of the frozen candidates (candidate endpoint)\n")
    out.append("*Endpoint note: these are the refitted **candidates**. The deployed repaired"
               " predictor is measured separately (A5.5, `research/holdout_deployed.py`);"
               " `test_risk_averaged_diagnostic` was never computed in this run.*\n")
    out.append("| family | arm | n | mean dev risk | mean sealed-test risk |")
    out.append("|---|---|---|---|---|")
    for m in d.get("search_arm_means", []):
        out.append("| %s | %s | %d | %.5f | %.5f |"
                   % (m["family"], m["arm"], m["n"], m["mean_dev_risk"],
                      m["mean_test_risk"]))
    out.append("")
    out.append("| family | contrast | pairs | mean diff | 95% CI | p_shift-boot | verdict |")
    out.append("|---|---|---|---|---|---|---|")
    for c in d.get("search_contrasts", []):
        out.append("| %s | %s vs %s | %d | %s | %s | %s | %s |"
                   % (c["family"], c["a"], c["b"], c["n_pairs"],
                      fmt(c["mean_diff_a_minus_b"]), ci(c["bootstrap"]),
                      pstr(c["p_shifted_bootstrap"]), c["verdict"]))
    out.append("")
    sc = load("research/HOLDOUT_SEARCH_CONTRASTS.json")
    if sc:
        out.append("### E-S7 paired against the `random` arm (regenerated from the "
                   "stored per-run record; no new sealed read)\n")
        out.append("| family | arm | vs | pairs | mean diff | 95% CI | p_shift-boot | "
                   "p_signflip | verdict |")
        out.append("|---|---|---|---|---|---|---|---|---|")
        for c in sc["contrasts"]:
            out.append("| %s | %s | %s | %d | %s | %s | %s | %s | %s |"
                       % (c["family"], c["a"], c["b"], c["n_pairs"],
                          fmt(c["mean_diff_a_minus_b"]), ci(c["bootstrap"]),
                          pstr(c["p_shifted_bootstrap"]), pstr(c["p_signflip"]),
                          c["verdict"]))
        out.append("")
    rows = e4["repair_contrasts"] if e4 else d["repair_contrasts"]
    out.append("### E-R4 repair arms on untouched data\n")
    out.append("| split | eta | contrast | units | mean diff | 95% CI | p_shift-boot | p_signflip | verdict |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for c in rows:
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
        out.append("| %s | %d | %.5f | %.5f | %d/%d | %d/%d | %d | %d | %d |"
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



def semantics_section(path, out):
    d = load(path)
    if d is None:
        out.append("_(A5.2/A5.3 verifier-semantics analysis not yet run)_")
        return
    out.append("## Verifier semantics: what a label-preservation gate can decide "
               "(A5.2 / A5.3)\n")
    out.append("- probe: %d rows, seed %s (%s)\n"
               % (d["probe"]["rows"], d["probe"]["seed"], d["probe"]["note"]))
    out.append("### Measured label-symmetry groups (all n! permutations tested)\n")
    out.append("| family | target | label-symmetry order | hypothesis space |L|/|S_n| | contains declared group | = full symmetric |")
    out.append("|---|---|---|---|---|---|---|")
    for fam, fd in d["families"].items():
        space = fd["full_symmetric_order"]
        for tgt, v in fd["label_symmetry_groups"].items():
            out.append("| %s | %s | %d | %d | %.4f | %s | %s |"
                       % (fam, tgt, v["order"], space, v["order"] / space,
                          v["contains_declared_group"], v["equals_full_symmetric"]))
    out.append("")
    out.append("### Fixed-panel selectivity (identical inputs, target varied)\n")
    out.append("| family | target | gate variant | sensitivity | false-accept |")
    out.append("|---|---|---|---|---|")
    for key, v in d["panel"].items():
        fam, tgt, gate = key.split("|")
        se, fa = v["sensitivity"], v["false_accept"]
        out.append("| %s | %s | %s | %d/%d = %s %s | %d/%d = %s %s |"
                   % (fam, tgt, gate, se["k"], se["n"],
                      "n/a" if se["rate"] is None else "%.2f" % se["rate"],
                      wil(se), fa["k"], fa["n"],
                      "n/a" if fa["rate"] is None else "%.2f" % fa["rate"], wil(fa)))
    out.append("")
    out.append("### Panel members: truth, gate decision under each variant, and margin\n")
    out.append("| family | target | member | closure order | sound on probe | accepted "
               "(implemented) | accepted (scored, tol 0) | accepted (scored, tol 1e-9) | "
               "gate margin (implemented) | gate margin (scored, tol 0) | "
               "gate margin (scored, tol 1e-9) | worst violated fraction (probe) |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    members = {}
    for key, v in d["panel"].items():
        fam, tgt, gate = key.split("|")
        for name, m in v["members"].items():
            row = members.setdefault((fam, tgt, name),
                                     {"order": m["closure_order"],
                                      "sound": m["sound_on_probe"],
                                      "worst": m["worst_violated_fraction"]})
            row["acc_" + gate] = m["accepted"]
            row["margin_" + gate] = m["gate_margin"]
    for (fam, tgt, name), r in sorted(members.items()):
        out.append("| %s | %s | %s | %d | %s | %s | %s | %s | %.5f | %.5f | %.5f | %.5f |"
                   % (fam, tgt, name, r["order"], r["sound"],
                      r.get("acc_implemented"), r.get("acc_target_specific"),
                      r.get("acc_target_specific_tol"),
                      r.get("margin_implemented", float("nan")),
                      r.get("margin_target_specific", float("nan")),
                      r.get("margin_target_specific_tol", float("nan")), r["worst"]))
    out.append("")
    out.append("### Search-generated hypotheses: status and recorded gate decisions\n")
    out.append("| family | target | exact declared | valid proper subgroup | valid supergroup | sound non-comparable | invalid |")
    out.append("|---|---|---|---|---|---|---|")
    for key, t in d["hypothesis_tally"].items():
        fam, tgt = key.split("|")
        out.append("| %s | %s | %d | %d | %d | %d | %d |"
                   % (fam, tgt, t.get("exact_declared", 0),
                      t.get("valid_proper_subgroup", 0), t.get("valid_supergroup", 0),
                      t.get("sound_noncomparable", 0), t.get("invalid", 0)))
    out.append("")
    out.append("| family | target | gate label-pass | of those invalid (false accepts) | gate label-fail | of those sound for the scored target |")
    out.append("|---|---|---|---|---|---|")
    for key, v in d.get("gate_cross_tabulation", {}).items():
        fam, tgt = key.split("|")
        fa, ms = v["false_accept_of_accepted"], v["missed_sound_of_rejected"]
        out.append("| %s | %s | %d | %d (%s %s) | %d | %d (%s %s) |"
                   % (fam, tgt, v["label_pass"], v["label_pass_invalid"],
                      "n/a" if fa["rate"] is None else "%.2f" % fa["rate"], wil(fa),
                      v["label_fail"], v["label_fail_sound"],
                      "n/a" if ms["rate"] is None else "%.2f" % ms["rate"], wil(ms)))
    out.append("")


def wil(entry):
    if not entry or entry.get("ci95_low") is None:
        return "[n/a]"
    return "[%s, %s]" % (("%.3f" % entry["ci95_low"]), ("%.3f" % entry["ci95_high"]))


def decision_section(path, out):
    d = load(path)
    if d is None:
        out.append("_(A5.4 decision-rule ablation not yet run)_")
        return
    out.append("## Verification as a decision rule (A5.4)\n")
    for fam, fd in d["families"].items():
        out.append("### %s — %d candidates, MC-twirl share %.2f, verify %.2fs vs average %.2fs\n"
                   % (fam, fd["n_runs"], fd["mc_twirl_share"],
                      fd["cost"]["mean_seconds_to_verify"],
                      fd["cost"]["mean_seconds_to_average"]))
        out.append("Thresholds (development only): median %.3g, q1 %.3g, q3 %.3g\n"
                   % (fd["thresholds"]["median"], fd["thresholds"]["q1"],
                      fd["thresholds"]["q3"]))
        out.append("| rule | fired | realised mean risk change | if always applied | precision | recall | harmed | missed beneficial (total gain) |")
        out.append("|---|---|---|---|---|---|---|---|")
        for rule, m in fd["rules"].items():
            pr, rc = m["precision_helped_given_fired"], m["recall_fired_given_helped"]
            out.append("| %s | %d/%d | %s | %s | %d/%d %s | %d/%d %s | %d | %d (%.4f) |"
                       % (rule, m["n_fired"], m["n_candidates"],
                          fmt(m.get("mean_realised_delta")),
                          fmt(m.get("mean_delta_if_always_applied",
                                    m.get("mean_delta_itt"))),
                          pr["k"], pr["n"], wil(pr), rc["k"], rc["n"], wil(rc),
                          m["n_harmed"], m["n_missed_beneficial"],
                          m["total_missed_gain"] or 0.0))
        out.append("")
        r4 = fd["R4_mismatch_control"]
        out.append("- **R4 mismatched-group control:** %s\n"
                   % ("mean risk change %s over %d candidates"
                      % (fmt(r4.get("mean_delta_mismatch")), r4["n_candidates"])
                      if r4.get("mean_delta_mismatch") is not None else r4["note"]))
        out.append("| arm | n | mean delta (declared-group average) | mean predictor defect | channel above repair floor | repair fired in the run |")
        out.append("|---|---|---|---|---|---|")
        for arm, a in fd["by_arm"].items():
            out.append("| %s | %d | %s | %.4f | %d | %d |"
                       % (arm, a["n"], fmt(a["mean_delta_declared"]),
                          a["mean_predictor_defect"], a["n_channel_above_floor"],
                          a["n_repair_fired_in_run"]))
        out.append("")


def deployed_section(path, access_path, out):
    d = load(path)
    if d is None:
        out.append("_(A5.5 deployed-endpoint evaluation not yet run)_")
        return
    a = load(access_path) or {}
    out.append("## Deployed-endpoint evaluation (A5.5)\n")
    out.append("- dry run: **%s**; self-check gate: %s (%d/%d exact, max |dev diff| %s)"
               " ; digests unchanged: %s; access record: `%s`\n"
               % (d.get("dry_run"), "PASS" if d["selfcheck"]["pass"] else "FAIL",
                  d["selfcheck"]["n_exact"], d["selfcheck"]["n"],
                  ("%.2e" % d["selfcheck"]["max_abs_dev_risk_diff"]),
                  d.get("unchanged", "n/a (dry run)"), access_path))
    for fam, src in d["sources"].items():
        out.append("- **%s** evaluation rows: %s" % (fam, src))
    out.append("")
    out.append("### Absolute risk per arm on the shared evaluation rows\n")
    out.append("| family | arm | candidate endpoint | deployed endpoint | declared-group "
               "twirl | repair fired (deployed) |")
    out.append("|---|---|---|---|---|---|")
    agg = {}
    for r in d["runs"]:
        k = (r["family"], r["arm"])
        e = agg.setdefault(k, {"c": [], "d": [], "t": [], "f": 0})
        e["c"].append(r["test_risk_candidate"])
        e["d"].append(r["test_risk_deployed"])
        e["t"].append(r["test_risk_declared_twirl"])
        e["f"] += bool(r["deployed_repair_frozen"])
    for (fam, arm), e in sorted(agg.items()):
        m = lambda v: sum(v) / len(v)
        out.append("| %s | %s | %s | %s | %s | %d/%d |"
                   % (fam, arm, fmt(m(e["c"]), "%.5f"), fmt(m(e["d"]), "%.5f"),
                      fmt(m(e["t"]), "%.5f"), e["f"], len(e["c"])))
    out.append("")
    out.append("### Endpoint contrasts (paired, run-level)\n")
    out.append("| family | arm | contrast | runs | mean diff | 95% CI | verdict |")
    out.append("|---|---|---|---|---|---|---|")
    for c in d["contrasts"]:
        out.append("| %s | %s | %s | %d | %s | %s | %s |"
                   % (c["family"], c["arm"], c["contrast"], c["n_runs"],
                      fmt(c["mean_diff"]), ci(c["bootstrap"]), c["verdict"]))
    out.append("")
    out.append("### Baselines fitted on training rows, scored on the same rows as the arms\n")
    out.append("| family | baseline | risk on evaluation rows | note |")
    out.append("|---|---|---|---|")
    for fam, b in d["baselines"].items():
        out.append("| %s | best constant (train mean) | %s | classical |"
                   % (fam, fmt(b["best_constant"]["risk"])))
        if "edge_count_rule" in b:
            out.append("| %s | edge-count rule (threshold %d, train-fitted) | %s | train risk %s |"
                       % (fam, b["edge_count_rule"]["threshold"],
                          fmt(b["edge_count_rule"]["risk"]),
                          fmt(b["edge_count_rule"]["train_risk"])))
        ce = b["constructive_equivariant"]
        out.append("| %s | constructive equivariant (%d seeds, %d steps) | %s | %s |"
                   % (fam, len(ce["risks"]), ce["steps"], fmt(ce["risk_mean"]),
                      ce["budget_note"]))
        o = b["oracle_reference"]
        out.append("| %s | oracle | %s | %s |" % (fam, fmt(o["risk"]), o["status"]))
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
    holdout_section("research/HOLDOUT_RESULTS.json", "research/HOLDOUT_ACCESS.json", out,
                    er4_path="research/HOLDOUT_RESULTS_v4.json",
                    er4_access="research/HOLDOUT_ACCESS_v4.json")
    breaking_section("research/search/breaking_target.json", out)
    semantics_section("research/search/verify_semantics.json", out)
    decision_section("research/search/decision_rules.json", out)
    deployed_section("research/HOLDOUT_DEPLOYED.json",
                     "research/HOLDOUT_DEPLOYED_ACCESS.json", out)
    with open(a.out, "w") as fh:
        fh.write("\n".join(out) + "\n")
    print("wrote %s (%d lines)" % (a.out, len(out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
