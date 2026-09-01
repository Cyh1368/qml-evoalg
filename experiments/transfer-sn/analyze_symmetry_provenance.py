#!/usr/bin/env python3
"""How did each arm arrive at the symmetry: fresh proposition, or inherited?

For every proposal we know (a) whether its own block contains a full 8-wire
tied family, and (b) whether its parent's block already did. That splits the
population four ways:

  INTRODUCTION  parent lacked it, child has it   -- a real discovery step
  INHERITED     parent had it, child keeps it    -- carried forward
  LOST          parent had it, child drops it    -- regression
  ABSENT        neither has it

Only INTRODUCTION events are discoveries. For each we record how the proposer
was working: patch_type (diff = edit the parent, full = rewrite, cross =
merge two programs), whether it was shown inspiration programs that already
contained the structure, and whether its own note cites prior programs or
their scores. That distinguishes "proposed the symmetry outright" from
"copied it from something already in the archive".

Writes symmetry_provenance.json for the figure script.

Usage:  python3 analyze_symmetry_provenance.py
"""
from __future__ import annotations

import itertools
import json
import math
import re
import sqlite3

import numpy as np

ARMS = ["weak", "mid", "frontier"]

# Generic symmetry vocabulary: any symmetry idea at all, including mirror
# layouts and measurement invariance.
GENERAL = re.compile(r"\b(symmetr\w*|invarian\w*|equivarian\w*|permut\w*|orbit\w*|"
                     r"exchangeab\w*|relabel\w*|interchange\w*|mirror\w*)", re.I)
# Task-specific: only meaningful for permutation symmetry of the qubits.
PERM = re.compile(r"\b(equivarian\w*|permut\w*|orbit\w*|exchangeab\w*|relabel\w*|"
                  r"interchange\w*|s_?8\b|s_?n\b)", re.I)
# Symmetry named but of the WRONG kind for this task.
MIRROR = re.compile(r"\b(mirror\w*|palindrom\w*|butterfly|reflect\w*)", re.I)
# Evidence the proposer reasoned from earlier programs rather than from scratch.
CITES_PRIOR = re.compile(
    r"\b(current program|prior program|previous program|second program|"
    r"the current ansatz|current best|earlier|previously|combined score|"
    r"parent|both programs|first program|recommendation)\b", re.I
)

ENV = {
    "N_QUBITS": 8, "N_UPLOADS": 3, "N_REPEATS": 2, "FEATURE_SCALE": math.pi / 2,
    "N_FEATURES": 28, "np": np, "math": math, "itertools": itertools,
    "ALLOWED_SINGLE_QUBIT_GATES": {"RX", "RY", "RZ"},
    "ALLOWED_TWO_QUBIT_GATES": {"CNOT", "CZ"},
    "ALLOWED_PARAM_TWO_QUBIT_GATES": {"CRX", "CRY", "CRZ"},
}


def spec_of(code, fp):
    lines = code.splitlines()
    try:
        a = next(i for i, l in enumerate(lines) if "EVOLVE-BLOCK-START" in l)
        b = next(i for i, l in enumerate(lines) if "EVOLVE-BLOCK-END" in l)
    except StopIteration:
        return None
    ns = dict(ENV, FEATURE_PAIRS=fp)
    try:
        exec(compile("\n".join(lines[a + 1:b]), "<blk>", "exec"), ns)
        return ns.get("ANSATZ_SPEC")
    except Exception:
        return None


def tied8(spec):
    """True if some single angle drives exactly 8 single-qubit gates (an S_8 orbit)."""
    if not spec:
        return False
    fams = {}
    for g in spec:
        p = g.get("param")
        if not p:
            continue
        fams.setdefault(p, []).append(2 if "wires" in g else 1)
    return any(len(v) == 8 and all(w == 1 for w in v) for v in fams.values())


def angles(spec):
    return len({g["param"] for g in spec if g.get("param")}) if spec else None


def main():
    fp = [tuple(int(w) for w in r) for r in np.load("dataset.npz")["feature_pairs"]]
    out = {}
    for arm in ARMS:
        con = sqlite3.connect(f"results_or_{arm}_r1/programs.sqlite")
        progs = {}
        for pid, parent, gen, score, correct, code, meta in con.execute(
            "select id, parent_id, generation, combined_score, correct, code, metadata from programs"
        ):
            m = json.loads(meta) if meta else {}
            spec = spec_of(code, fp)
            text = " ".join(str(m.get(k) or "") for k in ("patch_name", "patch_description"))
            progs[pid] = {
                "parent": parent, "gen": gen, "score": score, "correct": correct,
                "model": (m.get("model_name") or "seed").replace("openrouter/", ""),
                "patch_type": m.get("patch_type"), "patch_name": m.get("patch_name"),
                "text": text, "tied8": tied8(spec), "angles": angles(spec),
                "general": bool(GENERAL.search(text)), "perm": bool(PERM.search(text)),
                "mirror": bool(MIRROR.search(text)), "cites": bool(CITES_PRIOR.search(text)),
                "insp": (json.loads(m.get("archive_inspiration_ids") or "[]")
                         if isinstance(m.get("archive_inspiration_ids"), str)
                         else (m.get("archive_inspiration_ids") or [])),
            }

        events, rows = [], []
        for pid, p in progs.items():
            if p["model"] == "seed":
                continue
            par = progs.get(p["parent"])
            par_t8 = bool(par and par["tied8"])
            state = ("INTRODUCTION" if p["tied8"] and not par_t8 else
                     "INHERITED" if p["tied8"] and par_t8 else
                     "LOST" if par_t8 else "ABSENT")
            rows.append({**{k: p[k] for k in
                            ("gen", "score", "correct", "model", "patch_type", "patch_name",
                             "general", "perm", "mirror", "cites", "tied8", "angles")},
                         "state": state})
            if state == "INTRODUCTION":
                insp_t8 = any(progs.get(i, {}).get("tied8") for i in p["insp"])
                events.append({
                    "gen": p["gen"], "score": p["score"], "model": p["model"],
                    "patch_type": p["patch_type"], "patch_name": p["patch_name"],
                    "perm": p["perm"], "general": p["general"], "cites": p["cites"],
                    "parent_gen": par["gen"] if par else None,
                    "parent_angles": par["angles"] if par else None,
                    "angles": p["angles"],
                    "inspiration_had_it": insp_t8,
                })
        rows.sort(key=lambda r: r["gen"])
        events.sort(key=lambda e: e["gen"])
        out[arm] = {"rows": rows, "introductions": events}

        n = len(rows)
        print(f"\n{'=' * 74}\n{arm.upper()}  ({n} proposals)\n{'=' * 74}")
        for st in ("INTRODUCTION", "INHERITED", "LOST", "ABSENT"):
            c = sum(1 for r in rows if r["state"] == st)
            print(f"  {st:<14} {c:>3}  ({100 * c / n:4.1f}%)")
        print(f"  general symmetry language : {sum(r['general'] for r in rows):>3} "
              f"({100 * sum(r['general'] for r in rows) / n:4.1f}%)")
        print(f"  permutation-specific      : {sum(r['perm'] for r in rows):>3} "
              f"({100 * sum(r['perm'] for r in rows) / n:4.1f}%)")
        print(f"  mirror/reflection symmetry: {sum(r['mirror'] for r in rows):>3} "
              f"({100 * sum(r['mirror'] for r in rows) / n:4.1f}%)")
        if events:
            print(f"\n  DISCOVERY EVENTS (parent lacked an 8-tied family, child has one):")
            for e in events:
                print(f"    gen{e['gen']:<4} {e['patch_type']:<5} {e['model']:<34} "
                      f"angles {e['parent_angles']}->{e['angles']}  "
                      f"perm_lang={e['perm']!s:<5} cites_prior={e['cites']!s:<5} "
                      f"insp_had_it={e['inspiration_had_it']}")

    with open("symmetry_provenance.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote symmetry_provenance.json")


if __name__ == "__main__":
    main()
