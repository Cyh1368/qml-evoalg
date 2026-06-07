#!/usr/bin/env python3
"""Build an HTML ansatz report for a ShinkaEvolve tic-tac-toe run."""

from __future__ import annotations

import argparse
import html
import json
import math
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


GRID_EDGES = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (4, 5), (5, 6), (6, 7), (7, 0),
    (1, 8), (3, 8), (5, 8), (7, 8),
)
SAFE_BUILTINS = {
    "dict": dict,
    "enumerate": enumerate,
    "int": int,
    "len": len,
    "list": list,
    "range": range,
    "str": str,
    "tuple": tuple,
}
EVOLVE_START = "# EVOLVE-BLOCK-START"
EVOLVE_END = "# EVOLVE-BLOCK-END"


@dataclass
class Candidate:
    generation: int
    status: str
    source_path: Path | None
    program_id: str | None = None
    parent_id: str | None = None
    score: float | None = None
    correct: bool | None = None
    public_metrics: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    status_detail: str = ""
    code: str = ""
    ansatz_spec: list[dict[str, Any]] | None = None
    ansatz_error: str | None = None


def parse_json_maybe(value: Any, fallback: Any) -> Any:
    if not value:
        return fallback
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def find_latest_results_dir(results_root: Path) -> Path:
    db_paths = sorted(
        results_root.glob("*/programs.sqlite"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not db_paths:
        raise FileNotFoundError(f"No programs.sqlite files found under {results_root}")
    return db_paths[0].parent


def load_program_rows(results_dir: Path) -> dict[int, Candidate]:
    db_path = results_dir / "programs.sqlite"
    if not db_path.exists():
        return {}

    rows: dict[int, Candidate] = {}
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5) as conn:
        conn.row_factory = sqlite3.Row
        for row in conn.execute(
            """
            SELECT id, code, parent_id, generation, combined_score, correct,
                   public_metrics, metadata
            FROM programs
            ORDER BY generation, timestamp
            """
        ):
            generation = int(row["generation"])
            source_path = results_dir / f"gen_{generation}" / "main.py"
            metadata = parse_json_maybe(row["metadata"], {})
            public_metrics = parse_json_maybe(row["public_metrics"], {})
            correct = bool(row["correct"])
            rows[generation] = Candidate(
                generation=generation,
                status="correct" if correct else "incorrect",
                source_path=source_path if source_path.exists() else None,
                program_id=row["id"],
                parent_id=row["parent_id"],
                score=None if row["combined_score"] is None else float(row["combined_score"]),
                correct=correct,
                public_metrics=public_metrics if isinstance(public_metrics, dict) else {},
                metadata=metadata if isinstance(metadata, dict) else {},
                code=row["code"] or "",
            )
    return rows


def read_correct_detail(gen_dir: Path) -> str:
    path = gen_dir / "results" / "correct.json"
    if not path.exists():
        return ""
    payload = parse_json_maybe(path.read_text(encoding="utf-8"), {})
    if not isinstance(payload, dict):
        return ""
    error = payload.get("error")
    return "" if error in (None, "") else str(error)


def load_generation_candidates(results_dir: Path, db_candidates: dict[int, Candidate]) -> list[Candidate]:
    candidates = dict(db_candidates)
    for gen_dir in sorted(results_dir.glob("gen_*"), key=lambda path: int(path.name.split("_")[1])):
        generation = int(gen_dir.name.split("_")[1])
        source_path = gen_dir / "main.py"
        if generation in candidates:
            candidate = candidates[generation]
            candidate.source_path = source_path if source_path.exists() else candidate.source_path
            candidate.status_detail = read_correct_detail(gen_dir)
            if not candidate.code and source_path.exists():
                candidate.code = source_path.read_text(encoding="utf-8")
            continue

        code = source_path.read_text(encoding="utf-8") if source_path.exists() else ""
        failure_path = gen_dir / "failure.json"
        if failure_path.exists():
            failure = parse_json_maybe(failure_path.read_text(encoding="utf-8"), {})
            if not isinstance(failure, dict):
                failure = {}
            status = "failed proposal"
            detail = str(failure.get("failure_reason") or failure.get("failure_class") or "")
            metadata = {
                "patch_name": failure.get("patch_name"),
                "patch_type": failure.get("patch_type"),
                "patch_description": failure.get("patch_description"),
            }
        elif (gen_dir / ".generation_lock").exists() or (gen_dir / "results" / "job_log.out").exists():
            status = "incomplete"
            detail = "Generated/evaluation artifacts exist, but no program row was written to programs.sqlite."
            metadata = {}
        else:
            status = "generated"
            detail = "Generation directory exists, but no database row was found."
            metadata = {}

        candidates[generation] = Candidate(
            generation=generation,
            status=status,
            source_path=source_path if source_path.exists() else None,
            metadata=metadata,
            status_detail=detail,
            code=code,
        )

    return [candidates[key] for key in sorted(candidates)]


def extract_evolve_block(code: str) -> str:
    start = code.find(EVOLVE_START)
    end = code.find(EVOLVE_END)
    if start == -1 or end == -1 or end <= start:
        raise ValueError("EVOLVE-BLOCK markers not found")
    start = code.find("\n", start)
    if start == -1:
        raise ValueError("EVOLVE-BLOCK start marker has no following source")
    return code[start + 1:end]


def extract_ansatz_spec(code: str) -> list[dict[str, Any]]:
    block = extract_evolve_block(code)
    env: dict[str, Any] = {
        "__builtins__": SAFE_BUILTINS,
        "CORNERS": (0, 2, 4, 6),
        "EDGES": (1, 3, 5, 7),
        "CENTER": 8,
        "GRID_EDGES": GRID_EDGES,
        "GRID_EDGE_SET": {tuple(sorted(edge)) for edge in GRID_EDGES},
    }
    exec(compile(block, "<evolve_block>", "exec"), env, env)
    spec = env.get("ANSATZ_SPEC")
    if not isinstance(spec, list):
        raise ValueError("ANSATZ_SPEC did not evaluate to a list")
    for index, item in enumerate(spec):
        if not isinstance(item, dict):
            raise ValueError(f"ANSATZ_SPEC[{index}] is {type(item).__name__}, expected dict")
    return spec


def annotate_candidates(candidates: list[Candidate]) -> None:
    for candidate in candidates:
        if not candidate.code and candidate.source_path and candidate.source_path.exists():
            candidate.code = candidate.source_path.read_text(encoding="utf-8")
        if not candidate.code:
            candidate.ansatz_error = "No source code available"
            continue
        try:
            candidate.ansatz_spec = extract_ansatz_spec(candidate.code)
        except Exception as exc:  # noqa: BLE001 - report extraction errors verbatim.
            candidate.ansatz_error = str(exc)


def ordered_param_keys(spec: list[dict[str, Any]]) -> list[str]:
    keys: list[str] = []
    for item in spec:
        param = item.get("param")
        if isinstance(param, str) and param and param not in keys:
            keys.append(param)
    return keys


def gate_mix(spec: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(item.get("gate", "?")).upper() for item in spec)


def h(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def fmt_float(value: Any, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return h(value)
    if not math.isfinite(number):
        return "n/a"
    return f"{number:.{digits}f}"


def short_id(value: str | None) -> str:
    return "n/a" if not value else value[:8]


def render_score_chart(candidates: list[Candidate]) -> str:
    scored = [item for item in candidates if item.score is not None]
    if not scored:
        return "<p>No scored candidates were available.</p>"

    width = 980
    height = 250
    left = 48
    right = 24
    top = 24
    bottom = 44
    max_gen = max(item.generation for item in candidates)
    max_score = max(float(item.score or 0.0) for item in scored)
    min_score = min(float(item.score or 0.0) for item in scored)
    y_min = min(0.0, min_score)
    y_max = max(0.65, max_score)
    best_score = max_score

    def x_for(gen: int) -> float:
        if max_gen <= 0:
            return left
        return left + (width - left - right) * (gen / max_gen)

    def y_for(score: float) -> float:
        span = max(y_max - y_min, 1e-9)
        return top + (height - top - bottom) * (1 - ((score - y_min) / span))

    parts = [
        f'<svg class="score-chart" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Combined score by generation">',
        f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" class="axis"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" class="axis"/>',
    ]
    for tick in range(6):
        score = y_min + (y_max - y_min) * tick / 5
        y = y_for(score)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{left-8}" y="{y+4:.1f}" class="axis-label" text-anchor="end">{score:.2f}</text>')
    for gen in range(0, max_gen + 1, max(1, math.ceil(max_gen / 10))):
        x = x_for(gen)
        parts.append(f'<text x="{x:.1f}" y="{height-16}" class="axis-label" text-anchor="middle">{gen}</text>')
    points = [
        (x_for(item.generation), y_for(float(item.score)), item)
        for item in scored
    ]
    if len(points) > 1:
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points)
        parts.append(f'<polyline points="{poly}" class="score-line"/>')
    for x, y, item in points:
        cls = "score-point best" if float(item.score or 0.0) == best_score else "score-point"
        if item.correct is False:
            cls += " incorrect"
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" class="{cls}">'
            f'<title>Gen {item.generation}: {fmt_float(item.score)}</title></circle>'
        )
    parts.append('<text x="16" y="16" class="chart-title">Combined score</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def render_ansatz_svg(spec: list[dict[str, Any]]) -> str:
    col_width = 58
    row_height = 44
    left = 54
    right = 24
    top = 26
    bottom = 22
    width = left + right + max(1, len(spec)) * col_width
    height = top + bottom + 8 * row_height

    def y_for(wire: int) -> int:
        return top + wire * row_height

    gate_class = {
        "RX": "rx",
        "RY": "ry",
        "RZ": "rz",
        "CZ": "cz",
        "CNOT": "cnot",
        "CRX": "crx",
        "CRY": "cry",
        "CRZ": "crz",
    }
    parts = [f'<svg class="circuit" viewBox="0 0 {width} {height}" role="img">']
    for wire in range(9):
        y = y_for(wire)
        parts.append(f'<text x="10" y="{y+4}" class="wire-label">q{wire}</text>')
        parts.append(f'<line x1="{left-10}" y1="{y}" x2="{width-right+8}" y2="{y}" class="wire"/>')

    for index, item in enumerate(spec):
        gate = str(item.get("gate", "?")).upper()
        cls = gate_class.get(gate, "other")
        x = left + index * col_width + col_width / 2
        param = item.get("param")
        param_label = str(param) if isinstance(param, str) and param else ""
        title = h(json.dumps(item, sort_keys=True))
        if "wire" in item:
            wire = int(item.get("wire", 0))
            y = y_for(wire)
            parts.append(
                f'<g><title>{title}</title>'
                f'<rect x="{x-24:.1f}" y="{y-15}" width="48" height="30" rx="4" class="gate {cls}"/>'
                f'<text x="{x:.1f}" y="{y-3}" class="gate-label" text-anchor="middle">{h(gate)}</text>'
                f'<text x="{x:.1f}" y="{y+9}" class="param-label" text-anchor="middle">{h(param_label)}</text>'
                f'</g>'
            )
        elif "wires" in item:
            wires = [int(w) for w in item.get("wires", [])]
            if len(wires) != 2:
                continue
            y1, y2 = y_for(wires[0]), y_for(wires[1])
            y_mid = (y1 + y2) / 2
            parts.append(
                f'<g><title>{title}</title>'
                f'<line x1="{x:.1f}" y1="{min(y1,y2)}" x2="{x:.1f}" y2="{max(y1,y2)}" class="coupler {cls}"/>'
                f'<circle cx="{x:.1f}" cy="{y1}" r="4" class="node {cls}"/>'
                f'<circle cx="{x:.1f}" cy="{y2}" r="4" class="node {cls}"/>'
                f'<rect x="{x-26:.1f}" y="{y_mid-15:.1f}" width="52" height="30" rx="4" class="gate {cls}"/>'
                f'<text x="{x:.1f}" y="{y_mid-3:.1f}" class="gate-label" text-anchor="middle">{h(gate)}</text>'
                f'<text x="{x:.1f}" y="{y_mid+9:.1f}" class="param-label" text-anchor="middle">{h(param_label)}</text>'
                f'</g>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def render_gate_legend() -> str:
    gates = ["RX", "RY", "RZ", "CZ", "CNOT", "CRX", "CRY", "CRZ"]
    chunks = []
    for gate in gates:
        cls = gate.lower()
        chunks.append(f'<span class="legend-chip"><span class="legend-box {cls}"></span>{gate}</span>')
    return '<div class="legend">' + "\n".join(chunks) + "</div>"


def render_candidate(candidate: Candidate, best_generation: int | None) -> str:
    metadata = candidate.metadata or {}
    public = candidate.public_metrics or {}
    patch_name = metadata.get("patch_name") or "n/a"
    patch_type = metadata.get("patch_type") or "n/a"
    is_best = best_generation == candidate.generation
    spec = candidate.ansatz_spec
    param_keys = ordered_param_keys(spec) if spec else []
    mix = gate_mix(spec) if spec else Counter()
    status_class = candidate.status.replace(" ", "-")
    heading_badge = '<span class="best-badge">best score</span>' if is_best else ""
    metric_rows = [
        ("Score", fmt_float(candidate.score)),
        ("Status", candidate.status),
        ("Patch", f"{h(patch_name)} <span class=\"muted\">({h(patch_type)})</span>"),
        ("Program ID", h(short_id(candidate.program_id))),
        ("Parent ID", h(short_id(candidate.parent_id))),
        ("Train acc", fmt_float(public.get("train_accuracy_mean"))),
        ("Validation acc", fmt_float(public.get("validation_accuracy_mean"))),
        ("Test acc", fmt_float(public.get("test_accuracy_mean"))),
        ("Params", h(public.get("n_params") if public.get("n_params") is not None else len(param_keys) * 6)),
        ("Depth", h(public.get("depth_mean"))),
        ("Gate count", h(public.get("gate_count_mean"))),
        ("Block gates", h(len(spec) if spec else "n/a")),
        ("Param keys/block", h(len(param_keys) if spec else "n/a")),
    ]
    rows_html = "\n".join(
        f"<tr><th>{name}</th><td>{value}</td></tr>"
        for name, value in metric_rows
    )
    mix_html = " ".join(
        f'<span class="metric-pill">{h(gate)}: {count}</span>'
        for gate, count in sorted(mix.items())
    ) or '<span class="muted">No gate mix available</span>'
    param_html = " ".join(
        f'<span class="param-chip">{h(key)}</span>'
        for key in param_keys
    ) or '<span class="muted">No trainable parameter keys extracted</span>'
    detail = candidate.status_detail.strip()
    detail_html = (
        f'<p class="status-detail">{h(detail[:900])}{"..." if len(detail) > 900 else ""}</p>'
        if detail
        else ""
    )
    patch_description = str(metadata.get("patch_description") or "").strip()
    patch_html = (
        f'<details><summary>Patch description</summary><p>{h(patch_description)}</p></details>'
        if patch_description
        else ""
    )
    if spec:
        viz_html = f'<div class="circuit-wrap">{render_ansatz_svg(spec)}</div>'
        spec_json = h(json.dumps(spec, indent=2))
        details_html = f'<details><summary>ANSATZ_SPEC JSON</summary><pre>{spec_json}</pre></details>'
    else:
        viz_html = f'<p class="error">Could not extract ansatz: {h(candidate.ansatz_error)}</p>'
        details_html = ""
    return f"""
<section class="candidate {status_class}" id="gen-{candidate.generation}">
  <h2>Generation {candidate.generation} {heading_badge}</h2>
  <div class="candidate-grid">
    <table class="metrics">{rows_html}</table>
    <div class="candidate-notes">
      <div class="gate-mix">{mix_html}</div>
      <div class="param-list">{param_html}</div>
      {detail_html}
      {patch_html}
    </div>
  </div>
  {viz_html}
  {details_html}
</section>
"""


def render_summary_table(candidates: list[Candidate], best_generation: int | None) -> str:
    rows = []
    for candidate in candidates:
        public = candidate.public_metrics or {}
        metadata = candidate.metadata or {}
        marker = "best" if candidate.generation == best_generation else ""
        rows.append(
            "<tr>"
            f"<td><a href=\"#gen-{candidate.generation}\">{candidate.generation}</a></td>"
            f"<td>{h(candidate.status)}</td>"
            f"<td>{fmt_float(candidate.score)}</td>"
            f"<td>{fmt_float(public.get('validation_accuracy_mean'))}</td>"
            f"<td>{fmt_float(public.get('test_accuracy_mean'))}</td>"
            f"<td>{h(public.get('n_params') if public.get('n_params') is not None else '')}</td>"
            f"<td>{h(metadata.get('patch_name') or '')}</td>"
            f"<td>{marker}</td>"
            "</tr>"
        )
    return """
<table class="summary">
  <thead>
    <tr>
      <th>Gen</th><th>Status</th><th>Score</th><th>Val acc</th>
      <th>Test acc</th><th>Params</th><th>Patch</th><th></th>
    </tr>
  </thead>
  <tbody>
""" + "\n".join(rows) + """
  </tbody>
</table>
"""


def render_html(results_dir: Path, candidates: list[Candidate]) -> str:
    scored = [item for item in candidates if item.score is not None and item.correct]
    best = max(scored, key=lambda item: item.score or -1.0) if scored else None
    best_generation = best.generation if best else None
    max_completed = max((item.generation for item in candidates if item.program_id), default=None)
    generated_at = datetime.now().isoformat(timespec="seconds")
    candidate_sections = "\n".join(render_candidate(item, best_generation) for item in candidates)
    summary = render_summary_table(candidates, best_generation)
    chart = render_score_chart(candidates)
    stylesheet = """
body {
  margin: 0;
  color: #1f2933;
  background: #f7f8fb;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
main {
  max-width: 1220px;
  margin: 0 auto;
  padding: 28px;
}
h1 {
  margin: 0 0 8px;
  font-size: 28px;
}
h2 {
  margin: 0 0 16px;
  font-size: 20px;
}
.subtle, .muted {
  color: #697586;
}
.panel, .candidate {
  background: white;
  border: 1px solid #d9e1ec;
  border-radius: 8px;
  padding: 18px;
  margin: 16px 0;
}
.summary, .metrics {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.summary th, .summary td, .metrics th, .metrics td {
  border-bottom: 1px solid #e7ecf3;
  padding: 7px 8px;
  text-align: left;
  vertical-align: top;
}
.metrics th {
  width: 135px;
  color: #52606d;
  font-weight: 600;
}
.candidate-grid {
  display: grid;
  grid-template-columns: minmax(300px, 430px) 1fr;
  gap: 16px;
  align-items: start;
}
.candidate.incorrect, .candidate.failed-proposal, .candidate.incomplete {
  border-left: 5px solid #c2410c;
}
.best-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 7px;
  border-radius: 999px;
  color: #064e3b;
  background: #d1fae5;
  font-size: 12px;
  font-weight: 700;
}
.metric-pill, .param-chip, .legend-chip {
  display: inline-flex;
  gap: 5px;
  align-items: center;
  margin: 0 6px 6px 0;
  padding: 4px 7px;
  border-radius: 999px;
  background: #eef2f7;
  font-size: 12px;
}
.param-chip {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.circuit-wrap {
  margin-top: 16px;
  overflow-x: auto;
  border: 1px solid #e1e7ef;
  border-radius: 8px;
  background: #fbfcfe;
}
.circuit {
  min-width: 100%;
  height: auto;
  display: block;
}
.wire {
  stroke: #aab6c5;
  stroke-width: 1.2;
}
.wire-label, .axis-label {
  fill: #52606d;
  font-size: 12px;
}
.gate {
  stroke: rgba(31, 41, 55, 0.35);
  stroke-width: 1;
}
.gate-label {
  fill: #111827;
  font-size: 9px;
  font-weight: 700;
}
.param-label {
  fill: #334155;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 7px;
}
.coupler {
  stroke-width: 2.2;
}
.node {
  stroke: #1f2937;
  stroke-width: 1;
}
.rx, .legend-box.rx { fill: #bfdbfe; stroke: #2563eb; }
.ry, .legend-box.ry { fill: #bbf7d0; stroke: #16a34a; }
.rz, .legend-box.rz { fill: #fde68a; stroke: #ca8a04; }
.cz, .legend-box.cz { fill: #fecaca; stroke: #dc2626; }
.cnot, .legend-box.cnot { fill: #ddd6fe; stroke: #7c3aed; }
.crx, .legend-box.crx { fill: #bae6fd; stroke: #0284c7; }
.cry, .legend-box.cry { fill: #ccfbf1; stroke: #0d9488; }
.crz, .legend-box.crz { fill: #fed7aa; stroke: #ea580c; }
.other { fill: #e5e7eb; stroke: #6b7280; }
.legend {
  margin: 12px 0 0;
}
.legend-box {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 3px;
  border: 1px solid;
}
.score-chart {
  width: 100%;
  height: auto;
}
.axis {
  stroke: #64748b;
  stroke-width: 1.2;
}
.grid {
  stroke: #e2e8f0;
  stroke-width: 1;
}
.score-line {
  fill: none;
  stroke: #2563eb;
  stroke-width: 2.5;
}
.score-point {
  fill: #2563eb;
  stroke: white;
  stroke-width: 2;
}
.score-point.best {
  fill: #059669;
}
.score-point.incorrect {
  fill: #dc2626;
}
.chart-title {
  fill: #1f2937;
  font-size: 13px;
  font-weight: 700;
}
details {
  margin-top: 12px;
}
summary {
  cursor: pointer;
  color: #1d4ed8;
  font-weight: 600;
}
pre {
  overflow-x: auto;
  padding: 12px;
  background: #0f172a;
  color: #e5e7eb;
  border-radius: 6px;
  font-size: 12px;
}
.error, .status-detail {
  color: #9a3412;
}
@media (max-width: 820px) {
  main { padding: 16px; }
  .candidate-grid { grid-template-columns: 1fr; }
}
"""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ansatz Evolution Report - {h(results_dir.name)}</title>
  <style>{stylesheet}</style>
</head>
<body>
<main>
  <h1>Ansatz Evolution Report</h1>
  <p class="subtle">
    Results directory: <code>{h(results_dir)}</code><br>
    Generated: {h(generated_at)}<br>
    Completed database generations through: {h(max_completed)}.
    The visualizations show one ansatz block; the fixed circuit repeats that block
    twice after each of three data re-uploads.
  </p>
  <section class="panel">
    <h2>Run Summary</h2>
    <p>
      Best completed generation: <strong>{h(best_generation)}</strong>,
      score: <strong>{fmt_float(best.score if best else None)}</strong>.
      Candidate count in report: <strong>{len(candidates)}</strong>.
    </p>
    {render_gate_legend()}
    {chart}
    {summary}
  </section>
  {candidate_sections}
</main>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an ansatz HTML report for a ShinkaEvolve run.")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help="Specific run directory. Defaults to newest results/*/programs.sqlite.",
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=Path("results"),
        help="Root used when auto-detecting the newest run.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output HTML path. Defaults to <results-dir>/ansatz_report.html.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results_dir = args.results_dir or find_latest_results_dir(args.results_root)
    results_dir = results_dir.resolve()
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory does not exist: {results_dir}")

    db_candidates = load_program_rows(results_dir)
    candidates = load_generation_candidates(results_dir, db_candidates)
    annotate_candidates(candidates)

    output = (args.output or (results_dir / "ansatz_report.html")).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(results_dir, candidates), encoding="utf-8")
    print(f"Report: {output}")
    print(f"Results: {results_dir}")
    print(f"Candidates: {len(candidates)}")
    scored = [candidate for candidate in candidates if candidate.score is not None and candidate.correct]
    if scored:
        best = max(scored, key=lambda item: item.score or -1.0)
        print(f"Best generation: {best.generation}")
        print(f"Best score: {best.score:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
