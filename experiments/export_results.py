#!/usr/bin/env python
"""Export every transfer-sn (T2, with-context) run to CSV for replication.

Generated from the run databases, never hand-transcribed, so re-running this
after the in-flight arms finish refreshes the numbers with no manual editing.

Emits three files into --out-dir:

  runs_summary.csv     one row per run: models, best score, when the S_8
                       structure first appeared, cost, termination
  programs_all.csv     one row per evaluated program across all runs, with both
                       raw and rescaled score and the structural metrics
  discovery_events.csv the milestones that matter: first tied structure, each
                       new best, and any loss of tying afterwards

The structural columns are the load-bearing ones. `fully_tied_single_families`
counts single-qubit rotation families sharing ONE angle across all 8 wires,
which is what S_8-orbit tying means; patch names are recorded but must not be
used to judge discovery (an earlier name-based detector reported 48/49 hits
because the metadata blob embeds the model's reasoning text).

Usage: python export_results.py --out-dir <dir> [--task-dir <dir>]
"""
from __future__ import annotations

import argparse
import ast
import csv
import glob
import importlib.util
import json
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

# The analysis tool lives outside the task directory on purpose: it carries the
# answer key, which must never sit where an evolution run could read it.
_TOOL = Path(os.environ.get(
    "SN_TOOLS", os.path.expanduser("~/project/sn_tools"))) / "symmetry_analysis.py"
_spec = importlib.util.spec_from_file_location("symmetry_analysis", _TOOL)
_sym = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sym)
_structural_metrics = _sym.structural_metrics

# Spec extraction must handle programmatically-built specs, not just literals.
# Literal-only reading covered just 24 of 73 correct programs in az-mid-r1 and
# missed its best program entirely, which made the arm look untestable.
_se_path = Path(os.environ.get("SN_EXPORT_TOOLS", os.path.expanduser("~/project"))) / "structural_exec.py"
_se_spec = importlib.util.spec_from_file_location("structural_exec", _se_path)
_se = importlib.util.module_from_spec(_se_spec)
_se_spec.loader.exec_module(_se)
_spec_from_code = _se.spec_from_code

# Affine map used by evaluate.py from 2026-08-06 onward: seed -> 0, best
# symmetric solution -> 1. Runs before that date stored RAW scores, so this is
# applied here to put every run on one axis.
ANCHOR_SEED = 0.8545656310200919
ANCHOR_BEST = 0.9483080295061955
# Was {results_az_*}: the only pre-2026-08-06 runs still exported. Those Azure
# runs are outdated (Azure lacked models the final roster needs) and have been
# dropped, so nothing currently needs rescaling.
RESCALED_FROM: set[str] = set()

RUNS = [
    # dir, label, routing, models, notes
    ("results_gpt56sol_r2", "baseline-sol-solo", "openrouter",
     "openai/gpt-5.6-sol", "solo; reasoning effort NOT set (pricing flag bug)"),
    ("results_haiku_r2", "baseline-haiku-solo", "openrouter",
     "anthropic/claude-haiku-4.5", "solo"),
    ("results_sonnet_r2", "baseline-sonnet-solo", "openrouter",
     "anthropic/claude-sonnet-5", "solo"),
    ("results_ens3_r1", "ens3-openrouter-r1", "openrouter",
     "claude-haiku-4.5 + gemini-3.6-flash + gpt-5.6-luna", "small tier, 3 pipelines"),
    ("results_ens3_r2", "ens3-openrouter-r2", "openrouter",
     "claude-haiku-4.5 + gemini-3.6-flash + gpt-5.6-luna", "replicate of above"),
]


def rescale(raw):
    if raw is None:
        return None
    return (raw - ANCHOR_SEED) / (ANCHOR_BEST - ANCHOR_SEED)


def extract_spec(code):
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
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


def structural(spec):
    """Delegate to the verified metric in symmetry_analysis.py.

    Do NOT reimplement this. A first attempt here counted "gate family uses
    exactly one param name", which is a different quantity from what the tool
    measures -- "a param whose wire set covers all 8 wires" -- and it disagreed
    on real runs: it scored the baseline's generation-33 discovery as untied and
    invented a tied structure for the haiku arm at generation 14.
    """
    if not spec:
        return None
    m = _structural_metrics(spec)
    return {
        "n_unique_params": m["n_unique_params"],
        "fully_tied_single_families": m["fully_tied_single_families"],
        "single_param_counts": json.dumps(m["single_param_counts"], sort_keys=True),
    }


def snapshot(src_db):
    tmp = tempfile.mkdtemp()
    for f in glob.glob(src_db + "*"):
        shutil.copy(f, tmp)
    return os.path.join(tmp, os.path.basename(src_db)), tmp


def load_run(task_dir, run_dir):
    db = os.path.join(task_dir, run_dir, "programs.sqlite")
    if not os.path.exists(db):
        return None
    path, tmp = snapshot(db)
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT generation, combined_score, correct, code, metadata "
            "FROM programs ORDER BY generation"
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error:
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def patch_name(meta):
    if not meta:
        return ""
    try:
        return (json.loads(meta) or {}).get("patch_name", "") or ""
    except (ValueError, TypeError):
        return ""


def run_cost(task_dir, run_dir):
    """Last cumulative API cost the orchestrator logged."""
    log = os.path.join(task_dir, run_dir, "evolution_run.log")
    if not os.path.exists(log):
        return None
    last = None
    import re
    pat = re.compile(r"total: \$([0-9.]+)")
    with open(log, "rb") as fh:
        for line in fh:
            m = pat.search(line.decode("utf-8", "replace"))
            if m:
                last = float(m.group(1))
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-dir", default=os.path.expanduser("~/project/transfer_sn"))
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    prog_rows, summary_rows, event_rows = [], [], []

    for run_dir, label, routing, models, notes in RUNS:
        rows = load_run(a.task_dir, run_dir)
        if rows is None:
            print(f"skip {run_dir} (no database)")
            continue

        stored_rescaled = run_dir in RESCALED_FROM
        best_scaled, best_gen, best_name, best_struct = None, None, "", None
        first_tied_gen, first_tied_score = None, None
        max_gen, n_correct = 0, 0

        for r in rows:
            gen = r["generation"] or 0
            max_gen = max(max_gen, gen)
            raw = r["combined_score"]
            if stored_rescaled:
                scaled = raw
                raw_out = None if raw is None else raw * (ANCHOR_BEST - ANCHOR_SEED) + ANCHOR_SEED
            else:
                raw_out = raw
                scaled = rescale(raw)
            _sp, _how = _spec_from_code(r["code"] or "")
            st = structural(_sp) or {}
            st["spec_extraction"] = _how
            ok = bool(r["correct"])
            n_correct += ok
            nm = patch_name(r["metadata"])

            prog_rows.append({
                "run": label, "run_dir": run_dir, "routing": routing,
                "generation": gen, "correct": int(ok),
                "score_raw": None if raw_out is None else round(raw_out, 6),
                "score_rescaled": None if scaled is None else round(scaled, 4),
                "n_unique_params": st.get("n_unique_params"),
                "fully_tied_single_families": st.get("fully_tied_single_families"),
                "single_param_counts": st.get("single_param_counts"),
                "spec_extraction": st.get("spec_extraction"),
                "patch_name": nm,
            })

            if not ok or scaled is None:
                continue
            tied = st.get("fully_tied_single_families") or 0
            if tied >= 3 and first_tied_gen is None:
                first_tied_gen, first_tied_score = gen, scaled
                event_rows.append({
                    "run": label, "event": "first_S8_tied_structure",
                    "generation": gen, "score_rescaled": round(scaled, 4),
                    "fully_tied_single_families": tied,
                    "n_unique_params": st.get("n_unique_params"), "patch_name": nm,
                })
            if best_scaled is None or scaled > best_scaled:
                best_scaled, best_gen, best_name, best_struct = scaled, gen, nm, st
                event_rows.append({
                    "run": label, "event": "new_best",
                    "generation": gen, "score_rescaled": round(scaled, 4),
                    "fully_tied_single_families": tied,
                    "n_unique_params": st.get("n_unique_params"), "patch_name": nm,
                })

        summary_rows.append({
            "run": label, "run_dir": run_dir, "routing": routing, "models": models,
            "n_programs": len(rows), "n_correct": n_correct, "max_generation": max_gen,
            "best_score_rescaled": None if best_scaled is None else round(best_scaled, 4),
            "best_score_raw": None if best_scaled is None else round(
                best_scaled * (ANCHOR_BEST - ANCHOR_SEED) + ANCHOR_SEED, 6),
            "best_generation": best_gen,
            "best_patch_name": best_name,
            "best_n_unique_params": (best_struct or {}).get("n_unique_params"),
            "best_fully_tied_families": (best_struct or {}).get("fully_tied_single_families"),
            "found_S8_structure": int(first_tied_gen is not None),
            "first_S8_generation": first_tied_gen,
            "first_S8_score_rescaled": None if first_tied_score is None else round(first_tied_score, 4),
            "api_cost_usd": run_cost(a.task_dir, run_dir),
            "notes": notes,
        })
        print(f"exported {label:<22} programs={len(rows):>3} max_gen={max_gen:>3} "
              f"best={best_scaled if best_scaled is None else round(best_scaled,4)} "
              f"first_S8_gen={first_tied_gen}")

    def dump(name, rows, fields):
        p = out / name
        with p.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {p}  ({len(rows)} rows)")

    dump("runs_summary.csv", summary_rows, list(summary_rows[0].keys()))
    dump("programs_all.csv", prog_rows, list(prog_rows[0].keys()))
    dump("discovery_events.csv", event_rows, list(event_rows[0].keys()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
