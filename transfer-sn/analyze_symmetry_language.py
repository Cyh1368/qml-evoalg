#!/usr/bin/env python3
"""How often, and how early, does each run's proposer talk about symmetry?

The proposer is never told the records are graphs or that the label is invariant
under relabelling vertices. So its own words are the only evidence of whether it
worked the symmetry out. This counts that language in the LLM-authored fields
(patch name + patch description), never in evaluator feedback.

Two vocabularies are counted separately, because they are different claims:

  EXPLICIT  symmetry / equivariant / permutation / invariant / orbit / S_8 /
            exchangeable / relabel  -- naming the concept
  SHARING   shared / tied / collective / same angle -- the mechanism that
            implements it, which a model can reach without naming why

A model can implement sharing without understanding it (weak signal), or name
the symmetry without implementing it (talk). Reporting both separates those.

Usage:  python3 analyze_symmetry_language.py <run.sqlite> [more.sqlite ...]
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import defaultdict

EXPLICIT = re.compile(
    r"\b(symmetr\w*|equivarian\w*|permutation\w*|permut\w*|invarian\w*|orbit\w*|"
    r"exchangeab\w*|relabel\w*|interchange\w*|s_?8\b|s_?n\b)", re.I
)
SHARING = re.compile(
    r"\b(shared?|sharing|tied|tying|collective\w*|same angle|single angle|"
    r"one angle|global angle)\b", re.I
)


def analyse(path: str, label: str) -> dict:
    con = sqlite3.connect(path)
    rows = []
    for gen, score, correct, meta in con.execute(
        "select generation, combined_score, correct, metadata from programs order by generation"
    ):
        m = json.loads(meta) if meta else {}
        model = (m.get("model_name") or "seed").replace("openrouter/", "").replace("azure-", "")
        if model == "seed":
            continue
        # LLM-authored text only.
        text = " ".join(str(m.get(k) or "") for k in ("patch_name", "patch_description"))
        rows.append({
            "gen": gen, "score": score, "correct": correct, "model": model,
            "text": text,
            "explicit": bool(EXPLICIT.search(text)),
            "sharing": bool(SHARING.search(text)),
            "n_explicit": len(EXPLICIT.findall(text)),
        })

    n = len(rows)
    exp = [r for r in rows if r["explicit"]]
    shr = [r for r in rows if r["sharing"]]
    first_exp = min((r["gen"] for r in exp), default=None)
    first_shr = min((r["gen"] for r in shr), default=None)

    print(f"\n{'=' * 76}\n{label}\n{'=' * 76}")
    print(f"  proposals with LLM text        : {n}")
    print(f"  EXPLICIT symmetry language     : {len(exp):3d}  ({100 * len(exp) / n:5.1f}%)   "
          f"first at gen {first_exp}")
    print(f"  parameter-SHARING language     : {len(shr):3d}  ({100 * len(shr) / n:5.1f}%)   "
          f"first at gen {first_shr}")
    print(f"  total explicit term occurrences: {sum(r['n_explicit'] for r in rows)}")

    per = defaultdict(lambda: {"n": 0, "exp": 0})
    for r in rows:
        per[r["model"]]["n"] += 1
        per[r["model"]]["exp"] += r["explicit"]
    print(f"\n  {'model':<40}{'props':>6}{'explicit':>10}{'rate':>8}")
    for mdl, v in sorted(per.items(), key=lambda kv: -kv[1]["exp"] / max(kv[1]["n"], 1)):
        print(f"  {mdl:<40}{v['n']:>6}{v['exp']:>10}{100 * v['exp'] / v['n']:>7.0f}%")

    # Does naming it help? Compare scores of proposals that do vs don't.
    def mean(rs):
        vals = [r["score"] for r in rs if r["correct"] and r["score"] is not None]
        return sum(vals) / len(vals) if vals else float("nan")

    print(f"\n  mean score, explicit-symmetry proposals : {mean(exp):.3f}  (n={len(exp)})")
    print(f"  mean score, all other proposals         : "
          f"{mean([r for r in rows if not r['explicit']]):.3f}  "
          f"(n={len([r for r in rows if not r['explicit']])})")

    print(f"\n  first 6 proposals using explicit symmetry language:")
    for r in exp[:6]:
        sc = "  n/a " if r["score"] is None else f"{r['score']:6.3f}"
        terms = sorted({t.lower() for t in EXPLICIT.findall(r["text"])})[:4]
        print(f"    gen{r['gen']:<4} {sc}  {r['model']:<34} {','.join(terms)}")

    return {"n": n, "explicit": len(exp), "first": first_exp}


def main() -> int:
    for path in sys.argv[1:]:
        analyse(path, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
