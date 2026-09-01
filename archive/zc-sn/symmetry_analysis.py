"""Post-hoc S_n-discovery analysis for transfer task A (LOCAL ONLY — uses the
answer key; never ship to the cluster or show to the evolution loop).

For each evolved program in a run database:
  1. Structural metric — parameter-sharing uniformity: fraction of the block's
     single-qubit rotations that share one parameter across ALL 8 wires
     (S_8-orbit tying; under S_8 all wires are one orbit, all pairs one orbit).
  2. Behavioral metric — empirical equivariance error: |f(x) - f(pi . x)|
     averaged over random vertex permutations pi and test records, where pi
     acts jointly on qubits and features via the answer key's pair table.
     An S_8-equivariant model has error exactly 0.

Usage: python symmetry_analysis.py --results-dir <run dir with programs.sqlite>
"""
from __future__ import annotations

import argparse
import ast
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
KEY = json.loads((HERE / "answer_key.json").read_text())


def extract_spec(code: str):
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "ANSATZ_SPEC":
                    return ast.literal_eval(node.value)
    return None


def structural_metrics(spec) -> dict:
    """Parameter-sharing uniformity of single- and two-qubit gates."""
    single = defaultdict(set)   # (gate type) -> set of param names used
    single_wires = defaultdict(lambda: defaultdict(set))  # gate -> param -> wires
    two_params = defaultdict(set)
    n_single = n_two_param = 0
    for item in spec:
        g = str(item.get("gate", "")).upper()
        if g in ("RX", "RY", "RZ"):
            n_single += 1
            single[g].add(item["param"])
            single_wires[g][item["param"]].add(item["wire"])
        elif g in ("CRX", "CRY", "CRZ"):
            n_two_param += 1
            two_params[g].add(item["param"])
    # A gate family is "fully tied" if one param covers all 8 wires.
    fully_tied_families = sum(
        1 for g, params in single.items()
        for p in params
        if len(single_wires[g][p]) == 8
    )
    n_unique_params = len({item["param"] for item in spec if "param" in item})
    return {
        "n_gates": len(spec),
        "n_unique_params": n_unique_params,
        "n_single_gates": n_single,
        "single_param_counts": {g: len(ps) for g, ps in single.items()},
        "fully_tied_single_families": fully_tied_families,
        "two_qubit_param_counts": {g: len(ps) for g, ps in two_params.items()},
    }


def permute_record(x: np.ndarray, perm: np.ndarray, pair_index: dict) -> np.ndarray:
    """Apply vertex permutation to a record via the answer key structure."""
    qubit_relabel = np.array(KEY["qubit_relabel"])
    inv_relabel = np.argsort(qubit_relabel)
    out = np.empty_like(x)
    # feature k couples qubit pair FEATURE_PAIRS[k]; the vertex permutation
    # maps that pair to another pair, i.e. another feature index.
    for k, (qa, qb) in enumerate(pair_index["pairs"]):
        va, vb = inv_relabel[qa], inv_relabel[qb]
        wa, wb = perm[va], perm[vb]
        k2 = pair_index["lookup"][frozenset((int(qubit_relabel[wa]), int(qubit_relabel[wb])))]
        out[..., k2] = x[..., k]
    return out


def equivariance_error(n_perms: int = 8, n_records: int = 40, seed: int = 0) -> float:
    """|f(x) - f(pi x)| for the CURRENT initial_program module's predict fn.

    Call after copying a candidate's code over initial_program.py, or import
    dynamically; here we import the module fresh for the evolved best program
    written to best_program.py by --write-best.
    """
    raise NotImplementedError("driven by analyze() below")


def analyze(results_dir: Path) -> None:
    db = results_dir / "programs.sqlite"
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, code, generation, combined_score, correct FROM programs"
        ).fetchall()

    print(f"run: {results_dir.name}  programs: {len(rows)}")
    best = None
    lineage = []
    for r in sorted(rows, key=lambda q: (q["generation"], q["combined_score"] or -1)):
        if not r["correct"] or r["combined_score"] is None:
            continue
        spec = None
        try:
            spec = extract_spec(r["code"])
        except (SyntaxError, ValueError):
            continue
        if spec is None:
            continue
        m = structural_metrics(spec)
        if best is None or r["combined_score"] > best[0]:
            best = (r["combined_score"], r["id"], r["generation"], m, r["code"])
            lineage.append((r["generation"], r["combined_score"], m))

    print("\nbest-so-far lineage (gen, score, unique params, fully-tied 1q families):")
    for gen, score, m in lineage:
        print(f"  gen {gen:>3}  score {score:.4f}  params {m['n_unique_params']:>3}  "
              f"tied-families {m['fully_tied_single_families']}  "
              f"1q-param-counts {m['single_param_counts']}")

    if best is not None:
        score, pid, gen, m, code = best
        print(f"\nfinal best: gen {gen}, score {score:.4f}")
        print(json.dumps(m, indent=2))
        out = results_dir / "best_program_local.py"
        out.write_text(code)
        print(f"wrote {out} — run the behavioral equivariance check against it "
              f"with check_equivariance.py")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-dir", required=True)
    a = ap.parse_args()
    analyze(Path(a.results_dir))


if __name__ == "__main__":
    main()
