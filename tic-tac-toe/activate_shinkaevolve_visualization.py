#!/usr/bin/env python3
"""Launch the ShinkaEvolve web UI on the newest local results database."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import socket
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PORT = 8000
RESULT_TIMESTAMP_RE = re.compile(r"_(\d{8}_\d{6})(?:$|[/\\])")
SHINKA_DB_NAMES = {"programs.sqlite", "programs.db"}


@dataclass(frozen=True)
class DatabaseSummary:
    path: Path
    program_count: int
    max_generation: int | None


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def timestamp_key(db_path: Path) -> tuple[int, float]:
    """Prefer Shinka run timestamps, then fall back to file mtime."""
    match = RESULT_TIMESTAMP_RE.search(str(db_path))
    if match:
        return int(match.group(1).replace("_", "")), db_path.stat().st_mtime
    return 0, db_path.stat().st_mtime


def find_latest_database(results_root: Path) -> Path:
    candidates = [
        path
        for path in results_root.rglob("*")
        if path.is_file() and path.name in SHINKA_DB_NAMES
    ]
    if not candidates:
        raise FileNotFoundError(
            f"No Shinka program database found under {results_root}"
        )
    return max(candidates, key=timestamp_key)


def summarize_database(db_path: Path) -> DatabaseSummary:
    uri = f"file:{db_path}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            if "programs" not in tables:
                raise ValueError(f"{db_path} is missing the 'programs' table")

            program_count = int(
                conn.execute("SELECT COUNT(*) FROM programs").fetchone()[0]
            )
            max_generation = conn.execute(
                "SELECT MAX(generation) FROM programs"
            ).fetchone()[0]
            if max_generation is not None:
                max_generation = int(max_generation)
    except sqlite3.Error as exc:
        raise ValueError(f"Could not read Shinka database {db_path}: {exc}") from exc

    return DatabaseSummary(
        path=db_path,
        program_count=program_count,
        max_generation=max_generation,
    )


def find_shinka_visualize(repo: Path) -> Path:
    local_entrypoint = repo / ".venv-shinka-ttt" / "bin" / "shinka_visualize"
    if local_entrypoint.exists():
        return local_entrypoint

    resolved = shutil.which("shinka_visualize")
    if resolved:
        return Path(resolved)

    raise FileNotFoundError(
        "Could not find shinka_visualize. Expected "
        f"{local_entrypoint} or a shinka_visualize command on PATH."
    )


def port_is_available(port: int) -> bool | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("", port))
    except PermissionError:
        return None
    except OSError:
        return False
    return True


def choose_port(preferred_port: int, strict: bool) -> int:
    preferred_available = port_is_available(preferred_port)
    if preferred_available is True:
        return preferred_port
    if preferred_available is None:
        print(
            "Port availability check is not permitted in this environment; "
            f"using requested port {preferred_port}.",
            file=sys.stderr,
        )
        return preferred_port

    if strict:
        raise OSError(f"Port {preferred_port} is already in use")

    for port in range(preferred_port + 1, preferred_port + 100):
        if port_is_available(port):
            return port

    raise OSError(
        f"No available port found in range {preferred_port}-{preferred_port + 99}"
    )


def relative_to_repo(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo).as_posix()
    except ValueError:
        return str(path.resolve())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve the newest ShinkaEvolve results in the web UI."
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=repo_root() / "results",
        help="Directory to scan for Shinka results databases.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Specific programs.sqlite/programs.db to serve instead of auto-detecting.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("SHINKA_VIS_PORT", DEFAULT_PORT)),
        help=f"Preferred port for the web UI. Defaults to {DEFAULT_PORT}.",
    )
    parser.add_argument(
        "--strict-port",
        action="store_true",
        help="Fail instead of selecting the next free port when --port is busy.",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Ask ShinkaEvolve to open the visualization in a browser.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected database, URL, and command without starting the server.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = repo_root()
    results_root = args.results_root.expanduser().resolve()

    db_path = (
        args.db.expanduser().resolve()
        if args.db
        else find_latest_database(results_root)
    )
    summary = summarize_database(db_path)
    visualize = find_shinka_visualize(repo)
    port = choose_port(args.port, args.strict_port)
    db_arg = relative_to_repo(summary.path, repo)
    url = f"http://localhost:{port}/viz_tree.html?db_path={db_arg}"

    if port != args.port:
        print(f"Port {args.port} is busy; using {port}.")

    print(f"Selected database: {db_arg}")
    print(f"Programs: {summary.program_count}")
    print(f"Max generation: {summary.max_generation}")
    print(f"URL: {url}")

    command = [
        str(visualize),
        str(repo),
        "--db",
        db_arg,
        "--port",
        str(port),
    ]
    if args.open:
        command.append("--open")

    print("Command: " + " ".join(command))

    if args.dry_run:
        return 0

    venv_dir = repo / ".venv-shinka-ttt"
    if venv_dir.exists():
        os.environ["VIRTUAL_ENV"] = str(venv_dir)
        os.environ["PATH"] = (
            str(venv_dir / "bin") + os.pathsep + os.environ.get("PATH", "")
        )

    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(command[0], command)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
