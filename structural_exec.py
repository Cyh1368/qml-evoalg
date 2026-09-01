#!/usr/bin/env python
"""Structural S_8 verdicts that also cover programmatically-built ANSATZ_SPECs.

symmetry_analysis.extract_spec uses ast.literal_eval, so it only sees specs
written as a literal list. Measured coverage on the finished arms:

    az-frontier-r1   72/78 correct programs parseable
    az-weak-r1       63/64 parseable
    az-mid-r1        24/73 parseable   <-- including its best program

The mid arm's lineage builds the spec with loops and comprehensions, so a
literal-only reader gives it no verdict at all and silently reports an older,
worse generation as "final best". This module executes the candidate module in
an isolated namespace and reads the resulting ANSATZ_SPEC object, then applies
the SAME verified structural_metrics function.

Executing evolved code is acceptable here: it is our own code, on our own
cluster, and the evaluator already runs it. __name__ is set to a non-__main__
value so any main-guard training block stays dormant.
"""
from __future__ import annotations

import argparse
import ast
import glob
import importlib.util
import json
import multiprocessing as mp
import os
import shutil
import sqlite3
import tempfile

_TOOL = os.path.join(
    os.environ.get("SN_TOOLS", os.path.expanduser("~/project/sn_tools")),
    "symmetry_analysis.py",
)
_spec = importlib.util.spec_from_file_location("symmetry_analysis", _TOOL)
_sym = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sym)
structural_metrics = _sym.structural_metrics


def _exec_worker(code, q):
    try:
        ns = {"__name__": "_candidate_probe"}
        exec(compile(code, "<candidate>", "exec"), ns)
        spec = ns.get("ANSATZ_SPEC")
        if spec is None:
            q.put(("none", None))
            return
        # Keep only plain data so it survives pickling back to the parent.
        clean = [dict(item) for item in spec]
        q.put(("ok", clean))
    except Exception as e:  # noqa: BLE001 - any failure just means "no verdict"
        q.put(("err", f"{type(e).__name__}: {e}"[:160]))


def _module_constants(tree):
    """Module-level names bound to plain literals, e.g. N_QUBITS = 8.

    Enough to evaluate a spec written as a comprehension over N_QUBITS without
    executing the module (whose imports of _backend/pennylane fail outside the
    task directory, which is why whole-module exec returned an error for all 49
    non-literal programs in the mid arm).
    """
    consts = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if isinstance(tgt, ast.Name):
                try:
                    consts[tgt.id] = ast.literal_eval(node.value)
                except (ValueError, SyntaxError):
                    pass
    return consts


def spec_from_code(code, timeout=90):
    """literal -> expression-eval with module constants -> full exec."""
    tree = None
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return None, "unparseable"

    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "ANSATZ_SPEC":
                    target = node.value

    if target is not None:
        try:
            return ast.literal_eval(target), "literal"
        except (ValueError, SyntaxError):
            pass
        # Comprehensions and concatenations: evaluate the expression alone,
        # with the module's literal constants in scope. No imports involved.
        try:
            ns = _module_constants(tree)
            ns.setdefault("N_QUBITS", 8)
            spec = eval(  # noqa: S307 - our own evolved code, expression only
                compile(ast.Expression(target), "<ansatz_spec>", "eval"),
                {"__builtins__": {"range": range, "len": len, "list": list,
                                  "int": int, "str": str, "sorted": sorted,
                                  "enumerate": enumerate, "zip": zip, "min": min,
                                  "max": max, "abs": abs, "sum": sum}},
                ns,
            )
            if spec is not None:
                return [dict(i) for i in spec], "expr"
        except Exception:  # noqa: BLE001 - fall through to full exec
            pass

    q = mp.Queue()
    p = mp.Process(target=_exec_worker, args=(code, q))
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        return None, "timeout"
    try:
        status, payload = q.get_nowait()
    except Exception:
        return None, "no-result"
    return (payload, "exec") if status == "ok" else (None, status)


def analyse(task_dir, run_dir):
    src = os.path.join(task_dir, run_dir, "programs.sqlite")
    tmp = tempfile.mkdtemp()
    try:
        for f in glob.glob(src + "*"):
            shutil.copy(f, tmp)
        conn = sqlite3.connect(os.path.join(tmp, "programs.sqlite"))
        rows = conn.execute(
            "SELECT generation, combined_score, code, correct, metadata "
            "FROM programs ORDER BY generation"
        ).fetchall()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    best, lineage, how = None, [], {}
    for gen, score, code, correct, meta in rows:
        if not correct or score is None:
            continue
        spec, method = spec_from_code(code or "")
        how[method] = how.get(method, 0) + 1
        if spec is None:
            continue
        m = structural_metrics(spec)
        name = ""
        if meta:
            try:
                name = (json.loads(meta) or {}).get("patch_name", "") or ""
            except (ValueError, TypeError):
                name = ""
        rec = (gen, score, m["n_unique_params"], m["fully_tied_single_families"], name, method)
        if best is None or score > best[1]:
            best = rec
            lineage.append(rec)
    return best, lineage, how


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-dir", default=os.path.expanduser("~/project/transfer_sn"))
    ap.add_argument("runs", nargs="+")
    a = ap.parse_args()
    for run in a.runs:
        best, lineage, how = analyse(a.task_dir, run)
        print(f"\n########## {run} ##########")
        print(f"extraction: {how}")
        print(f"{'gen':>5} {'score':>8} {'params':>7} {'tied':>5}  method    patch")
        for gen, score, params, tied, name, method in lineage:
            print(f"{gen:>5} {score:>8.4f} {params:>7} {tied:>5}  {method:<9} {name}")
        if best:
            gen, score, params, tied, name, method = best
            verdict = "EQUIVARIANT" if tied >= 3 else "not tied"
            print(f"  -> best gen {gen}, score {score:.4f}, {params} params, "
                  f"{tied} tied families [{method}] = {verdict}   {name}")


if __name__ == "__main__":
    raise SystemExit(main())
