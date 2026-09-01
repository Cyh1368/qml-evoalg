#!/usr/bin/env python3
"""Add archive_inspiration_ids / top_k_inspiration_ids to already-built run files.

build_data.py now reads these columns, but a full rebuild also re-renders every
circuit SVG through PennyLane, which is slow. This backfills just the two new
fields into viz/data/run_*.js in place, leaving everything else byte-identical.

Runs are matched to their source DB by program-id set, not by slug, so a renamed
run directory can't silently pair a run with the wrong database.

    python3 viz/backfill_inspirations.py [--repo-root .] [--data viz/data]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

PREFIX_RE = re.compile(r"^window\.VIZ_RUNS\[(?P<slug>.+?)\] = ", re.MULTILINE)


def parse_run_js(path: Path) -> tuple[str, dict]:
    text = path.read_text(encoding="utf-8")
    m = PREFIX_RE.search(text)
    if not m:
        raise ValueError(f"{path.name}: no window.VIZ_RUNS[...] assignment found")
    slug = json.loads(m.group("slug"))
    payload = json.loads(text[m.end():].rstrip().rstrip(";"))
    return slug, payload


def write_run_js(path: Path, slug: str, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write("window.VIZ_RUNS = window.VIZ_RUNS || {};\n")
        f.write(f"window.VIZ_RUNS[{json.dumps(slug)}] = ")
        json.dump(payload, f, ensure_ascii=False)
        f.write(";\n")


def db_index(repo_root: Path) -> list[tuple[Path, frozenset[str], dict]]:
    """(db path, its program-id set, {id: (archive_ids, top_k_ids)}) for every run db."""
    out = []
    for db in sorted(repo_root.rglob("programs.sqlite")):
        try:
            con = sqlite3.connect(f"file://{db.resolve()}?mode=ro", uri=True, timeout=5)
            rows = con.execute(
                "select id, archive_inspiration_ids, top_k_inspiration_ids from programs"
            ).fetchall()
        except sqlite3.Error as exc:
            print(f"  skip unreadable {db}: {exc}")
            continue
        finally:
            try:
                con.close()
            except Exception:
                pass
        ids = frozenset(r[0] for r in rows)
        table = {r[0]: (_ids(r[1]), _ids(r[2])) for r in rows}
        if ids:
            out.append((db, ids, table))
    return out


def _ids(raw) -> list[str]:
    if not raw:
        return []
    try:
        val = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        return []
    return [str(x) for x in val if x] if isinstance(val, list) else []


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--data", default="viz/data")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    data_dir = Path(args.data).resolve()

    dbs = db_index(repo_root)
    print(f"indexed {len(dbs)} databases under {repo_root}")

    total_updated = total_with = 0
    for js in sorted(data_dir.glob("run_*.js")):
        slug, payload = parse_run_js(js)
        programs = payload.get("programs", [])
        run_ids = frozenset(p["id"] for p in programs)

        matches = [(db, tbl) for db, ids, tbl in dbs if run_ids and run_ids <= ids]
        if not matches:
            print(f"  {slug}: NO MATCHING DB — left unchanged")
            continue
        if len(matches) > 1:
            # prefer the db whose id set matches exactly
            exact = [m for m in matches if len(m[1]) == len(run_ids)] or matches
            # several run dirs are duplicate copies of the same run; that is only
            # a problem if they disagree about the ids we are about to write
            answers = {
                json.dumps({i: tbl.get(i, ([], [])) for i in sorted(run_ids)}, sort_keys=True)
                for _, tbl in exact
            }
            if len(answers) != 1:
                print(f"  {slug}: {len(exact)} candidate dbs disagree — left unchanged")
                continue
            matches = exact
        db, table = matches[0]

        n_with = 0
        for p in programs:
            arch, topk = table.get(p["id"], ([], []))
            p["archive_inspiration_ids"] = arch
            p["top_k_inspiration_ids"] = topk
            if arch or topk:
                n_with += 1
        write_run_js(js, slug, payload)
        total_updated += 1
        total_with += n_with
        print(f"  {slug}: {n_with}/{len(programs)} programs have inspirations  <- {db.parent.name}")

    print(f"\nupdated {total_updated} run files, {total_with} programs carry inspiration ids")


if __name__ == "__main__":
    main()
