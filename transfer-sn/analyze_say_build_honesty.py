#!/usr/bin/env python3
"""Test the hypothesis: weaker ensembles' patch notes are less honest, either by
naming a symmetry they don't build, or by building one they don't name.

Two directions, tested separately because they are different claims:

  OVER-CLAIM   said a symmetry word -> did the patch actually add symmetric
               structure?   1 - P(introduced | said)
  SILENT BUILD introduced symmetric structure -> did the patch notes say so?
               1 - P(said | introduced)

Both are computed on the INTRODUCTION set: proposals whose parent lacked the
structure, so the proposal had to author it. Without that restriction both
directions are dominated by inheritance -- a child that keeps a motif its parent
already had counts as "built" while doing nothing, which manufactures fake
silent-building, and a child that says "preserving the symmetry" while changing
nothing else counts as an over-claim when it is simply accurate.

Three build tests, from strictest to loosest, because "some symmetry" is a
wider claim than the perm-motif alone:

  perm-motif   one parameter on single-qubit gates across all 8 wires (S_8)
  mirror-motif one parameter on single-qubit gates on exactly {i, 7-i}
  any-tying    one parameter on single-qubit gates on 2 or more wires --
               the loosest reading of "satisfies some symmetry"

Usage:  python3 analyze_say_build_honesty.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

import verify_run_metrics as V

HERE = Path(__file__).resolve().parent


def tying_level(spec):
    """Loosest structural test: does any parameter drive single-qubit gates on
    2+ distinct wires? Returns None if the spec is unparseable."""
    if spec is None:
        return None
    families = defaultdict(set)
    for g in spec:
        if not isinstance(g, dict) or not g.get("param"):
            continue
        if "wires" in g:
            continue                      # two-qubit gate; not a wire tying
        families[g["param"]].add(g.get("wire"))
    return any(len(ws) >= 2 for ws in families.values())


def collect(feature_pairs):
    """Per-proposal records with parent structure attached."""
    recs = []
    for rec in V.run_inventory():
        rows = V.read_proposals(rec["dir"] / "programs.sqlite", feature_pairs)
        # re-derive the loose tying flag, which read_proposals doesn't carry
        con_rows = {}
        import sqlite3
        con = sqlite3.connect(f"file://{(rec['dir'] / 'programs.sqlite').resolve()}?mode=ro",
                              uri=True)
        try:
            for pid, code in con.execute("select id, code from programs"):
                con_rows[pid] = tying_level(V.extract_ansatz_spec(code, feature_pairs))
        finally:
            con.close()

        by_id = {r["id"]: r for r in rows}
        for r in rows:
            r["any_tying"] = con_rows.get(r["id"])
        for r in rows:
            if r["is_seed"] or not r["struct"]:
                continue
            p = by_id.get(r["parent"])
            if not p or not p["struct"]:
                continue
            recs.append({
                "group": rec["group"], "condition": rec["condition"],
                "arm": rec["arm"], "run": rec["run"],
                "says_any": r["says_any"], "says_perm": r["says_perm"],
                "says_mirror": r["says_mirror"],
                "built_perm": r["struct"]["perm_motif"],
                "built_mirror": r["struct"]["mirror_motif"],
                "built_tying": bool(r["any_tying"]),
                "parent_perm": p["struct"]["perm_motif"],
                "parent_mirror": p["struct"]["mirror_motif"],
                "parent_tying": bool(p["any_tying"]),
            })
    return recs


def pct(n, d):
    return f"{100.0 * n / d:5.1f}%" if d else "   -- "


ARMS = [("real", "real", "weak"), ("real", "real", "mid"), ("real", "real", "frontier"),
        ("null", "null", "weak"), ("null", "null", "mid"), ("null", "null", "frontier"),
        ("rewind", "real", "weak"), ("roster", "real", "mixed")]

TESTS = [
    ("perm-motif  (S_8, the correct one)", "built_perm", "parent_perm"),
    ("mirror-motif", "built_mirror", "parent_mirror"),
    ("any-tying (>=2 wires on one param)", "built_tying", "parent_tying"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    args = ap.parse_args()

    fp = [tuple(int(w) for w in r) for r in np.load(HERE / "dataset.npz")["feature_pairs"]]
    recs = collect(fp)
    print(f"[honesty] {len(recs)} proposals with a measurable parent\n")

    out = {}
    for label, build_key, parent_key in TESTS:
        print("=" * 100)
        print(f"BUILD TEST: {label}")
        print("  restricted to proposals whose parent LACKED it, so the proposal had to introduce it")
        print("=" * 100)
        print(f"  {'group/arm':22} {'opps':>5} {'said':>5} {'built':>6} "
              f"{'said&built':>11} {'OVER-CLAIM':>11} {'SILENT BUILD':>13} {'lift':>7}")
        for grp, cond, arm in ARMS:
            g = [r for r in recs if r["group"] == grp and r["condition"] == cond
                 and r["arm"] == arm and not r[parent_key]]
            if not g:
                continue
            said = [r for r in g if r["says_any"]]
            built = [r for r in g if r[build_key]]
            both = [r for r in g if r["says_any"] and r[build_key]]
            # over-claim: said it, didn't introduce it
            over = len(said) - len(both)
            # silent build: introduced it, never said it
            silent = len(built) - len(both)
            base = (len(built) - len(both)) / (len(g) - len(said)) if len(g) - len(said) else None
            hit = len(both) / len(said) if said else None
            lift = (100 * (hit - base)) if (hit is not None and base is not None) else None
            key = f"{grp}/{arm}"
            print(f"  {key:22} {len(g):5} {len(said):5} {len(built):6} {len(both):11} "
                  f"{pct(over, len(said)):>11} {pct(silent, len(built)):>13} "
                  f"{(f'{lift:+.1f}' if lift is not None else '--'):>7}")
            out.setdefault(label, {})[key] = {
                "opportunities": len(g), "said": len(said), "built": len(built),
                "said_and_built": len(both), "over_claim_n": over, "silent_n": silent,
                "over_claim_pct": (100.0 * over / len(said)) if said else None,
                "silent_pct": (100.0 * silent / len(built)) if built else None,
            }
        print()

    print("OVER-CLAIM   = of proposals that named a symmetry, the share that introduced no such structure")
    print("SILENT BUILD = of proposals that introduced the structure, the share whose notes never named a symmetry")
    print("lift         = P(built | said) - P(built | didn't say), in points; ~0 means the notes carry no signal\n")

    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=2))
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
