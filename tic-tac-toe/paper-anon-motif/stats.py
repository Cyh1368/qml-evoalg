"""Compute the paper's numbers from rundata.json."""
import json
import math
import sys
from itertools import combinations
from pathlib import Path

SP = Path(__file__).resolve().parent
data = json.loads((SP / "rundata.json").read_text())


def binom_sf(k, n, p):
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))


def analyse(run):
    win = {frozenset(t) for t in run["win"]}
    edges = {frozenset(e) for e in run["edges"]}

    def deg(t):
        return sum(1 for pr in combinations(sorted(t), 2) if frozenset(pr) in edges)

    all_t = [frozenset(t) for t in combinations(range(9), 3)]
    invisible = {t for t in win if deg(t) == 0}
    p_uni = len(win) / len(all_t)
    s2 = [t for t in all_t if deg(t) == 2]
    p_e2 = sum(1 for t in s2 if t in win) / len(s2) if s2 else None

    strata = {}
    for d in (0, 1, 2, 3):
        grp = [t for t in all_t if deg(t) == d]
        if grp:
            strata[d] = {"n": len(grp), "n_win": sum(1 for t in grp if t in win)}

    progs = []
    for p in run["programs"]:
        tr = [frozenset(int(w) for w in it["wires"])
              for it in (p["spec"] or [])
              if isinstance(it, dict)
              and str(it.get("gate", "")).upper() in ("ZZZ", "CCRZ")
              and isinstance(it.get("wires"), (list, tuple)) and len(it["wires"]) == 3]
        progs.append({**p, "tr": tr, "n_tr": len(tr),
                      "n_win": sum(1 for t in tr if t in win)})

    ok = [p for p in progs if p["correct"] and p["score"] is not None]
    best, traj = None, []
    for p in sorted(ok, key=lambda q: (q["gen"], q["score"])):
        if best is None or p["score"] > best["score"]:
            best = p
            traj.append({"gen": p["gen"], "score": p["score"], "val": p["val"],
                         "test": p["test"], "n_tr": p["n_tr"], "n_win": p["n_win"],
                         "covered": len({t for t in p["tr"]} & win),
                         "invisible": len({t for t in p["tr"]} & invisible)})

    pop = [t for p in progs if p["correct"] for t in p["tr"]]
    pop_w = sum(1 for t in pop if t in win)
    pop_deg = {d: sum(1 for t in pop if deg(t) == d) for d in (0, 1, 2)}
    pop2 = [t for t in pop if deg(t) == 2]

    # first generation at which the best-so-far lineage touches a winning line
    first_hit = next((t["gen"] for t in traj if t["n_win"] > 0), None)

    return {
        "model": run["model"], "p_uni": p_uni, "p_e2": p_e2,
        "strata": strata,
        "invisible": sorted(tuple(sorted(t)) for t in invisible),
        "n_programs": len(progs), "n_correct": sum(1 for p in progs if p["correct"]),
        "n_using": sum(1 for p in progs if p["correct"] and p["n_tr"] > 0),
        "max_gen": max(p["gen"] for p in progs) + 1,
        "trajectory": traj,
        "first_hit_gen": first_hit,
        "best": {
            "gen": best["gen"], "score": best["score"], "val": best["val"],
            "test": best["test"], "train": best["train"], "gap": best["gap"],
            "n_params": best["n_params"], "n_tr": best["n_tr"], "n_win": best["n_win"],
            "covered": len({t for t in best["tr"]} & win),
            "invisible_found": sorted(tuple(sorted(t))
                                      for t in ({t for t in best["tr"]} & invisible)),
            "p_uni": binom_sf(best["n_win"], best["n_tr"], p_uni) if best["n_tr"] else None,
            "p_e2": binom_sf(best["n_win"], best["n_tr"], p_e2) if best["n_tr"] else None,
            "triples": sorted(tuple(sorted(t)) for t in best["tr"]),
            "spec": best["spec"],
        },
        "population": {
            "n": len(pop), "n_win": pop_w,
            "frac": pop_w / len(pop) if pop else None,
            "by_deg": pop_deg,
            "n_2edge": len(pop2),
            "frac_2edge": len(pop2) / len(pop) if pop else None,
            "win_within_2edge": (sum(1 for t in pop2 if t in win) / len(pop2)) if pop2 else None,
            "p_uni": binom_sf(pop_w, len(pop), p_uni) if pop else None,
            "p_e2": binom_sf(pop_w, len(pop), p_e2) if pop else None,
        },
    }


res = {tag: analyse(run) for tag, run in data.items()}
(SP / "stats.json").write_text(json.dumps(res, indent=2, default=str))

for tag, r in res.items():
    b, pop = r["best"], r["population"]
    print(f"\n===== {tag}  ({r['model']})  gens={r['max_gen']}")
    print(f"  correct {r['n_correct']}/{r['n_programs']}, using triples {r['n_using']}")
    print(f"  nulls: uniform={r['p_uni']:.4f}  2-edge stratum={r['p_e2']:.4f}")
    print(f"  strata: {r['strata']}")
    print(f"  BEST gen{b['gen']}: score={b['score']:.4f} val={b['val']} test={b['test']} "
          f"params={b['n_params']}")
    print(f"    triples {b['n_win']}/{b['n_tr']} on lines, {b['covered']}/8 lines covered")
    print(f"    p_uniform={b['p_uni']}  p_edge2={b['p_e2']}")
    print(f"    invisible found: {b['invisible_found']}  (of {r['invisible']})")
    print(f"  POPULATION {pop['n_win']}/{pop['n']} = {pop['frac']:.3f} on lines")
    print(f"    by edge-degree {pop['by_deg']}; 2-edge share {pop['frac_2edge']:.3f}; "
          f"win-rate within 2-edge {pop['win_within_2edge']}")
    print(f"    p_uniform={pop['p_uni']:.3g}  p_edge2={pop['p_e2']:.3g}")
    print(f"  first winning-line hit in best lineage: gen {r['first_hit_gen']}")
