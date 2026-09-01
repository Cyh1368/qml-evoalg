#!/usr/bin/env python3
"""Experiment 1: how much does the score move when nothing changes?

Ten runs of the cheap ensemble, byte-identical configs, 20 generations, bandit
seed fixed at 1. The only thing free to vary is what the language models happen
to emit. The spread across these ten runs is the noise floor of the benchmark:
any effect smaller than it cannot be measured by this instrument.

Decision thresholds were fixed in BENCHMARK_PLAN.md before the runs finished.

Usage: ./viz/.venv_render/bin/python transfer-sn/analyze_exp1.py
"""
import json
import sqlite3
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
RUNS = [f"results_or_weak_e1_r{i}" for i in range(1, 11)]
# older weak runs, same ensemble but 50 generations and a varying bandit seed
OLD = [f"results_or_weak_r{i}" for i in range(1, 6)]


def traj(run_dir, maxg=20):
    """Best-so-far score and cumulative cost after each generation."""
    p = ROOT / run_dir / "programs.sqlite"
    if not p.exists():
        return None
    con = sqlite3.connect(str(p))
    rs = [dict(zip(("g", "c", "s", "m"), r)) for r in con.execute(
        "SELECT generation,correct,combined_score,metadata FROM programs")]
    con.close()
    best = np.full(maxg, np.nan)
    cost = np.zeros(maxg)
    b, cum = -np.inf, 0.0
    for g in range(maxg):
        for r in rs:
            if r["g"] == g:
                if r["c"] and r["s"] is not None and r["s"] > b:
                    b = r["s"]
                m = json.loads(r["m"] or "{}")
                cum += sum(m.get(k) or 0.0 for k in
                           ("api_costs", "embed_cost", "meta_cost", "novelty_cost"))
        best[g] = b if np.isfinite(b) else np.nan
        cost[g] = cum
    models = {}
    for r in rs:
        m = json.loads(r["m"] or "{}")
        mn = (m.get("model_name") or "seed").split("/")[-1]
        models[mn] = models.get(mn, 0) + 1
    return {"best": best, "cost": cost, "n": len(rs), "models": models,
            "final": best[maxg - 1]}


def levene(groups):
    """Brown-Forsythe test for equal spread (median-centered Levene)."""
    zs = [np.abs(np.asarray(g, float) - np.median(g)) for g in groups]
    k = len(zs)
    N = sum(len(z) for z in zs)
    zbar = np.concatenate(zs).mean()
    num = sum(len(z) * (z.mean() - zbar) ** 2 for z in zs) / (k - 1)
    den = sum(((z - z.mean()) ** 2).sum() for z in zs) / (N - k)
    W = num / den if den > 0 else float("nan")
    return W, k - 1, N - k


def main():
    T = {r: traj(r) for r in RUNS}
    T = {k: v for k, v in T.items() if v}
    finals = np.array([v["final"] for v in T.values()])

    print("=" * 76)
    print("EXPERIMENT 1: 10 identical runs, cheap ensemble, 20 generations")
    print("=" * 76)
    print(f"\n{'run':10s} {'progs':>5} {'best@20':>9} {'cost$':>7}   model proposal counts")
    for name, v in T.items():
        mods = ", ".join(f"{k.split('-')[0]}:{n}" for k, n in
                         sorted(v["models"].items(), key=lambda kv: -kv[1]) if k != "seed")
        print(f"{name.replace('results_or_weak_',''):10s} {v['n']:5d} "
              f"{v['final']:9.4f} {v['cost'][-1]:7.3f}   {mods}")

    lo, hi = finals.min(), finals.max()
    print(f"\n{'':10s} n={len(finals)}  mean {finals.mean():.4f}  sd {finals.std(ddof=1):.4f}")
    print(f"{'':10s} min {lo:.4f}  max {hi:.4f}  BEST-WORST GAP {hi-lo:.4f}")
    print(f"{'':10s} median {np.median(finals):.4f}  "
          f"IQR {np.percentile(finals,75)-np.percentile(finals,25):.4f}")
    print(f"{'':10s} total spend ${sum(v['cost'][-1] for v in T.values()):.2f}")
    print(f"{'':10s} distinct final scores: {len(set(np.round(finals,4)))} of {len(finals)}")

    # spread at earlier generations, free from stored trajectories
    print(f"\nspread vs generation budget (same runs, truncated):")
    print(f"{'gen':>4} {'mean':>8} {'sd':>8} {'min':>8} {'max':>8} {'gap':>8} {'mean$':>7}")
    for g in (4, 9, 14, 19):
        v = np.array([t["best"][g] for t in T.values()], float)
        v = v[np.isfinite(v)]
        c = np.mean([t["cost"][g] for t in T.values()])
        print(f"{g+1:4d} {v.mean():8.4f} {v.std(ddof=1):8.4f} {v.min():8.4f} "
              f"{v.max():8.4f} {v.max()-v.min():8.4f} {c:7.3f}")

    # comparison against the older varying-seed runs
    O = {r: traj(r, maxg=50) for r in OLD}
    O = {k: v for k, v in O.items() if v}
    old50 = np.array([v["best"][49] for v in O.values()])
    old20 = np.array([v["best"][19] for v in O.values()])
    print(f"\n--- fixed seed (new, n={len(finals)}) vs varying seed (old, n={len(old20)}) ---")
    print(f"at generation 20:  new sd {finals.std(ddof=1):.4f}   old sd {old20.std(ddof=1):.4f}")
    print(f"                   new range [{lo:.4f}, {hi:.4f}]   "
          f"old range [{old20.min():.4f}, {old20.max():.4f}]")
    W, df1, df2 = levene([finals, old20])
    print(f"Brown-Forsythe equal-spread test: W={W:.3f} (df {df1},{df2}); "
          f"W below ~4.5 means no detectable difference in spread")
    print(f"\nold runs at generation 50 for reference: sd {old50.std(ddof=1):.4f} "
          f"range [{old50.min():.4f}, {old50.max():.4f}]")

    # verdict against pre-registered thresholds
    sd = finals.std(ddof=1)
    print("\n" + "=" * 76)
    print("VERDICT against thresholds fixed in BENCHMARK_PLAN.md")
    print("=" * 76)
    print(f"  noise floor (within-arm sd, identical configs) = {sd:.4f}")
    print(f"  pre-registered FAIL line for this arm          = 0.25")
    print(f"  -> {'FAIL: a single score cannot characterise an ensemble' if sd > 0.25 else 'below the fail line'}")
    print(f"\n  smallest gap another arm must clear to be detectable at n=10/arm:")
    print(f"     ~{2.8*sd*np.sqrt(2/10):.4f} (80% power)")
    for label, val in (("mid arm mean (existing, n=3)", 0.3836),
                       ("frontier single run (existing)", 1.1002)):
        print(f"     {label:34s} {val:.4f}")

    out = ROOT / "exp1_metrics.json"
    json.dump({"finals": finals.tolist(), "mean": float(finals.mean()),
               "sd": float(sd), "min": float(lo), "max": float(hi),
               "gap": float(hi - lo),
               "cost_total": float(sum(v["cost"][-1] for v in T.values())),
               "old_seed_varied_at20": old20.tolist(),
               "old_seed_varied_at50": old50.tolist()},
              open(out, "w"), indent=1)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
