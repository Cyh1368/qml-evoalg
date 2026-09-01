#!/usr/bin/env python3
"""Per-run metric table for every ensemble run on the S_n task, real and null.

One row per run. Writes RUN_METRICS.md (tables only) and run_metrics.json.

Definitions are inherited verbatim from the existing analysis scripts so the
numbers stay comparable with earlier write-ups:

  GENERAL / PERM / MIRROR vocabulary   analyze_symmetry_provenance.py
  ANSATZ_SPEC extraction + tied8       analyze_symmetry_talk_vs_build.py
  best-program structure               symmetry_analysis.py

The mirror BUILD test is reimplemented here: the script that produced
onepager_symmetry/mirror_stats.json is no longer in the tree. A proposal
"builds mirror" if some parameter drives single-qubit gates on exactly the
wire pair {i, 7-i} (i != 7-i), which is the pairing the one-pager describes.
Reproduced against mirror_stats.json in main().

Usage:  python3 build_run_metrics.py [--check]
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

N_QUBITS = 8

GENERAL = re.compile(r"\b(symmetr\w*|invarian\w*|equivarian\w*|permut\w*|orbit\w*|"
                     r"exchangeab\w*|relabel\w*|interchange\w*|mirror\w*)", re.I)
PERM = re.compile(r"\b(equivarian\w*|permut\w*|orbit\w*|exchangeab\w*|relabel\w*|"
                  r"interchange\w*|s_?8\b|s_?n\b)", re.I)
MIRROR = re.compile(r"\b(mirror\w*|palindrom\w*|butterfly|reflect\w*)", re.I)

ENV = {
    "N_QUBITS": N_QUBITS, "N_UPLOADS": 3, "N_REPEATS": 2,
    "FEATURE_SCALE": math.pi / 2, "N_FEATURES": 28,
    "np": np, "math": math, "itertools": itertools,
    "ALLOWED_SINGLE_QUBIT_GATES": {"RX", "RY", "RZ"},
    "ALLOWED_TWO_QUBIT_GATES": {"CNOT", "CZ"},
    "ALLOWED_PARAM_TWO_QUBIT_GATES": {"CRX", "CRY", "CRZ"},
}


# --------------------------------------------------------------------------
# run inventory
# --------------------------------------------------------------------------

def inventory() -> list[dict]:
    """(group, arm, run label, results dir, condition) for every ensemble run."""
    runs: list[dict] = []

    def add(group, arm, label, relpath, condition):
        p = HERE / relpath
        if (p / "programs.sqlite").exists():
            if condition == "null":
                series = "null-20gen"
            elif "_e1_" in label:
                series = "e1-20gen"
            else:
                series = "r-50gen"
            runs.append({"group": group, "arm": arm, "run": label, "dir": p,
                         "condition": condition, "series": series})

    # Real task, main arms. Two protocols: the original r* series (50 gens,
    # varying bandit seed) and the e1 series (20 gens, bandit seed fixed at 1).
    for i in range(1, 6):
        add("real", "weak", f"weak_r{i}", f"results_or_weak_r{i}", "real")
    for i in range(1, 11):
        add("real", "weak", f"weak_e1_r{i}", f"results_or_weak_e1_r{i}", "real")
    for i in range(1, 4):
        add("real", "mid", f"mid_r{i}", f"results_or_mid_r{i}", "real")
    for i in range(1, 6):
        add("real", "mid", f"mid_e1_r{i}", f"results_or_mid_e1_r{i}", "real")
    add("real", "frontier", "frontier_r1", "results_or_frontier_r1", "real")
    for i in range(1, 3):
        add("real", "frontier", f"frontier_e1_r{i}", f"results_or_frontier_e1_r{i}", "real")

    # Null task.
    for i in range(1, 6):
        add("null", "weak", f"null_weak_r{i}", f"null/results_weak_r{i}", "null")
    for i in range(1, 6):
        add("null", "mid", f"null_mid_r{i}", f"null/results_mid_r{i}", "null")
    for i in range(1, 4):
        add("null", "frontier", f"null_frontier_r{i}", f"null/results_frontier_r{i}", "null")

    # Rewind ablations (weak arm only).
    for rw in ("rw13", "rw20"):
        for kind in ("ctl", "abl"):
            for i in range(1, 5):
                add("rewind", "weak", f"{rw}_{kind}_r{i}",
                    f"results_or_weak_{rw}_{kind}_r{i}", "real")

    # Alternate ensemble rosters.
    #
    # The Azure-served rosters (az_weak_r1 / az_mid_r1 / az_frontier_r1) are
    # DELIBERATELY EXCLUDED. Azure lacked several models we wanted, so the tier
    # rosters there were not the ones we settled on; every Azure run predates
    # the switch to OpenRouter and is outdated. The results_az_* dirs are kept
    # on disk for provenance but are not part of any analysis. Do not add them
    # back without re-deciding the ensemble.
    for i in (1, 2):
        add("roster", "mixed", f"ens3_r{i}", f"results_ens3_r{i}", "real")

    return runs


# --------------------------------------------------------------------------
# structure extraction
# --------------------------------------------------------------------------

def spec_of(code: str, feature_pairs):
    lines = code.splitlines()
    try:
        a = next(i for i, l in enumerate(lines) if "EVOLVE-BLOCK-START" in l)
        b = next(i for i, l in enumerate(lines) if "EVOLVE-BLOCK-END" in l)
    except StopIteration:
        return None
    ns = dict(ENV, FEATURE_PAIRS=feature_pairs)
    try:
        exec(compile("\n".join(lines[a + 1:b]), "<blk>", "exec"), ns)
        return ns.get("ANSATZ_SPEC")
    except Exception:
        return None


# Gates whose two wires are interchangeable, so an unordered-pair orbit suffices.
SYMMETRIC_TWO_QUBIT = {"CZ"}


# Gates that are diagonal in the computational basis, hence commute with each
# other. Used to decide whether two blocks of the same family, separated by
# other gates, may be merged before the orbit test.
DIAGONAL_GATES = {"RZ", "CZ", "CRZ"}


def s8_parts(spec):
    """Split S_8 invariance into its two halves, layer by layer.

    The task fixes the meaning of the symmetry. `feature_map` in
    `initial_program.py` encodes feature k as an IsingZZ on FEATURE_PAIRS[k],
    and those 28 pairs are exactly the edges of K8; the readout is the mean of
    PauliZ over all 8 wires. So a relabelling of the qubits permutes wires and
    features together, the feature map is equivariant by construction and the
    readout invariant, and the model is S_8-invariant exactly when the ANSATZ is.

    That requires two things, and they are not equally hard:

      sq_ok  every single-qubit block covers all 8 wires
      tq_ok  every two-qubit block covers all 28 pairs (the complete graph)

    `sq_ok` falls out of any edit that shares rotation angles to cut the
    parameter count. `tq_ok` requires replacing the seed's CZ *line chain* with
    the complete graph, which means recognising that the features are the edges
    of K8. `has_2q` records whether the circuit has any two-qubit gate at all: an
    ansatz with none passes both tests vacuously, having discarded the
    interaction structure rather than symmetrised it.

    BLOCK, not family. Gates are keyed by (parameter, gate type) -- fixed gates
    by gate type alone -- and then split into maximal runs of CONSECUTIVE spec
    entries. Each run must be a full orbit on its own. Testing the family's
    pooled wire set instead would accept a circuit that applies 16 of the 28 CZ
    pairs, then a layer of RX/RY, then the other 12: the union is K8, but a
    relabelling moves the first block off itself, so the circuit is not
    invariant. 18 of the 44 circuits that pass the pooled test fail this one,
    nearly all of them the 16+12 CZ split in `frontier_r1`.

    Two blocks of a diagonal gate separated by a span of diagonal gates DO
    merge, since everything in the span commutes with them; that case is real
    (2 circuits) and is handled explicitly.

    Keying by (parameter, gate) rather than by parameter matters: one parameter
    legitimately drives more than one gate type, e.g. `frontier_r1` gen 39 shares
    `collective_mid` across an RY layer on all 8 wires and an RX layer on all 8
    wires. Each part is a full orbit, so those layers are fine.
    """
    ordered = set(itertools.permutations(range(N_QUBITS), 2))
    unordered = {frozenset(p) for p in ordered}

    def full_orbit(gate, wires):
        if len(wires[0]) == 1:
            return {w[0] for w in wires} == set(range(N_QUBITS))
        if gate in SYMMETRIC_TWO_QUBIT:
            return {frozenset(w) for w in wires} == unordered
        return set(wires) == ordered

    blocks: dict[tuple, list] = defaultdict(list)
    for i, g in enumerate(spec):
        if not isinstance(g, dict):
            return None
        gate = str(g.get("gate", "")).upper()
        key = (g.get("param") or "FIXED", gate)
        if "wires" in g:
            w = g["wires"]
            wires = tuple(w) if isinstance(w, (list, tuple)) else (w,)
        else:
            wires = (g.get("wire"),)
        runs = blocks[key]
        if runs and runs[-1][-1][0] == i - 1:
            runs[-1].append((i, wires))
        else:
            runs.append([(i, wires)])
    if not blocks:
        return None

    sq_ok = tq_ok = True
    has_2q = False
    for (_, gate), runs in blocks.items():
        arity = len(runs[0][0][1])
        if arity == 2:
            has_2q = True
        elif arity != 1:
            return {"sq_ok": False, "tq_ok": False, "has_2q": has_2q}

        ok = all(full_orbit(gate, [w for _, w in run]) for run in runs)
        if not ok and len(runs) > 1 and gate in DIAGONAL_GATES:
            lo, hi = runs[0][0][0], runs[-1][-1][0]
            span = {str(spec[i].get("gate", "")).upper() for i in range(lo, hi + 1)}
            if span <= DIAGONAL_GATES:
                ok = full_orbit(gate, [w for run in runs for _, w in run])
        if not ok:
            if arity == 1:
                sq_ok = False
            else:
                tq_ok = False
    return {"sq_ok": sq_ok, "tq_ok": tq_ok, "has_2q": has_2q}


def s8_invariant(spec):
    """Is the WHOLE circuit invariant under relabelling of the 8 qubits?

    Both halves of `s8_parts` must hold, block by block. Note this is satisfied
    vacuously by an ansatz with no two-qubit gate; the `real entangler` column in
    section 1C separates those out.

    Contrast the legacy `tied-8` test in `measure()`, which fires when SOME one
    parameter drives single-qubit gates on all 8 wires and looks at nothing else.
    tied-8 is neither necessary nor sufficient for this: `weak_e1_r1` gen 12
    passes tied-8 on an `rx_global` layer while its CZ line chain, disjoint-pair
    CRZ and `ry_low`/`ry_high` split all break S_8; `frontier_e1_r1` gen 10 fails
    tied-8 (one parameter drives RY, RZ and RX layers, so the family has 24 gates
    rather than 8) while being fully invariant.

    Keying families by (parameter, gate) rather than by parameter matters: one
    parameter legitimately drives more than one gate type, e.g. `frontier_r1` gen
    39 shares `collective_mid` across an RY layer on all 8 wires and an RX layer
    on all 8 wires. Each part is a full orbit, so the circuit is invariant.
    """
    parts = s8_parts(spec)
    if parts is None:
        return None
    return parts["sq_ok"] and parts["tq_ok"]


def measure(spec):
    """Parameter families -> the structural readouts."""
    fams: dict[str, list] = defaultdict(list)
    for g in spec:
        if not isinstance(g, dict):   # malformed spec entry (seen in az_weak_r1)
            continue
        p = g.get("param")
        if not p:
            continue
        gate = str(g.get("gate", "")).upper()
        if "wires" in g:
            w = g["wires"]
            wires = tuple(w) if isinstance(w, (list, tuple)) else (w,)
            n_wires = 2
        else:
            wires, n_wires = (g.get("wire"),), 1
        fams[p].append((gate, n_wires, wires))

    if not fams:
        return None

    sizes = [len(v) for v in fams.values()]

    # the motif: one param driving single-qubit gates on all 8 wires
    tied8 = any(len(v) == N_QUBITS and all(w == 1 for _, w, _ in v)
                and {ws[0] for _, _, ws in v} == set(range(N_QUBITS))
                for v in fams.values())

    # mirror: one param driving single-qubit gates on exactly {i, 7-i}
    mirror_built = False
    for v in fams.values():
        if not all(w == 1 for _, w, _ in v):
            continue
        ws = {ws_[0] for _, _, ws_ in v}
        if len(ws) == 2:
            i, j = sorted(ws)
            if j == N_QUBITS - 1 - i and i != j:
                mirror_built = True
                break

    return {"angles": len(fams), "max_family": max(sizes),
            "tied8": tied8, "mirror_built": mirror_built,
            "s8": s8_invariant(spec),
            "s8_parts": s8_parts(spec)}


def load_run(db: Path, feature_pairs) -> list[dict]:
    con = sqlite3.connect(f"file://{db}?mode=ro", uri=True)
    out = []
    try:
        rows = con.execute(
            "select id, parent_id, generation, combined_score, correct, code, metadata "
            "from programs order by generation"
        ).fetchall()
    finally:
        con.close()

    for pid, parent, gen, score, correct, code, meta in rows:
        m = json.loads(meta) if meta else {}
        model = (m.get("model_name") or "seed").replace("openrouter/", "").replace("azure-", "")
        is_seed = model == "seed"
        text = " ".join(str(m.get(k) or "") for k in ("patch_name", "patch_description"))
        spec = spec_of(code, feature_pairs)
        meas = measure(spec) if spec else None
        out.append({
            "id": pid, "parent": parent,
            "gen": gen, "score": score, "correct": bool(correct), "model": model,
            "seed": is_seed,
            "says_any": bool(GENERAL.search(text)),
            "says_perm": bool(PERM.search(text)),
            "says_mirror": bool(MIRROR.search(text)),
            "meas": meas,
        })
    return out


def pct(num, den):
    return None if not den else 100.0 * num / den


def summarise(rec: dict, feature_pairs) -> dict:
    rows = load_run(rec["dir"] / "programs.sqlite", feature_pairs)
    proposals = [r for r in rows if not r["seed"]]
    parseable = [r for r in proposals if r["meas"]]

    seed_rows = [r for r in rows if r["seed"] and r["score"] is not None]
    seed_score = seed_rows[0]["score"] if seed_rows else None

    scored = [r for r in rows if r["correct"] and r["score"] is not None]
    best = max(scored, key=lambda r: r["score"]) if scored else None

    # structure of the best program
    best_meas = best["meas"] if best and best["meas"] else None

    by_id = {r["id"]: r for r in rows}

    def authored(r, field):
        """Did this proposal introduce `field`, i.e. did its parent lack it?"""
        par = by_id.get(r["parent"])
        return par is None or par.get("meas") is None or not par["meas"][field]

    built = [r for r in parseable if r["meas"]["tied8"]]
    s8_built = [r for r in parseable if r["meas"]["s8"]]
    s8_authored = [r for r in s8_built if authored(r, "s8")]
    motif_authored = [r for r in built if authored(r, "tied8")]
    said_perm = [r for r in parseable if r["says_perm"]]
    said_mirror = [r for r in parseable if r["says_mirror"]]
    said_any = [r for r in parseable if r["says_any"]]

    return {
        "group": rec["group"], "arm": rec["arm"], "run": rec["run"],
        "condition": rec["condition"], "series": rec.get("series", ""),
        "n_proposals": len(proposals),
        "n_parseable": len(parseable),
        "max_gen": max((r["gen"] for r in proposals if r["gen"] is not None), default=None),
        "seed_score": seed_score,
        "best_score": best["score"] if best else None,
        "best_gen": best["gen"] if best else None,
        "best_params": best_meas["angles"] if best_meas else None,
        "best_max_family": best_meas["max_family"] if best_meas else None,
        "best_has_motif": best_meas["tied8"] if best_meas else None,
        "motif_rate": pct(len(built), len(parseable)),
        "motif_first_gen": min((r["gen"] for r in built), default=None),
        "n_motif_authored": len(motif_authored),
        # circuit-level S_8 invariance, as opposed to the tied-8 layer test
        "n_s8": len(s8_built),
        "s8_rate": pct(len(s8_built), len(parseable)),
        "s8_first_gen": min((r["gen"] for r in s8_built), default=None),
        "n_s8_authored": len(s8_authored),
        "n_s8_authored_says_perm": sum(1 for r in s8_authored if r["says_perm"]),
        # the two halves of the condition, counted separately
        "n_sq_ok": sum(1 for r in parseable if r["meas"]["s8_parts"]["sq_ok"]),
        "n_tq_ok": sum(1 for r in parseable if r["meas"]["s8_parts"]["tq_ok"]),
        "n_s8_real_entangler": sum(1 for r in s8_built if r["meas"]["s8_parts"]["has_2q"]),
        "best_is_s8": best_meas["s8"] if best_meas else None,
        "mirror_rate_built": pct(sum(r["meas"]["mirror_built"] for r in parseable),
                                 len(parseable)),
        "says_any_rate": pct(len(said_any), len(parseable)),
        "says_perm_rate": pct(len(said_perm), len(parseable)),
        "says_mirror_rate": pct(len(said_mirror), len(parseable)),
        "n_says_any": len(said_any),
        "n_says_perm": len(said_perm),
        "n_says_mirror": len(said_mirror),
        "build_given_say_any": pct(sum(r["meas"]["tied8"] for r in said_any), len(said_any)),
        "build_given_say_perm": pct(sum(r["meas"]["tied8"] for r in said_perm), len(said_perm)),
        "build_given_say_mirror": pct(sum(r["meas"]["mirror_built"] for r in said_mirror),
                                      len(said_mirror)),

        # --- raw counts, so the headline table can pool over proposals ---
        "n_built_perm": sum(1 for r in parseable if r["meas"]["tied8"]),
        "n_built_mirror": sum(1 for r in parseable if r["meas"]["mirror_built"]),
        # said permutation-symmetry vocabulary, and what they then built
        "n_perm_built_perm": sum(1 for r in said_perm if r["meas"]["tied8"]),
        "n_perm_built_mirror_only": sum(1 for r in said_perm
                                        if r["meas"]["mirror_built"]
                                        and not r["meas"]["tied8"]),
        "n_perm_built_neither": sum(1 for r in said_perm
                                    if not r["meas"]["tied8"]
                                    and not r["meas"]["mirror_built"]),
        # said mirror vocabulary, and what they then built
        "n_mirror_built_mirror": sum(1 for r in said_mirror if r["meas"]["mirror_built"]),
        "n_any_built_perm": sum(1 for r in said_any if r["meas"]["tied8"]),
        # "builds what it says": named perm and built the perm motif, OR named
        # mirror (without naming perm) and built a mirror pair.
        "n_faithful": sum(1 for r in said_any
                          if (r["says_perm"] and r["meas"]["tied8"])
                          or (not r["says_perm"] and r["says_mirror"]
                              and r["meas"]["mirror_built"])),
        "n_says_perm_or_mirror": sum(1 for r in parseable
                                     if r["says_perm"] or r["says_mirror"]),
        # base rate: built the perm-motif WITHOUT naming permutation symmetry.
        # The conditional above is meaningless without this: once the motif is
        # in the population it propagates by inheritance, so a high
        # "builds | says" can be pure base rate.
        "n_no_perm": sum(1 for r in parseable if not r["says_perm"]),
        "n_no_perm_built_perm": sum(1 for r in parseable
                                    if not r["says_perm"] and r["meas"]["tied8"]),
        "n_faithful_pm": sum(1 for r in parseable
                             if (r["says_perm"] and r["meas"]["tied8"])
                             or (not r["says_perm"] and r["says_mirror"]
                                 and r["meas"]["mirror_built"])),
    }


# --------------------------------------------------------------------------
# task setup: real vs null
# --------------------------------------------------------------------------

# Verified on the cluster 2026-08-18 by byte-comparing
# ~/project/transfer_sn against ~/project/transfer_sn_null, and by flattening
# both shinka configs to key paths. Recorded here because those task dirs are
# not in this repo; rerun the comparison with:
#   ssh bouchet 'cmp -s $HOME/project/transfer_sn/<f> $HOME/project/transfer_sn_null/<f>'
SHIPPED_FILES = [
    ("`initial_program.py`", "seed circuit the models edit", "identical"),
    ("`evaluate.py`", "scoring code, never shown to the proposer", "identical"),
    ("`task_sys_msg`", "prompt text the models read", "identical"),
    ("`feature_pairs`", "28-entry qubit-pair table", "identical (md5)"),
    ("`activate_eval_cluster.sh`", "env paths for eval jobs", "differs: 3 path strings"),
    ("`answer_key*`", "labelling rule", "absent from null dir (launch guard)"),
]

CONFIG_DIFF = [
    ("weak", 20, "$2", 20, "$4"),
    ("mid", 20, "$3", 20, "$6"),
    ("frontier", 20, "$24", 15, "$9"),
]


def linear_probe(d) -> float:
    X = d["x_train"].astype(float)
    X1 = np.hstack([X, np.ones((len(X), 1))])
    w, *_ = np.linalg.lstsq(X1, d["y_train"].astype(float), rcond=None)
    Xt = d["x_test"].astype(float)
    Xt1 = np.hstack([Xt, np.ones((len(Xt), 1))])
    return float(np.mean(np.sign(Xt1 @ w) == d["y_test"]))


def task_setup_section(fp_real, fp_null) -> list[str]:
    real = np.load(HERE / "dataset.npz")
    null = np.load(HERE / "dataset_null.npz")

    L = ["\n## 3. Task setup: real versus null\n"]
    L.append("The null control changes the labelling rule and nothing else. "
             "`real: label = +1 iff the graph is CONNECTED` (invariant under S_8) "
             "becomes `null: label = +1 iff deg(v*) >= 2`, v* = vertex 3 "
             "(not invariant: the optimal circuit must single out one qubit). "
             "Source: `make_dataset.py` vs `make_dataset_null.py`.\n")

    L.append("### Shipped task files\n")
    L.append(table(SHIPPED_FILES, [
        ("file", lambda r: r[0]),
        ("role", lambda r: r[1]),
        ("real vs null", lambda r: r[2]),
    ], aligns=["---", "---", "---"]))
    L.append("\nCluster comparison of `~/project/transfer_sn` against "
             "`~/project/transfer_sn_null`, 2026-08-18. The three differing path "
             "strings are `MPLCONFIGDIR`, `TTT_LOG_DIR` and `TASK_DATA`.\n")

    L.append("\n### Config\n")
    L.append(table(CONFIG_DIFF, [
        ("arm", lambda r: r[0]),
        ("real gens", lambda r: str(r[1])),
        ("real cost cap", lambda r: r[2]),
        ("null gens", lambda r: str(r[3])),
        ("null cost cap", lambda r: r[4]),
    ]))
    L.append("\nReal side is the `e1-20gen` protocol. Every other config key is "
             "identical, including `llm_models`, `patch_type_probs`, UCB1 settings "
             "and bandit seed 1.\n")

    L.append("\n### Dataset\n")
    rows = []
    for split in ("train", "validation", "test"):
        rows.append({
            "split": split,
            "n": len(real[f"x_{split}"]),
            "r_bal": float(np.mean(real[f"y_{split}"] > 0)),
            "n_bal": float(np.mean(null[f"y_{split}"] > 0)),
            "r_den": float(real[f"x_{split}"].mean()),
            "n_den": float(null[f"x_{split}"].mean()),
        })
    L.append(table(rows, [
        ("split", lambda r: r["split"]),
        ("rows", lambda r: f(r["n"])),
        ("real +1 frac", lambda r: f(r["r_bal"], 3)),
        ("null +1 frac", lambda r: f(r["n_bal"], 3)),
        ("real edge density", lambda r: f(r["r_den"], 4)),
        ("null edge density", lambda r: f(r["n_den"], 4)),
    ]))

    L.append("\n### Derived\n")
    derived = [
        ("`feature_pairs` md5 match", *(("yes", "yes") if fp_real == fp_null
                                        else ("NO", "NO"))),
        ("linear probe on raw features, test accuracy",
         f"{linear_probe(real):.3f}", f"{linear_probe(null):.3f}"),
        ("seed program score (rescaled)", "0.0000", "1.2490"),
    ]
    L.append(table(derived, [
        ("quantity", lambda r: r[0]),
        ("real", lambda r: r[1]),
        ("null", lambda r: r[2]),
    ], aligns=["---", "---:", "---:"]))
    L.append("\nThe null label rule is nearly linear in the inputs, so the null task "
             "is much easier and its scores sit above anything reached on the real "
             "task. Scores are not comparable across conditions; the structural "
             "columns are. Edge density differs because rejection sampling to a "
             "50/50 split under a different label rule accepts a different subset of "
             "the same distribution.\n")
    return L


# --------------------------------------------------------------------------
# markdown emission
# --------------------------------------------------------------------------

def f(v, nd=2, suffix=""):
    if v is None:
        return "--"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.{nd}f}{suffix}"
    return f"{v}{suffix}"


def table(rows, cols, aligns=None):
    head = "| " + " | ".join(c[0] for c in cols) + " |"
    if aligns is None:
        aligns = ["---"] + ["---:"] * (len(cols) - 1)
    sep = "|" + "|".join(aligns) + "|"
    body = ["| " + " | ".join(c[1](r) for c in cols) + " |" for r in rows]
    return "\n".join([head, sep] + body)


def agg(rows, key, weight_num=None, weight_den=None):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return sum(vals) / len(vals) if vals else None


def pooled(rows, num_key, den_key):
    n = sum(r[num_key] for r in rows if r.get(num_key) is not None)
    d = sum(r[den_key] for r in rows if r.get(den_key) is not None)
    return pct(n, d)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="cross-check mirror counts against mirror_stats.json")
    args = ap.parse_args()

    fp_real = [tuple(int(w) for w in row)
               for row in np.load(HERE / "dataset.npz")["feature_pairs"]]
    fp_null = [tuple(int(w) for w in row)
               for row in np.load(HERE / "dataset_null.npz")["feature_pairs"]]
    assert fp_real == fp_null, "feature_pairs differ between conditions"

    recs = inventory()
    print(f"[metrics] {len(recs)} runs found")
    out = []
    for rec in recs:
        fp = fp_null if rec["condition"] == "null" else fp_real
        try:
            out.append(summarise(rec, fp))
        except Exception as exc:
            print(f"[metrics] SKIP {rec['run']}: {exc}")
    (HERE / "run_metrics.json").write_text(json.dumps(out, indent=2))

    ARM_ORDER = {"weak": 0, "mid": 1, "frontier": 2, "mixed": 3}
    out.sort(key=lambda r: (ARM_ORDER.get(r["arm"], 9), r["run"]))

    def sel(group, condition=None):
        return [r for r in out if r["group"] == group
                and (condition is None or r["condition"] == condition)]

    score_cols = [
        ("run", lambda r: f"`{r['run']}`"),
        ("arm", lambda r: r["arm"]),
        ("protocol", lambda r: r["series"]),
        ("gens", lambda r: f(r["max_gen"])),
        ("proposals", lambda r: f(r["n_proposals"])),
        ("parsed", lambda r: f(r["n_parseable"])),
        ("seed", lambda r: f(r["seed_score"], 4)),
        ("best", lambda r: f(r["best_score"], 4)),
        ("best gen", lambda r: f(r["best_gen"])),
        ("params", lambda r: f(r["best_params"])),
        ("max family", lambda r: f(r["best_max_family"])),
        ("perm-motif in best", lambda r: f(r["best_has_motif"])),
    ]
    motif_cols = [
        ("run", lambda r: f"`{r['run']}`"),
        ("arm", lambda r: r["arm"]),
        ("builds perm-motif %", lambda r: f(r["motif_rate"], 1)),
        ("first gen", lambda r: f(r["motif_first_gen"])),
        ("perm-motif in best", lambda r: f(r["best_has_motif"])),
        ("builds S_8-invariant circuit %", lambda r: f(r["s8_rate"], 1)),
        ("S_8 first gen", lambda r: f(r["s8_first_gen"])),
        ("S_8 in best", lambda r: f(r["best_is_s8"])),
        ("builds mirror-motif %", lambda r: f(r["mirror_rate_built"], 1)),
        ("params in best", lambda r: f(r["best_params"])),
    ]
    lang_cols = [
        ("run", lambda r: f"`{r['run']}`"),
        ("arm", lambda r: r["arm"]),
        ("says any-symmetry %", lambda r: f(r["says_any_rate"], 1)),
        ("says perm %", lambda r: f(r["says_perm_rate"], 1)),
        ("says mirror %", lambda r: f(r["says_mirror_rate"], 1)),
        ("n said any", lambda r: f(r["n_says_any"])),
        ("n said perm", lambda r: f(r["n_says_perm"])),
        ("n said mirror", lambda r: f(r["n_says_mirror"])),
    ]
    follow_cols = [
        ("run", lambda r: f"`{r['run']}`"),
        ("arm", lambda r: r["arm"]),
        ("builds perm-motif \\| says any-symmetry %", lambda r: f(r["build_given_say_any"], 1)),
        ("builds perm-motif \\| says perm %", lambda r: f(r["build_given_say_perm"], 1)),
        ("builds mirror-motif only \\| says perm %", lambda r: f(pct(r["n_perm_built_mirror_only"], r["n_says_perm"]), 1)),
        ("builds neither \\| says perm %", lambda r: f(pct(r["n_perm_built_neither"], r["n_says_perm"]), 1)),
        ("builds mirror-motif \\| says mirror %", lambda r: f(r["build_given_say_mirror"], 1)),
        ("n said any", lambda r: f(r["n_says_any"])),
        ("n said perm", lambda r: f(r["n_says_perm"])),
        ("n said mirror", lambda r: f(r["n_says_mirror"])),
    ]

    L = []
    L.append("# Run metrics\n")
    L.append("S_n transfer task. One row per run. Generated by `build_run_metrics.py`; "
             "raw values in `run_metrics.json`.\n")
    L.append("""### Terminology

Every quantity below is one of two kinds, and the column names say which:

**BUILD side (what is in the circuit code).** Several distinct structures are
measured. They are different structures, not different names for one thing:

| term used in this document | structural test | relation to the task |
|---|---|---|
| **S_8-invariant circuit** | *both* halves below hold | the whole circuit is unchanged by relabelling the qubits; this is the symmetry the task actually has |
| &nbsp;&nbsp;half 1: **ties all 8 wires** | every single-qubit *block* covers all 8 wires | the cheap half: any "cut the parameter count" edit produces it |
| &nbsp;&nbsp;half 2: **K8 entangler** | every two-qubit *block* covers all 28 pairs | the hard half: requires replacing the seed's CZ line chain with the complete graph |
| **perm-motif** (`tied-8`) | *some one* parameter drives single-qubit gates on all 8 wires | a legacy layer metric. It is a weak proxy for half 1 only, and says nothing about the entangler or the rest of the circuit |
| **mirror-motif** | one parameter drives single-qubit gates on exactly the pair {i, 7-i} | a reflection pairing; *not* S_8-invariant, so on the real task this is a **wrong** symmetry |

A **block** is a maximal run of consecutive spec entries sharing one
(parameter, gate type) key; fixed gates are keyed by gate type alone. Each block
must be a full S_8 orbit on its own, not merely the pooled wire set of the whole
family. A circuit that applies 16 of the 28 CZ pairs, then a layer of RX/RY, then
the other 12, has a pooled union of K8 but is not invariant, because a
relabelling moves the first block off itself. Two blocks of a *diagonal* gate
separated by a span of diagonal gates do merge, since everything in the span
commutes with them.

**Where the symmetry comes from.** `feature_map` in `initial_program.py` encodes
feature k as an `IsingZZ` on `FEATURE_PAIRS[k]`, and those 28 pairs are exactly
the edges of K8; the readout is the mean of `PauliZ` over all 8 wires. A
relabelling of the qubits therefore permutes wires and features together, the
feature map is equivariant by construction and the readout invariant, so the
model is S_8-invariant precisely when the ansatz is. The real task's label
(is the graph connected) is invariant under that relabelling; the null task's
(deg(v*) >= 2 for a fixed v*) is not.

**perm-motif is not the task's symmetry, and earlier versions of this document
said it was.** It fires on one tied layer regardless of what surrounds it, and
it is neither necessary nor sufficient for S_8 invariance. `weak_e1_r1` gen 12
passes it on an `rx_global` RX layer across all 8 wires while its fixed CZ line
chain, CRZ on the disjoint pairs {0,1},{2,3},{4,5},{6,7}, CRY on {1,2},{3,4},{5,6}
and `ry_low`/`ry_high` split on wires 0-3 / 4-7 all break S_8; the patch note asks
only for "a global RX mixer ... +1 parameter per block" for expressivity.
Conversely `frontier_e1_r1` gen 10 fails perm-motif while being fully invariant,
because one parameter drives RY, RZ and RX layers and the family has 24 gates
rather than 8. Section 1C gives the arm-level consequence: perm-motif scores the
cheap half of the condition, so in the weak and mid arms it is measuring
parameter tying and nothing more. `builds perm-motif %` is kept only for
continuity with the earlier write-ups; prefer the section 1C columns.

The bare word "motif" is not used on its own anywhere below. Where earlier
write-ups said "motif", they meant **perm-motif**.

**SAY side (what the LLM wrote in its patch name and description).** Three
independent regexes over LLM-authored text only, never over code:

| term | regex family | meaning |
|---|---|---|
| **says any-symmetry** | symmetr*, invarian*, equivarian*, permut*, orbit*, exchangeab*, relabel*, interchange*, mirror* | named symmetry of *any* kind, correct or not |
| **says perm** | equivarian*, permut*, orbit*, exchangeab*, relabel*, interchange*, S_8, S_n | named **permutation** symmetry specifically |
| **says mirror** | mirror*, palindrom*, butterfly, reflect* | named a **reflection/mirror** symmetry |

The three are independent regexes, so `any` is not a strict superset of
`mirror`: `butterfly`, `palindromic` and `reflect*` match mirror only (11 such
proposals in `mid_r2`). `perm` and `mirror` can both fire on one proposal.
Definitions kept as published so these numbers stay comparable with the earlier
write-ups.

Rates are over parsed proposals, seed excluded. A column named
`builds X | says Y` is a conditional: denominator is proposals that *said* Y.\n""")

    # ---- headline: say versus build ----
    L.append("\n## 1. Headline: do the models build what they say?\n")
    L.append("Pooled over **proposals** (not runs), so each row is a straight count "
             "over every parsed proposal in that arm. Real-task main arms (`or_*`, both "
             "protocols), the null task for contrast, and the alternate ensemble "
             "roster of section 7 (`ens3_*`). "
             "Read the columns as: how often a symmetry gets *named*, how often the "
             "correct (S_8) structure gets *built*, and, conditional on naming "
             "permutation symmetry, what actually appears in the code.\n")

    def headline_rows():
        rows = []
        for label, rs in (("real", sel("real", "real")),
                          ("null", sel("null", "null")),
                          ("real (alt roster)", sel("roster"))):
            for arm in ("weak", "mid", "frontier", "mixed"):
                g = [r for r in rs if r["arm"] == arm]
                if not g:
                    continue
                tot = lambda k: sum(r[k] for r in g if r.get(k) is not None)
                rows.append({"task": label, "arm": arm, "runs": len(g),
                             "n": tot("n_parseable"),
                             "n_any": tot("n_says_any"), "n_perm": tot("n_says_perm"),
                             "n_mirror": tot("n_says_mirror"),
                             "n_built_perm": tot("n_built_perm"),
                             "n_pbp": tot("n_perm_built_perm"),
                             "n_pbm": tot("n_perm_built_mirror_only"),
                             "n_pbn": tot("n_perm_built_neither"),
                             "n_mbm": tot("n_mirror_built_mirror"),
                             "n_faith": tot("n_faithful_pm"),
                             "n_saidpm": tot("n_says_perm_or_mirror"),
                             "n_noperm": tot("n_no_perm"),
                             "n_noperm_bp": tot("n_no_perm_built_perm"),
                             "n_s8": tot("n_s8"),
                             "n_s8_auth": tot("n_s8_authored"),
                             "n_s8_auth_perm": tot("n_s8_authored_says_perm"),
                             "n_motif_auth": tot("n_motif_authored"),
                             "n_sq": tot("n_sq_ok"), "n_tq": tot("n_tq_ok"),
                             "n_s8_real": tot("n_s8_real_entangler")})
        return rows

    hr = headline_rows()
    L.append("**A. Say rates and build rates, unconditional.**\n")
    L.append(table(hr, [
        ("task", lambda r: r["task"]),
        ("arm", lambda r: r["arm"]),
        ("runs", lambda r: f(r["runs"])),
        ("proposals", lambda r: f(r["n"])),
        ("says any-symmetry %", lambda r: f(pct(r["n_any"], r["n"]), 1)),
        ("says perm %", lambda r: f(pct(r["n_perm"], r["n"]), 1)),
        ("says mirror %", lambda r: f(pct(r["n_mirror"], r["n"]), 1)),
        ("builds perm-motif %", lambda r: f(pct(r["n_built_perm"], r["n"]), 1)),
    ]))
    L.append("\n`says perm %` is the answer to *how often do they say permutation "
             "symmetry*: it counts proposals whose text names permutation / "
             "equivariance / relabelling / S_8, over all parsed proposals.\n")

    L.append("\n**B. Conditional on saying permutation symmetry, what do they build?** "
             "The three percentage columns partition the same denominator "
             "(`n said perm`) and sum to 100.\n")
    L.append(table(hr, [
        ("task", lambda r: r["task"]),
        ("arm", lambda r: r["arm"]),
        ("n said perm", lambda r: f(r["n_perm"])),
        ("builds perm-motif (right) %", lambda r: f(pct(r["n_pbp"], r["n_perm"]), 1)),
        ("builds mirror-motif only (wrong) %", lambda r: f(pct(r["n_pbm"], r["n_perm"]), 1)),
        ("builds neither %", lambda r: f(pct(r["n_pbn"], r["n_perm"]), 1)),
        ("BASE: builds perm-motif without saying perm %",
         lambda r: f(pct(r["n_noperm_bp"], r["n_noperm"]), 1)),
        ("lift", lambda r: f((pct(r["n_pbp"], r["n_perm"]) or 0)
                             - (pct(r["n_noperm_bp"], r["n_noperm"]) or 0), 1)
                 if r["n_perm"] else "--"),
    ]))
    L.append("""
**Read column 4 against the BASE column, never on its own.** Once the perm-motif
is in a run's population it propagates to children by inheritance, so a proposal
can "build" it without authoring it. Where the base rate is already high
a high conditional can be almost entirely base rate. The only clean version of
this test restricts to proposals whose parent program lacked the motif, so the
proposal had to introduce it: on those, frontier introduces it in 10/10 of the
proposals that named permutation symmetry against a 19.2% background, while weak
and mid never name permutation symmetry at all (0 of 324 and 0 of 192 parsed
proposals). Section 1C adds the second correction: what weak and mid introduce
is a tied single-qubit layer, never the complete-graph entangler that the task's
symmetry actually requires.
""")
    L.append("\n`builds perm-motif (right) %` is *how often they build the permutation "
             "symmetry when they say it*. `builds mirror-motif only (wrong) %` is "
             "*how often they build a wrong symmetry instead* (a reflection pairing, "
             "which is not S_8-invariant). `builds neither %` is naming the symmetry "
             "and shipping no symmetric parameter tying at all.\n")

    L.append("""
**C. Does the circuit actually have the task's symmetry?** The perm-motif
column above is a layer test (see Terminology). This table replaces it with the
condition the task imposes, split into its two halves: `ties all 8 wires` is the
single-qubit half, `K8 entangler` is the two-qubit half, and a circuit is
S_8-invariant when both hold. `real entangler` excludes circuits that pass
vacuously by containing no two-qubit gate at all. `authored` restricts to
proposals whose parent was not already S_8-invariant.
""")
    L.append(table(hr, [
        ("task", lambda r: r["task"]),
        ("arm", lambda r: r["arm"]),
        ("proposals", lambda r: f(r["n"])),
        ("builds perm-motif (layer test)", lambda r: f(r["n_built_perm"])),
        ("ties all 8 wires", lambda r: f(r["n_sq"])),
        ("K8 entangler (all 28 pairs)", lambda r: f(r["n_tq"])),
        ("S_8-invariant", lambda r: f(r["n_s8"])),
        ("of which real entangler", lambda r: f(r["n_s8_real"])),
        ("S_8 authored", lambda r: f(r["n_s8_auth"])),
        ("S_8 authored & says perm", lambda r: f(r["n_s8_auth_perm"])),
    ]))
    L.append("""
The two halves are nothing alike in difficulty, and that is the point. Weak
satisfies the 8-wire tying 12 times and the complete-graph entangler once; mid,
10 times and never. Tying single-qubit rotations is what falls out of any
"reduce the parameter count" edit, which is what those patch notes ask for.
Replacing the seed's CZ *line chain* with all 28 pairs is the move that requires
recognising that the features are the edges of K8, and only the frontier arm
makes it (`collective_complete_graph`, `factorized_complete_graph`,
`complete_graph_two_axis`). This is why `builds perm-motif %` overstates the weak
and mid arms so badly: it scores the cheap half of the condition.

Read the `real entangler` column before quoting the null-frontier row. Two of
its three S_8-invariant proposals contain no two-qubit gate at all, so they are
invariant only by having discarded the interaction structure, leaving one real
case. Per-proposal detail is in `PERM_MOTIF_EVENTS.md`.

The block rule is what keeps the frontier number honest. Testing each family's
pooled wire set instead scores real-frontier at 41 rather than 24 on the
entangler half: 18 circuits, nearly all the recurring 16+12 CZ split in
`frontier_r1`, apply two partial CZ blocks separated by RX/RY layers. Their union
is the complete graph but neither block is, so they are not invariant. Any figure
quoted from an earlier draft of this document that put real-frontier S_8 near 40
came from the pooled test and is too high.
""")

    L.append("\n**D. Do they build what they say, overall?** A proposal counts as "
             "*faithful* if it named permutation symmetry and built the perm-motif, "
             "or named mirror symmetry (without naming permutation) and built a "
             "mirror pair. Denominator is proposals that named a *specific* symmetry "
             "(perm or mirror); proposals that only said a vague `symmetr*` word are "
             "excluded because there is no specific structure to check them against.\n")
    L.append(table(hr, [
        ("task", lambda r: r["task"]),
        ("arm", lambda r: r["arm"]),
        ("n named a specific symmetry", lambda r: f(r["n_saidpm"])),
        ("builds what it says %", lambda r: f(pct(r["n_faith"], r["n_saidpm"]), 1)),
        ("n said mirror", lambda r: f(r["n_mirror"])),
        ("builds mirror-motif \\| says mirror %", lambda r: f(pct(r["n_mbm"], r["n_mirror"]), 1)),
    ]))
    L.append("\nPer-run versions of every number in this section are in the "
             "`Say versus build` table of each section below.\n")

    # ---- arm summary ----
    L.append("\n## 2. Arm summary\n")
    L.append("Real task main arms (`or_*`) and null task, split by protocol: "
             "`e1-20gen` = 20 generations, bandit seed fixed at 1; `r-50gen` = "
             "50 generations, bandit seed varying; `null-20gen` = 20 generations "
             "on the null dataset (frontier null ran 15). Run-level means. "
             "`perm-motif in best` is the layer test and `S_8-invariant in best` "
             "the circuit test; they disagree, and the circuit column is the one "
             "that means the model found the task's symmetry.\n")
    summary_rows = []
    for cond, group, series in (("real", "real", "e1-20gen"),
                                ("real", "real", "r-50gen"),
                                ("null", "null", "null-20gen")):
        for arm in ("weak", "mid", "frontier"):
            rs = [r for r in sel(group, cond)
                  if r["arm"] == arm and r["series"] == series]
            if not rs:
                continue
            scores = [r["best_score"] for r in rs if r["best_score"] is not None]
            mean = sum(scores) / len(scores) if scores else None
            sd = (sum((s - mean) ** 2 for s in scores) / (len(scores) - 1)) ** 0.5 \
                if scores and len(scores) > 1 else None
            summary_rows.append({
                "cond": cond, "series": series, "arm": arm, "n": len(rs),
                "mean": mean, "sd": sd, "cv": (sd / mean) if (sd and mean) else None,
                "motif_rate": agg(rs, "motif_rate"),
                "motif_best": sum(1 for r in rs if r["best_has_motif"]),
                "s8_rate": agg(rs, "s8_rate"),
                "s8_best": sum(1 for r in rs if r["best_is_s8"]),
                "says_any": agg(rs, "says_any_rate"),
                "says_perm": agg(rs, "says_perm_rate"),
                "says_mirror": agg(rs, "says_mirror_rate"),
                "params": agg(rs, "best_params"),
            })
    L.append(table(summary_rows, [
        ("task", lambda r: r["cond"]),
        ("protocol", lambda r: r["series"]),
        ("arm", lambda r: r["arm"]),
        ("runs", lambda r: f(r["n"])),
        ("mean best", lambda r: f(r["mean"], 4)),
        ("sd", lambda r: f(r["sd"], 4)),
        ("CV", lambda r: f(r["cv"], 2)),
        ("builds perm-motif %", lambda r: f(r["motif_rate"], 1)),
        ("perm-motif in best", lambda r: f"{r['motif_best']}/{r['n']}"),
        ("builds S_8-invariant circuit %", lambda r: f(r["s8_rate"], 1)),
        ("S_8-invariant in best", lambda r: f"{r['s8_best']}/{r['n']}"),
        ("params in best", lambda r: f(r["params"], 1)),
        ("says any-symmetry %", lambda r: f(r["says_any"], 1)),
        ("says perm %", lambda r: f(r["says_perm"], 1)),
        ("says mirror %", lambda r: f(r["says_mirror"], 1)),
    ]))

    L.extend(task_setup_section(fp_real, fp_null))

    sections = [
        ("4. Real task, main arms", sel("real", "real")),
        ("5. Null task", sel("null", "null")),
        ("6. Rewind ablations (weak arm)", sel("rewind")),
        ("7. Alternate ensemble rosters", sel("roster")),
    ]
    for title, rows in sections:
        if not rows:
            continue
        L.append(f"\n## {title}\n")
        L.append("### Scores and best-program structure\n")
        L.append(table(rows, score_cols))
        L.append("\n### Motif\n")
        L.append(table(rows, motif_cols))
        L.append("\n### Symmetry vocabulary\n")
        L.append(table(rows, lang_cols))
        L.append("\n### Say versus build\n")
        L.append(table(rows, follow_cols))

    (HERE / "RUN_METRICS.md").write_text("\n".join(L) + "\n")
    print(f"[metrics] wrote RUN_METRICS.md ({len(out)} runs)")

    if args.check:
        # The lost generator of mirror_stats.json used one 50-generation run per
        # arm. Reproducing its says/built/both counts validates the mirror test
        # reimplemented in measure().
        ref = json.loads((HERE / "onepager_symmetry" / "mirror_stats.json").read_text())
        by_run = {r["run"]: r for r in out}
        ok = True
        print("\n[check] mirror_stats.json reproduction")
        for arm, run in (("weak", "weak_r1"), ("mid", "mid_r1"), ("frontier", "frontier_r1")):
            r, want = by_run[run], ref[arm]
            got = {
                "n": r["n_parseable"],
                "says": r["n_says_mirror"],
                "built": round(r["mirror_rate_built"] / 100 * r["n_parseable"]),
                "both": round((r["build_given_say_mirror"] or 0) / 100 * r["n_says_mirror"]),
            }
            match = all(got[k] == want[k] for k in ("n", "says", "built", "both"))
            ok &= match
            print(f"  {arm:9} {run:12} got {got}  want {want}  {'OK' if match else 'MISMATCH'}")
        print("[check]", "all reproduced" if ok else "MISMATCH -- do not trust the mirror columns")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
