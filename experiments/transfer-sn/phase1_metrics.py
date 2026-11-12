#!/usr/bin/env python3
"""Phase 1: per-model contribution metrics from ShinkaEvolve run databases.

For each run computes, per model:
  1. Best-so-far chain credit: authorship of record-setting generations and of
     the ancestry chain of the final best program, with improvement magnitude.
  2. Cost-weighted credit: improvement contributed per dollar spent, counting
     every proposal (including failures) against the model.
  3. Chunk analysis: maximal same-model segments of the record-setter sequence.
  4. Novelty: mean embedding distance of each model's proposals to the nearest
     earlier program (structural newness proxy).

Usage: python3 phase1_metrics.py results_or_weak_r1 [more result dirs ...]
"""
import json, sqlite3, sys
import numpy as np


def load(run_dir):
    con = sqlite3.connect(f"{run_dir}/programs.sqlite")
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(
        "SELECT id, parent_id, generation, combined_score, correct, "
        "embedding, metadata FROM programs ORDER BY generation")]
    for r in rows:
        m = json.loads(r["metadata"] or "{}")
        r["model"] = (m.get("model_name") or m.get("model") or "seed")
        r["cost"] = m.get("api_costs") or 0.0
        r["novelty"] = m.get("max_similarity")  # lower = more novel
        emb = r.pop("embedding", None)
        r["emb"] = np.array(json.loads(emb), dtype=float) if emb else None
    con.close()
    return rows


def short(model):
    return model.split("/")[-1] if model else "seed"


def analyze(run_dir):
    rows = load(run_dir)
    by_id = {r["id"]: r for r in rows}
    models = sorted({short(r["model"]) for r in rows if r["generation"] > 0})

    # 1. record-setters and improvement magnitude
    best, records = -np.inf, []
    for r in rows:
        if r["correct"] and r["combined_score"] is not None and r["combined_score"] > best:
            if r["generation"] > 0:
                records.append({"gen": r["generation"], "model": short(r["model"]),
                                "score": r["combined_score"],
                                "delta": r["combined_score"] - (best if np.isfinite(best) else 0.0)})
            best = r["combined_score"]

    # ancestry chain of the final best program
    final_best = max((r for r in rows if r["correct"] and r["combined_score"] is not None),
                     key=lambda r: r["combined_score"])
    chain, cur = [], final_best
    while cur is not None:
        chain.append(cur)
        cur = by_id.get(cur["parent_id"])
    chain.reverse()

    # 3. chunks over the record-setter sequence
    chunks, prev = [], None
    for rec in records:
        if prev and rec["model"] == prev["model"]:
            chunks[-1]["len"] += 1
        else:
            chunks.append({"model": rec["model"], "len": 1, "from_gen": rec["gen"]})
        prev = rec

    # per-model aggregates
    stats = {m: {"proposals": 0, "fails": 0, "cost": 0.0, "delta": 0.0,
                 "records": 0, "chain": 0, "novelty": [], "embdist": []}
             for m in models}
    seen_embs = []
    for r in rows:
        if r["generation"] == 0:
            if r["emb"] is not None:
                seen_embs.append(r["emb"])
            continue
        s = stats[short(r["model"])]
        s["proposals"] += 1
        s["cost"] += r["cost"]
        if not r["correct"]:
            s["fails"] += 1
        if r["novelty"] is not None:
            s["novelty"].append(r["novelty"])
        if r["emb"] is not None:
            if seen_embs:
                d = min(np.linalg.norm(r["emb"] - e) for e in seen_embs)
                s["embdist"].append(d)
            seen_embs.append(r["emb"])
    for rec in records:
        stats[rec["model"]]["records"] += 1
        stats[rec["model"]]["delta"] += rec["delta"]
    for r in chain:
        if r["generation"] > 0:
            stats[short(r["model"])]["chain"] += 1

    print(f"\n{'='*72}\n{run_dir}: {len(rows)} programs, best {final_best['combined_score']:.4f} "
          f"@gen{final_best['generation']} ({short(final_best['model'])}), "
          f"chain length {len(chain)-1}")
    print(f"record-setters: " + " ".join(
        f"g{r['gen']}:{r['model'][:12]}(+{r['delta']:.3f})" for r in records))
    print(f"chunks: " + " ".join(f"{c['model'][:12]}x{c['len']}" for c in chunks))
    hdr = f"{'model':28s} {'prop':>4} {'fail':>4} {'cost$':>7} {'recs':>4} " \
          f"{'chain':>5} {'delta':>6} {'d/$':>7} {'maxsim':>7} {'embdist':>7}"
    print(hdr); print("-" * len(hdr))
    for m in models:
        s = stats[m]
        dpc = s["delta"] / s["cost"] if s["cost"] > 0 else float("nan")
        nov = np.mean(s["novelty"]) if s["novelty"] else float("nan")
        emb = np.mean(s["embdist"]) if s["embdist"] else float("nan")
        print(f"{m:28s} {s['proposals']:4d} {s['fails']:4d} {s['cost']:7.2f} "
              f"{s['records']:4d} {s['chain']:5d} {s['delta']:6.3f} {dpc:7.3f} "
              f"{nov:7.3f} {emb:7.3f}")
    return {"run": run_dir, "records": records, "chunks": chunks,
            "chain": [(r["generation"], short(r["model"])) for r in chain],
            "stats": {m: {k: v for k, v in s.items() if k not in ("novelty", "embdist")}
                      for m, s in stats.items()}}


if __name__ == "__main__":
    dirs = sys.argv[1:] or ["results_or_weak_r1", "results_or_mid_r1",
                            "results_or_frontier_r1"]
    out = [analyze(d) for d in dirs]
    with open("phase1_metrics.json", "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("\nwrote phase1_metrics.json")
