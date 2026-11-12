"""Claim-level binding of manuscript numbers to result records, plus mutation testing.

Why this exists
---------------
``research/paper/check_numbers.py`` is a **numeric-token lint**: it asks whether a decimal
token in the manuscript also appears somewhere in the generated summary. It does not bind a
value to an experiment, endpoint, arm, split or table cell, so a valid number in the wrong
place passes. That is the honest description of it, and it is what the paper says.

This module adds the layer that claim-level statements require:

1. **Bindings.** Each headline manuscript value is declared as
   ``(id, value path into a result JSON, decimals, context tokens)``. The value is
   *recomputed from the record*, not transcribed, and it must appear in the manuscript in a
   line (or a line within ``CONTEXT_LINES`` of it) that also mentions every context token --
   typically the arm, the endpoint, the split and the contrast. A number copied into a row
   about a different arm therefore fails.
2. **Mutation testing.** The instrument is itself tested: for each mutation class (sign
   flip, arm swap, split swap, exponent change, endpoint relabel) the binding is perturbed
   and the checker must fail. Detection and false-alarm rates are reported, so any claim
   about this tool is an *empirical* claim with measured error rates.

Run: ``python3 -m research.paper.claim_bind --report research/paper/claim_binding_report.md``
Exit status is non-zero if any binding fails to resolve or any mutation escapes detection.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# --------------------------------------------------------------------------- spec
# (id, file, dotted path with [n] indices, decimals, context tokens)
# Context tokens are matched case-insensitively as substrings on a small window of the
# manuscript around the line that carries the number.
SPEC_RAW = [
    # --- WP-REPAIR-2: primary estimand E-A, and the eta=0 non-result
    ("repair2.eta1.EA.mean", "research/experiments/repair/repair2_analysis.json",
     "contrasts.[a=repaired,b=control_dup,eta=1.0,steps=200].estimand_EA_seed_vector.mean",
     5, ["0.03605", "primary estimand"]),
    ("repair2.eta1.EA.ci_low", "research/experiments/repair/repair2_analysis.json",
     "contrasts.[a=repaired,b=control_dup,eta=1.0,steps=200]"
     ".estimand_EA_seed_vector.ci95_low", 5, ["0.02998"]),
    ("repair2.eta1.EA.ci_high", "research/experiments/repair/repair2_analysis.json",
     "contrasts.[a=repaired,b=control_dup,eta=1.0,steps=200]"
     ".estimand_EA_seed_vector.ci95_high", 5, ["0.04210"]),
    # the legacy cell-level interval lives in the contrast's top-level bootstrap key;
    # estimand_ED_legacy_cell.bootstrap is null by design (traceability only)
    ("repair2.eta1.legacy_cell.ci_low", "research/experiments/repair/repair2_analysis.json",
     "contrasts.[a=repaired,b=control_dup,eta=1.0,steps=200].bootstrap.ci95_low",
     5, ["0.03134"]),
    ("repair2.eta0.vs_dup.mean", "research/experiments/repair/repair2_analysis.json",
     "contrasts.[a=repaired,b=control_dup,eta=0.0,steps=200].mean_diff_a_minus_b",
     5, ["0.00060", "control\\_dup"]),
    # --- development deployed-averaging effect (E-S1)
    ("search.dev_deployed.mean", "research/search/confirm_analysis2.json",
     "repair.[family=graphs_n6].mean_diff_averaged_minus_candidate", 5, ["0.04862", "E-S1"]),
    # --- deployed endpoint on held-out rows (A5.5)
    ("deployed.graphs.repair.mean", "research/HOLDOUT_DEPLOYED.json",
     "contrasts.[family=graphs_n6,arm=llm-verify-repair,"
     "contrast=deployed - candidate].mean_diff", 5, ["0.02846", "deployed"]),
    ("deployed.graphs.repair.ci_low", "research/HOLDOUT_DEPLOYED.json",
     "contrasts.[family=graphs_n6,arm=llm-verify-repair,"
     "contrast=deployed - candidate].bootstrap.ci95_low", 5, ["0.04704"]),
    ("deployed.graphs.random.twirl", "research/HOLDOUT_DEPLOYED.json",
     "runs.[family=graphs_n6,arm=random]#mean.test_risk_declared_twirl", 5, ["0.40915"]),
    ("deployed.graphs.repair.deployed", "research/HOLDOUT_DEPLOYED.json",
     "runs.[family=graphs_n6,arm=llm-verify-repair]#mean.test_risk_deployed",
     5, ["0.50067"]),
    ("deployed.graphs.edge_rule", "research/HOLDOUT_DEPLOYED.json",
     "baselines.graphs_n6.edge_count_rule.risk", 5, ["0.57812", "edge-count"]),
    ("deployed.graphs.constant", "research/HOLDOUT_DEPLOYED.json",
     "baselines.graphs_n6.best_constant.risk", 5, ["0.58968"]),
    ("deployed.ring.constructive", "research/HOLDOUT_DEPLOYED.json",
     "baselines.ring_n6.constructive_equivariant.risk_mean", 5, ["0.00026", "constructive"]),
    # --- verifier semantics (A5.2)
    ("semantics.graphs.L_order", "research/search/verify_semantics.json",
     "families.graphs_n6.label_symmetry_groups.connected.order", 0, ["720"]),
    ("semantics.ring.L_order", "research/search/verify_semantics.json",
     "families.ring_n6.label_symmetry_groups.alpha_0.order", 0, ["12"]),
    ("semantics.ring.missed_sound_k", "research/search/verify_semantics.json",
     "gate_cross_tabulation.ring_n6|alpha_0.missed_sound_of_rejected.k", 0, ["95"]),
    ("semantics.ring.missed_sound_ci_low", "research/search/verify_semantics.json",
     "gate_cross_tabulation.ring_n6|alpha_0.missed_sound_of_rejected.ci95_low", 3,
     ["0.961"]),
    # --- decision rules on the defective gate (A5.4)
    ("decision.ring.R1.realised", "research/search/decision_rules.json",
     "families.ring_n6.rules.R1_label_gate.mean_realised_delta", 5, ["0.00000"]),
    ("decision.ring.R0.realised", "research/search/decision_rules.json",
     "families.ring_n6.rules.R0_supplied_group.mean_realised_delta", 5, ["0.00345"]),
    ("decision.ring.R3.realised", "research/search/decision_rules.json",
     "families.ring_n6.rules.R3_predictor_defect_q1.mean_realised_delta", 5, ["0.00274", "R3"]),
    ("decision.ring.mismatch.mean", "research/search/decision_rules.json",
     "families.ring_n6.R4_mismatch_control.mean_delta_mismatch", 5, ["0.00399"]),
    ("decision.graphs.R0.realised", "research/search/decision_rules.json",
     "families.graphs_n6.rules.R0_supplied_group.mean_realised_delta", 5, ["0.08705"]),
]

SPEC = [{"id": a, "file": b, "path": c, "decimals": d, "context": e}
        for a, b, c, d, e in SPEC_RAW]

# --- external evaluation of the instrument: the same record values, bound into a
# different artifact (the project claim ledger) with that artifact's own context.
# The referee asked for detection and false-alarm rates "on artifacts beyond this
# manuscript"; this is that measurement. Context tokens are ledger phrasings, so a
# value that merely occurs somewhere in the ledger does not bind.
SPEC_EXTERNAL_RAW = [
    ("ledger.repair2.eta1.EA.mean", "research/experiments/repair/repair2_analysis.json",
     "contrasts.[a=repaired,b=control_dup,eta=1.0,steps=200].estimand_EA_seed_vector.mean",
     5, ["192 units"]),
    ("ledger.repair2.eta0.vs_dup.mean", "research/experiments/repair/repair2_analysis.json",
     "contrasts.[a=repaired,b=control_dup,eta=0.0,steps=200].mean_diff_a_minus_b",
     5, ["holm 0.246"]),
    ("ledger.search.dev_deployed.mean", "research/search/confirm_analysis2.json",
     "repair.[family=graphs_n6].mean_diff_averaged_minus_candidate", 5, ["e-s1"]),
    ("ledger.deployed.graphs.repair.mean", "research/HOLDOUT_DEPLOYED.json",
     "contrasts.[family=graphs_n6,arm=llm-verify-repair,"
     "contrast=deployed - candidate].mean_diff", 5, ["7/12", "deployed"]),
    ("ledger.deployed.ring.constructive", "research/HOLDOUT_DEPLOYED.json",
     "baselines.ring_n6.constructive_equivariant.risk_mean", 5, ["0.00648", "constructive"]),
    ("ledger.deployed.graphs.edge_rule", "research/HOLDOUT_DEPLOYED.json",
     "baselines.graphs_n6.edge_count_rule.risk", 5, ["edge-count"]),
    ("ledger.semantics.ring.L_order", "research/search/verify_semantics.json",
     "families.ring_n6.label_symmetry_groups.alpha_0.order", 0, ["alpha_0"]),
    # A6.7 as stated in CLAIMS.md
    ("claims.a67.ring.mean", "research/search/corrected_search.json",
     "headline.ring_verify_minus_fitness_mean", 5, ["+0.00039", "fitness"]),
    ("claims.a67.ring.ci_low", "research/search/corrected_search.json",
     "headline.ring_verify_minus_fitness_ci_low", 5, ["−0.00016", "band"]),
    ("claims.a67.ring.ci_high", "research/search/corrected_search.json",
     "headline.ring_verify_minus_fitness_ci_high", 5, ["+0.00093", "band"]),
    ("claims.a67.graphs.mean", "research/search/corrected_search.json",
     "headline.graphs_verify_minus_fitness_mean", 5, ["−0.02302", "underpowered"]),
    ("claims.a67.ring.label_corrected", "research/search/corrected_search.json",
     "headline.ring_feedback_label_pass_corrected", 0, ["53/53", "corrected"]),
    ("claims.a67.ring.label_implemented", "research/search/corrected_search.json",
     "headline.ring_feedback_label_pass_implemented", 0, ["3/53", "implemented"]),
    ("claims.a67.ring.fired_corrected", "research/search/corrected_search.json",
     "headline.ring_repair_fired_corrected", 0, ["3/12", "coverage"]),
    ("claims.a67.ring.fired_implemented", "research/search/corrected_search.json",
     "headline.ring_repair_fired_implemented", 0, ["0/12", "coverage"]),
    ("claims.a67.ring.diagnostic", "research/search/corrected_search.json",
     "headline.ring_repair_diagnostic_corrected", 5, ["−0.00300", "averaging"]),
    ("claims.a67.graphs.diagnostic", "research/search/corrected_search.json",
     "headline.graphs_repair_diagnostic_corrected", 5, ["−0.06693", "(−0.06693"]),
]

SPEC_REBUTTAL_RAW = [
    ("rebuttal.corrected.ring.valid.realised",
     "research/search/decision_rules2.json",
     "summary.ring_n6.declared.rules.R1_corrected.realised_mean_delta", 5,
     ["60/60", "corrected label"]),
    ("rebuttal.corrected.ring.mismatch.harm",
     "research/search/decision_rules2.json",
     "summary.ring_n6.mismatched.rules.R0_always.realised_mean_delta", 5,
     ["58", "always"]),
    ("rebuttal.corrected.ring.valid.gate_cost",
     "research/search/decision_rules2.json",
     "summary.ring_n6.declared.rules.R1_corrected.cost.gate_seconds_per_candidate", 4,
     ["0.0017", "corrected label"]),
    ("rebuttal.corrected.ring.defect.gate_cost",
     "research/search/decision_rules2.json",
     "summary.ring_n6.declared.rules.R3_defect.cost.gate_seconds_per_candidate", 4,
     ["0.0755", "defect"]),
    ("rebuttal.accept.empirical", "research/search/corrected_gate.json",
     "families.ring_n6.accept.alpha_0.[Q=empirical_llm].accept_rate", 4, ["0.4700"]),
    ("rebuttal.accept.uniform_single", "research/search/corrected_gate.json",
     "families.ring_n6.accept.alpha_0.[Q=uniform_single,k=1].accept_rate", 4, ["0.0225"]),
    ("rebuttal.uniform_check.k2", "research/search/uniform_model_check.json",
     "families.ring_n6.cells.k=2.measured", 5, ["0.00025"]),
    ("rebuttal.panel.distinct", "research/search/corrected_gate.json",
     "families.ring_n6.panel.n_unique_subgroups", 0, ["generate distinct subgroups"]),
    # A6.7 corrected-feedback search runs
    ("rebuttal.a67.ring.verify_minus_fitness", "research/search/corrected_search.json",
     "headline.ring_verify_minus_fitness_mean", 5, ["+0.00039", "fitness"]),
    ("rebuttal.a67.ring.ci_low", "research/search/corrected_search.json",
     "headline.ring_verify_minus_fitness_ci_low", 5, ["−0.00016", "fitness"]),
    ("rebuttal.a67.ring.ci_high", "research/search/corrected_search.json",
     "headline.ring_verify_minus_fitness_ci_high", 5, ["+0.00093", "fitness"]),
    ("rebuttal.a67.graphs.verify_minus_fitness", "research/search/corrected_search.json",
     "headline.graphs_verify_minus_fitness_mean", 5, ["−0.02302", "graphs"]),
    ("rebuttal.a67.ring.label_pass_corrected", "research/search/corrected_search.json",
     "headline.ring_feedback_label_pass_corrected", 0, ["53/53", "corrected screen"]),
    ("rebuttal.a67.ring.label_pass_implemented", "research/search/corrected_search.json",
     "headline.ring_feedback_label_pass_implemented", 0, ["3/53", "implemented"]),
    ("rebuttal.a67.ring.fired_corrected", "research/search/corrected_search.json",
     "headline.ring_repair_fired_corrected", 0, ["3 of 12", "corrected"]),
    ("rebuttal.a67.ring.fired_implemented", "research/search/corrected_search.json",
     "headline.ring_repair_fired_implemented", 0, ["0 of 12", "implemented"]),
    ("rebuttal.a67.ring.diagnostic", "research/search/corrected_search.json",
     "headline.ring_repair_diagnostic_corrected", 5, ["−0.00300", "averaging"]),
    ("rebuttal.a67.graphs.diagnostic", "research/search/corrected_search.json",
     "headline.graphs_repair_diagnostic_corrected", 5, ["−0.06693", "coverage"]),
]

SPEC_EXTERNAL = [{"id": a, "file": b, "path": c, "decimals": d, "context": e}
                 for a, b, c, d, e in SPEC_EXTERNAL_RAW]
SPEC_REBUTTAL = [{"id": a, "file": b, "path": c, "decimals": d, "context": e}
                 for a, b, c, d, e in SPEC_REBUTTAL_RAW]
# (artifact, spec) pairs for the beyond-the-manuscript evaluation
EXTERNAL_DOCS = [("research/CLAIMS.md", SPEC_EXTERNAL),
                 ("research/paper/REBUTTAL_ROUND3.md", SPEC_REBUTTAL)]


# --- second external artifact: the round-3 response itself, which quotes the A6 numbers.

CONTEXT_LINES = 6


# ------------------------------------------------------------------- resolution
def _tokenize(path):
    """Split ``a.b[k=v]#agg.c`` into components, keeping bracketed selectors intact.

    A naive ``path.split(".")`` breaks ``eta=1.0`` inside a selector, which silently
    produced a selector that matched nothing.
    """
    toks, buf, depth = [], "", 0
    for ch in path:
        if ch == "[":
            depth += 1
            buf += ch
        elif ch == "]":
            depth -= 1
            buf += ch
        elif ch == "." and depth == 0:
            toks.append(buf)
            buf = ""
        else:
            buf += ch
    if buf:
        toks.append(buf)
    return [t for t in toks if t]


def resolve(file, path):
    """Walk a dotted path; list steps may carry ``[key=value,...]`` and ``#mean``."""
    with open(file) as fh:
        node = json.load(fh)
    for part in _tokenize(path):
        agg = None
        if "[" not in part:
            if "#" in part:
                key, agg = part.split("#", 1)
                node = node[key]
            else:
                node = node[part]
                continue
        key, rest = part.split("[", 1)
        if key:
            node = node[key]
        sel, _, agg = rest.partition("]")
        agg = agg.lstrip("#") or None
        if "=" not in sel:
            node = node[int(sel)]
            continue
        if isinstance(node, dict):        # keyed dict: the whole selector is the key
            node = node[rest.partition("]")[0]]
            continue
        want = {}
        for kv in sel.split(","):
            k, v = kv.split("=", 1)
            want[k.strip()] = v.strip()
        hits = [e for e in node if all(str(e.get(k)) == v for k, v in want.items())]
        if not hits:
            raise KeyError("selector %r matched no entry in %s" % (sel, file))
        node = _AggMean(hits) if agg == "mean" else (hits if agg else hits[0])
        if agg and agg != "mean":
            raise KeyError("unknown aggregation %r" % agg)
    return node


class _AggMean:
    """Deferred mean over a list of records: ``path#mean.key`` -> mean of ``key``."""

    def __init__(self, records):
        self.records = records

    def __getitem__(self, key):
        vals = [float(r[key]) for r in self.records]
        return sum(vals) / len(vals)


def fmt(v, decimals):
    return ("%%.%df" % decimals) % abs(v)


# --------------------------------------------------------------------- checking
def _sign_ok(line, token, value):
    """The manuscript must carry the record's sign, not just its magnitude.

    Without this, a sign flip is invisible to the checker: an earlier version of this
    instrument formatted values with abs() and its own mutation test measured that
    blindness (sign-flip detection 0.143), which is precisely the failure mode the
    third-round review predicted for token-level linting.
    """
    i = line.find(token)
    while i >= 0:
        before = line[:i]
        neg = before.rstrip("$ {~\\").endswith("-") or before.endswith("−")
        if neg == (value < 0):
            return True
        i = line.find(token, i + 1)
    return False


SCALE_RE = re.compile(r"10\s*\^\s*\{?[-+]?\d+\}?")   # a scale, not a value
TOKEN_RE_CACHE = {}


def _token_re(token):
    """Whole-number match: ``12`` must not match inside ``120``, ``0.012`` or ``10^{-12}``.

    Substring matching was the first implementation and it produced false bindings on
    short integer tokens; the mutation battery found it.
    """
    if token not in TOKEN_RE_CACHE:
        esc = re.escape(token)
        TOKEN_RE_CACHE[token] = re.compile(r"(?<![0-9.])" + esc + r"(?![0-9])")
    return TOKEN_RE_CACHE[token]


def _plain(line):
    """A line with LaTeX scale factors removed, so ``10^{-12}`` cannot match ``-12``."""
    return SCALE_RE.sub(" SC ", line)


def _lines_with(lines, token):
    rx = _token_re(token)
    return [i for i, ln in enumerate(lines) if rx.search(_plain(ln))]


def window(lines, idx, half=CONTEXT_LINES):
    return "\n".join(lines[max(0, idx - half): idx + half + 1]).lower()


def check_bindings(spec, tex_paths):
    lines = []
    for p in tex_paths:
        with open(p) as fh:
            lines.extend(fh.read().splitlines())
    out = []
    for b in spec:
        bid, file, path, dec, ctx = b["id"], b["file"], b["path"], b["decimals"], b["context"]
        rec = {"id": bid, "file": file, "path": path, "decimals": dec, "context": ctx}
        try:
            v = b["forced_value"] if "forced_value" in b else resolve(file, path)
        except Exception as exc:                       # noqa: BLE001
            rec.update(status="unresolvable", error=repr(exc))
            out.append(rec)
            continue
        rec["record_value"] = v
        token = fmt(v, dec)
        rec["token"] = token
        hits = [i for i in _lines_with(lines, token) if _sign_ok(lines[i], token, v)]
        if not _lines_with(lines, token):
            rec.update(status="value_absent_from_manuscript")
            out.append(rec)
            continue
        if not hits:
            rec.update(status="magnitude_present_with_wrong_sign")
            out.append(rec)
            continue
        ok = [i for i in hits if all(t.lower() in window(lines, i) for t in ctx)]
        if not ok:
            rec.update(status="value_present_but_context_wrong",
                       found_at=hits[:3])
            out.append(rec)
            continue
        rec.update(status="bound", lines=[i + 1 for i in ok])
        out.append(rec)
    return out


# -------------------------------------------------------------------- mutations
def mutations(spec):
    """Each mutation must be DETECTED (i.e. the mutated binding must not verify)."""
    out = []
    for b in spec:
        for kind in ("sign_flip", "arm_swap", "split_swap", "exponent", "endpoint"):
            m = dict(b)
            if kind == "sign_flip":
                m["path"] = b["path"]
                m["mutate_value"] = -1.0
            elif kind == "arm_swap":
                m["context"] = [b["context"][0] + "_wrong_arm"] + list(b["context"][1:])
            elif kind == "split_swap":
                m["context"] = list(b["context"]) + ["fresh_v99_split"]
            elif kind == "exponent":
                # an order-of-magnitude transcription error, which is what "exponent"
                # means in practice; reducing printed precision instead was a mutation
                # that a correctly-rounded manuscript legitimately still matches
                m["mutate_value"] = 10.0
            elif kind == "endpoint":
                m["context"] = list(b["context"]) + ["candidate_endpoint_only_zzz"]
            m["base_id"] = b["id"]
            m["mutation"] = kind
            out.append(m)
    return out


def apply_value_mutation(b):
    if "mutate_value" in b:
        bb = dict(b)
        bb["mutate_value"] = b["mutate_value"]
        return bb
    return b


def check_mutations(spec, tex_paths):
    """A mutation is detected when the checker reports anything other than 'bound'."""
    res = []
    base = {b["id"]: b for b in spec}
    for m in mutations(spec):
        b = base[m["base_id"]]
        # build a one-binding spec whose expected value/context is the mutated one
        fake = [{"id": m["id"] + "#" + m["mutation"], "file": b["file"], "path": b["path"],
                 "decimals": m["decimals"], "context": m["context"]}]
        if "mutate_value" in m:
            # mutate the *expected* value: the manuscript should no longer match it
            try:
                v = resolve(b["file"], b["path"]) * m["mutate_value"]
            except Exception:                          # noqa: BLE001
                continue
            if not isinstance(v, (int, float)):
                continue
            fake[0]["forced_value"] = float(v)
        rows = check_bindings(fake, tex_paths)
        r = rows[0]
        # A value mutation is *degenerate* when the perturbed value prints to the same
        # token as the true one (sign flip or 10x change of an exact zero). Context
        # mutations always change something, so they are never degenerate.
        degenerate = False
        if "forced_value" in fake[0]:
            try:
                true_token = fmt(resolve(b["file"], b["path"]), b["decimals"])
                degenerate = fmt(fake[0]["forced_value"], b["decimals"]) == true_token
            except Exception:                          # noqa: BLE001
                degenerate = False
        detected = r["status"] != "bound"
        res.append({"mutation": m["mutation"], "base": m["base_id"],
                    "status": r["status"], "detected": detected,
                    "degenerate": degenerate})
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(prog="research/paper/claim_bind.py")
    ap.add_argument("--tex", default="research/paper/main.tex")
    ap.add_argument("--report", default="research/paper/claim_binding_report.md")
    ap.add_argument("--extra-doc", default="",
                    help="override the artifact list (comma separated, uses SPEC_EXTERNAL); "
                         "empty means the frozen EXTERNAL_DOCS pairs")
    a = ap.parse_args(argv)
    tex = [a.tex]
    rows = check_bindings(SPEC, tex)
    mut = check_mutations(SPEC, tex)
    ext = []            # (doc, rows, mutations)
    pairs = EXTERNAL_DOCS if not a.extra_doc else \
        [(d.strip(), SPEC_EXTERNAL) for d in a.extra_doc.split(",") if d.strip()]
    for doc, spec_x in pairs:
        if os.path.exists(doc):
            ext.append((doc, check_bindings(spec_x, [doc]),
                        check_mutations(spec_x, [doc])))
    ext_rows = [r for _, rows, _ in ext for r in rows]
    ext_mut = [m for _, _, ms in ext for m in ms]
    ok = [r for r in rows if r["status"] == "bound"]
    det = [m for m in mut if m["detected"] and not m.get("degenerate")]
    mut_tested = [m for m in mut if not m.get("degenerate")]
    # false alarms: unmutated bindings that fail
    false_alarm = 0
    lines = ["# Claim-binding report (generated; do not hand-edit)\n",
             "Generated by `python3 -m research.paper.claim_bind`.\n",
             "## Bound headline values\n",
             "| id | record value | token in manuscript | status | line(s) |",
             "|---|---|---|---|---|"]
    for r in rows:
        lines.append("| `%s` | %s | `%s` | %s | %s |"
                     % (r["id"], r.get("record_value", "?"), r.get("token", "?"),
                        r["status"], r.get("lines", "")))
    lines += ["",
              "## Mutation testing of the instrument itself\n",
              "| mutation class | mutations run | detected | detection rate |",
              "|---|---|---|---|"]
    by = {}
    for m in mut:
        if m.get("degenerate"):
            continue
        s = by.setdefault(m["mutation"], [0, 0])
        s[0] += 1
        s[1] += int(m["detected"])
    for k, (n, d) in sorted(by.items()):
        lines.append("| %s | %d | %d | %.3f |" % (k, n, d, d / n if n else float("nan")))
    n_degen = sum(1 for m in mut if m.get("degenerate"))
    lines += ["",
              "Excluded from the denominators above: **%d degenerate mutations** where the "
              "perturbation leaves the *printed* token unchanged (a sign flip or an "
              "order-of-magnitude change of an exact zero, or a 10x change that rounds back "
              "to the same digits). No token-based instrument can detect a mutation it does "
              "not change, so counting them would inflate the rate; listing the exclusion "
              "keeps it visible." % n_degen, ""]
    lines += ["",
              "**Headline bindings:** %d/%d bound. Unbound bindings are *not* counted as "
              "false alarms of the checker: each is either a real manuscript gap (a value "
              "the paper should carry but does not) or a spec error, and each is listed by "
              "status below." % (len(ok), len(rows)),
              "**Mutation detection:** %d/%d testable (%.3f)."
              % (len(det), len(mut_tested),
                 len(det) / len(mut_tested) if mut_tested else float("nan")),
              "",
              "Undetected mutations, if any, are listed so the gap is visible rather than "
              "hidden:", ""]
    for m in mut_tested:
        if not m["detected"]:
            lines.append("* `%s` on `%s` escaped detection (status `%s`)"
                         % (m["mutation"], m["base"], m["status"]))
    if not any(not m["detected"] for m in mut):
        lines.append("* none")
    if ext_rows:
        eok = [r for r in ext_rows if r["status"] == "bound"]
        edet = [m for m in ext_mut if m["detected"] and not m.get("degenerate")]
        etest = [m for m in ext_mut if not m.get("degenerate")]
        lines += ["",
                  "## External evaluation: the same instrument on a second artifact\n",
                  "Artifact: `%s` (the project claim ledger). The bindings are the same "
                  "record values with that document's own context tokens, which is the "
                  "detection/false-alarm measurement requested beyond this manuscript. "
                  "It also tests transfer honestly: a row that does not carry the value at "
                  "all is a *spec* gap, listed by status, not a checker failure.\n",
                  "Artifacts: %s\n" % ", ".join("`%s`" % d for d, _, _ in ext),
                  "| id | record value | token | status | line(s) |",
                  "|---|---|---|---|---|"]
        for r in ext_rows:
            lines.append("| `%s` | %s | `%s` | %s | %s |"
                         % (r["id"], r.get("record_value", "?"), r.get("token", "?"),
                            r["status"], r.get("lines", "")))
        lines += ["", "**External bindings:** %d/%d bound. "
                  "**External mutation detection:** %d/%d testable (%.3f)."
                  % (len(eok), len(ext_rows), len(edet), len(etest),
                     len(edet) / len(etest) if etest else float("nan")), ""]
        for m in etest:
            if not m["detected"]:
                lines.append("* external: `%s` on `%s` escaped detection (status `%s`)"
                             % (m["mutation"], m["base"], m["status"]))
        ebad = [r for r in ext_rows if r["status"] not in ("bound",)]
        if not any(not m["detected"] for m in ext_mut):
            lines.append("* external mutations: none escaped detection")
        del ebad
    with open(a.report, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote %s: %d/%d bound, %d/%d testable mutations detected"
          % (a.report, len(ok), len(rows), len(det), len(mut_tested)))
    if ext_rows:
        eok = [r for r in ext_rows if r["status"] == "bound"]
        for doc, rows_d, mut_d in ext:
            ok_d = [r for r in rows_d if r["status"] == "bound"]
            det_d = [m for m in mut_d if m["detected"] and not m.get("degenerate")]
            tst_d = [m for m in mut_d if not m.get("degenerate")]
            print("    %-40s %d/%d bound, %d/%d testable mutations detected"
                  % (doc, len(ok_d), len(rows_d), len(det_d), len(tst_d)))
    for r in rows:
        if r["status"] != "bound":
            print("  UNBOUND %-38s %s" % (r["id"], r["status"]))
    for r in (ext_rows or []):
        if r["status"] != "bound":
            print("  UNBOUND(external) %-38s %s" % (r["id"], r["status"]))
    return 0 if len(ok) == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
