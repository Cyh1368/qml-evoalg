#!/usr/bin/env python3
"""Extract the ANSATZ_SPEC of a hand-picked set of transfer-sn circuits into
circuits_data.js for the static circuit-gallery page (index.html).

Covered:
  * the ShinkaEvolve seed ansatz (initial_program.py)
  * the hand-designed S_8-equivariant baseline (baseline_program.py)
  * the best program of each of the three current model-ensemble runs
    (or_weak_r1, or_mid_r1, or_frontier_r1)
  * every node on the frontier run's winning lineage, so the significant
    score jumps that produced it can be read off gate by gate

Usage: python3 build_circuits.py [--repo-root ../..] [--out circuits_data.js]
"""

from __future__ import annotations

import argparse
import ast
import json
import sqlite3
from pathlib import Path

TASK_DIR = "experiments/transfer-sn"

# The current ensemble arms: OpenRouter rosters with disjoint, three-vendor
# pools at xhigh reasoning. The earlier Azure-routed arms (az_*) are gone --
# Azure lacked several models we wanted and their mid/frontier pools shared 2 of
# 3 members, so those runs are outdated and excluded from the analysis. Any run
# directory that is missing (or has no database yet) is skipped.
RUNS = {
    "weak": "results_or_weak_r1",
    "mid": "results_or_mid_r1",
    "frontier": "results_or_frontier_r1",
}

# Arms whose full winning lineage is expanded, not just the best program.
LINEAGE_TIERS = {"frontier"}


def extract_spec(code: str, env: dict) -> list[dict]:
    """Evaluate the EVOLVE-BLOCK to get ANSATZ_SPEC.

    Evolved programs don't always assign a literal — several build the spec
    with comprehensions or list concatenation — so the block is executed in a
    sandbox namespace holding only the problem constants it may legitimately
    reference (N_QUBITS, FEATURE_PAIRS, ...), never the rest of the module.
    """
    lines = code.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if "EVOLVE-BLOCK-START" in l)
        end = next(i for i, l in enumerate(lines) if "EVOLVE-BLOCK-END" in l)
    except StopIteration:
        raise ValueError("no EVOLVE-BLOCK markers found")

    ns = dict(env)
    exec(compile("\n".join(lines[start + 1 : end]), "<evolve-block>", "exec"), ns)
    if "ANSATZ_SPEC" not in ns:
        raise ValueError("EVOLVE-BLOCK defines no ANSATZ_SPEC")
    return ns["ANSATZ_SPEC"]


def normalize(spec: list[dict]) -> list[dict]:
    """One uniform gate record: gate, wires (list), param (or None)."""
    out = []
    for item in spec:
        gate = str(item["gate"]).upper()
        if "wires" in item:
            wires = [int(w) for w in item["wires"]]
        else:
            wires = [int(item["wire"])]
        out.append({"gate": gate, "wires": wires, "param": item.get("param")})
    return out


def spec_stats(gates: list[dict], n_uploads=3, n_repeats=2) -> dict:
    params = [g["param"] for g in gates if g["param"]]
    unique = list(dict.fromkeys(params))
    families: dict[str, dict] = {}
    for g in gates:
        if not g["param"]:
            continue
        fam = families.setdefault(g["param"], {"param": g["param"], "gates": [], "count": 0})
        fam["count"] += 1
        if g["gate"] not in fam["gates"]:
            fam["gates"].append(g["gate"])
    return {
        "n_gates": len(gates),
        "n_params_per_block": len(unique),
        "n_params": len(unique) * n_uploads * n_repeats + 2,  # +2 readout gain/bias
        "families": sorted(families.values(), key=lambda f: -f["count"]),
    }


def load_program_row(db: Path, program_id: str) -> dict:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    cur = con.execute(
        "select id, generation, combined_score, parent_id, code, public_metrics, metadata "
        "from programs where id = ?",
        (program_id,),
    )
    row = cur.fetchone()
    con.close()
    if row is None:
        raise KeyError(program_id)
    meta = json.loads(row[6]) if row[6] else {}
    return {
        "id": row[0],
        "generation": row[1],
        "score": row[2],
        "parent_id": row[3],
        "code": row[4],
        "metrics": json.loads(row[5]) if row[5] else {},
        "patch_name": meta.get("patch_name"),
        "patch_description": meta.get("patch_description"),
        "model_name": meta.get("model_name"),
        "patch_type": meta.get("patch_type"),
    }


def best_program_id(db: Path) -> str:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    row = con.execute(
        "select id from programs where correct = 1 and combined_score is not null "
        "order by combined_score desc, generation asc limit 1"
    ).fetchone()
    con.close()
    return row[0]


def lineage(db: Path, program_id: str) -> list[str]:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    parents = dict(con.execute("select id, parent_id from programs"))
    con.close()
    chain, cur, seen = [], program_id, set()
    while cur in parents and cur not in seen:
        seen.add(cur)
        chain.append(cur)
        cur = parents[cur]
    chain.reverse()
    return chain


def metric_block(m: dict) -> dict:
    keys = [
        "test_accuracy_mean",
        "validation_accuracy_mean",
        "generalization_gap_mean",
        "validation_loss_mean",
        "n_params",
        "depth_mean",
        "gate_count_mean",
        "convergence_step_mean",
    ]
    return {k: m.get(k) for k in keys if m.get(k) is not None}


def main() -> None:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=str(here.parent.parent))
    ap.add_argument("--out", default=str(here / "circuits_data.js"))
    args = ap.parse_args()

    task = Path(args.repo_root).resolve() / TASK_DIR

    # Constants an EVOLVE-BLOCK is allowed to reference, mirroring the values
    # initial_program.py defines above the block.
    import itertools
    import math

    import numpy as np

    data = np.load(task / "dataset.npz")
    env = {
        "N_QUBITS": 8,
        "N_UPLOADS": 3,
        "N_REPEATS": 2,
        "FEATURE_SCALE": math.pi / 2,
        "FEATURE_PAIRS": [tuple(int(w) for w in row) for row in data["feature_pairs"]],
        "N_FEATURES": len(data["feature_pairs"]),
        "ALLOWED_SINGLE_QUBIT_GATES": {"RX", "RY", "RZ"},
        "ALLOWED_TWO_QUBIT_GATES": {"CNOT", "CZ"},
        "ALLOWED_PARAM_TWO_QUBIT_GATES": {"CRX", "CRY", "CRZ"},
        "np": np,
        "math": math,
        "itertools": itertools,
    }

    entries = []

    # --- 1. the two reference circuits, straight from source ---
    for key, fname, title, kind in [
        ("seed", "initial_program.py", "Seed ansatz", "reference"),
        ("baseline", "baseline_program.py", "Hand-designed S_8-equivariant baseline", "reference"),
    ]:
        gates = normalize(extract_spec((task / fname).read_text(), env))
        entries.append(
            {
                "key": key,
                "kind": kind,
                "title": title,
                "source": f"experiments/transfer-sn/{fname}",
                "gates": gates,
                "stats": spec_stats(gates),
            }
        )

    # --- 2. best of each ensemble run + the frontier lineage ---
    for tier, run_dir in RUNS.items():
        db = task / run_dir / "programs.sqlite"
        if not db.exists():
            print(f"  skip {tier}: no database at {run_dir}")
            continue
        try:
            best = best_program_id(db)
        except (TypeError, sqlite3.Error):
            print(f"  skip {tier}: no scored programs yet in {run_dir}")
            continue
        chain = lineage(db, best)
        wanted = (
            [(pid, "lineage") for pid in chain]
            if tier in LINEAGE_TIERS
            else [(best, "best")]
        )
        for pid, kind in wanted:
            row = load_program_row(db, pid)
            gates = normalize(extract_spec(row["code"], env))
            entries.append(
                {
                    "key": f"{tier}-gen{row['generation']}",
                    "kind": kind if pid != best else ("best" if kind == "best" else "lineage-best"),
                    "tier": tier,
                    "run": run_dir,
                    "title": f"{tier} ensemble — generation {row['generation']}",
                    "source": f"experiments/transfer-sn/{run_dir}/programs.sqlite",
                    "program_id": row["id"],
                    "parent_id": row["parent_id"],
                    "generation": row["generation"],
                    "score": row["score"],
                    "model_name": row["model_name"],
                    "patch_type": row["patch_type"],
                    "patch_name": row["patch_name"],
                    "patch_description": row["patch_description"],
                    "metrics": metric_block(row["metrics"]),
                    "gates": gates,
                    "stats": spec_stats(gates),
                }
            )

    out = Path(args.out)
    out.write_text("window.CIRCUITS = " + json.dumps(entries, indent=1) + ";\n")
    print(f"wrote {out} ({len(entries)} circuits, {out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
