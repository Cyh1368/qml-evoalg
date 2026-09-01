"""Analysis of the zc-su2 v2 runs (jobs 20032629-31, 80 generations, 3 arms).

LOCAL ONLY: uses answer_key.json. Emits v2_results/v2_analysis.json.

Reports, per arm:
  - run bookkeeping (programs, valid, generations reached, score trajectory)
  - the score frame from the pre-launch probe ladder
    (seed 0.5949 / trivial basin 0.6619 / tied-exchange 0.7604)
  - SU(2) structural signature of every valid program: isotropic tying
    (XX=YY=ZZ under one shared name), symmetry-breaking budget (single-qubit
    rotation params), and post-hoc bond placement vs the answer key
  - best-so-far lineage with the same metrics
"""
from __future__ import annotations

import ast
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "v2_results"
KEY = json.loads((HERE / "answer_key.json").read_text())

RING_BONDS = {
    frozenset((int(KEY["qubit_relabel"][a]), int(KEY["qubit_relabel"][b])))
    for a, b in KEY["bonds_site_order"]
}
EVEN_BONDS = {
    frozenset((int(KEY["qubit_relabel"][a]), int(KEY["qubit_relabel"][b])))
    for i, (a, b) in enumerate(KEY["bonds_site_order"]) if i % 2 == 0
}
ODD_BONDS = {
    frozenset((int(KEY["qubit_relabel"][a]), int(KEY["qubit_relabel"][b])))
    for i, (a, b) in enumerate(KEY["bonds_site_order"]) if i % 2 == 1
}

PROBE = {  # v2.1 pre-launch ladder, section 7 of the redesign report
    "exchange_true": 0.7604,
    "exchange_wrong": 0.7560,
    "exchange_untied": 0.7104,
    "trivial_1p": 0.6619,
    "seed": 0.5949,
    "fixed_0p": 0.4498,
}

ARMS = ["haiku", "sonnet", "gpt56sol"]


def extract_spec(code: str):
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "ANSATZ_SPEC":
                    return ast.literal_eval(node.value)
    return None


def structural_metrics(spec) -> dict:
    ising = defaultdict(dict)
    single_params = set()
    pairs_used = set()
    gate_hist = Counter()
    for item in spec:
        g = str(item.get("gate", "")).upper()
        gate_hist[g] += 1
        if g in ("RX", "RY", "RZ"):
            single_params.add(item["param"])
        elif g in ("XX", "YY", "ZZ"):
            pair = frozenset(int(w) for w in item["wires"])
            ising[pair][g] = item["param"]
            pairs_used.add(pair)
        elif g in ("CRX", "CRY", "CRZ", "CZ", "CNOT", "SWAP", "ISWAP"):
            pairs_used.add(frozenset(int(w) for w in item["wires"]))

    iso_pairs = [
        p for p, gates in ising.items()
        if {"XX", "YY", "ZZ"} <= set(gates)
        and len({gates["XX"], gates["YY"], gates["ZZ"]}) == 1
    ]
    # partially tied: all three present but >1 distinct name
    untied_triples = [
        p for p, gates in ising.items()
        if {"XX", "YY", "ZZ"} <= set(gates)
        and len({gates["XX"], gates["YY"], gates["ZZ"]}) > 1
    ]
    ising_pairs = list(ising.keys())
    on_ring = [p for p in pairs_used if p in RING_BONDS]
    iso_on_even = [p for p in iso_pairs if p in EVEN_BONDS]
    iso_on_odd = [p for p in iso_pairs if p in ODD_BONDS]
    iso_disjoint = _is_disjoint(iso_pairs)
    return {
        "n_gates": len(spec),
        "gate_hist": dict(gate_hist),
        "n_unique_params": len({i["param"] for i in spec if "param" in i}),
        "n_single_qubit_params": len(single_params),
        "n_pairs_used": len(pairs_used),
        "n_ising_pairs": len(ising_pairs),
        "n_isotropic_exchange_pairs": len(iso_pairs),
        "n_untied_xyz_triples": len(untied_triples),
        "isotropic_fraction_of_ising": (len(iso_pairs) / len(ising_pairs)) if ising_pairs else None,
        "pairs_on_true_ring": len(on_ring),
        "ring_fraction_of_pairs": (len(on_ring) / len(pairs_used)) if pairs_used else None,
        "iso_pairs_on_even_sublattice": len(iso_on_even),
        "iso_pairs_on_odd_sublattice": len(iso_on_odd),
        "iso_pairs_disjoint": iso_disjoint,
        # exact SU(2)-equivariance signature: every entangler tied, no 1q rotations
        "su2_equivariant_signature": (
            len(iso_pairs) > 0
            and len(iso_pairs) == len(ising_pairs)
            and len(single_params) == 0
            and not any(g in gate_hist for g in ("CZ", "CNOT", "CRX", "CRY", "CRZ"))
        ),
    }


def _is_disjoint(pairs) -> bool:
    seen = set()
    for p in pairs:
        if seen & set(p):
            return False
        seen |= set(p)
    return bool(pairs)


def load_rows(db: Path):
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(
            "SELECT id, code, parent_id, generation, combined_score, correct, "
            "public_metrics, private_metrics, timestamp FROM programs"
        )]


def analyze_arm(arm: str) -> dict:
    rows = load_rows(OUT / f"results_{arm}" / "programs.sqlite")
    recs = []
    for r in rows:
        pub = json.loads(r["public_metrics"] or "{}")
        rec = {
            "id": r["id"],
            "parent_id": r["parent_id"],
            "generation": r["generation"],
            "score": r["combined_score"],
            "correct": bool(r["correct"]),
            "public": pub,
        }
        try:
            spec = extract_spec(r["code"] or "")
        except (SyntaxError, ValueError):
            spec = None
        rec["struct"] = structural_metrics(spec) if spec else None
        rec["code"] = r["code"]
        recs.append(rec)

    valid = [r for r in recs if r["correct"] and r["score"] is not None]
    valid.sort(key=lambda r: (r["generation"], r["id"]))

    # best-so-far lineage
    lineage, best = [], None
    for r in valid:
        if best is None or r["score"] > best["score"]:
            best = r
            lineage.append({
                "generation": r["generation"], "id": r["id"], "score": r["score"],
                "n_distinct_params": r["public"].get("n_distinct_params"),
                "worst_group_margin": r["public"].get("worst_group_margin_mean"),
                "test_accuracy": r["public"].get("test_accuracy_mean"),
                "validation_accuracy": r["public"].get("validation_accuracy_mean"),
                "struct": r["struct"],
            })

    iso_any = [r for r in valid if r["struct"] and r["struct"]["n_isotropic_exchange_pairs"] > 0]
    equivariant = [r for r in valid if r["struct"] and r["struct"]["su2_equivariant_signature"]]
    ising_any = [r for r in valid if r["struct"] and r["struct"]["n_ising_pairs"] > 0]

    return {
        "arm": arm,
        "n_programs": len(recs),
        "n_valid": len(valid),
        "n_invalid": len(recs) - len(valid),
        "generations_reached": max((r["generation"] for r in recs), default=None),
        "best": {
            "generation": best["generation"], "id": best["id"], "score": best["score"],
            "public": best["public"], "struct": best["struct"], "code": best["code"],
        } if best else None,
        "lineage": lineage,
        "score_min": min(r["score"] for r in valid) if valid else None,
        "score_median": sorted(r["score"] for r in valid)[len(valid) // 2] if valid else None,
        "score_max": max(r["score"] for r in valid) if valid else None,
        "n_with_ising": len(ising_any),
        "n_with_isotropic_tie": len(iso_any),
        "n_su2_equivariant_signature": len(equivariant),
        "isotropic_examples": [
            {"gen": r["generation"], "id": r["id"], "score": r["score"],
             "iso_pairs": r["struct"]["n_isotropic_exchange_pairs"],
             "ising_pairs": r["struct"]["n_ising_pairs"],
             "1q_params": r["struct"]["n_single_qubit_params"],
             "ring_frac": r["struct"]["ring_fraction_of_pairs"],
             "disjoint": r["struct"]["iso_pairs_disjoint"],
             "equivariant": r["struct"]["su2_equivariant_signature"]}
            for r in sorted(iso_any, key=lambda x: -x["score"])
        ],
        "param_count_hist": dict(Counter(
            r["public"].get("n_distinct_params") for r in valid)),
        "all_scores": [{"gen": r["generation"], "score": r["score"],
                        "names": r["public"].get("n_distinct_params"),
                        "wgm": r["public"].get("worst_group_margin_mean"),
                        "vacc": r["public"].get("validation_accuracy_mean"),
                        "tacc": r["public"].get("test_accuracy_mean"),
                        "iso": (r["struct"] or {}).get("n_isotropic_exchange_pairs"),
                        "ising": (r["struct"] or {}).get("n_ising_pairs"),
                        "p1q": (r["struct"] or {}).get("n_single_qubit_params")}
                       for r in valid],
    }


def main():
    result = {"probe_frame": PROBE, "arms": {a: analyze_arm(a) for a in ARMS}}
    (OUT / "v2_analysis.json").write_text(json.dumps(result, indent=2))

    for a in ARMS:
        d = result["arms"][a]
        b = d["best"]
        print(f"\n=== {a}: {d['n_valid']}/{d['n_programs']} valid, "
              f"gens 0..{d['generations_reached']}")
        print(f"  best gen {b['generation']} score {b['score']:.4f} "
              f"names={b['public'].get('n_distinct_params')} "
              f"wgm={b['public'].get('worst_group_margin_mean')} "
              f"test={b['public'].get('test_accuracy_mean')}")
        print(f"  struct: iso {b['struct']['n_isotropic_exchange_pairs']}"
              f"/{b['struct']['n_ising_pairs']} ising pairs, "
              f"1q params {b['struct']['n_single_qubit_params']}, "
              f"equivariant={b['struct']['su2_equivariant_signature']}")
        print(f"  programs with any XX=YY=ZZ tie: {d['n_with_isotropic_tie']}, "
              f"with any Ising gate: {d['n_with_ising']}, "
              f"full SU(2) signature: {d['n_su2_equivariant_signature']}")
        print(f"  scores min/med/max: {d['score_min']:.4f}/"
              f"{d['score_median']:.4f}/{d['score_max']:.4f}")
    print(f"\nwrote {OUT / 'v2_analysis.json'}")


if __name__ == "__main__":
    main()
