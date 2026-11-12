#!/usr/bin/env python3
"""Who actually moves the frontier? Credit-assignment over a ShinkaEvolve run.

Answers three separate questions that are easy to conflate:

  1. Which generations advanced the best-so-far, and which model authored each?
     (record-setters -- the only proposals that changed the outcome)
  2. How much did each model contribute PER PROPOSAL, not in absolute count?
     UCB1 hands more turns to models that are doing well, so raw counts
     conflate "this model is good" with "the bandit picked it often".
  3. What does each model's whole score distribution look like? A model can
     never set a record and still be doing useful exploration -- or be pure
     noise, which the mean and the valid-rate separate.

Usage:  python3 analyze_frontier_credit.py <run.sqlite> [<compare.sqlite>]
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import defaultdict


def load(path: str) -> list[dict]:
    con = sqlite3.connect(path)
    rows = []
    q = ("select generation, combined_score, correct, metadata "
         "from programs order by generation asc")
    for gen, score, correct, meta in con.execute(q):
        m = json.loads(meta) if meta else {}
        rows.append({
            "gen": gen,
            "score": score,
            "correct": correct,
            "model": (m.get("model_name") or "seed").replace("openrouter/", "").replace("azure-", ""),
            "patch": m.get("patch_name"),
        })
    return rows


def report(path: str, label: str) -> None:
    rows = load(path)
    scored = [r for r in rows if r["correct"] and r["score"] is not None]
    print(f"\n{'=' * 78}\n{label}   ({len(rows)} programs, {len(scored)} valid-and-scored)\n{'=' * 78}")

    # ---- 1. record setters -------------------------------------------------
    best = float("-inf")
    records = []
    for r in scored:
        if r["score"] > best:
            records.append({**r, "delta": (r["score"] - best) if best > float("-inf") else 0.0})
            best = r["score"]

    print("\n1. GENERATIONS THAT ADVANCED THE BEST-SO-FAR")
    print(f"   {'gen':>5}  {'score':>9}  {'delta':>9}  {'model':<32} patch")
    for r in records:
        print(f"   {r['gen']:>5}  {r['score']:>9.4f}  {r['delta']:>+9.4f}  {r['model']:<32} {r['patch']}")

    by_model_rec = defaultdict(lambda: {"n": 0, "gain": 0.0})
    for r in records:
        if r["model"] == "seed":
            continue
        by_model_rec[r["model"]]["n"] += 1
        by_model_rec[r["model"]]["gain"] += r["delta"]
    total_gain = sum(v["gain"] for v in by_model_rec.values()) or 1.0

    # ---- 2 & 3. per-model rates -------------------------------------------
    stats = defaultdict(lambda: {"prop": 0, "valid": 0, "pos": 0, "scores": []})
    for r in rows:
        if r["model"] == "seed":
            continue
        s = stats[r["model"]]
        s["prop"] += 1
        if r["correct"] and r["score"] is not None:
            s["valid"] += 1
            s["scores"].append(r["score"])
            if r["score"] > 0:
                s["pos"] += 1

    print("\n2. CREDIT PER MODEL  (records = best-so-far advances)")
    print(f"   {'model':<32} {'props':>6} {'valid':>6} {'>0':>4} {'recs':>5} "
          f"{'rec/prop':>9} {'gain':>8} {'gain%':>7} {'mean':>8} {'best':>8}")
    for model in sorted(stats, key=lambda m: -by_model_rec[m]["gain"]):
        s = stats[model]
        rec = by_model_rec[model]
        mean = sum(s["scores"]) / len(s["scores"]) if s["scores"] else float("nan")
        bst = max(s["scores"]) if s["scores"] else float("nan")
        print(f"   {model:<32} {s['prop']:>6} {s['valid']:>6} {s['pos']:>4} {rec['n']:>5} "
              f"{rec['n'] / s['prop']:>9.2f} {rec['gain']:>8.4f} "
              f"{100 * rec['gain'] / total_gain:>6.1f}% {mean:>8.3f} {bst:>8.4f}")

    # ---- concentration -----------------------------------------------------
    if by_model_rec:
        shares = sorted((v["gain"] / total_gain for v in by_model_rec.values()), reverse=True)
        hhi = sum(x * x for x in shares)
        n_eff = 1 / hhi if hhi else 0
        print(f"\n   top model's share of total gain : {shares[0] * 100:.1f}%")
        print(f"   effective number of contributors: {n_eff:.2f}  "
              f"(1.0 = one model does everything, {len(stats):.1f} = perfectly equal)")


def main() -> int:
    for i, path in enumerate(sys.argv[1:]):
        report(path, path)
    print("\nNote: record-setting is a small-sample statistic. Early in a run a "
          "handful of\nproposals decide everything, so read these as provisional "
          "until the run ends.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
