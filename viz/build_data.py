#!/usr/bin/env python3
"""Build-time compiler: every ShinkaEvolve `programs.sqlite` in this repo ->
static JS data files for a static web viewer (viz/data/manifest.js and
viz/data/run_<slug>.js).

Only the standard library is used for the sqlite-reading / JS-writing parts
of this script. Circuit rendering needs PennyLane + matplotlib, which are not
stdlib; that work is delegated to viz/_render_worker.py, run as a subprocess
under whichever Python interpreter on this machine can `import pennylane`
(see find_render_python()). If none can be found, circuits are shipped with
circuit_svg = circuit_text = null and the summary table says so.

Usage:
    python3 viz/build_data.py [--repo-root .] [--out viz/data]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RENDER_WORKER = SCRIPT_DIR / "_render_worker.py"
RENDER_BATCH_TIMEOUT_BASE = 30   # seconds, + per-item allowance below
RENDER_BATCH_TIMEOUT_PER_ITEM = 5
RENDER_MAX_WORKERS = 4
DB_OPEN_RETRIES = 3
DB_OPEN_RETRY_DELAY = 0.3

TASK_ALIASES = {"tic-tac-toe": "ttt"}
TASK_DISPLAY = {"ttt": "Tic-Tac-Toe", "su2": "SU(2) Transfer", "sn": "S_n Transfer"}


# ---------------------------------------------------------------------------
# DB discovery / loading
# ---------------------------------------------------------------------------

def find_databases(repo_root: Path) -> list[Path]:
    dbs = []
    for p in sorted(repo_root.rglob("programs.sqlite")):
        parts = p.relative_to(repo_root).parts
        if any(part.startswith(".venv") or part == "node_modules" for part in parts):
            continue
        if parts and parts[0] == "viz":
            continue
        dbs.append(p)
    return _dedupe_by_content(dbs, repo_root)


def _dedupe_by_content(dbs: list[Path], repo_root: Path) -> list[Path]:
    # The same run can exist under two paths (e.g. a cluster results dir that
    # was rsynced twice under different names). Keep one copy per content
    # hash, preferring the shortest repo-relative path.
    by_hash: dict[str, Path] = {}
    for p in dbs:
        h = hashlib.md5(p.read_bytes()).hexdigest()
        prev = by_hash.get(h)
        if prev is None:
            by_hash[h] = p
        else:
            keep, drop = sorted([prev, p], key=lambda q: (len(str(q.relative_to(repo_root))), str(q)))
            by_hash[h] = keep
            print(f"[build_data] duplicate db: keeping {keep.relative_to(repo_root)}, "
                  f"skipping {drop.relative_to(repo_root)}")
    return sorted(by_hash.values())


def open_db_readonly(db_path: Path) -> sqlite3.Connection:
    """Open read-only via an absolute file: URI (relative file: URIs have been
    observed to intermittently fail to open on this machine); retry a few
    times, then fall back to a plain read-write connect (we never write)."""
    abs_path = db_path.resolve()
    last_exc: Exception | None = None
    for attempt in range(DB_OPEN_RETRIES):
        try:
            uri = f"file://{abs_path}?mode=ro"
            con = sqlite3.connect(uri, uri=True, timeout=5)
            con.execute("select 1 from programs limit 1")
            return con
        except sqlite3.OperationalError as exc:
            last_exc = exc
            time.sleep(DB_OPEN_RETRY_DELAY)
    try:
        con = sqlite3.connect(str(abs_path), timeout=5)
        con.execute("select 1 from programs limit 1")
        return con
    except sqlite3.OperationalError as exc:
        raise RuntimeError(f"could not open {db_path} after retries: {last_exc} / {exc}") from exc


def count_rows(con: sqlite3.Connection) -> int:
    return con.execute("select count(*) from programs").fetchone()[0]


PROGRAM_COLUMNS = (
    "id, parent_id, generation, timestamp, code_diff, combined_score, "
    "public_metrics, text_feedback, complexity, correct, children_count, "
    "metadata, island_idx, code"
)


def load_programs(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        f"SELECT {PROGRAM_COLUMNS} FROM programs ORDER BY generation ASC, timestamp ASC"
    ).fetchall()
    out = []
    for (id_, parent_id, generation, timestamp, code_diff, combined_score,
         public_metrics_raw, text_feedback, complexity, correct,
         children_count, metadata_raw, island_idx, code) in rows:
        meta = _parse_json(metadata_raw, {})
        if not isinstance(meta, dict):
            meta = {}
        public_metrics = _parse_json(public_metrics_raw, {})
        if not isinstance(public_metrics, dict):
            public_metrics = {}
        out.append({
            "id": id_,
            "parent_id": parent_id,
            "generation": int(generation) if generation is not None else None,
            "island_idx": int(island_idx) if island_idx is not None else None,
            "combined_score": float(combined_score) if combined_score is not None else None,
            "correct": bool(correct),
            "children_count": int(children_count) if children_count is not None else 0,
            "timestamp": float(timestamp) if timestamp is not None else None,
            "complexity": float(complexity) if complexity is not None else None,
            "patch_name": meta.get("patch_name"),
            "patch_description": meta.get("patch_description"),
            "patch_type": meta.get("patch_type"),
            "model_name": meta.get("model_name"),
            "text_feedback": text_feedback,
            "public_metrics": public_metrics,
            "code_diff": code_diff,
            "code": code,
            "circuit_svg": None,
            "circuit_text": None,
        })
    return out


def _parse_json(raw, fallback):
    if not raw:
        return fallback
    if not isinstance(raw, str):
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


# ---------------------------------------------------------------------------
# task / variant / model / slug derivation (path-segment driven, no hardcoded
# per-run tables -- new zc-*/results_* and transfer-sn/ dirs are picked up
# automatically)
# ---------------------------------------------------------------------------

def _norm_token(seg: str) -> str:
    """Strip filler words like 'result(s)' and collapse separators to '-'."""
    s = re.sub(r"results?", "", seg, flags=re.IGNORECASE)
    s = re.sub(r"[_\-]+", "-", s).strip("-")
    return s


def _norm_model_token(rundir: str, task: str) -> str:
    s = rundir
    s = re.sub(r"^results[_-]?", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^ea[_-]", "", s, flags=re.IGNORECASE)
    s = re.sub(r"[_-]?result$", "", s, flags=re.IGNORECASE)
    s = re.sub(rf"^{re.escape(task)}_qml_", "", s, flags=re.IGNORECASE)
    s = s.strip("_-")
    return s or rundir


def _normalize_for_compare(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def derive_identity(rel_dir_parts: tuple[str, ...], programs: list[dict]) -> dict:
    first = rel_dir_parts[0]
    if first in TASK_ALIASES:
        task = TASK_ALIASES[first]
        group_prefix = None
    elif "-" in first:
        group_prefix, task = first.split("-", 1)
    else:
        task = first
        group_prefix = None

    mid_segments = rel_dir_parts[1:-1]
    rundir = rel_dir_parts[-1]

    mid_parts = [p for p in (_norm_token(s) for s in mid_segments) if p]
    variant_parts = ([group_prefix] if group_prefix else []) + mid_parts
    variant = "-".join(variant_parts) if variant_parts else "local"

    model_slug = _norm_model_token(rundir, task)
    # a rerun suffix like "_r2" is part of the run identity (kept in the slug)
    # but not part of the model name
    model_base = re.sub(r"[_-]r\d+$", "", model_slug)

    distinct_models = sorted({
        p["model_name"] for p in programs if p.get("model_name")
    })
    metadata_last_segments = {_normalize_for_compare(m.rsplit("/", 1)[-1]) for m in distinct_models}
    model_base_norm = _normalize_for_compare(model_base)

    if model_base_norm and (
        model_base_norm in metadata_last_segments
        or any(model_base_norm in seg or seg in model_base_norm for seg in metadata_last_segments)
    ):
        model = model_base
    elif len(distinct_models) == 1:
        model = distinct_models[0].rsplit("/", 1)[-1]
    elif len(distinct_models) == 0:
        model = model_base
    else:
        model = "mixed/unknown"

    slug_raw = f"{task}-{variant}-{model_slug}".lower()
    slug = re.sub(r"[^a-z0-9_-]", "-", slug_raw)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")

    task_display = TASK_DISPLAY.get(task, task.upper())
    variant_display = variant.replace("-", " ").title()
    label = f"{task_display} · {variant_display} · {model}"

    return {"task": task, "variant": variant, "model": model, "slug": slug, "label": label}


# ---------------------------------------------------------------------------
# Rendering (delegated to a PennyLane-capable interpreter, via subprocess)
# ---------------------------------------------------------------------------

def find_render_python(repo_root: Path) -> Path | None:
    candidates = [
        SCRIPT_DIR / ".venv_render" / "bin" / "python3",
        repo_root / "tic-tac-toe" / ".venv-shinka-ttt" / "bin" / "python3",
        Path(sys.executable),
    ]
    for py in candidates:
        if not py.exists():
            continue
        try:
            r = subprocess.run(
                [str(py), "-c", "import pennylane, matplotlib"],
                capture_output=True, timeout=15,
            )
        except Exception:
            continue
        if r.returncode == 0:
            return py
    return None


def needs_render(prog: dict) -> bool:
    return bool(prog["correct"]) or prog["generation"] == 0


def render_run(render_py: Path, run_slug: str, programs: list[dict]) -> Counter:
    """Mutates `programs` in place with circuit_svg/circuit_text; returns a
    Counter of outcome -> count for this run."""
    stats = Counter()
    targets = [p for p in programs if needs_render(p)]
    stats["skipped_incorrect"] = len(programs) - len(targets)
    if not targets:
        return stats

    items = [{"id": p["id"], "code": p["code"]} for p in targets]
    timeout = RENDER_BATCH_TIMEOUT_BASE + RENDER_BATCH_TIMEOUT_PER_ITEM * len(items)
    try:
        proc = subprocess.run(
            [str(render_py), str(RENDER_WORKER)],
            input=json.dumps({"items": items}).encode("utf-8"),
            capture_output=True, timeout=timeout,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"worker exited {proc.returncode}: {proc.stderr.decode('utf-8', 'replace')[-2000:]}"
            )
        payload = json.loads(proc.stdout.decode("utf-8"))
        results = payload["results"]
    except Exception as exc:
        stats["batch_failed"] = len(targets)
        stats["batch_error_example"] = f"{type(exc).__name__}: {exc}"
        for p in targets:
            p["circuit_svg"] = None
            p["circuit_text"] = None
        return stats

    by_id = {p["id"]: p for p in targets}
    for pid, res in results.items():
        p = by_id.get(pid)
        if p is None:
            continue
        p["circuit_svg"] = res.get("circuit_svg")
        p["circuit_text"] = res.get("circuit_text")
        if res.get("circuit_svg"):
            stats["svg_ok"] += 1
        elif res.get("circuit_text"):
            stats["text_fallback"] += 1
        else:
            stats["failed"] += 1
    stats["failed_example_msg"] = _first_error_message(results)
    return stats


def _first_error_message(results: dict) -> str:
    for res in results.values():
        if not res.get("circuit_svg") and not res.get("circuit_text") and res.get("error"):
            return res["error"]
    return ""


# ---------------------------------------------------------------------------
# JS output
# ---------------------------------------------------------------------------

def write_run_js(out_dir: Path, slug: str, programs: list[dict]) -> Path:
    path = out_dir / f"run_{slug}.js"
    payload = {"run_id": slug, "programs": programs}
    with path.open("w", encoding="utf-8") as f:
        f.write("window.VIZ_RUNS = window.VIZ_RUNS || {};\n")
        f.write(f"window.VIZ_RUNS[{json.dumps(slug)}] = ")
        json.dump(payload, f, ensure_ascii=False)
        f.write(";\n")
    return path


def write_manifest_js(out_dir: Path, runs: list[dict]) -> Path:
    path = out_dir / "manifest.js"
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runs": runs,
    }
    with path.open("w", encoding="utf-8") as f:
        f.write("window.VIZ_MANIFEST = ")
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write(";\n")
    return path


def best_program(programs: list[dict]) -> tuple[float | None, str | None]:
    correct = [p for p in programs if p["correct"] and p["combined_score"] is not None]
    pool = correct or [p for p in programs if p["combined_score"] is not None]
    if not pool:
        return None, None
    best = max(pool, key=lambda p: p["combined_score"])
    return best["combined_score"], best["id"]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--out", default="viz/data")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    render_py = find_render_python(repo_root)
    if render_py:
        print(f"[build_data] rendering with: {render_py}")
    else:
        print("[build_data] WARNING: no Python with `import pennylane` found; "
              "all circuit_svg/circuit_text will be null.")

    db_paths = find_databases(repo_root)
    print(f"[build_data] found {len(db_paths)} programs.sqlite under {repo_root}")

    runs_summary = []
    manifest_runs = []
    used_slugs: dict[str, int] = {}

    render_jobs = []  # (slug, programs) pairs still needing rendering
    run_records = []  # (identity, programs, db_path) after skip/empty filtering

    for db_path in db_paths:
        rel = db_path.parent.relative_to(repo_root)
        try:
            con = open_db_readonly(db_path)
        except Exception as exc:
            print(f"[build_data] SKIP (unopenable): {rel} :: {exc}")
            continue
        try:
            n = count_rows(con)
            if n == 0:
                con.close()
                continue
            programs = load_programs(con)
        finally:
            con.close()

        identity = derive_identity(rel.parts, programs)
        slug = identity["slug"]
        if slug in used_slugs:
            used_slugs[slug] += 1
            slug = f"{slug}-{used_slugs[slug]}"
            identity = {**identity, "slug": slug}
        else:
            used_slugs[slug] = 1

        run_records.append((identity, programs, db_path, rel))

    if render_py:
        with ThreadPoolExecutor(max_workers=RENDER_MAX_WORKERS) as pool:
            futures = {
                pool.submit(render_run, render_py, identity["slug"], programs): identity["slug"]
                for identity, programs, _, _ in run_records
            }
            render_stats_by_slug = {}
            for fut in as_completed(futures):
                slug = futures[fut]
                render_stats_by_slug[slug] = fut.result()
    else:
        render_stats_by_slug = {identity["slug"]: Counter(skipped_incorrect=len(programs))
                                 for identity, programs, _, _ in run_records}

    for identity, programs, db_path, rel in run_records:
        slug = identity["slug"]
        stats = render_stats_by_slug.get(slug, Counter())

        write_run_js(out_dir, slug, programs)

        max_gen = max((p["generation"] for p in programs if p["generation"] is not None), default=None)
        score, best_id = best_program(programs)
        manifest_runs.append({
            "id": slug,
            "task": identity["task"],
            "variant": identity["variant"],
            "model": identity["model"],
            "label": identity["label"],
            "db_path": str(rel / "programs.sqlite"),
            "n_programs": len(programs),
            "max_generation": max_gen,
            "best_score": score,
            "best_program_id": best_id,
        })
        runs_summary.append({
            "slug": slug,
            "db": str(rel),
            "n": len(programs),
            "svg_ok": stats.get("svg_ok", 0),
            "text_fallback": stats.get("text_fallback", 0),
            "failed": stats.get("failed", 0) + stats.get("batch_failed", 0),
            "skipped": stats.get("skipped_incorrect", 0),
            "error_example": stats.get("failed_example_msg") or stats.get("batch_error_example", ""),
        })

    manifest_runs.sort(key=lambda r: (r["task"], r["variant"], r["model"]))
    write_manifest_js(out_dir, manifest_runs)

    # ---- summary table ----
    print()
    header = f'{"run":45} {"n":>5} {"svg_ok":>7} {"text_fb":>8} {"failed":>7} {"skipped":>8}'
    print(header)
    print("-" * len(header))
    for r in sorted(runs_summary, key=lambda r: r["slug"]):
        print(f'{r["slug"]:45} {r["n"]:>5} {r["svg_ok"]:>7} {r["text_fallback"]:>8} '
              f'{r["failed"]:>7} {r["skipped"]:>8}')
    print()
    for r in runs_summary:
        if r["failed"] and r["error_example"]:
            print(f'[build_data] {r["slug"]}: failure example: {r["error_example"][:300]}')

    total_svg = sum(r["svg_ok"] for r in runs_summary)
    total_text = sum(r["text_fallback"] for r in runs_summary)
    total_failed = sum(r["failed"] for r in runs_summary)
    total_programs = sum(r["n"] for r in runs_summary)
    print(f"\n[build_data] {len(runs_summary)} runs, {total_programs} programs total; "
          f"svg_ok={total_svg} text_fallback={total_text} failed={total_failed}")
    print(f"[build_data] wrote manifest + {len(runs_summary)} run files to {out_dir}")


if __name__ == "__main__":
    main()
