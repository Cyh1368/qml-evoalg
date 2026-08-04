"""Post-hoc motif-discovery analysis for the extended-vocabulary EA run.

The motif variant lets evolution place ZZZ / CCRZ gates on ANY of the
C(9,3) = 84 qubit triples. Exactly 8 of those triples are tic-tac-toe winning
lines (3 rows, 3 columns, 2 diagonals). The task prompt never mentions them.

This script answers: did evolution allocate three-qubit interactions to the
winning lines more often than chance?

  * null model: triples chosen uniformly at random -> P(winning) = 8/84 = 0.0952
  * per program: n_triples, n_winning, plus fitness metadata
  * per generation: allocation trajectory of the best-so-far lineage
  * exact binomial test on the final best program's triple allocation

The analysis is deliberately POST-HOC: nothing in the evaluator or LLM
feedback references winning lines, so any enrichment is discovered, not
prompted.

Usage:
  python motif_analysis.py [--results-dir results/<run>]   # newest run if omitted
"""
from __future__ import annotations

import argparse
import ast
import json
import math
import sqlite3
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent

WIN_LINES = {
    frozenset(t) for t in (
        (0, 1, 2), (7, 8, 3), (6, 5, 4),
        (0, 7, 6), (1, 8, 5), (2, 3, 4),
        (0, 8, 4), (2, 8, 6),
    )
}
ALL_TRIPLES = {frozenset(t) for t in combinations(range(9), 3)}
P_NULL = len(WIN_LINES) / len(ALL_TRIPLES)  # 8/84


def extract_spec(code: str):
    """Pull the ANSATZ_SPEC literal out of a program's source."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "ANSATZ_SPEC":
                    return ast.literal_eval(node.value)
    return None


def triple_stats(spec) -> dict:
    triples = [
        frozenset(int(w) for w in item["wires"])
        for item in spec
        if isinstance(item, dict)
        and str(item.get("gate", "")).upper() in ("ZZZ", "CCRZ")
        and isinstance(item.get("wires"), (list, tuple))
        and len(item["wires"]) == 3
    ]
    n = len(triples)
    n_win = sum(1 for t in triples if t in WIN_LINES)
    distinct = {t for t in triples}
    distinct_win = {t for t in distinct if t in WIN_LINES}
    return {
        "n_triple_gates": n,
        "n_on_winning_lines": n_win,
        "winning_fraction": (n_win / n) if n else None,
        "n_distinct_triples": len(distinct),
        "n_distinct_winning": len(distinct_win),
        "winning_lines_covered": sorted(tuple(sorted(t)) for t in distinct_win),
    }


def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p), exact."""
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def newest_run(results_root: Path) -> Path:
    dbs = sorted(results_root.glob("*/programs.sqlite"), key=lambda p: p.stat().st_mtime)
    if not dbs:
        raise FileNotFoundError(f"no programs.sqlite under {results_root}")
    return dbs[-1].parent


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-dir", default=None)
    ap.add_argument("--out", default=None, help="write JSON summary here")
    a = ap.parse_args()
    run_dir = Path(a.results_dir) if a.results_dir else newest_run(HERE / "results")
    db = run_dir / "programs.sqlite"

    with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, code, generation, combined_score, correct FROM programs"
        ).fetchall()

    programs = []
    for r in rows:
        spec = None
        try:
            spec = extract_spec(r["code"])
        except (SyntaxError, ValueError):
            pass
        if spec is None:
            continue
        st = triple_stats(spec)
        programs.append({
            "id": r["id"], "generation": r["generation"],
            "combined_score": r["combined_score"], "correct": bool(r["correct"]),
            **st,
        })

    print(f"run: {run_dir.name}  programs parsed: {len(programs)}  "
          f"null P(winning triple) = {P_NULL:.4f}")

    used = [p for p in programs if p["correct"] and p["n_triple_gates"] > 0]
    print(f"programs using any triple gate: {len(used)} / "
          f"{sum(1 for p in programs if p['correct'])} correct")

    # best-so-far trajectory
    best = None
    trajectory = []
    for p in sorted((q for q in programs if q["correct"] and q["combined_score"] is not None),
                    key=lambda q: (q["generation"], q["combined_score"])):
        if best is None or p["combined_score"] > best["combined_score"]:
            best = p
            trajectory.append(p)
    print("\nbest-so-far lineage (gen, score, triples, on-lines, coverage):")
    for p in trajectory:
        print(f"  gen {p['generation']:>3}  score {p['combined_score']:.4f}  "
              f"triples {p['n_triple_gates']:>2}  winning {p['n_on_winning_lines']:>2}  "
              f"lines covered {p['n_distinct_winning']}/8")

    if best is not None and best["n_triple_gates"] > 0:
        k, n = best["n_on_winning_lines"], best["n_triple_gates"]
        pv = binom_sf(k, n, P_NULL)
        print(f"\nfinal best program: {k}/{n} triple gates on winning lines "
              f"(chance {P_NULL:.3f}); exact binomial P(X>={k}) = {pv:.2e}")
    elif best is not None:
        print("\nfinal best program uses no triple gates — "
              "vocabulary was available but not selected.")

    if a.out:
        Path(a.out).write_text(json.dumps(
            {"run": run_dir.name, "p_null": P_NULL, "programs": programs},
            indent=2))
        print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
