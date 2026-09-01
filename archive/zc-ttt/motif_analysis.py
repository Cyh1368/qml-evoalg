"""Post-hoc motif-discovery analysis for the ANONYMIZED EA run.

The evolving model saw no board semantics, no winning-line constants, no
"tic-tac-toe" naming, and a secret qubit-label permutation, so the true
structure-bearing triples (the permuted winning lines) are geometrically
meaningless in the coordinates the model works in. Any enrichment of
three-qubit gates on those triples therefore reflects the training signal, not
prior knowledge.

Ground-truth permuted winning lines are read from permutation_meta.json (the
secret build metadata), so this script tracks whatever permutation build_data.py
used. Two of the eight lines are "graph-invisible" (none of their qubit pairs
are hardware edges) — finding those is the strongest evidence of genuine,
score-driven discovery.

Usage:
  python motif_analysis.py [--results-dir results/<run>] [--meta permutation_meta.json]
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


def load_win_lines(meta_path: Path):
    meta = json.loads(Path(meta_path).read_text())
    win = {frozenset(t) for t in meta["permuted_win_lines"]}
    edges = {frozenset(e) for e in meta["permuted_hardware_edges"]}
    graph_invisible = {
        t for t in win
        if sum(1 for pair in combinations(sorted(t), 2) if frozenset(pair) in edges) == 0
    }
    return win, graph_invisible


def extract_spec(code: str):
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "ANSATZ_SPEC":
                    return ast.literal_eval(node.value)
    return None


def triple_stats(spec, win_lines) -> dict:
    triples = [
        frozenset(int(w) for w in item["wires"])
        for item in spec
        if isinstance(item, dict)
        and str(item.get("gate", "")).upper() in ("ZZZ", "CCRZ")
        and isinstance(item.get("wires"), (list, tuple))
        and len(item["wires"]) == 3
    ]
    n = len(triples)
    n_win = sum(1 for t in triples if t in win_lines)
    distinct = {t for t in triples}
    distinct_win = {t for t in distinct if t in win_lines}
    return {
        "n_triple_gates": n,
        "n_on_winning_lines": n_win,
        "winning_fraction": (n_win / n) if n else None,
        "n_distinct_triples": len(distinct),
        "n_distinct_winning": len(distinct_win),
        "winning_lines_covered": sorted(tuple(sorted(t)) for t in distinct_win),
    }


def binom_sf(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def newest_run(results_root: Path) -> Path:
    dbs = sorted(results_root.glob("*/programs.sqlite"), key=lambda p: p.stat().st_mtime)
    if not dbs:
        raise FileNotFoundError(f"no programs.sqlite under {results_root}")
    return dbs[-1].parent


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-dir", default=None)
    ap.add_argument("--meta", default=str(HERE / "permutation_meta.json"))
    ap.add_argument("--out", default=None, help="write JSON summary here")
    a = ap.parse_args()

    win_lines, graph_invisible = load_win_lines(Path(a.meta))
    all_triples = {frozenset(t) for t in combinations(range(9), 3)}
    p_null = len(win_lines) / len(all_triples)

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
        st = triple_stats(spec, win_lines)
        programs.append({
            "id": r["id"], "generation": r["generation"],
            "combined_score": r["combined_score"], "correct": bool(r["correct"]),
            **st,
        })

    print(f"run: {run_dir.name}  programs parsed: {len(programs)}  "
          f"null P(winning triple) = {p_null:.4f}  (target lines are geometrically hidden)")

    used = [p for p in programs if p["correct"] and p["n_triple_gates"] > 0]
    print(f"programs using any triple gate: {len(used)} / "
          f"{sum(1 for p in programs if p['correct'])} correct")

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
        pv = binom_sf(k, n, p_null)
        covered = {frozenset(t) for t in best["winning_lines_covered"]}
        hidden_found = sorted(tuple(sorted(t)) for t in (covered & graph_invisible))
        print(f"\nfinal best program: {k}/{n} triple gates on winning lines "
              f"(chance {p_null:.3f}); exact binomial P(X>={k}) = {pv:.2e}")
        print(f"graph-invisible lines found (only discoverable via the score): "
              f"{hidden_found} of {sorted(tuple(sorted(t)) for t in graph_invisible)}")
    elif best is not None:
        print("\nfinal best program uses no triple gates — "
              "vocabulary was available but not selected.")

    if a.out:
        Path(a.out).write_text(json.dumps(
            {"run": run_dir.name, "p_null": p_null, "programs": programs}, indent=2))
        print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
