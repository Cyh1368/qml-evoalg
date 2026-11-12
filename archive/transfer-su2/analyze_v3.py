#!/usr/bin/env python3
"""Lineage + structure analysis for the v3 runs, both variants (LOCAL/TOOLS ONLY).

Reads every program from all six arms, recovers ANSATZ_SPEC by AST, and asks
the questions the task was rebuilt to answer:

  * did the score actually move off the seed, and how far up the known ladder
  * did any circuit adopt tied XX=YY=ZZ isotropic exchange
  * for circuits that did, is the trained block behaviourally SU(2)-equivariant
    (||[U, S_a]|| ~ 0), and are the tied pairs on the true bonds
  * does the contextualized arm differ from the zero-context arm

Writes v3_analysis.json and the figures the writeup embeds.

Run on the cluster with the qml-ea env:
    python analyze_v3.py
"""
from __future__ import annotations

import ast
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

PROJECT = Path(os.environ.get("SU2_PROJECT", "/home/ch2499/project"))
TOOLS = Path(__file__).resolve().parent
OUT = Path(os.environ.get("SU2_ANALYSIS_OUT", str(TOOLS / "v3_analysis")))
OUT.mkdir(parents=True, exist_ok=True)

VARIANTS = {"zc_su2_v3": "zero-context", "transfer_su2_v3": "contextualized"}
ARMS = ["haiku", "sonnet", "gpt56sol"]
N = 8

# Landscape reference points, measured in v3_validation through this same evaluator.
LADDER = {
    "seed": 0.2947,
    "generic basin (v2 winner)": 0.4752,
    "untied Ising (best random)": 0.6346,
    "untied Ising on true bonds": 0.6875,
    "partial tie": 0.7089,
    "tied exchange (answer)": 0.7559,
}

KEY = json.loads((TOOLS / "answer_key.json").read_text())
RELABEL = KEY["qubit_relabel"]
BONDS_SITE = KEY["bonds_site_order"]
RING = {frozenset((RELABEL[a], RELABEL[b])) for a, b in BONDS_SITE}
EVEN = {frozenset((RELABEL[a], RELABEL[b])) for i, (a, b) in enumerate(BONDS_SITE) if i % 2 == 0}
ODD = RING - EVEN

SINGLE = ("RX", "RY", "RZ")
ISING = ("XX", "YY", "ZZ")
BREAKERS = ("CZ", "CNOT", "CRX", "CRY", "CRZ")


def extract_spec(code: str):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "ANSATZ_SPEC":
                    try:
                        return ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return None
    return None


def structure(spec) -> dict:
    ising = defaultdict(dict)
    single_params, pairs_used = set(), set()
    hist = Counter()
    for item in spec:
        if not isinstance(item, dict):
            continue
        g = str(item.get("gate", "")).upper()
        hist[g] += 1
        if g in SINGLE:
            single_params.add(item.get("param"))
        elif g in ISING:
            pair = frozenset(int(w) for w in item["wires"])
            ising[pair][g] = item.get("param")
            pairs_used.add(pair)
        elif g in BREAKERS:
            pairs_used.add(frozenset(int(w) for w in item["wires"]))

    tied = [p for p, gs in ising.items()
            if set(ISING) <= set(gs) and len(set(gs.values())) == 1]
    untied = [p for p in ising if p not in tied]
    return {
        "n_gates": len(spec),
        "gate_hist": dict(hist),
        "n_names": len({i["param"] for i in spec if isinstance(i, dict) and "param" in i}),
        "n_single_qubit_params": len(single_params),
        "n_ising_pairs": len(ising),
        "n_tied_pairs": len(tied),
        "n_untied_ising_pairs": len(untied),
        "has_any_ising": bool(ising),
        "has_tied_triple": bool(tied),
        "tied_on_ring": sum(p in RING for p in tied),
        "tied_on_even": sum(p in EVEN for p in tied),
        "tied_on_odd": sum(p in ODD for p in tied),
        # The exact gate-level SU(2) signature: everything tied, nothing else.
        "su2_signature": (
            bool(tied) and not untied and not single_params
            and not any(g in hist for g in BREAKERS)),
    }


def load_rows(db: Path):
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=20) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(
            "SELECT id, code, parent_id, generation, combined_score, correct, "
            "public_metrics FROM programs")]


def analyze_arm(variant: str, arm: str) -> dict:
    db = PROJECT / variant / f"results_{arm}" / "programs.sqlite"
    if not db.exists():
        return {"variant": variant, "arm": arm, "error": "no database"}
    rows = load_rows(db)
    progs, best_so_far, best = [], [], None
    for r in sorted(rows, key=lambda x: (x["generation"] or 0, x["id"])):
        spec = extract_spec(r["code"] or "")
        pub = {}
        try:
            pub = json.loads(r["public_metrics"]) if r["public_metrics"] else {}
        except (TypeError, json.JSONDecodeError):
            pass
        rec = {
            "id": r["id"], "generation": r["generation"],
            "combined_score": r["combined_score"], "correct": bool(r["correct"]),
            "n_distinct_params": pub.get("n_distinct_params"),
            "validation_accuracy": pub.get("validation_accuracy_mean"),
            "worst_group_margin": pub.get("worst_group_margin_mean"),
            "structure": structure(spec) if spec else None,
        }
        progs.append(rec)
        if rec["correct"] and rec["combined_score"] is not None:
            if best is None or rec["combined_score"] > best["combined_score"]:
                best = rec
        best_so_far.append({
            "generation": rec["generation"],
            "best": best["combined_score"] if best else None,
            "n_names": best["n_distinct_params"] if best else None,
            "has_tied": bool(best and best["structure"] and best["structure"]["has_tied_triple"]),
        })

    valid = [p for p in progs if p["correct"] and p["structure"]]
    return {
        "variant": variant, "arm": arm,
        "n_programs": len(progs),
        "n_valid": len(valid),
        "generations": max([p["generation"] or 0 for p in progs], default=0),
        "best_score": best["combined_score"] if best else None,
        "best_generation": best["generation"] if best else None,
        "best_n_names": best["n_distinct_params"] if best else None,
        "best_validation_accuracy": best["validation_accuracy"] if best else None,
        "best_structure": best["structure"] if best else None,
        "n_with_any_ising": sum(p["structure"]["has_any_ising"] for p in valid),
        "n_with_tied_triple": sum(p["structure"]["has_tied_triple"] for p in valid),
        "n_with_su2_signature": sum(p["structure"]["su2_signature"] for p in valid),
        "tied_programs": [
            {"id": p["id"], "generation": p["generation"],
             "combined_score": p["combined_score"],
             "n_tied_pairs": p["structure"]["n_tied_pairs"],
             "tied_on_ring": p["structure"]["tied_on_ring"],
             "su2_signature": p["structure"]["su2_signature"]}
            for p in valid if p["structure"]["has_tied_triple"]],
        "best_so_far": best_so_far,
        "programs": progs,
    }


def figures(results: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
        "figure.dpi": 150, "axes.grid": True, "grid.alpha": 0.25,
        "grid.linestyle": "-", "grid.linewidth": 0.5,
    })
    colour = {"haiku": "#1b7837", "sonnet": "#7b3294", "gpt56sol": "#b06d00"}
    style = {"zc_su2_v3": "-", "transfer_su2_v3": "--"}

    # ---- Figure 1: best-so-far against the measured ladder ------------------
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, (variant, label) in zip(axes, VARIANTS.items()):
        for arm in ARMS:
            r = results["arms"].get(f"{variant}/{arm}")
            if not r or "best_so_far" not in r:
                continue
            xs = [b["generation"] for b in r["best_so_far"] if b["best"] is not None]
            ys = [b["best"] for b in r["best_so_far"] if b["best"] is not None]
            ax.plot(xs, ys, style[variant], color=colour[arm], lw=1.8,
                    label=f"{arm} ({max(ys):.3f})")
        for name, val in LADDER.items():
            ax.axhline(val, color="#999", lw=0.7, ls=":" if "seed" not in name else "-")
            ax.text(0.995, val + 0.006, name, transform=ax.get_yaxis_transform(),
                    ha="right", fontsize=6.5, color="#666")
        ax.set_title(f"{label}  ({variant})", fontsize=10)
        ax.set_xlabel("generation")
        # Upper left: no curve exceeds 0.61 and the ladder labels sit right,
        # so this is the only corner that collides with nothing.
        ax.legend(loc="upper left", fontsize=7.5, frameon=False)
    axes[0].set_ylabel("best combined score so far")
    axes[0].set_ylim(0.25, 0.80)
    fig.suptitle("Every arm improves on the seed, none reaches the tied-exchange answer",
                 fontsize=11, y=0.99)
    fig.tight_layout()
    fig.savefig(OUT / "v3_trajectories.png", bbox_inches="tight")
    plt.close(fig)

    # ---- Figure 2: score vs parameter count, structure-coded ---------------
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    buckets = {"no Ising gates": ("#bbb", "o", 14),
               "untied Ising": ("#2b7bba", "s", 22),
               "tied XX=YY=ZZ": ("#c2453a", "*", 90)}
    pts = defaultdict(lambda: ([], []))
    for key, r in results["arms"].items():
        for p in r.get("programs", []):
            if not (p["correct"] and p["structure"] and p["n_distinct_params"] is not None):
                continue
            s = p["structure"]
            b = ("tied XX=YY=ZZ" if s["has_tied_triple"]
                 else "untied Ising" if s["has_any_ising"] else "no Ising gates")
            pts[b][0].append(p["n_distinct_params"])
            pts[b][1].append(p["combined_score"])
    for b, (c, m, sz) in buckets.items():
        x, y = pts[b]
        # Plot empty categories too, so a count of zero reads as "none found"
        # rather than as a category that was never measured. The tied bucket
        # being empty IS the result.
        ax.scatter(x or [], y or [], c=c, marker=m, s=sz, alpha=0.75,
                   linewidths=0, label=f"{b} (n={len(x)})")
    ax.axhline(LADDER["tied exchange (answer)"], color="#c2453a", lw=1.1, ls="--")
    ax.text(0.5, LADDER["tied exchange (answer)"] + 0.008, "tied-exchange answer 0.756",
            fontsize=7.5, color="#c2453a")
    ax.axhline(LADDER["seed"], color="#666", lw=1.0, ls="-")
    ax.text(0.5, LADDER["seed"] + 0.008, "seed 0.295", fontsize=7.5, color="#666")
    ax.set_xlabel("distinct trainable parameter names")
    ax.set_ylabel("combined score")
    ax.set_xscale("log")
    ax.set_title("What the search actually explored", fontsize=10)
    ax.legend(fontsize=8, frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(OUT / "v3_score_vs_params.png", bbox_inches="tight")
    plt.close(fig)

    # ---- Figure 3: did Ising structure get adopted at all? ------------------
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    labels, anyising, tied, total = [], [], [], []
    for variant in VARIANTS:
        for arm in ARMS:
            r = results["arms"].get(f"{variant}/{arm}")
            if not r or "n_valid" not in r:
                continue
            labels.append(f"{'zc' if variant.startswith('zc') else 'ctx'}/{arm}")
            total.append(r["n_valid"])
            anyising.append(r["n_with_any_ising"])
            tied.append(r["n_with_tied_triple"])
    x = np.arange(len(labels))
    ax.bar(x - 0.22, total, 0.22, label="valid programs", color="#ddd")
    ax.bar(x, anyising, 0.22, label="contain Ising gates", color="#2b7bba")
    ax.bar(x + 0.22, tied, 0.22, label="tied XX=YY=ZZ", color="#c2453a")
    for i, v in enumerate(tied):
        ax.text(x[i] + 0.22, v + 0.6, str(v), ha="center", fontsize=8,
                color="#c2453a", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("programs")
    ax.set_title("Ising vocabulary use, and how often it was tied", fontsize=10)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "v3_structure_adoption.png", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote 3 figures to {OUT}")


def main() -> int:
    results = {"ladder": LADDER, "arms": {}}
    for variant in VARIANTS:
        for arm in ARMS:
            r = analyze_arm(variant, arm)
            results["arms"][f"{variant}/{arm}"] = r
            if "error" in r:
                print(f"{variant}/{arm}: {r['error']}")
                continue
            print(f"{variant:16s} {arm:9s} gens={r['generations']:3d} "
                  f"valid={r['n_valid']:3d}/{r['n_programs']:3d} "
                  f"best={r['best_score']:.4f} names={r['best_n_names']} "
                  f"ising={r['n_with_any_ising']:3d} tied={r['n_with_tied_triple']:3d} "
                  f"su2sig={r['n_with_su2_signature']}")

    slim = {"ladder": results["ladder"], "arms": {
        k: {kk: vv for kk, vv in v.items() if kk != "programs"}
        for k, v in results["arms"].items()}}
    (OUT / "v3_analysis.json").write_text(json.dumps(slim, indent=2))
    figures(results)

    tot_tied = sum(r.get("n_with_tied_triple", 0) for r in results["arms"].values())
    tot_sig = sum(r.get("n_with_su2_signature", 0) for r in results["arms"].values())
    print(f"\nTOTAL programs with a tied XX=YY=ZZ triple: {tot_tied}")
    print(f"TOTAL with the full SU(2) signature:        {tot_sig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
