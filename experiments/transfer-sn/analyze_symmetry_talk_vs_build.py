#!/usr/bin/env python3
"""Does naming the symmetry mean building it?

analyze_symmetry_language.py showed the mid arm names symmetry most often (67%)
and earliest (gen 2) while scoring worst, and the weak arm barely names it (6%)
while scoring 3x better. So mention-frequency is clearly not the thing that
matters. This separates the talk from the build.

For every proposal it extracts the ANSATZ_SPEC and measures what was actually
constructed:

  angles/block  distinct parameter names -- 3 is the fully orbit-tied ideal,
                24 is the unsymmetric seed
  max_family    largest number of gates driven by ONE angle. 8 means a family
                tied across all wires (an S_8 orbit); 1 means every gate has
                its own angle
  tied8         does the block contain at least one family of exactly 8 tied
                single-qubit gates, i.e. a genuine full-wire orbit?

Then it cross-tabulates against whether the LLM's own patch note used explicit
symmetry vocabulary.

Usage:  python3 analyze_symmetry_talk_vs_build.py <run.sqlite> [...]
"""
from __future__ import annotations

import itertools
import json
import math
import re
import sqlite3
import sys

import numpy as np

EXPLICIT = re.compile(
    r"\b(symmetr\w*|equivarian\w*|permutation\w*|permut\w*|invarian\w*|orbit\w*|"
    r"exchangeab\w*|relabel\w*|interchange\w*|s_?8\b|s_?n\b)", re.I
)

ENV = {
    "N_QUBITS": 8, "N_UPLOADS": 3, "N_REPEATS": 2, "FEATURE_SCALE": math.pi / 2,
    "N_FEATURES": 28, "np": np, "math": math, "itertools": itertools,
    "ALLOWED_SINGLE_QUBIT_GATES": {"RX", "RY", "RZ"},
    "ALLOWED_TWO_QUBIT_GATES": {"CNOT", "CZ"},
    "ALLOWED_PARAM_TWO_QUBIT_GATES": {"CRX", "CRY", "CRZ"},
}


def spec_of(code: str, feature_pairs):
    lines = code.splitlines()
    try:
        a = next(i for i, l in enumerate(lines) if "EVOLVE-BLOCK-START" in l)
        b = next(i for i, l in enumerate(lines) if "EVOLVE-BLOCK-END" in l)
    except StopIteration:
        return None
    ns = dict(ENV, FEATURE_PAIRS=feature_pairs)
    try:
        exec(compile("\n".join(lines[a + 1:b]), "<blk>", "exec"), ns)
        return ns.get("ANSATZ_SPEC")
    except Exception:
        return None


def measure(spec):
    fams = {}
    for g in spec:
        p = g.get("param")
        if not p:
            continue
        gate = str(g.get("gate", "")).upper()
        n_wires = 2 if "wires" in g else 1
        fams.setdefault(p, []).append((gate, n_wires))
    if not fams:
        return None
    sizes = [len(v) for v in fams.values()]
    tied8 = any(len(v) == 8 and all(w == 1 for _, w in v) for v in fams.values())
    return {"angles": len(fams), "max_family": max(sizes), "tied8": tied8}


def run(path: str, feature_pairs):
    con = sqlite3.connect(path)
    out = []
    for gen, score, correct, code, meta in con.execute(
        "select generation, combined_score, correct, code, metadata from programs order by generation"
    ):
        m = json.loads(meta) if meta else {}
        model = (m.get("model_name") or "seed").replace("openrouter/", "").replace("azure-", "")
        if model == "seed":
            continue
        spec = spec_of(code, feature_pairs)
        meas = measure(spec) if spec else None
        if not meas:
            continue
        text = " ".join(str(m.get(k) or "") for k in ("patch_name", "patch_description"))
        out.append({**meas, "gen": gen, "score": score, "correct": correct,
                    "model": model, "says": bool(EXPLICIT.search(text))})
    return out


def report(path, label, feature_pairs):
    rs = run(path, feature_pairs)
    if not rs:
        print(f"\n{label}: no parseable specs")
        return
    print(f"\n{'=' * 74}\n{label}   ({len(rs)} parseable proposals)\n{'=' * 74}")

    def blk(sub, name):
        if not sub:
            print(f"  {name:<26} n=0")
            return
        ang = sum(r["angles"] for r in sub) / len(sub)
        mx = sum(r["max_family"] for r in sub) / len(sub)
        t8 = sum(r["tied8"] for r in sub)
        sc = [r["score"] for r in sub if r["correct"] and r["score"] is not None]
        ms = sum(sc) / len(sc) if sc else float("nan")
        print(f"  {name:<26} n={len(sub):<4} angles/blk={ang:5.1f}  "
              f"max_family={mx:4.1f}  has_8-tied={t8:>3}/{len(sub):<3} ({100*t8/len(sub):3.0f}%)  "
              f"mean_score={ms:6.3f}")

    blk([r for r in rs if r["says"]], "SAYS symmetry")
    blk([r for r in rs if not r["says"]], "does NOT say it")
    blk(rs, "all proposals")

    t8 = [r for r in rs if r["tied8"]]
    print(f"\n  proposals that actually BUILT an 8-wire tied family: "
          f"{len(t8)}/{len(rs)} ({100*len(t8)/len(rs):.0f}%)")
    if t8:
        print(f"    first at generation {min(r['gen'] for r in t8)}")
        says_and_builds = sum(1 for r in t8 if r["says"])
        print(f"    of those, {says_and_builds}/{len(t8)} also used symmetry language")
    says = [r for r in rs if r["says"]]
    if says:
        print(f"    of the {len(says)} that SAID it, {sum(1 for r in says if r['tied8'])} BUILT it "
              f"({100*sum(1 for r in says if r['tied8'])/len(says):.0f}%)")


def main() -> int:
    data = np.load("dataset.npz")
    fp = [tuple(int(w) for w in row) for row in data["feature_pairs"]]
    for path in sys.argv[1:]:
        report(path, path, fp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
