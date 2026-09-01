#!/usr/bin/env python3
"""Phase 2/3 analysis for the symmetry-transfer ablations.

Phase 2 (replication): weak arm r1-r5, mid arm r1-r3, independent seeds. Asks
how much of a single run's outcome is seed noise.

Phase 3 (rewind ablations): a completed weak run is rewound to generation k,
then continued to generation 50 with either the full 3-model ensemble (ctl) or
the ensemble minus one model (abl), 4 seeds per arm.

  rw13: rewind at gen 13, ablate qwen3-coder
  rw20: rewind at gen 20, ablate gemini-3.1-flash-lite

Both arms of a rewind pair share an identical inherited prefix, so any
divergence after gen k is attributable to the ensemble composition plus seed.

Usage: ./viz/.venv_render/bin/python transfer-sn/analyze_phase23.py
"""
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent

# rewind experiment -> (rewind generation, ablated model)
REWINDS = {
    "rw13": (13, "qwen3-coder"),
    "rw20": (20, "gemini-3.1-flash-lite-preview"),
}
REPLICATES = ["r1", "r2", "r3", "r4"]


def load(run_dir):
    """Return generation-ordered program rows with model/cost pulled out."""
    path = ROOT / run_dir / "programs.sqlite"
    if not path.exists():
        return None
    # plain connect: these databases are in WAL mode, and mode=ro cannot open a
    # WAL database when the -shm sidecar is absent
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(
        "SELECT id, parent_id, generation, combined_score, correct, metadata "
        "FROM programs ORDER BY generation")]
    con.close()
    for r in rows:
        m = json.loads(r["metadata"] or "{}")
        r["model"] = (m.get("model_name") or "seed").split("/")[-1]
        r["cost"] = m.get("api_costs") or 0.0
    return rows


def best_upto(rows, gen):
    """Best correct score among programs at or before `gen` (-inf if none)."""
    scores = [r["combined_score"] for r in rows
              if r["correct"] and r["combined_score"] is not None
              and r["generation"] <= gen]
    return max(scores) if scores else float("-inf")


def summarize(run_dir, rewind_gen=None):
    rows = load(run_dir)
    if not rows:
        return None
    correct = [r for r in rows if r["correct"] and r["combined_score"] is not None]
    if not correct:
        return None
    final = max(correct, key=lambda r: r["combined_score"])
    out = {
        "run": run_dir,
        "programs": len(rows),
        "evaluated": len(correct),
        "fail_rate": 1 - len(correct) / len(rows),
        "last_gen": max(r["generation"] for r in rows),
        "best": final["combined_score"],
        "best_gen": final["generation"],
        "best_model": final["model"],
        "cost": sum(r["cost"] for r in rows),
    }
    if rewind_gen is not None:
        base = best_upto(rows, rewind_gen)
        out["base"] = base
        out["gain"] = out["best"] - base
        # generations after the rewind point before the prefix best was beaten
        beat = [r["generation"] for r in correct
                if r["generation"] > rewind_gen and r["combined_score"] > base]
        out["gens_to_beat"] = (min(beat) - rewind_gen) if beat else None
        # per-model authorship of post-rewind record setters
        recs, run_best = [], base
        for r in rows:
            if (r["correct"] and r["combined_score"] is not None
                    and r["generation"] > rewind_gen
                    and r["combined_score"] > run_best):
                recs.append((r["generation"], r["model"], r["combined_score"] - run_best))
                run_best = r["combined_score"]
        out["records"] = recs
    return out


def mean_sd(xs):
    a = np.array([x for x in xs if x is not None], dtype=float)
    if a.size == 0:
        return float("nan"), float("nan")
    return float(a.mean()), float(a.std(ddof=1)) if a.size > 1 else 0.0


def welch(a, b):
    """Welch t-test; returns (t, df, two-sided p) without scipy."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.size < 2 or b.size < 2:
        return float("nan"), float("nan"), float("nan")
    va, vb = a.var(ddof=1) / a.size, b.var(ddof=1) / b.size
    if va + vb == 0:
        return float("nan"), float("nan"), float("nan")
    t = (a.mean() - b.mean()) / np.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (a.size - 1) + vb ** 2 / (b.size - 1))
    # two-sided p from the t distribution via its incomplete-beta form
    x = df / (df + t * t)
    p = _betainc(df / 2, 0.5, x)
    return float(t), float(df), float(p)


def _betainc(a, b, x, terms=2000):
    """Regularized incomplete beta I_x(a,b) by series expansion."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    from math import lgamma, log, exp
    lbeta = lgamma(a) + lgamma(b) - lgamma(a + b)
    front = exp(a * log(x) + b * log(1 - x) - lbeta) / a
    # Lentz continued fraction
    f, c, d = 1.0, 1.0, 0.0
    for i in range(terms):
        m = i // 2
        if i == 0:
            num = 1.0
        elif i % 2 == 0:
            num = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m))
        else:
            num = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + num * d
        d = 1e-30 if abs(d) < 1e-30 else d
        d = 1.0 / d
        c = 1.0 + num / c
        c = 1e-30 if abs(c) < 1e-30 else c
        f *= c * d
        if abs(1 - c * d) < 1e-12:
            break
    return front * (f - 1)


def mannwhitney(a, b):
    """Exact-ish Mann-Whitney U with a normal approximation p-value."""
    a, b = list(a), list(b)
    combined = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    ranks, i = {}, 0
    vals = [c[0] for c in combined]
    rank_of = [0.0] * len(vals)
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[j + 1] == vals[i]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            rank_of[k] = avg
        i = j + 1
    ra = sum(r for r, c in zip(rank_of, combined) if c[1] == 0)
    na, nb = len(a), len(b)
    u = ra - na * (na + 1) / 2
    mu = na * nb / 2
    sd = np.sqrt(na * nb * (na + nb + 1) / 12)
    z = (u - mu) / sd if sd > 0 else float("nan")
    from math import erfc
    p = erfc(abs(z) / np.sqrt(2)) if sd > 0 else float("nan")
    return float(u), float(z), float(p)


def main():
    report = {}

    # ---------- Phase 2: seed replication ----------
    print("=" * 78)
    print("PHASE 2  seed replication (no rewind, independent seeds)")
    print("=" * 78)
    for arm, reps in (("weak", ["r1", "r2", "r3", "r4", "r5"]),
                      ("mid", ["r1", "r2", "r3"])):
        rs = [summarize(f"results_or_{arm}_{r}") for r in reps]
        rs = [r for r in rs if r]
        if not rs:
            continue
        print(f"\n-- {arm} arm, n={len(rs)}")
        print(f"{'run':28s} {'best':>8} {'gen':>4} {'author':>28} {'cost$':>7} {'fail':>6}")
        for s in rs:
            print(f"{s['run']:28s} {s['best']:8.4f} {s['best_gen']:4d} "
                  f"{s['best_model']:>28s} {s['cost']:7.2f} {s['fail_rate']:6.2f}")
        m, sd = mean_sd([s["best"] for s in rs])
        lo, hi = min(s["best"] for s in rs), max(s["best"] for s in rs)
        print(f"{'':28s} mean {m:.4f}  sd {sd:.4f}  range [{lo:.4f}, {hi:.4f}]  "
              f"spread {hi - lo:.4f}")
        report[f"phase2_{arm}"] = {"runs": rs, "mean": m, "sd": sd,
                                   "min": lo, "max": hi}

    # ---------- Phase 3: rewind ablations ----------
    print("\n" + "=" * 78)
    print("PHASE 3  rewind ablations (shared prefix, ensemble composition varied)")
    print("=" * 78)
    for tag, (gen, ablated) in REWINDS.items():
        ctl = [summarize(f"results_or_weak_{tag}_ctl_{r}", gen) for r in REPLICATES]
        abl = [summarize(f"results_or_weak_{tag}_abl_{r}", gen) for r in REPLICATES]
        ctl = [s for s in ctl if s]
        abl = [s for s in abl if s]
        if not ctl or not abl:
            continue
        print(f"\n-- {tag}: rewind at gen {gen}, ablation removes {ablated}")
        bases = {s["base"] for s in ctl + abl}
        print(f"   inherited prefix best @gen{gen}: "
              f"{'/'.join(f'{b:.4f}' for b in sorted(bases))}"
              f"{'  (SHARED)' if len(bases) == 1 else '  (WARNING: prefixes differ)'}")
        print(f"\n{'run':32s} {'base':>8} {'best':>8} {'gain':>8} {'t2beat':>7} "
              f"{'cost$':>7} {'author':>26}")
        for s in ctl + abl:
            t2b = s["gens_to_beat"]
            print(f"{s['run']:32s} {s['base']:8.4f} {s['best']:8.4f} {s['gain']:8.4f} "
                  f"{(str(t2b) if t2b is not None else 'never'):>7} {s['cost']:7.2f} "
                  f"{s['best_model']:>26s}")

        cg, ag = [s["gain"] for s in ctl], [s["gain"] for s in abl]
        cm, csd = mean_sd(cg)
        am, asd = mean_sd(ag)
        t, df, p = welch(cg, ag)
        u, z, pu = mannwhitney(cg, ag)
        print(f"\n   ctl gain  mean {cm:.4f} sd {csd:.4f}   n={len(cg)}")
        print(f"   abl gain  mean {am:.4f} sd {asd:.4f}   n={len(ag)}")
        print(f"   difference (ctl - abl) = {cm - am:+.4f}")
        print(f"   Welch t={t:.3f} df={df:.2f} p={p:.3f} | "
              f"Mann-Whitney U={u:.1f} z={z:.2f} p={pu:.3f}")

        # who actually set the post-rewind records in the control arm
        auth = {}
        for s in ctl:
            for _, model, d in s["records"]:
                a = auth.setdefault(model, {"n": 0, "delta": 0.0})
                a["n"] += 1
                a["delta"] += d
        if auth:
            print(f"\n   control-arm post-rewind record setters:")
            for model, a in sorted(auth.items(), key=lambda kv: -kv[1]["delta"]):
                print(f"     {model:34s} {a['n']:2d} records  "
                      f"total gain {a['delta']:.4f}")
            if ablated in auth:
                print(f"     -> ablated model {ablated} authored "
                      f"{auth[ablated]['n']} of "
                      f"{sum(a['n'] for a in auth.values())} records "
                      f"({auth[ablated]['delta']:.4f} of "
                      f"{sum(a['delta'] for a in auth.values()):.4f} total gain)")
            else:
                print(f"     -> ablated model {ablated} set NO records in control")

        report[f"phase3_{tag}"] = {
            "rewind_gen": gen, "ablated": ablated,
            "ctl": ctl, "abl": abl,
            "ctl_gain_mean": cm, "ctl_gain_sd": csd,
            "abl_gain_mean": am, "abl_gain_sd": asd,
            "diff": cm - am, "welch_t": t, "welch_df": df, "welch_p": p,
            "mw_u": u, "mw_z": z, "mw_p": pu,
            "ctl_record_authors": auth,
        }

    out = ROOT / "phase23_metrics.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=1, default=float)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    sys.exit(main())
