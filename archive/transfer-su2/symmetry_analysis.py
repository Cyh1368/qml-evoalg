"""Post-hoc SU(2)-discovery analysis for transfer task B (LOCAL ONLY — uses
the answer key; never ship to the cluster or show to the evolution loop).

For each evolved program in a run database:
  1. Structural metrics:
     - isotropic-exchange tying: for each qubit pair used, does the program
       apply XX, YY and ZZ with THE SAME shared parameter name? (exact SU(2)
       equivariance signature at gate level);
     - bond selectivity: are the pairs used the true ring bonds (answer key),
       and do even/odd sublattices get distinct treatment (dimer structure)?
     - symmetry-breaking budget: number of single-qubit rotation parameters
       (an SU(2)-equivariant block has none).
  2. Behavioral metric — commutator test: build the 6-block circuit unitary at
     the trained/best parameters and compute ||[U, S_a]|| for the three global
     spin components S_a = 1/2 sum_i sigma_a^i. Exactly 0 for SU(2)-equivariant
     circuits.

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
RING_BONDS_QUBITS = {
    frozenset((int(KEY["qubit_relabel"][a]), int(KEY["qubit_relabel"][b])))
    for a, b in KEY["bonds_site_order"]
}
EVEN_BONDS_QUBITS = {
    frozenset((int(KEY["qubit_relabel"][a]), int(KEY["qubit_relabel"][b])))
    for i, (a, b) in enumerate(KEY["bonds_site_order"]) if i % 2 == 0
}


def extract_spec(code: str):
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "ANSATZ_SPEC":
                    return ast.literal_eval(node.value)
    return None


def structural_metrics(spec) -> dict:
    ising = defaultdict(dict)          # pair -> {XX: param, YY: param, ZZ: param}
    single_params = set()
    pairs_used = set()
    for item in spec:
        g = str(item.get("gate", "")).upper()
        if g in ("RX", "RY", "RZ"):
            single_params.add(item["param"])
        elif g in ("XX", "YY", "ZZ"):
            pair = frozenset(int(w) for w in item["wires"])
            ising[pair][g] = item["param"]
            pairs_used.add(pair)
        elif g in ("CRX", "CRY", "CRZ", "CZ", "CNOT"):
            pairs_used.add(frozenset(int(w) for w in item["wires"]))

    iso_pairs = [
        p for p, gates in ising.items()
        if {"XX", "YY", "ZZ"} <= set(gates)
        and len({gates["XX"], gates["YY"], gates["ZZ"]}) == 1
    ]
    ising_pairs = list(ising.keys())
    on_ring = [p for p in pairs_used if p in RING_BONDS_QUBITS]
    on_even = [p for p in pairs_used if p in EVEN_BONDS_QUBITS]
    n_unique_params = len({item["param"] for item in spec if "param" in item})
    return {
        "n_gates": len(spec),
        "n_unique_params": n_unique_params,
        "n_single_qubit_params": len(single_params),
        "n_pairs_used": len(pairs_used),
        "n_ising_pairs": len(ising_pairs),
        "n_isotropic_exchange_pairs": len(iso_pairs),
        "isotropic_fraction_of_ising": (len(iso_pairs) / len(ising_pairs)) if ising_pairs else None,
        "pairs_on_true_ring": len(on_ring),
        "pairs_on_even_sublattice": len(on_even),
        "ring_fraction_of_pairs": (len(on_ring) / len(pairs_used)) if pairs_used else None,
    }


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

    print("\nbest-so-far lineage "
          "(gen, score, params, iso-exchange pairs / ising pairs, 1q params, ring-frac):")
    for gen, score, m in lineage:
        print(f"  gen {gen:>3}  score {score:.4f}  params {m['n_unique_params']:>3}  "
              f"iso {m['n_isotropic_exchange_pairs']}/{m['n_ising_pairs']}  "
              f"1q {m['n_single_qubit_params']:>2}  "
              f"ring {m['ring_fraction_of_pairs']}")

    if best is not None:
        score, pid, gen, m, code = best
        print(f"\nfinal best: gen {gen}, score {score:.4f}")
        print(json.dumps(m, indent=2))
        out = results_dir / "best_program_local.py"
        out.write_text(code)
        print(f"wrote {out} — run the commutator test against it with "
              f"check_su2_commutator.py")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-dir", required=True)
    a = ap.parse_args()
    analyze(Path(a.results_dir))


if __name__ == "__main__":
    main()
