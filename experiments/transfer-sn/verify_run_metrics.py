#!/usr/bin/env python3
"""Independently recompute every number in RUN_METRICS.md and diff it against
the committed file.

This is a CHECKER, not a generator. It deliberately does NOT import
build_run_metrics.py: the regexes, the ANSATZ_SPEC extraction, the structural
tests and the counting are all reimplemented here from the definitions, so a
bug in one file does not silently validate itself. Anything the two files
disagree about is reported as a MISMATCH.

What it covers:

  * every cell of every table in RUN_METRICS.md, recomputed from the raw
    results_*/programs.sqlite and from dataset*.npz
  * the four lineage numbers quoted in the section-1 prose (10/10, 19.2%,
    324, 192), which are hardcoded text in the generator
  * the "11 such proposals in mid_r2" claim in the terminology note

What it CANNOT check, and reports as UNVERIFIABLE instead of passing silently:

  * section 3's "Shipped task files" and "Config" tables, and the null seed
    score. Those were transcribed from a byte-comparison run on the Bouchet
    cluster (2026-08-18) against ~/project/transfer_sn{,_null}, which is not in
    this repo. Re-verify them there with the command in build_run_metrics.py.

Usage
  python3 verify_run_metrics.py                 # check, print a summary
  python3 verify_run_metrics.py --verbose       # print every cell checked
  python3 verify_run_metrics.py --show          # print the recomputed tables
  python3 verify_run_metrics.py --tolerance 0.1

Exit code is 0 if every checkable number matches, 1 otherwise.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DOC = HERE / "RUN_METRICS.md"

N_QUBITS = 8

# --------------------------------------------------------------------------
# definitions, restated from the write-up rather than imported
# --------------------------------------------------------------------------
#
# SAY side: three independent regexes over LLM-authored patch name +
# description. "any" is not a superset of "mirror" -- butterfly/palindromic/
# reflect* match mirror only.
SAY_ANY = re.compile(r"\b(symmetr\w*|invarian\w*|equivarian\w*|permut\w*|orbit\w*|"
                     r"exchangeab\w*|relabel\w*|interchange\w*|mirror\w*)", re.I)
SAY_PERM = re.compile(r"\b(equivarian\w*|permut\w*|orbit\w*|exchangeab\w*|relabel\w*|"
                      r"interchange\w*|s_?8\b|s_?n\b)", re.I)
SAY_MIRROR = re.compile(r"\b(mirror\w*|palindrom\w*|butterfly|reflect\w*)", re.I)

# Namespace the EVOLVE-BLOCK may legitimately reference. Nothing else is in
# scope, so a block that reaches for anything more fails to parse and the
# proposal is excluded from the "parsed" denominator.
BLOCK_ENV = {
    "N_QUBITS": N_QUBITS, "N_UPLOADS": 3, "N_REPEATS": 2,
    "FEATURE_SCALE": math.pi / 2, "N_FEATURES": 28,
    "np": np, "math": math, "itertools": itertools,
    "ALLOWED_SINGLE_QUBIT_GATES": {"RX", "RY", "RZ"},
    "ALLOWED_TWO_QUBIT_GATES": {"CNOT", "CZ"},
    "ALLOWED_PARAM_TWO_QUBIT_GATES": {"CRX", "CRY", "CRZ"},
}


def run_inventory() -> list[dict]:
    """Every run in the analysis, with the group/arm/protocol labels the doc uses.

    The Azure-served rosters (results_az_*) are excluded: Azure lacked models
    the final roster needs and every Azure run predates the switch to
    OpenRouter. If one of those directories is present it is reported, so an
    accidental re-inclusion upstream is visible here too.
    """
    runs = []

    def add(group, arm, label, relpath, condition):
        d = HERE / relpath
        if not (d / "programs.sqlite").exists():
            return
        if condition == "null":
            protocol = "null-20gen"
        elif "_e1_" in label:
            protocol = "e1-20gen"
        else:
            protocol = "r-50gen"
        runs.append({"group": group, "arm": arm, "run": label, "dir": d,
                     "condition": condition, "protocol": protocol})

    for i in range(1, 6):
        add("real", "weak", f"weak_r{i}", f"results_or_weak_r{i}", "real")
    for i in range(1, 11):
        add("real", "weak", f"weak_e1_r{i}", f"results_or_weak_e1_r{i}", "real")
    for i in range(1, 4):
        add("real", "mid", f"mid_r{i}", f"results_or_mid_r{i}", "real")
    for i in range(1, 6):
        add("real", "mid", f"mid_e1_r{i}", f"results_or_mid_e1_r{i}", "real")
    add("real", "frontier", "frontier_r1", "results_or_frontier_r1", "real")
    for i in range(1, 3):
        add("real", "frontier", f"frontier_e1_r{i}", f"results_or_frontier_e1_r{i}", "real")

    for i in range(1, 6):
        add("null", "weak", f"null_weak_r{i}", f"null/results_weak_r{i}", "null")
    for i in range(1, 6):
        add("null", "mid", f"null_mid_r{i}", f"null/results_mid_r{i}", "null")
    for i in range(1, 4):
        add("null", "frontier", f"null_frontier_r{i}", f"null/results_frontier_r{i}", "null")

    for rw in ("rw13", "rw20"):
        for kind in ("ctl", "abl"):
            for i in range(1, 5):
                add("rewind", "weak", f"{rw}_{kind}_r{i}",
                    f"results_or_weak_{rw}_{kind}_r{i}", "real")

    for i in (1, 2):
        add("roster", "mixed", f"ens3_r{i}", f"results_ens3_r{i}", "real")

    return runs


# --------------------------------------------------------------------------
# structural measurement
# --------------------------------------------------------------------------

def extract_ansatz_spec(code: str, feature_pairs):
    """Recover ANSATZ_SPEC by executing the EVOLVE-BLOCK in a sandbox namespace.

    Evolved programs don't always assign a literal (several build the spec with
    comprehensions or concatenation), so the block is executed rather than
    parsed. Returns None if the markers are missing or the block raises, which
    is what "parsed < proposals" in the doc counts.
    """
    lines = code.splitlines()
    try:
        a = next(i for i, l in enumerate(lines) if "EVOLVE-BLOCK-START" in l)
        b = next(i for i, l in enumerate(lines) if "EVOLVE-BLOCK-END" in l)
    except StopIteration:
        return None
    ns = dict(BLOCK_ENV, FEATURE_PAIRS=feature_pairs)
    try:
        exec(compile("\n".join(lines[a + 1:b]), "<evolve-block>", "exec"), ns)
    except Exception:
        return None
    return ns.get("ANSATZ_SPEC")


def structure(spec):
    """The two build-side tests, plus the parameter-family shape.

    perm-motif  (tied-8): one parameter drives single-qubit gates on all 8 wires
    mirror-motif        : one parameter drives single-qubit gates on exactly
                          {i, 7-i} with i != 7-i
    """
    if spec is None:
        return None

    families: dict[str, list] = defaultdict(list)
    for gate in spec:
        if not isinstance(gate, dict):     # malformed entry; skip, don't crash
            continue
        param = gate.get("param")
        if not param:
            continue
        if "wires" in gate:
            w = gate["wires"]
            wires = tuple(w) if isinstance(w, (list, tuple)) else (w,)
            arity = 2
        else:
            wires, arity = (gate.get("wire"),), 1
        families[param].append((arity, wires))

    if not families:
        return None

    perm_motif = False
    mirror_motif = False
    for members in families.values():
        single = all(arity == 1 for arity, _ in members)
        if not single:
            continue
        wireset = {wires[0] for _, wires in members}
        if len(members) == N_QUBITS and wireset == set(range(N_QUBITS)):
            perm_motif = True
        if len(wireset) == 2:
            i, j = sorted(wireset)
            if j == N_QUBITS - 1 - i and i != j:
                mirror_motif = True

    return {"n_params": len(families),
            "max_family": max(len(v) for v in families.values()),
            "perm_motif": perm_motif,
            "mirror_motif": mirror_motif}


def read_proposals(db: Path, feature_pairs) -> list[dict]:
    con = sqlite3.connect(f"file://{db.resolve()}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "select id, parent_id, generation, combined_score, correct, code, metadata "
            "from programs order by generation"
        ).fetchall()
    finally:
        con.close()

    out = []
    for pid, parent, gen, score, correct, code, meta in rows:
        m = json.loads(meta) if meta else {}
        text = " ".join(str(m.get(k) or "") for k in ("patch_name", "patch_description"))
        out.append({
            "id": pid, "parent": parent, "gen": gen, "score": score,
            "correct": bool(correct),
            "is_seed": (m.get("model_name") or "seed") == "seed",
            "says_any": bool(SAY_ANY.search(text)),
            "says_perm": bool(SAY_PERM.search(text)),
            "says_mirror": bool(SAY_MIRROR.search(text)),
            "struct": structure(extract_ansatz_spec(code, feature_pairs)),
        })
    return out


def rate(num, den):
    return None if not den else 100.0 * num / den


def summarise_run(rec, feature_pairs) -> dict:
    rows = read_proposals(rec["dir"] / "programs.sqlite", feature_pairs)
    proposals = [r for r in rows if not r["is_seed"]]
    parsed = [r for r in proposals if r["struct"]]

    seeds = [r for r in rows if r["is_seed"] and r["score"] is not None]
    scored = [r for r in rows if r["correct"] and r["score"] is not None]
    best = max(scored, key=lambda r: r["score"]) if scored else None
    best_struct = best["struct"] if best else None

    said_any = [r for r in parsed if r["says_any"]]
    said_perm = [r for r in parsed if r["says_perm"]]
    said_mirror = [r for r in parsed if r["says_mirror"]]
    no_perm = [r for r in parsed if not r["says_perm"]]
    built_perm = [r for r in parsed if r["struct"]["perm_motif"]]

    def n_perm_built(pred):
        return sum(1 for r in said_perm if pred(r["struct"]))

    return {
        **{k: rec[k] for k in ("group", "arm", "run", "condition", "protocol")},
        "n_proposals": len(proposals),
        "n_parsed": len(parsed),
        "max_gen": max((r["gen"] for r in proposals if r["gen"] is not None), default=None),
        "seed_score": seeds[0]["score"] if seeds else None,
        "best_score": best["score"] if best else None,
        "best_gen": best["gen"] if best else None,
        "best_params": best_struct["n_params"] if best_struct else None,
        "best_max_family": best_struct["max_family"] if best_struct else None,
        "best_perm_motif": best_struct["perm_motif"] if best_struct else None,

        "perm_rate": rate(len(built_perm), len(parsed)),
        "perm_first_gen": min((r["gen"] for r in built_perm), default=None),
        "mirror_rate": rate(sum(r["struct"]["mirror_motif"] for r in parsed), len(parsed)),

        "n_said_any": len(said_any),
        "n_said_perm": len(said_perm),
        "n_said_mirror": len(said_mirror),
        "say_any_rate": rate(len(said_any), len(parsed)),
        "say_perm_rate": rate(len(said_perm), len(parsed)),
        "say_mirror_rate": rate(len(said_mirror), len(parsed)),

        "perm_given_any": rate(sum(r["struct"]["perm_motif"] for r in said_any), len(said_any)),
        "perm_given_perm": rate(n_perm_built(lambda s: s["perm_motif"]), len(said_perm)),
        "mirror_only_given_perm": rate(
            n_perm_built(lambda s: s["mirror_motif"] and not s["perm_motif"]), len(said_perm)),
        "neither_given_perm": rate(
            n_perm_built(lambda s: not s["mirror_motif"] and not s["perm_motif"]), len(said_perm)),
        "mirror_given_mirror": rate(
            sum(r["struct"]["mirror_motif"] for r in said_mirror), len(said_mirror)),

        # raw counts for the proposal-pooled headline tables
        "c_parsed": len(parsed),
        "c_said_any": len(said_any),
        "c_said_perm": len(said_perm),
        "c_said_mirror": len(said_mirror),
        "c_built_perm": len(built_perm),
        "c_perm_built_perm": n_perm_built(lambda s: s["perm_motif"]),
        "c_perm_built_mirror_only": n_perm_built(lambda s: s["mirror_motif"] and not s["perm_motif"]),
        "c_perm_built_neither": n_perm_built(lambda s: not s["mirror_motif"] and not s["perm_motif"]),
        "c_mirror_built_mirror": sum(r["struct"]["mirror_motif"] for r in said_mirror),
        "c_no_perm": len(no_perm),
        "c_no_perm_built_perm": sum(r["struct"]["perm_motif"] for r in no_perm),
        "c_said_specific": sum(1 for r in parsed if r["says_perm"] or r["says_mirror"]),
        "c_faithful": sum(1 for r in parsed
                          if (r["says_perm"] and r["struct"]["perm_motif"])
                          or (not r["says_perm"] and r["says_mirror"]
                              and r["struct"]["mirror_motif"])),
        "_rows": rows,
    }


# --------------------------------------------------------------------------
# lineage: the only clean say-vs-build test
# --------------------------------------------------------------------------

def lineage_counts(summaries) -> dict:
    """Restrict to proposals whose PARENT lacked the perm-motif, so the proposal
    had to introduce it rather than inherit it. This is what the section-1 prose
    quotes, and it is the number the say-vs-build claim should rest on."""
    agg = defaultdict(lambda: {"opportunities": 0, "introduced": 0,
                               "said_perm": 0, "said_perm_introduced": 0,
                               "no_perm": 0, "no_perm_introduced": 0})
    for s in summaries:
        by_id = {r["id"]: r for r in s["_rows"]}
        a = agg[(s["group"], s["condition"], s["arm"])]
        for r in s["_rows"]:
            if r["is_seed"] or not r["struct"]:
                continue
            parent = by_id.get(r["parent"])
            if not parent or not parent["struct"]:
                continue
            if parent["struct"]["perm_motif"]:
                continue                      # inherited it; no choice to make
            a["opportunities"] += 1
            a["introduced"] += r["struct"]["perm_motif"]
            if r["says_perm"]:
                a["said_perm"] += 1
                a["said_perm_introduced"] += r["struct"]["perm_motif"]
            else:
                a["no_perm"] += 1
                a["no_perm_introduced"] += r["struct"]["perm_motif"]
    return dict(agg)


# --------------------------------------------------------------------------
# expected tables, rebuilt from the recomputed per-run summaries
# --------------------------------------------------------------------------

def pooled(group, key):
    return sum(s[key] for s in group if s[key] is not None)


def mean(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def fmt(v, nd=2):
    if v is None:
        return "--"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def headline_groups(summaries):
    """(label, arm) -> pooled counts, matching section 1's row order."""
    out = []
    for label, cond, grp in (("real", "real", "real"),
                             ("null", "null", "null"),
                             ("real (alt roster)", None, "roster")):
        for arm in ("weak", "mid", "frontier", "mixed"):
            g = [s for s in summaries if s["group"] == grp and s["arm"] == arm
                 and (cond is None or s["condition"] == cond)]
            if g:
                out.append((f"{label}|{arm}", label, arm, g))
    return out


def build_expected(summaries, real_ds, null_ds):
    """Every doc table, keyed by (section signature, row key) -> {column: value}."""
    tables: dict[str, dict[str, dict]] = {}

    # ---- section 1A ----
    t = {}
    for key, label, arm, g in headline_groups(summaries):
        n = pooled(g, "c_parsed")
        t[key] = {
            "runs": len(g), "proposals": n,
            "says any-symmetry %": rate(pooled(g, "c_said_any"), n),
            "says perm %": rate(pooled(g, "c_said_perm"), n),
            "says mirror %": rate(pooled(g, "c_said_mirror"), n),
            "builds perm-motif %": rate(pooled(g, "c_built_perm"), n),
        }
    tables["1A"] = t

    # ---- section 1B ----
    t = {}
    for key, label, arm, g in headline_groups(summaries):
        np_ = pooled(g, "c_said_perm")
        base = rate(pooled(g, "c_no_perm_built_perm"), pooled(g, "c_no_perm"))
        right = rate(pooled(g, "c_perm_built_perm"), np_)
        t[key] = {
            "n said perm": np_,
            "builds perm-motif (right) %": right,
            "builds mirror-motif only (wrong) %": rate(pooled(g, "c_perm_built_mirror_only"), np_),
            "builds neither %": rate(pooled(g, "c_perm_built_neither"), np_),
            "BASE: builds perm-motif without saying perm %": base,
            "lift": (right - base) if (right is not None and base is not None) else None,
        }
    tables["1B"] = t

    # ---- section 1C ----
    t = {}
    for key, label, arm, g in headline_groups(summaries):
        spec_n = pooled(g, "c_said_specific")
        mir_n = pooled(g, "c_said_mirror")
        t[key] = {
            "n named a specific symmetry": spec_n,
            "builds what it says %": rate(pooled(g, "c_faithful"), spec_n),
            "n said mirror": mir_n,
            "builds mirror-motif | says mirror %": rate(pooled(g, "c_mirror_built_mirror"), mir_n),
        }
    tables["1C"] = t

    # ---- section 2: arm summary (run-level means) ----
    t = {}
    for cond, grp, proto in (("real", "real", "e1-20gen"),
                             ("real", "real", "r-50gen"),
                             ("null", "null", "null-20gen")):
        for arm in ("weak", "mid", "frontier"):
            g = [s for s in summaries if s["group"] == grp and s["condition"] == cond
                 and s["arm"] == arm and s["protocol"] == proto]
            if not g:
                continue
            scores = [s["best_score"] for s in g if s["best_score"] is not None]
            m = mean(scores)
            sd = ((sum((x - m) ** 2 for x in scores) / (len(scores) - 1)) ** 0.5
                  if len(scores) > 1 else None)
            t[f"{cond}|{proto}|{arm}"] = {
                "runs": len(g), "mean best": m, "sd": sd,
                "CV": (sd / m) if (sd and m) else None,
                "builds perm-motif %": mean([s["perm_rate"] for s in g]),
                "perm-motif in best": f"{sum(1 for s in g if s['best_perm_motif'])}/{len(g)}",
                "params in best": mean([s["best_params"] for s in g]),
                "says any-symmetry %": mean([s["say_any_rate"] for s in g]),
                "says perm %": mean([s["say_perm_rate"] for s in g]),
                "says mirror %": mean([s["say_mirror_rate"] for s in g]),
            }
    tables["2"] = t

    # ---- per-run tables (sections 4-7 share these four shapes) ----
    scores, motif, vocab, saybuild = {}, {}, {}, {}
    for s in summaries:
        k = s["run"]
        scores[k] = {
            "protocol": s["protocol"], "gens": s["max_gen"],
            "proposals": s["n_proposals"], "parsed": s["n_parsed"],
            "seed": s["seed_score"], "best": s["best_score"],
            "best gen": s["best_gen"], "params": s["best_params"],
            "max family": s["best_max_family"],
            "perm-motif in best": s["best_perm_motif"],
        }
        motif[k] = {
            "builds perm-motif %": s["perm_rate"], "first gen": s["perm_first_gen"],
            "perm-motif in best": s["best_perm_motif"],
            "builds mirror-motif %": s["mirror_rate"], "params in best": s["best_params"],
        }
        vocab[k] = {
            "says any-symmetry %": s["say_any_rate"], "says perm %": s["say_perm_rate"],
            "says mirror %": s["say_mirror_rate"], "n said any": s["n_said_any"],
            "n said perm": s["n_said_perm"], "n said mirror": s["n_said_mirror"],
        }
        saybuild[k] = {
            "builds perm-motif | says any-symmetry %": s["perm_given_any"],
            "builds perm-motif | says perm %": s["perm_given_perm"],
            "builds mirror-motif only | says perm %": s["mirror_only_given_perm"],
            "builds neither | says perm %": s["neither_given_perm"],
            "builds mirror-motif | says mirror %": s["mirror_given_mirror"],
            "n said any": s["n_said_any"], "n said perm": s["n_said_perm"],
            "n said mirror": s["n_said_mirror"],
        }
    tables["run-scores"] = scores
    tables["run-motif"] = motif
    tables["run-vocab"] = vocab
    tables["run-saybuild"] = saybuild

    # ---- section 3: dataset + derived (the computable half) ----
    t = {}
    for split in ("train", "validation", "test"):
        t[split] = {
            "rows": len(real_ds[f"x_{split}"]),
            "real +1 frac": float(np.mean(real_ds[f"y_{split}"] > 0)),
            "null +1 frac": float(np.mean(null_ds[f"y_{split}"] > 0)),
            "real edge density": float(real_ds[f"x_{split}"].mean()),
            "null edge density": float(null_ds[f"x_{split}"].mean()),
        }
    tables["3-dataset"] = t

    fp_r = [tuple(int(w) for w in r) for r in real_ds["feature_pairs"]]
    fp_n = [tuple(int(w) for w in r) for r in null_ds["feature_pairs"]]
    tables["3-derived"] = {
        "feature_pairs` md5 match": {"real": "yes" if fp_r == fp_n else "NO",
                                     "null": "yes" if fp_r == fp_n else "NO"},
        "linear probe on raw features, test accuracy": {
            "real": linear_probe(real_ds), "null": linear_probe(null_ds)},
    }
    return tables


def linear_probe(d) -> float:
    X = np.hstack([d["x_train"].astype(float), np.ones((len(d["x_train"]), 1))])
    w, *_ = np.linalg.lstsq(X, d["y_train"].astype(float), rcond=None)
    Xt = np.hstack([d["x_test"].astype(float), np.ones((len(d["x_test"]), 1))])
    return float(np.mean(np.sign(Xt @ w) == d["y_test"]))


# --------------------------------------------------------------------------
# markdown parsing
# --------------------------------------------------------------------------

def parse_markdown_tables(text: str) -> list[dict]:
    """Every pipe table in the doc, with the heading path that precedes it."""
    tables = []
    section = subsection = bold = ""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            section, subsection, bold = line[3:].strip(), "", ""
        elif line.startswith("### "):
            subsection = line[4:].strip()
        elif line.startswith("**") and line.count("**") >= 2:
            bold = line.split("**")[1].strip()
        elif line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[-: |]+\|$", lines[i + 1]):
            header = [c.strip().replace("\\|", "|") for c in line.strip("|").split("|")]
            rows = []
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip().replace("\\|", "|") for c in lines[i].strip("|").split("|")]
                rows.append(cells)
                i += 1
            tables.append({"section": section, "subsection": subsection,
                           "bold": bold, "header": header, "rows": rows})
            continue
        i += 1
    return tables


def cell_matches(doc_value: str, expected, tol: float) -> bool:
    doc_value = doc_value.strip().strip("*").replace("`", "")
    if expected is None:
        return doc_value in ("--", "")
    if isinstance(expected, bool):
        return doc_value == ("yes" if expected else "no")
    if isinstance(expected, str):
        return doc_value == expected
    m = re.fullmatch(r"-?\d+(?:\.\d+)?", doc_value)
    if not m:
        return False
    got = float(doc_value)
    if isinstance(expected, int) and float(expected).is_integer():
        return abs(got - expected) < 1e-9
    # tolerance covers the doc's rounding to 1, 2 or 4 decimals
    return abs(got - float(expected)) <= max(tol, abs(float(expected)) * 1e-6)


# --------------------------------------------------------------------------
# checking
# --------------------------------------------------------------------------

# Rows whose values were transcribed from the cluster comparison rather than
# computed from anything in this repo. Reported at the end, never silently passed.
UNVERIFIABLE_ROWS = {"seed program score (rescaled)"}

TABLE_KIND = {
    "Scores and best-program structure": "run-scores",
    "Motif": "run-motif",
    "Symmetry vocabulary": "run-vocab",
    "Say versus build": "run-saybuild",
}


def identify(tbl) -> tuple[str | None, str | None]:
    """(expected-table id, name of the column holding the row key)."""
    h, sec, sub, bold = tbl["header"], tbl["section"], tbl["subsection"], tbl["bold"]
    if sec.startswith("1.") and bold.startswith("A."):
        return "1A", None
    if sec.startswith("1.") and bold.startswith("B."):
        return "1B", None
    if sec.startswith("1.") and bold.startswith("C."):
        return "1C", None
    if sec.startswith("2."):
        return "2", None
    if sub in TABLE_KIND and h and h[0] == "run":
        return TABLE_KIND[sub], "run"
    if sub == "Dataset":
        return "3-dataset", "split"
    if sub == "Derived":
        return "3-derived", "quantity"
    return None, None


def row_key(table_id, header, cells) -> str:
    idx = {c: i for i, c in enumerate(header)}
    if table_id in ("1A", "1B", "1C"):
        return f"{cells[idx['task']]}|{cells[idx['arm']]}"
    if table_id == "2":
        return f"{cells[idx['task']]}|{cells[idx['protocol']]}|{cells[idx['arm']]}"
    return cells[0].strip().strip("`")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verbose", action="store_true", help="print every cell checked")
    ap.add_argument("--show", action="store_true", help="dump the recomputed values as JSON")
    ap.add_argument("--tolerance", type=float, default=0.06,
                    help="absolute tolerance for rounded values (default 0.06)")
    ap.add_argument("--doc", default=str(DOC))
    args = ap.parse_args()

    stray = sorted(p.name for p in HERE.glob("results_az_*") if (p / "programs.sqlite").exists())
    if stray:
        print(f"[note] Azure run dirs present on disk but excluded from the "
              f"analysis: {', '.join(stray)}\n")

    fp = [tuple(int(w) for w in row) for row in np.load(HERE / "dataset.npz")["feature_pairs"]]
    fp_null = [tuple(int(w) for w in row)
               for row in np.load(HERE / "dataset_null.npz")["feature_pairs"]]
    if fp != fp_null:
        print("[FAIL] feature_pairs differ between the real and null datasets")
        return 1

    recs = run_inventory()
    print(f"[verify] recomputing {len(recs)} runs from programs.sqlite ...")
    summaries = []
    for rec in recs:
        try:
            summaries.append(summarise_run(rec, fp))
        except Exception as exc:
            print(f"[verify] ERROR reading {rec['run']}: {exc}")
    print(f"[verify] {len(summaries)} runs measured, "
          f"{sum(s['n_parsed'] for s in summaries)} proposals parsed\n")

    real_ds = np.load(HERE / "dataset.npz")
    null_ds = np.load(HERE / "dataset_null.npz")
    expected = build_expected(summaries, real_ds, null_ds)

    if args.show:
        print(json.dumps({k: v for k, v in expected.items()}, indent=2, default=str))

    doc_text = Path(args.doc).read_text()
    tables = parse_markdown_tables(doc_text)

    checked = failed = skipped_tables = 0
    failures = []

    for tbl in tables:
        tid, _ = identify(tbl)
        if tid is None:
            skipped_tables += 1
            continue
        exp_rows = expected[tid]
        for cells in tbl["rows"]:
            key = row_key(tid, tbl["header"], cells)
            if key in UNVERIFIABLE_ROWS:
                continue
            exp = exp_rows.get(key)
            if exp is None:
                failures.append(f"{tbl['section']} / {tbl['subsection'] or tbl['bold']}: "
                                f"row '{key}' is in the doc but not in the recomputed data")
                failed += 1
                continue
            for col, val in zip(tbl["header"], cells):
                if col not in exp:
                    continue
                checked += 1
                ok = cell_matches(val, exp[col], args.tolerance)
                if args.verbose:
                    print(f"  {'ok  ' if ok else 'FAIL'} {tid:12} {key:22} {col:44} "
                          f"doc={val:>10}  recomputed={fmt(exp[col], 4):>10}")
                if not ok:
                    failed += 1
                    failures.append(
                        f"{tbl['section']} / {tbl['subsection'] or tbl['bold']}: "
                        f"[{key}] {col}: doc says {val!r}, recomputed {fmt(exp[col], 4)!r}")
        # every recomputed row should also be present in the doc
        doc_keys = {row_key(tid, tbl["header"], c) for c in tbl["rows"]}
        if tid.startswith("run-"):
            continue    # per-run tables are split across sections 4-7 by group
        for key in exp_rows:
            if key in UNVERIFIABLE_ROWS:
                continue
            if key not in doc_keys:
                failed += 1
                failures.append(f"{tbl['section']} / {tbl['subsection'] or tbl['bold']}: "
                                f"row '{key}' was recomputed but is missing from the doc")

    # ---- prose numbers ----
    print("Prose numbers quoted in section 1 (hardcoded text in the generator):\n")
    lin = lineage_counts(summaries)
    print("  Parent LACKED the perm-motif -> did this proposal INTRODUCE it?")
    def n_pct(num, den):
        """n/den (pct%) -- both columns report the same thing in the same units."""
        r = rate(num, den)
        return f"{num}/{den} ({fmt(r, 1)}%)" if den else f"{num}/{den} (--)"

    print(f"    {'group/task/arm':20} {'opportunities':>13} "
          f"{'SAID perm: introduced':>24} {'DIDNT say: introduced':>24}")
    for (grp, cond, arm), a in sorted(lin.items()):
        print(f"    {grp + '/' + cond + '/' + arm:20} {a['opportunities']:13} "
              f"{n_pct(a['said_perm_introduced'], a['said_perm']):>24} "
              f"{n_pct(a['no_perm_introduced'], a['no_perm']):>24}")

    fr = lin.get(("real", "real", "frontier"))
    claims = []
    if fr:
        claims.append((f"frontier introduces it in {fr['said_perm_introduced']}/{fr['said_perm']} "
                       f"of proposals that named permutation symmetry",
                       "10/10", f"{fr['said_perm_introduced']}/{fr['said_perm']}"))
        claims.append(("frontier background introduction rate",
                       "19.2", fmt(rate(fr['no_perm_introduced'], fr['no_perm']), 1)))
    for arm, want in (("weak", "324"), ("mid", "192")):
        n = sum(s["c_parsed"] for s in summaries
                if s["condition"] == "real" and s["group"] == "real" and s["arm"] == arm)
        said = sum(s["c_said_perm"] for s in summaries
                   if s["condition"] == "real" and s["group"] == "real" and s["arm"] == arm)
        claims.append((f"real/{arm}: said perm {said} of {n} parsed proposals",
                       f"0 of {want}", f"{said} of {n}"))

    mid_r2 = next((s for s in summaries if s["run"] == "mid_r2"), None)
    if mid_r2:
        rows = [r for r in mid_r2["_rows"] if not r["is_seed"] and r["struct"]]
        mirror_only = sum(1 for r in rows if r["says_mirror"] and not r["says_any"])
        claims.append(("mid_r2 proposals matching mirror but not any-symmetry",
                       "11", str(mirror_only)))

    print("\n  claim                                                          doc      recomputed")
    for desc, doc_val, got in claims:
        ok = doc_val.replace("0 of ", "0 of ") == got or doc_val == got
        checked += 1
        if not ok:
            failed += 1
            failures.append(f"section 1 prose: {desc}: doc says {doc_val!r}, recomputed {got!r}")
        print(f"  {'ok  ' if ok else 'FAIL'} {desc:58} {doc_val:>8}  {got:>10}")

    # ---- unverifiable ----
    print("\nUNVERIFIABLE here (transcribed from a cluster comparison, not in this repo):")
    print("  * section 3 'Shipped task files' (identical / differs column)")
    print("  * section 3 'Config' (generations and cost caps per arm)")
    print("  * section 3 'Derived' seed program scores (0.0000 / 1.2490)")
    print("  Re-check on the cluster:")
    print("    ssh bouchet 'cmp -s $HOME/project/transfer_sn/<f> "
          "$HOME/project/transfer_sn_null/<f>'")

    print(f"\n{'=' * 72}")
    print(f"checked {checked} numbers across {len(tables) - skipped_tables} tables "
          f"({skipped_tables} tables not machine-checkable)")
    if failed:
        print(f"{failed} MISMATCH(ES):\n")
        for f_ in failures:
            print(f"  * {f_}")
        return 1
    print("all recomputed numbers match RUN_METRICS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
