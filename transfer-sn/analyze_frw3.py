#!/usr/bin/env python3
"""What do the frw3 continuations build after generation 3?

The frw3 runs rewind results_or_frontier_r1 to gen 3 (gpt-5.6-sol's
`shared_cube_mixer`, combined_score 0.44771504) and continue under a different
ensemble: weak x10, mid x10, frontier x5, frontier-minus-gpt-5.6-sol x5.

Structural readout is s8_parts() from build_run_metrics.py, i.e. the layer-aware
test of BOTH halves of S_8 invariance (every single-qubit block on all 8 wires,
every two-qubit block covering all 28 K8 edges). The legacy tied-8 motif tests
only the first half and overstates the cheap arms; see RUN_METRICS.md section 1C.

Usage:  python3 analyze_frw3.py [--results-root results/2026-08-22]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_run_metrics as B  # noqa: E402

# combined_score of the gen-3 parent every run starts from.
START = 0.44771504252627536
ARMS = (("weak", 10), ("mid", 10), ("frontier", 5), ("frontabl", 5))


def new_programs(db: Path, feature_pairs):
    """Every program proposed after the rewind point, with structure measured."""
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        con.execute("select 1 from programs limit 1")
    except sqlite3.Error:
        # a run copied while its orchestrator still held the WAL open can leave a
        # sidecar the reader cannot replay; immutable reads the main file alone.
        con = sqlite3.connect(f"file:{db}?immutable=1", uri=True)
    try:
        rows = con.execute(
            "select generation, code, combined_score, correct, metadata "
            "from programs where generation > 3 order by generation").fetchall()
    finally:
        con.close()
    out = []
    for gen, code, score, correct, meta in rows:
        m = json.loads(meta) if meta else {}
        spec = B.spec_of(code, feature_pairs)
        meas = B.measure(spec) if spec else None
        pairs = {frozenset(int(w) for w in it["wires"]) for it in (spec or [])
                 if isinstance(it.get("wires"), (list, tuple)) and len(it["wires"]) == 2}
        parts = (meas or {}).get("s8_parts") or {}
        out.append(dict(
            gen=gen, score=score, correct=bool(correct),
            model=(m.get("model_name") or "?").replace("openrouter/", ""),
            patch_name=m.get("patch_name") or "",
            angles=(meas or {}).get("angles"), tied8=(meas or {}).get("tied8"),
            sq_ok=parts.get("sq_ok"), tq_ok=parts.get("tq_ok"),
            s8=(meas or {}).get("s8"), n_pairs=len(pairs),
            spec_key=json.dumps(spec, sort_keys=True, default=str) if spec else None,
        ))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-root", default="results/2026-08-22")
    args = ap.parse_args()
    root = (HERE / args.results_root).resolve()

    fp = [tuple(int(w) for w in row)
          for row in np.load(HERE / "dataset.npz")["feature_pairs"]]

    runs, by_model, s8_model, k8_model, specs, pair_hist = [], Counter(), Counter(), Counter(), {}, Counter()
    for arm, n in ARMS:
        for i in range(1, n + 1):
            db = root / f"results_frw3_{arm}_r{i}" / "programs.sqlite"
            if not db.exists():
                print(f"[frw3] MISSING {db}", file=sys.stderr)
                continue
            try:
                progs = new_programs(db, fp)
            except sqlite3.Error as exc:
                print(f"[frw3] UNREADABLE {db.parent.name}: {exc}", file=sys.stderr)
                continue
            for p in progs:
                by_model[(arm, p["model"])] += 1
                s8_model[(arm, p["model"])] += bool(p["s8"])
                k8_model[(arm, p["model"])] += p["n_pairs"] == 28
                pair_hist[p["n_pairs"]] += 1
                if p["spec_key"]:
                    specs.setdefault(p["spec_key"], []).append((f"{arm}_r{i}", p["gen"]))
            scored = [p for p in progs if p["correct"] and p["score"] is not None]
            runs.append(dict(
                arm=arm, run=f"{arm}_r{i}", n=len(progs),
                best=max((p["score"] for p in scored), default=None),
                sq=sum(bool(p["sq_ok"]) for p in progs),
                tq=sum(bool(p["tq_ok"]) for p in progs),
                s8=sum(bool(p["s8"]) for p in progs),
                k8=sum(p["n_pairs"] == 28 for p in progs),
                progs=progs))

    print("%-13s %4s %9s %9s %5s %5s %5s %5s" %
          ("run", "new", "best", "delta", "sq", "tq", "S8", "K8"))
    for r in runs:
        b = r["best"]
        print("%-13s %4d %9s %9s %5d %5d %5d %5d" % (
            r["run"], r["n"], "-" if b is None else "%.4f" % b,
            "-" if b is None else "%+.4f" % (b - START),
            r["sq"], r["tq"], r["s8"], r["k8"]))

    for arm, _ in ARMS:
        sel = [r for r in runs if r["arm"] == arm]
        if not sel:
            continue
        tot = sum(r["n"] for r in sel)
        bests = sorted(r["best"] for r in sel if r["best"] is not None)
        print(f"\n{arm}: {len(sel)} runs, {tot} new programs")
        if bests:
            print("  improved on start  : %d/%d" % (sum(b > START for b in bests), len(bests)))
            print("  best / median best : %.4f / %.4f" % (max(bests), bests[len(bests) // 2]))
        print("  ties all 8 wires   : %d/%d programs, %d/%d runs"
              % (sum(r["sq"] for r in sel), tot, sum(r["sq"] > 0 for r in sel), len(sel)))
        print("  K8 entangler       : %d/%d programs, %d/%d runs"
              % (sum(r["tq"] for r in sel), tot, sum(r["tq"] > 0 for r in sel), len(sel)))
        print("  S_8-invariant      : %d/%d programs, %d/%d runs"
              % (sum(r["s8"] for r in sel), tot, sum(r["s8"] > 0 for r in sel), len(sel)))

    print("\nproposals by model (arm, model, proposals, S_8-invariant, 28-pair entangler):")
    for k in sorted(by_model):
        print("  %-9s %-34s %4d %4d %4d" % (k[0], k[1], by_model[k], s8_model[k], k8_model[k]))

    print("\ndistinct qubit pairs touched by two-qubit gates (parent has 12, K8 needs 28):")
    for k in sorted(pair_hist):
        print("  %2d pairs : %3d programs%s" % (k, pair_hist[k], "   <- K8" if k == 28 else ""))

    dupes = {k: v for k, v in specs.items() if len(v) > 1}
    print(f"\ndistinct ansatz specs: {len(specs)} over {sum(len(v) for v in specs.values())} programs")
    for v in sorted(dupes.values(), key=len, reverse=True):
        print("  repeated %dx: %s" % (len(v), ", ".join(f"{r}@g{g}" for r, g in v)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
