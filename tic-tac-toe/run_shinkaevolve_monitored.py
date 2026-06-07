#!/usr/bin/env python3
"""Extract notebook code, run ShinkaEvolve, and terminate stale runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import re
import shlex
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_NOTEBOOK = "tic_tac_toe_shinkaevolve_ansatz_search.ipynb"
DEFAULT_TASK_DIR = "shinka_cli_task"
DEFAULT_GENERATIONS = 20
DEFAULT_STALE_SECONDS = 30 * 60
DEFAULT_POLL_SECONDS = 10
DEFAULT_EVAL_PRESET = "quick"


WRITEFILE_RE = re.compile(r"^%%writefile\s+(?P<target>\S+)\s*$")
COMPLETED_RE = re.compile(r"Completed generations updated:\s*(\d+)\s*->\s*(\d+)")

COMMON_EVAL_ENV = {
    "PYTHONUNBUFFERED": "1",
    "PYTHONIOENCODING": "utf-8",
    "MPLCONFIGDIR": "/tmp/matplotlib-shinka-ttt",
    "NUM_WORKERS": "1",
    "SAMPLE_WITH_REPLACEMENT": "1",
    "USE_TEST_IN_SCORE": "0",
    "TTT_LOG_DIR": "logs/ttt_training",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}

EVAL_PRESETS = {
    "smoke": {
        "NUM_RUNS": "1",
        "TRAIN_SIZE": "30",
        "VALIDATION_SIZE": "30",
        "TEST_SIZE": "30",
        "N_EPOCHS": "1",
        "STEPS_PER_EPOCH": "1",
        "BATCH_SIZE": "5",
        "LEARNING_RATE": "0.03",
        "CONVERGENCE_THRESHOLD": "0.90",
        "EVAL_EVERY_EPOCHS": "1",
        "VERBOSE_TRAINING": "0",
    },
    "quick": {
        "NUM_RUNS": "1",
        "TRAIN_SIZE": "60",
        "VALIDATION_SIZE": "45",
        "TEST_SIZE": "60",
        "N_EPOCHS": "3",
        "STEPS_PER_EPOCH": "3",
        "BATCH_SIZE": "10",
        "LEARNING_RATE": "0.03",
        "CONVERGENCE_THRESHOLD": "0.90",
        "EVAL_EVERY_EPOCHS": "1",
        "VERBOSE_TRAINING": "1",
    },
    "full": {
        "NUM_RUNS": "2",
        "TRAIN_SIZE": "450",
        "VALIDATION_SIZE": "300",
        "TEST_SIZE": "600",
        "N_EPOCHS": "100",
        "STEPS_PER_EPOCH": "30",
        "BATCH_SIZE": "15",
        "LEARNING_RATE": "0.03",
        "CONVERGENCE_THRESHOLD": "0.90",
        "EVAL_EVERY_EPOCHS": "1",
        "VERBOSE_TRAINING": "1",
    },
}


@dataclass
class ExtractedFile:
    notebook_target: str
    output_path: str
    sha256: str
    bytes: int


@dataclass
class ProgressSnapshot:
    program_count: int = 0
    max_generation: int | None = None
    max_score: float | None = None
    correct_count: int = 0
    result_mtime: float | None = None
    parsed_completed_generations: int | None = None


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_notebook(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Notebook is not valid JSON: {path}") from exc


def iter_writefile_cells(notebook: dict[str, Any]) -> dict[str, str]:
    extracted: dict[str, str] = {}
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        lines = source.splitlines()
        if not lines:
            continue
        match = WRITEFILE_RE.match(lines[0].strip())
        if not match:
            continue
        target = match.group("target")
        body = "\n".join(lines[1:]) + "\n"
        extracted[target] = body
    return extracted


def extract_task_files(notebook_path: Path, task_dir: Path) -> list[ExtractedFile]:
    notebook = load_notebook(notebook_path)
    writefiles = iter_writefile_cells(notebook)

    required = ("initial_program.py", "evaluate.py")
    missing = [target for target in required if target not in writefiles]
    if missing:
        raise FileNotFoundError(
            "Notebook is missing required %%writefile cells: " + ", ".join(missing)
        )

    task_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "initial_program.py": task_dir / "initial.py",
        "evaluate.py": task_dir / "evaluate.py",
    }

    extracted_files: list[ExtractedFile] = []
    for notebook_target, output_path in outputs.items():
        text = writefiles[notebook_target]
        output_path.write_text(text, encoding="utf-8")
        extracted_files.append(
            ExtractedFile(
                notebook_target=notebook_target,
                output_path=str(output_path),
                sha256=sha256_text(text),
                bytes=len(text.encode("utf-8")),
            )
        )

    return extracted_files


def extract_task_prompt(notebook_path: Path) -> str:
    notebook = load_notebook(notebook_path)
    marker = 'TASK_SYS_MSG = """'
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        if marker not in source:
            continue
        start = source.find(marker)
        if start != -1:
            start += len(marker)
            end = source.find('"""', start)
            if end != -1:
                return source[start:end]

    raise ValueError(f"Could not extract TASK_SYS_MSG from {notebook_path}")


def eval_settings_for_preset(preset: str) -> dict[str, str]:
    if preset not in EVAL_PRESETS:
        raise ValueError(
            f"Unknown eval preset {preset!r}. "
            f"Expected one of: {', '.join(sorted(EVAL_PRESETS))}"
        )
    return {**COMMON_EVAL_ENV, **EVAL_PRESETS[preset]}


def apply_eval_cli_overrides(
    eval_settings: dict[str, str],
    args: argparse.Namespace,
) -> dict[str, str]:
    overrides: dict[str, object | None] = {
        "NUM_RUNS": args.num_runs,
        "NUM_WORKERS": args.num_workers,
        "BASE_SEED": args.base_seed,
        "DATA_SEED": args.data_seed,
        "TRAIN_SIZE": args.train_size,
        "VALIDATION_SIZE": args.validation_size,
        "TEST_SIZE": args.test_size,
        "N_EPOCHS": args.n_epochs,
        "STEPS_PER_EPOCH": args.steps_per_epoch,
        "BATCH_SIZE": args.batch_size,
        "LEARNING_RATE": args.learning_rate,
        "CONVERGENCE_THRESHOLD": args.convergence_threshold,
        "EVAL_EVERY_EPOCHS": args.eval_every_epochs,
        "MAX_PARAMS": args.max_params,
        "TTT_LOG_DIR": args.ttt_log_dir,
    }
    bool_overrides = {
        "SAMPLE_WITH_REPLACEMENT": args.sample_with_replacement,
        "USE_TEST_IN_SCORE": args.use_test_in_score,
        "VERBOSE_TRAINING": args.verbose_training,
    }

    updated = dict(eval_settings)
    for key, value in overrides.items():
        if value is not None:
            updated[key] = str(value)
    for key, value in bool_overrides.items():
        if value is not None:
            updated[key] = "1" if value else "0"
    return updated


def validate_eval_settings(eval_settings: dict[str, str]) -> None:
    positive_int_keys = (
        "NUM_RUNS",
        "NUM_WORKERS",
        "TRAIN_SIZE",
        "VALIDATION_SIZE",
        "TEST_SIZE",
        "N_EPOCHS",
        "STEPS_PER_EPOCH",
        "BATCH_SIZE",
        "EVAL_EVERY_EPOCHS",
        "MAX_PARAMS",
    )
    for key in positive_int_keys:
        if key in eval_settings and int(eval_settings[key]) <= 0:
            raise ValueError(f"{key} must be > 0")
    for key in ("LEARNING_RATE", "CONVERGENCE_THRESHOLD"):
        if key in eval_settings and float(eval_settings[key]) <= 0:
            raise ValueError(f"{key} must be > 0")


def write_eval_activate_script(
    *,
    task_dir: Path,
    venv_activate_script: Path,
    eval_settings: dict[str, str],
) -> Path:
    """Create an activation wrapper sourced by Shinka evaluator jobs."""
    task_dir.mkdir(parents=True, exist_ok=True)
    wrapper_path = task_dir / "activate_eval_env.sh"
    lines = [
        "#!/usr/bin/env bash\n",
        "set -e\n",
        f"source {shlex.quote(str(venv_activate_script))}\n",
    ]
    for key in sorted(eval_settings):
        value = eval_settings[key]
        lines.append(f'export {key}="${{{key}:-{value}}}"\n')

    wrapper_path.write_text("".join(lines), encoding="utf-8")
    wrapper_path.chmod(0o755)
    return wrapper_path


def write_shinka_config(
    *,
    notebook_path: Path,
    task_dir: Path,
    activate_script: Path,
    max_api_costs: float,
) -> Path:
    task_sys_msg = extract_task_prompt(notebook_path)
    config = {
        "evo": {
            "task_sys_msg": task_sys_msg,
            "patch_types": ["diff", "full", "cross"],
            "patch_type_probs": [0.65, 0.25, 0.10],
            "max_patch_resamples": 3,
            "max_patch_attempts": 2,
            "llm_models": [
                "openrouter/anthropic/claude-haiku-4-5",
                "openrouter/openai/gpt-5-nano",
            ],
            "llm_kwargs": {
                "temperatures": [0.0, 0.5, 1.0],
                "max_tokens": 16384,
            },
            "llm_dynamic_selection": "ucb1",
            "llm_dynamic_selection_kwargs": {
                "exploration_coef": 1.0,
                "cost_aware_coef": 0.7,
            },
            "meta_rec_interval": 5,
            "meta_llm_models": ["openrouter/openai/o4-mini"],
            "meta_llm_kwargs": {"temperatures": [0.0], "max_tokens": 8192},
            "embedding_model": "openrouter/openai/text-embedding-3-small",
            "max_novelty_attempts": 2,
            "code_embed_sim_threshold": 0.99,
            "novelty_llm_models": ["openrouter/openai/o4-mini"],
            "novelty_llm_kwargs": {"temperatures": [0.0]},
            "max_api_costs": max_api_costs,
        },
        "db": {
            "num_islands": 1,
            "archive_size": 20,
            "elite_selection_ratio": 0.30,
            "num_archive_inspirations": 1,
            "num_top_k_inspirations": 1,
            "parent_selection_strategy": "weighted",
            "parent_selection_lambda": 10,
            "archive_selection_strategy": "crowding",
            "archive_criteria": {
                "combined_score": 1.0,
                "validation_accuracy_mean": 0.5,
                "generalization_gap_mean": -0.3,
                "n_params": -0.1,
            },
            "enable_dynamic_islands": False,
        },
        "job": {
            "activate_script": str(activate_script),
            "time": "02:00:00",
        },
        "max_evaluation_jobs": 1,
        "max_proposal_jobs": 1,
        "max_db_workers": 2,
        "verbose": True,
        "debug": False,
    }

    config_path = task_dir / "shinka_config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config_path


def build_environment(
    *,
    repo: Path,
    eval_settings: dict[str, str],
) -> dict[str, str]:
    env = os.environ.copy()
    for key, value in eval_settings.items():
        env[key] = value

    venv_bin = repo / ".venv-shinka-ttt" / "bin"
    if venv_bin.exists():
        env["VIRTUAL_ENV"] = str(repo / ".venv-shinka-ttt")
        env["PATH"] = str(venv_bin) + os.pathsep + env.get("PATH", "")

    return env


def compact_float(value: object) -> str:
    if isinstance(value, (float, int)):
        return f"{float(value):.4g}"
    return "?"


def format_job_log_line(path: Path, raw_line: str) -> str | None:
    text = raw_line.strip()
    if not text:
        return None

    generation = path.parent.parent.name
    if text.startswith("{"):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return f"[{generation}] {text}\n"

        event = payload.get("event")
        if event == "start":
            dataset = payload.get("dataset") or {}
            train_rows = ((dataset.get("train") or {}).get("rows")) or "?"
            validation_rows = ((dataset.get("validation") or {}).get("rows")) or "?"
            test_rows = ((dataset.get("test") or {}).get("rows")) or "?"
            return (
                f"[{generation}] eval start: run seed={payload.get('seed', '?')} "
                f"epochs={payload.get('n_epochs', '?')} "
                f"steps/epoch={payload.get('steps_per_epoch', '?')} "
                f"train={train_rows} validation={validation_rows} test={test_rows}\n"
            )
        if event == "epoch":
            return (
                f"[{generation}] epoch {payload.get('epoch', '?')}: "
                f"train_acc={compact_float(payload.get('train_accuracy'))} "
                f"validation_acc={compact_float(payload.get('validation_accuracy'))} "
                f"test_acc={compact_float(payload.get('test_accuracy'))} "
                f"validation_loss={compact_float(payload.get('validation_loss'))}\n"
            )
        return f"[{generation}] {event or 'event'}: {text}\n"

    return f"[{generation}] {text}\n"


def read_new_job_log_lines(
    results_dir: Path,
    offsets: dict[Path, int],
) -> list[str]:
    messages: list[str] = []
    for path in sorted(results_dir.glob("gen_*/results/job_log.out")):
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            continue

        offset = offsets.get(path, 0)
        if size < offset:
            offset = 0
        if size == offset:
            continue

        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                handle.seek(offset)
                while True:
                    raw_line = handle.readline()
                    if not raw_line:
                        break
                    message = format_job_log_line(path, raw_line)
                    if message is not None:
                        messages.append(message)
                offsets[path] = handle.tell()
        except OSError:
            continue

    return messages


def newest_result_mtime(results_dir: Path) -> float | None:
    if not results_dir.exists():
        return None
    latest: float | None = None
    for path in results_dir.rglob("*"):
        if not path.is_file():
            continue
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            continue
        latest = mtime if latest is None else max(latest, mtime)
    return latest


def read_progress(results_dir: Path) -> ProgressSnapshot:
    snapshot = ProgressSnapshot(result_mtime=newest_result_mtime(results_dir))
    db_path = results_dir / "programs.sqlite"
    if not db_path.exists():
        return snapshot

    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=2) as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS program_count,
                    MAX(generation) AS max_generation,
                    MAX(combined_score) AS max_score,
                    SUM(CASE WHEN correct THEN 1 ELSE 0 END) AS correct_count
                FROM programs
                """
            ).fetchone()
    except sqlite3.Error:
        return snapshot

    if row is None:
        return snapshot
    snapshot.program_count = int(row[0] or 0)
    snapshot.max_generation = None if row[1] is None else int(row[1])
    snapshot.max_score = None if row[2] is None else float(row[2])
    snapshot.correct_count = int(row[3] or 0)
    return snapshot


def terminate_process(process: subprocess.Popen[str], grace_seconds: int = 20) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except OSError:
        process.terminate()
    try:
        process.wait(timeout=grace_seconds)
        return
    except subprocess.TimeoutExpired:
        pass

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except OSError:
        process.kill()
    process.wait(timeout=grace_seconds)


def start_reader_thread(
    process: subprocess.Popen[str],
    line_queue: "queue.Queue[str]",
    log_handle,
) -> threading.Thread:
    def reader() -> None:
        assert process.stdout is not None
        for line in process.stdout:
            log_handle.write(line)
            log_handle.flush()
            line_queue.put(line)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    return thread


def progress_changed(before: ProgressSnapshot, after: ProgressSnapshot) -> bool:
    return (
        before.program_count != after.program_count
        or before.max_generation != after.max_generation
        or before.max_score != after.max_score
        or before.correct_count != after.correct_count
        or before.result_mtime != after.result_mtime
        or before.parsed_completed_generations != after.parsed_completed_generations
    )


def monitor_process(
    *,
    process: subprocess.Popen[str],
    results_dir: Path,
    monitor_log: Path,
    stale_seconds: int,
    poll_seconds: int,
) -> tuple[str, ProgressSnapshot]:
    lines: "queue.Queue[str]" = queue.Queue()
    monitor_log.parent.mkdir(parents=True, exist_ok=True)
    last_activity = time.time()
    snapshot = read_progress(results_dir)
    parsed_completed_generations: int | None = None
    job_log_offsets: dict[Path, int] = {}

    with monitor_log.open("a", encoding="utf-8", buffering=1) as log_handle:
        thread = start_reader_thread(process, lines, log_handle)
        while True:
            line_activity = False
            try:
                while True:
                    line = lines.get_nowait()
                    line_activity = True
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    match = COMPLETED_RE.search(line)
                    if match:
                        parsed_completed_generations = int(match.group(2))
            except queue.Empty:
                pass

            for message in read_new_job_log_lines(results_dir, job_log_offsets):
                line_activity = True
                log_handle.write(message)
                log_handle.flush()
                sys.stdout.write(message)
                sys.stdout.flush()

            current = read_progress(results_dir)
            current.parsed_completed_generations = parsed_completed_generations
            if line_activity or progress_changed(snapshot, current):
                last_activity = time.time()
                snapshot = current

            returncode = process.poll()
            if returncode is not None:
                thread.join(timeout=5)
                while not lines.empty():
                    line = lines.get_nowait()
                    sys.stdout.write(line)
                    sys.stdout.flush()
                for message in read_new_job_log_lines(results_dir, job_log_offsets):
                    log_handle.write(message)
                    log_handle.flush()
                    sys.stdout.write(message)
                    sys.stdout.flush()
                status = "completed" if returncode == 0 else f"failed:{returncode}"
                return status, current

            idle_seconds = time.time() - last_activity
            if idle_seconds >= stale_seconds:
                terminate_process(process)
                thread.join(timeout=5)
                current = read_progress(results_dir)
                current.parsed_completed_generations = parsed_completed_generations
                return "stale_terminated", current

            time.sleep(poll_seconds)


def write_report(
    *,
    report_path: Path,
    status: str,
    command: list[str],
    results_dir: Path,
    extracted_files: list[ExtractedFile],
    progress: ProgressSnapshot,
    started_at: float,
    finished_at: float,
    stale_seconds: int,
    eval_preset: str,
    eval_settings: dict[str, str],
) -> None:
    payload = {
        "status": status,
        "started_at": datetime.fromtimestamp(started_at).isoformat(),
        "finished_at": datetime.fromtimestamp(finished_at).isoformat(),
        "elapsed_seconds": round(finished_at - started_at, 3),
        "stale_seconds": stale_seconds,
        "results_dir": str(results_dir),
        "command": command,
        "eval_preset": eval_preset,
        "eval_settings": eval_settings,
        "extracted_files": [asdict(item) for item in extracted_files],
        "progress": asdict(progress),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract initial/evaluator code from the notebook, run ShinkaEvolve "
            "for the requested number of generations, and terminate if the run "
            "becomes stale."
        )
    )
    parser.add_argument("--notebook", type=Path, default=Path(DEFAULT_NOTEBOOK))
    parser.add_argument("--task-dir", type=Path, default=Path(DEFAULT_TASK_DIR))
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--num-generations", type=int, default=DEFAULT_GENERATIONS)
    parser.add_argument("--stale-seconds", type=int, default=DEFAULT_STALE_SECONDS)
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--max-api-costs", type=float, default=3.0)
    parser.add_argument(
        "--eval-preset",
        choices=sorted(EVAL_PRESETS),
        default=DEFAULT_EVAL_PRESET,
        help=(
            "Evaluator workload preset. quick is the default for CLI evolution; "
            "use full only when you intentionally want the long research run."
        ),
    )
    parser.add_argument(
        "--smoke-eval",
        action="store_true",
        help="Alias for --eval-preset smoke.",
    )
    parser.add_argument("--num-runs", type=int, default=None)
    parser.add_argument("--num-workers", type=int, default=None)
    parser.add_argument("--base-seed", type=int, default=None)
    parser.add_argument("--data-seed", type=int, default=None)
    parser.add_argument("--train-size", type=int, default=None)
    parser.add_argument("--validation-size", type=int, default=None)
    parser.add_argument("--test-size", type=int, default=None)
    parser.add_argument("--n-epochs", type=int, default=None)
    parser.add_argument("--steps-per-epoch", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--learning-rate", type=float, default=None)
    parser.add_argument("--convergence-threshold", type=float, default=None)
    parser.add_argument("--eval-every-epochs", type=int, default=None)
    parser.add_argument("--max-params", type=int, default=None)
    parser.add_argument("--ttt-log-dir", type=str, default=None)
    parser.add_argument(
        "--sample-with-replacement",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--use-test-in-score",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--verbose-training",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--allow-missing-api-key",
        action="store_true",
        help="Do not fail early if OPENROUTER_API_KEY is absent.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract files and print the command/config without launching ShinkaEvolve.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = repo_root()
    notebook_path = (repo / args.notebook).resolve()
    task_dir = (repo / args.task_dir).resolve()
    run_id = datetime.now().strftime("ttt_qml_cli_%Y%m%d_%H%M%S")
    results_dir = (repo / args.results_dir).resolve() if args.results_dir else repo / "results" / run_id
    activate_script = (repo / ".venv-shinka-ttt" / "bin" / "activate").resolve()
    shinka_run = (repo / ".venv-shinka-ttt" / "bin" / "shinka_run").resolve()

    if args.num_generations <= 0:
        raise ValueError("--num-generations must be > 0")
    if args.stale_seconds <= 0:
        raise ValueError("--stale-seconds must be > 0")
    if args.poll_seconds <= 0:
        raise ValueError("--poll-seconds must be > 0")
    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook not found: {notebook_path}")
    if not activate_script.exists():
        raise FileNotFoundError(f"Activation script not found: {activate_script}")
    if not shinka_run.exists():
        raise FileNotFoundError(f"shinka_run not found: {shinka_run}")
    if not args.allow_missing_api_key and not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Export it, or pass "
            "--allow-missing-api-key if you are intentionally testing failure handling."
        )

    eval_preset = "smoke" if args.smoke_eval else args.eval_preset
    eval_settings = apply_eval_cli_overrides(eval_settings_for_preset(eval_preset), args)
    validate_eval_settings(eval_settings)
    extracted_files = extract_task_files(notebook_path, task_dir)
    eval_activate_script = write_eval_activate_script(
        task_dir=task_dir,
        venv_activate_script=activate_script,
        eval_settings=eval_settings,
    )
    config_path = write_shinka_config(
        notebook_path=notebook_path,
        task_dir=task_dir,
        activate_script=eval_activate_script,
        max_api_costs=args.max_api_costs,
    )
    manifest_path = task_dir / "notebook_extract_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "notebook": str(notebook_path),
                "extracted_at": datetime.now().isoformat(),
                "files": [asdict(item) for item in extracted_files],
                "config": str(config_path),
                "eval_preset": eval_preset,
                "eval_settings": eval_settings,
                "eval_activate_script": str(eval_activate_script),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    env = build_environment(repo=repo, eval_settings=eval_settings)
    command = [
        str(shinka_run),
        "--task-dir",
        str(task_dir),
        "--results_dir",
        str(results_dir),
        "--num_generations",
        str(args.num_generations),
        "--config-fname",
        str(config_path),
    ]

    print(f"Extracted notebook code into: {task_dir}")
    for item in extracted_files:
        print(f"  {item.notebook_target} -> {item.output_path} ({item.sha256[:12]})")
    print(f"Config: {config_path}")
    print(f"Eval preset: {eval_preset}")
    print(f"Eval activation wrapper: {eval_activate_script}")
    print(f"Results: {results_dir}")
    print(f"Stale timeout: {args.stale_seconds}s")
    print("Command: " + " ".join(command))

    if args.dry_run:
        return 0

    results_dir.mkdir(parents=True, exist_ok=True)
    monitor_log = results_dir / "monitor.log"
    report_path = results_dir / "monitor_report.json"
    started_at = time.time()
    process = subprocess.Popen(
        command,
        cwd=repo,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
    )
    print(f"Started shinka_run PID {process.pid}")

    try:
        status, progress = monitor_process(
            process=process,
            results_dir=results_dir,
            monitor_log=monitor_log,
            stale_seconds=args.stale_seconds,
            poll_seconds=args.poll_seconds,
        )
    except KeyboardInterrupt:
        print("\nInterrupted; terminating shinka_run...")
        terminate_process(process)
        status = "interrupted_terminated"
        progress = read_progress(results_dir)

    finished_at = time.time()
    write_report(
        report_path=report_path,
        status=status,
        command=command,
        results_dir=results_dir,
        extracted_files=extracted_files,
        progress=progress,
        started_at=started_at,
        finished_at=finished_at,
        stale_seconds=args.stale_seconds,
        eval_preset=eval_preset,
        eval_settings=eval_settings,
    )

    print(f"Monitor status: {status}")
    print(f"Programs: {progress.program_count}")
    print(f"Max generation: {progress.max_generation}")
    print(f"Correct programs: {progress.correct_count}")
    print(f"Max score: {progress.max_score}")
    print(f"Monitor log: {monitor_log}")
    print(f"Report: {report_path}")

    return 0 if status == "completed" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
