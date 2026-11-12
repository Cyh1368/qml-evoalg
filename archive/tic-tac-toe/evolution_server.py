"""
Evolution dashboard server for ShinkaEvolve QML ansatz runs.

Watches all programs.sqlite databases under results/ and serves a live
web UI at http://localhost:5050 showing:
  - Evolution tree (Plotly, coloured by score)
  - Per-node info panel (metrics, feedback, circuit diagram)
  - PCA 2D scatter of the embedding landscape
  - Score timeline chart

Usage:
    python3 evolution_server.py                          # auto-latest run
    python3 evolution_server.py --results-dir results/ttt_qml_cli_20260605_124906
    python3 evolution_server.py --port 5050
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sqlite3
import sys
import threading
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import networkx as nx
import numpy as np
import pennylane as qml
from pennylane.drawer import draw_mpl
from flask import Flask, Response, jsonify, render_template_string, request

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
RESULTS_ROOT = BASE_DIR / "results"
DEFAULT_PORT = 5050
POLL_INTERVAL = 4  # seconds between DB polls


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def find_databases(root: Path) -> list[Path]:
    """Return all programs.sqlite paths sorted newest-first."""
    dbs = sorted(root.rglob("programs.sqlite"), key=lambda p: p.stat().st_mtime, reverse=True)
    return dbs


def load_programs(db_path: Path) -> list[dict]:
    """Load all program rows from a ShinkaEvolve SQLite database."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    rows = con.execute(
        """SELECT id, parent_id, generation, combined_score, correct,
                  public_metrics, text_feedback, embedding_pca_2d,
                  embedding_pca_3d, code_diff, metadata, code
           FROM programs ORDER BY generation ASC"""
    ).fetchall()
    meta_rows = con.execute("SELECT key, value FROM metadata_store").fetchall()
    con.close()

    meta = {k: v for k, v in meta_rows}
    programs = []
    for row in rows:
        (id_, parent, gen, score, correct, pub_raw,
         feedback, pca2d_raw, pca3d_raw, diff, meta_raw, code) = row
        pub = json.loads(pub_raw) if pub_raw else {}
        pca2d = json.loads(pca2d_raw) if pca2d_raw else None
        meta_d = json.loads(meta_raw) if meta_raw else {}
        programs.append({
            "id": id_,
            "parent_id": parent,
            "generation": gen,
            "score": score or 0.0,
            "correct": bool(correct),
            "pub": pub,
            "feedback": feedback or "",
            "pca2d": pca2d,
            "diff": diff or "",
            "stdout_log": meta_d.get("stdout_log", ""),
            "code": code or "",
        })
    return programs, meta


def load_best_meta(db_path: Path) -> dict:
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        rows = con.execute("SELECT key, value FROM metadata_store").fetchall()
        con.close()
        return {k: v for k, v in rows}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Circuit rendering
# ---------------------------------------------------------------------------

_circuit_cache: dict[str, str] = {}
_cache_lock = threading.Lock()


def render_circuit_svg(code: str, program_id: str) -> str:
    """Render ONE feature_map + ansatz block (not the full 3×2 circuit)."""
    with _cache_lock:
        if program_id in _circuit_cache:
            return _circuit_cache[program_id]

    try:
        ns: dict = {}
        exec(compile(code, "<ansatz>", "exec"), ns)

        n_qubits = ns.get("N_QUBITS", 9)
        n_params_per_block = ns.get("N_PARAMS_PER_BLOCK", 0)
        feature_map_fn = ns.get("feature_map")
        apply_ansatz_block_fn = ns.get("apply_ansatz_block")
        if feature_map_fn is None or apply_ansatz_block_fn is None:
            return "<p style='color:#888;padding:10px'>feature_map or apply_ansatz_block not found</p>"

        dev = qml.device("default.qubit", wires=n_qubits, shots=None)

        @qml.qnode(dev, interface="autograd")
        def single_block(board, params):
            feature_map_fn(board)
            apply_ansatz_block_fn(params, 0)
            return [qml.expval(qml.PauliZ(w)) for w in range(n_qubits)]

        params = np.zeros(max(n_params_per_block, 1))
        board = np.zeros(n_qubits, dtype=np.int8)

        fig, _ax = draw_mpl(single_block)(board, params)
        buf = io.BytesIO()
        fig.savefig(buf, format="svg", bbox_inches="tight")
        plt.close(fig)
        svg = buf.getvalue().decode("utf-8")

        svg = re.sub(r"<\?xml[^>]+\?>", "", svg)
        svg = re.sub(r"<!DOCTYPE[^>]+>", "", svg)
        svg = svg.strip()

        with _cache_lock:
            _circuit_cache[program_id] = svg
        return svg
    except Exception as exc:
        return f"<pre style='color:red'>Circuit render error:\n{exc}</pre>"


# ---------------------------------------------------------------------------
# Graph / Plotly data builders
# ---------------------------------------------------------------------------

def _rt_layout(G: nx.DiGraph, roots: list[str]) -> dict[str, tuple[float, float]]:
    """Reingold-Tilford layout: x = tree depth (collapsed), y = subtree-centred."""
    # BFS depth from roots
    depth: dict[str, int] = {}
    queue = list(roots)
    for r in roots:
        depth[r] = 0
    while queue:
        node = queue.pop(0)
        for child in G.successors(node):
            if child not in depth:
                depth[child] = depth[node] + 1
                queue.append(child)
    # Any disconnected nodes get depth 0
    for node in G.nodes():
        if node not in depth:
            depth[node] = 0

    pos: dict[str, tuple[float, float]] = {}
    counter = [0.0]

    def assign(node: str) -> None:
        children = list(G.successors(node))
        if not children:
            pos[node] = (float(depth[node]), counter[0])
            counter[0] += 1.0
        else:
            for c in children:
                assign(c)
            child_ys = [pos[c][1] for c in children]
            pos[node] = (float(depth[node]), (child_ys[0] + child_ys[-1]) / 2.0)

    for r in roots:
        assign(r)

    return pos


def build_tree_plotly(programs: list[dict], highlight_id: str | None = None) -> dict:
    """Return a Plotly figure dict for the evolution tree."""
    if not programs:
        return {}

    id_to_prog = {p["id"]: p for p in programs}

    G = nx.DiGraph()
    for p in programs:
        G.add_node(p["id"])
    for p in programs:
        if p["parent_id"] and p["parent_id"] in id_to_prog:
            G.add_edge(p["parent_id"], p["id"])

    roots = [p["id"] for p in programs if not p["parent_id"] or p["parent_id"] not in id_to_prog]
    pos = _rt_layout(G, roots)

    # Score range capped to actual min/max of valid programs
    valid_scores = [p["score"] for p in programs if p["correct"] and p["score"] > 0]
    score_min = min(valid_scores) if valid_scores else 0.0
    score_max = max(valid_scores) if valid_scores else 1.0
    if score_max == score_min:
        score_min = max(0.0, score_max - 0.1)

    # Edges
    edge_x, edge_y = [], []
    for src, dst in G.edges():
        x0, y0 = pos[src]
        x1, y1 = pos[dst]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    node_text = []
    for p in programs:
        pub = p["pub"]
        val_acc = pub.get("validation_accuracy_mean", "?")
        n_params = pub.get("n_params", "?")
        depth = pub.get("depth_mean", "?")
        node_text.append(
            f"Gen {p['generation']}<br>"
            f"Score: {p['score']:.4f}<br>"
            f"Val acc: {val_acc}<br>"
            f"Params: {n_params} | Depth: {depth}<br>"
            f"{'✓' if p['correct'] else '✗ FAILED'}"
        )

    border_colors = ["#ff4444" if p["id"] == highlight_id else "#ffffff" for p in programs]
    border_widths = [3 if p["id"] == highlight_id else 1 for p in programs]

    edge_trace = {
        "type": "scatter",
        "x": edge_x, "y": edge_y,
        "mode": "lines",
        "line": {"width": 1, "color": "#888"},
        "hoverinfo": "none",
    }

    # Separate valid vs failed nodes for colouring
    valid_x, valid_y, valid_c, valid_text, valid_border, valid_bw, valid_ids = [], [], [], [], [], [], []
    fail_x, fail_y, fail_text, fail_border, fail_bw, fail_ids = [], [], [], [], [], []
    for i, p in enumerate(programs):
        if p["correct"]:
            valid_x.append(pos[p["id"]][0])
            valid_y.append(pos[p["id"]][1])
            valid_c.append(p["score"])
            valid_text.append(node_text[i])
            valid_border.append(border_colors[i])
            valid_bw.append(border_widths[i])
            valid_ids.append(p["id"])
        else:
            fail_x.append(pos[p["id"]][0])
            fail_y.append(pos[p["id"]][1])
            fail_text.append(node_text[i])
            fail_border.append(border_colors[i])
            fail_bw.append(border_widths[i])
            fail_ids.append(p["id"])

    valid_trace = {
        "type": "scatter",
        "x": valid_x, "y": valid_y,
        "mode": "markers",
        "marker": {
            "size": 18,
            "color": valid_c,
            "colorscale": "Viridis",
            "cmin": score_min, "cmax": score_max,
            "showscale": True,
            "colorbar": {
                "title": "Score",
                "thickness": 14, "len": 0.8,
                "tickformat": ".3f",
            },
            "line": {"color": valid_border, "width": valid_bw},
        },
        "text": valid_text,
        "hoverinfo": "text",
        "customdata": valid_ids,
        "name": "Valid",
    }
    fail_trace = {
        "type": "scatter",
        "x": fail_x, "y": fail_y,
        "mode": "markers",
        "marker": {
            "size": 18,
            "color": "#555555",
            "symbol": "x",
            "line": {"color": fail_border, "width": fail_bw},
        },
        "text": fail_text,
        "hoverinfo": "text",
        "customdata": fail_ids,
        "name": "Failed",
    }

    layout = {
        "paper_bgcolor": "#1a1a2e",
        "plot_bgcolor": "#16213e",
        "font": {"color": "#e0e0e0", "family": "monospace"},
        "xaxis": {
            "title": "Depth",
            "color": "#aaa",
            "gridcolor": "#333",
            "zeroline": False,
            "dtick": 1,
        },
        "yaxis": {
            "visible": False,
            "zeroline": False,
        },
        "showlegend": False,
        "margin": {"l": 40, "r": 20, "t": 20, "b": 40},
        "hovermode": "closest",
    }

    return {"data": [edge_trace, valid_trace, fail_trace], "layout": layout}


def build_score_timeline(programs: list[dict]) -> dict:
    """Return a Plotly figure dict for score over generation."""
    valid = [p for p in programs if p["correct"]]
    gens = [p["generation"] for p in valid]
    scores = [p["score"] for p in valid]

    score_min = min(scores) if scores else 0.0
    score_max = max(scores) if scores else 1.0
    pad = (score_max - score_min) * 0.1 or 0.05

    # Running best
    best_so_far = []
    cur_best = 0.0
    for p in sorted(valid, key=lambda x: x["generation"]):
        cur_best = max(cur_best, p["score"])
        best_so_far.append((p["generation"], cur_best))

    scatter = {
        "type": "scatter",
        "x": gens, "y": scores,
        "mode": "markers",
        "marker": {"size": 8, "color": scores, "colorscale": "Viridis",
                   "cmin": score_min, "cmax": score_max, "showscale": False},
        "name": "Score",
        "hovertemplate": "Gen %{x}: %{y:.4f}<extra></extra>",
    }
    best_line = {
        "type": "scatter",
        "x": [b[0] for b in best_so_far],
        "y": [b[1] for b in best_so_far],
        "mode": "lines",
        "line": {"color": "#ff9f43", "width": 2, "dash": "dash"},
        "name": "Best",
        "hovertemplate": "Best at gen %{x}: %{y:.4f}<extra></extra>",
    }
    layout = {
        "paper_bgcolor": "#1a1a2e",
        "plot_bgcolor": "#16213e",
        "font": {"color": "#e0e0e0", "family": "monospace"},
        "xaxis": {"title": "Generation", "color": "#aaa", "gridcolor": "#333"},
        "yaxis": {
            "title": "Score", "color": "#aaa", "gridcolor": "#333",
            "range": [score_min - pad, score_max + pad],
        },
        "showlegend": False,
        "margin": {"l": 50, "r": 10, "t": 10, "b": 40},
        "hovermode": "closest",
    }
    return {"data": [scatter, best_line], "layout": layout}


def build_pca_scatter(programs: list[dict]) -> dict:
    """Return a Plotly figure dict for PCA 2D scatter."""
    valid = [p for p in programs if p["pca2d"] and p["correct"]]
    if not valid:
        return {"data": [], "layout": {}}

    x = [p["pca2d"][0] for p in valid]
    y = [p["pca2d"][1] for p in valid]
    scores = [p["score"] for p in valid]
    ids = [p["id"] for p in valid]
    text = [f"Gen {p['generation']} | Score {p['score']:.4f}" for p in valid]

    score_min = min(scores) if scores else 0.0
    score_max = max(scores) if scores else 1.0

    scatter = {
        "type": "scatter",
        "x": x, "y": y,
        "mode": "markers+text",
        "text": [str(p["generation"]) for p in valid],
        "textposition": "top center",
        "textfont": {"size": 9, "color": "#aaa"},
        "marker": {
            "size": 12,
            "color": scores,
            "colorscale": "Plasma",
            "cmin": score_min, "cmax": score_max,
            "showscale": True,
            "colorbar": {"title": "Score", "thickness": 14, "tickformat": ".3f"},
        },
        "hovertext": text,
        "hoverinfo": "text",
        "customdata": ids,
    }
    layout = {
        "paper_bgcolor": "#1a1a2e",
        "plot_bgcolor": "#16213e",
        "font": {"color": "#e0e0e0", "family": "monospace"},
        "xaxis": {"title": "PCA 1", "color": "#aaa", "gridcolor": "#333"},
        "yaxis": {"title": "PCA 2", "color": "#aaa", "gridcolor": "#333"},
        "margin": {"l": 50, "r": 10, "t": 10, "b": 40},
        "hovermode": "closest",
        "showlegend": False,
    }
    return {"data": [scatter], "layout": layout}


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class EvolutionState:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.programs: list[dict] = []
        self.meta: dict = {}
        self._last_mtime: float = 0.0
        self._lock = threading.Lock()
        self._listeners: list[queue_type] = []
        self.refresh()

    def refresh(self) -> bool:
        """Reload from DB if changed. Returns True if updated."""
        try:
            # SQLite WAL mode: writes go to the -wal file; the main file mtime
            # stays frozen while the writer is active. Use the newest mtime
            # across all three files so live runs are detected correctly.
            mtime = self.db_path.stat().st_mtime
            for suffix in ("-wal", "-shm"):
                sidecar = self.db_path.with_name(self.db_path.name + suffix)
                try:
                    mtime = max(mtime, sidecar.stat().st_mtime)
                except FileNotFoundError:
                    pass
        except FileNotFoundError:
            return False
        if mtime <= self._last_mtime:
            return False
        try:
            programs, meta = load_programs(self.db_path)
        except Exception:
            return False
        with self._lock:
            self.programs = programs
            self.meta = meta
            self._last_mtime = mtime
        self._notify_listeners()
        return True

    def get_programs(self) -> list[dict]:
        with self._lock:
            return list(self.programs)

    def get_meta(self) -> dict:
        with self._lock:
            return dict(self.meta)

    def subscribe(self, q):
        self._listeners.append(q)

    def unsubscribe(self, q):
        try:
            self._listeners.remove(q)
        except ValueError:
            pass

    def _notify_listeners(self):
        for q in list(self._listeners):
            try:
                q.put_nowait("update")
            except Exception:
                pass


import queue as queue_module
queue_type = queue_module.Queue


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)
_state: EvolutionState | None = None


def _poll_loop(state: EvolutionState):
    while True:
        time.sleep(POLL_INTERVAL)
        state.refresh()


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ShinkaEvolve QML Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #0d0d1a;
  color: #e0e0e0;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
#header {
  background: #1a1a2e;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 20px;
  border-bottom: 1px solid #333;
  flex-shrink: 0;
}
#header h1 { font-size: 15px; color: #7ec8e3; letter-spacing: 1px; }
#run-selector { background: #16213e; color: #e0e0e0; border: 1px solid #444; padding: 3px 8px; font-family: inherit; font-size: 12px; }
#status-badge {
  margin-left: auto;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  background: #2d2d44;
  color: #aaa;
}
#status-badge.live { background: #1a3a1a; color: #6fcf6f; }
#main {
  display: flex;
  flex: 1;
  overflow: hidden;
}
#left-col {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}
#tree-panel {
  flex: 3;
  min-height: 0;
  border-bottom: 1px solid #333;
  position: relative;
}
#bottom-charts {
  flex: 2;
  display: flex;
  min-height: 0;
}
#timeline-panel { flex: 1; border-right: 1px solid #333; }
#pca-panel { flex: 1; }
.chart { width: 100%; height: 100%; }
#right-col {
  width: 400px;
  flex-shrink: 0;
  border-left: 1px solid #333;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
#info-header {
  padding: 10px 14px;
  background: #1a1a2e;
  border-bottom: 1px solid #333;
  font-size: 11px;
  color: #7ec8e3;
  flex-shrink: 0;
}
#info-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 12px 14px;
}
#info-scroll::-webkit-scrollbar { width: 6px; }
#info-scroll::-webkit-scrollbar-track { background: #1a1a2e; }
#info-scroll::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
.metric-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 10px;
  margin-bottom: 12px;
}
.metric-item { display: flex; flex-direction: column; }
.metric-label { font-size: 10px; color: #888; }
.metric-value { font-size: 13px; color: #e0e0e0; }
.metric-value.good { color: #6fcf6f; }
.metric-value.bad { color: #eb5757; }
.section-title {
  font-size: 10px;
  color: #7ec8e3;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 10px 0 5px;
  border-bottom: 1px solid #333;
  padding-bottom: 3px;
}
#feedback-text {
  font-size: 11px;
  color: #ccc;
  line-height: 1.6;
  white-space: pre-wrap;
}
#circuit-container {
  margin-top: 10px;
  background: #fff;
  border-radius: 4px;
  overflow: hidden;
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}
#circuit-container svg {
  max-width: 100%;
  height: auto;
}
#circuit-loading {
  color: #888;
  font-size: 11px;
  padding: 20px;
}
#diff-container {
  font-size: 10px;
  line-height: 1.5;
  overflow-x: auto;
  background: #0d0d1a;
  border: 1px solid #333;
  border-radius: 3px;
  padding: 8px;
  margin-top: 6px;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre;
}
.diff-add { color: #6fcf6f; }
.diff-del { color: #eb5757; }
.diff-hdr { color: #7ec8e3; }
#summary-bar {
  display: flex;
  gap: 20px;
  padding: 6px 16px;
  background: #1a1a2e;
  border-bottom: 1px solid #333;
  flex-shrink: 0;
  font-size: 11px;
}
.sum-item { display: flex; gap: 6px; }
.sum-label { color: #888; }
.sum-value { color: #7ec8e3; font-weight: bold; }
</style>
</head>
<body>
<div id="header">
  <h1>&#x26A1; ShinkaEvolve QML Dashboard</h1>
  <label style="color:#888;font-size:11px">Run:</label>
  <select id="run-selector" onchange="switchRun(this.value)"></select>
  <span id="status-badge">connecting...</span>
</div>
<div id="summary-bar">
  <div class="sum-item"><span class="sum-label">Programs:</span><span class="sum-value" id="s-total">-</span></div>
  <div class="sum-item"><span class="sum-label">Correct:</span><span class="sum-value" id="s-correct">-</span></div>
  <div class="sum-item"><span class="sum-label">Best Score:</span><span class="sum-value" id="s-best">-</span></div>
  <div class="sum-item"><span class="sum-label">Best Gen:</span><span class="sum-value" id="s-bestgen">-</span></div>
  <div class="sum-item"><span class="sum-label">Generations:</span><span class="sum-value" id="s-maxgen">-</span></div>
</div>
<div id="main">
  <div id="left-col">
    <div id="tree-panel"><div id="tree-chart" class="chart"></div></div>
    <div id="bottom-charts">
      <div id="timeline-panel"><div id="timeline-chart" class="chart"></div></div>
      <div id="pca-panel"><div id="pca-chart" class="chart"></div></div>
    </div>
  </div>
  <div id="right-col">
    <div id="info-header">&#x25B6; Click a node to inspect</div>
    <div id="info-scroll">
      <div id="info-content" style="color:#555;font-size:11px;margin-top:20px">Select a program node in the tree...</div>
    </div>
  </div>
</div>

<script>
let currentRunId = null;
let selectedProgramId = null;
let evtSource = null;
let treeData = null;

// ---- SSE live updates ----
function connectSSE(runId) {
  if (evtSource) { evtSource.close(); }
  const badge = document.getElementById('status-badge');
  badge.textContent = 'connecting...';
  badge.className = '';
  evtSource = new EventSource('/sse?run=' + encodeURIComponent(runId));
  evtSource.onopen = () => { badge.textContent = 'live'; badge.className = 'live'; };
  evtSource.onerror = () => { badge.textContent = 'disconnected'; badge.className = ''; };
  evtSource.onmessage = (e) => {
    if (e.data === 'update') { refreshCharts(runId); }
  };
}

// ---- Run selector ----
async function loadRuns() {
  const res = await fetch('/runs');
  const runs = await res.json();
  const sel = document.getElementById('run-selector');
  sel.innerHTML = '';
  runs.forEach(r => {
    const opt = document.createElement('option');
    opt.value = r.id;
    opt.textContent = r.name;
    sel.appendChild(opt);
  });
  if (runs.length > 0) {
    currentRunId = runs[0].id;
    sel.value = currentRunId;
    connectSSE(currentRunId);
    await refreshCharts(currentRunId);
  }
}

function switchRun(runId) {
  currentRunId = runId;
  selectedProgramId = null;
  document.getElementById('info-content').innerHTML = '<span style="color:#555;font-size:11px">Select a program node...</span>';
  document.getElementById('info-header').textContent = '▶ Click a node to inspect';
  connectSSE(runId);
  refreshCharts(runId);
}

// ---- Charts ----
async function refreshCharts(runId) {
  const res = await fetch('/charts?run=' + encodeURIComponent(runId));
  const data = await res.json();
  treeData = data;

  updateSummaryBar(data.summary);
  renderTree(data.tree, selectedProgramId);
  renderTimeline(data.timeline);
  renderPCA(data.pca);
}

function updateSummaryBar(s) {
  if (!s) return;
  document.getElementById('s-total').textContent = s.total;
  document.getElementById('s-correct').textContent = s.correct;
  document.getElementById('s-best').textContent = s.best_score != null ? s.best_score.toFixed(4) : '-';
  document.getElementById('s-bestgen').textContent = s.best_gen != null ? s.best_gen : '-';
  document.getElementById('s-maxgen').textContent = s.max_gen != null ? s.max_gen : '-';
}

function renderTree(fig, highlightId) {
  if (!fig || !fig.data) return;
  const el = document.getElementById('tree-chart');
  const config = { responsive: true, displayModeBar: false };
  Plotly.react(el, fig.data, { ...fig.layout, height: el.clientHeight }, config);
  el.on('plotly_click', (evt) => {
    const pt = evt.points[0];
    if (pt && pt.customdata) { selectProgram(pt.customdata); }
  });
}

function renderTimeline(fig) {
  if (!fig || !fig.data) return;
  const el = document.getElementById('timeline-chart');
  Plotly.react(el, fig.data, { ...fig.layout, height: el.clientHeight }, { responsive: true, displayModeBar: false });
  el.on('plotly_click', (evt) => {
    const pt = evt.points[0];
    if (pt && pt.customdata) { selectProgram(pt.customdata); }
  });
}

function renderPCA(fig) {
  if (!fig || !fig.data) return;
  const el = document.getElementById('pca-chart');
  Plotly.react(el, fig.data, { ...fig.layout, height: el.clientHeight }, { responsive: true, displayModeBar: false });
  el.on('plotly_click', (evt) => {
    const pt = evt.points[0];
    if (pt && pt.customdata) { selectProgram(pt.customdata); }
  });
}

// ---- Info panel ----
let currentCircuitProgramId = null;

async function selectProgram(programId) {
  selectedProgramId = programId;
  document.getElementById('info-header').textContent = '▶ Loading...';

  // Re-render tree with highlight
  if (treeData && treeData.tree) {
    renderTree(treeData.tree, programId);
  }

  const res = await fetch('/program?id=' + encodeURIComponent(programId) + '&run=' + encodeURIComponent(currentRunId));
  const prog = await res.json();
  showInfo(prog);
}

function showInfo(p) {
  const pub = p.pub || {};
  document.getElementById('info-header').textContent = '▶ Gen ' + p.generation + ' | Score ' + (p.score || 0).toFixed(4);

  // Preserve the existing circuit container contents across re-renders so it
  // never flashes to "Rendering..." while a fetch is in flight.
  const existingCircuit = document.getElementById('circuit-container');
  const savedCircuitHTML = existingCircuit ? existingCircuit.innerHTML : null;

  let html = '';

  // 1. Circuit diagram — stable placeholder; contents restored immediately below
  html += '<div class="section-title">Circuit (one block: feature map + ansatz)</div>';
  html += '<div id="circuit-container"></div>';

  // 2. Metrics grid
  html += '<div class="section-title" style="margin-top:12px">Metrics</div>';
  html += '<div class="metric-grid">';
  html += metric('Score', (p.score || 0).toFixed(4), p.score > 0.55 ? 'good' : p.score < 0.35 ? 'bad' : '');
  html += metric('Valid', p.correct ? '✓ Yes' : '✗ No', p.correct ? 'good' : 'bad');
  html += metric('Val Acc', fmt(pub.validation_accuracy_mean));
  html += metric('Test Acc', fmt(pub.test_accuracy_mean));
  html += metric('Train Acc', fmt(pub.train_accuracy_mean));
  html += metric('Gen Gap', fmt(pub.generalization_gap_mean), pub.generalization_gap_mean > 0.15 ? 'bad' : 'good');
  html += metric('Params', pub.n_params != null ? pub.n_params : '?');
  html += metric('Depth', pub.depth_mean != null ? pub.depth_mean : '?');
  html += metric('Gates', pub.gate_count_mean != null ? pub.gate_count_mean : '?');
  html += metric('Val Loss', fmt(pub.validation_loss_mean));
  html += metric('Conv Step', pub.convergence_step_mean != null ? pub.convergence_step_mean : 'N/A');
  html += '</div>';

  // 3. Feedback
  if (p.feedback) {
    html += '<div class="section-title">Feedback</div>';
    html += '<div id="feedback-text">' + escHtml(p.feedback) + '</div>';
  }

  // 4. Diff
  if (p.diff) {
    html += '<div class="section-title">Code Diff</div>';
    html += '<div id="diff-container">' + colorDiff(p.diff) + '</div>';
  }

  document.getElementById('info-content').innerHTML = html;

  // Restore previous circuit immediately so there is no blank flash.
  const container = document.getElementById('circuit-container');
  if (savedCircuitHTML) {
    container.innerHTML = savedCircuitHTML;
  } else {
    container.innerHTML = '<span id="circuit-loading">Rendering...</span>';
  }

  // Skip fetch if this program's circuit is already displayed.
  if (p.id === currentCircuitProgramId) return;

  // Fetch new circuit; swap in atomically only when ready (no intermediate blank).
  fetch('/circuit?id=' + encodeURIComponent(p.id) + '&run=' + encodeURIComponent(currentRunId))
    .then(r => r.text())
    .then(svg => {
      const c = document.getElementById('circuit-container');
      if (c) { c.innerHTML = svg; currentCircuitProgramId = p.id; }
    })
    .catch(() => {
      const c = document.getElementById('circuit-container');
      if (c) { c.innerHTML = '<span style="color:#888;font-size:11px;padding:10px">Circuit unavailable</span>'; }
    });
}

function metric(label, value, cls = '') {
  return `<div class="metric-item"><span class="metric-label">${label}</span><span class="metric-value ${cls}">${value}</span></div>`;
}
function fmt(v) { return (v != null && v !== undefined) ? Number(v).toFixed(4) : '?'; }
function escHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function colorDiff(diff) {
  return diff.split('\n').map(line => {
    if (line.startsWith('+++') || line.startsWith('---')) return '<span class="diff-hdr">' + escHtml(line) + '</span>';
    if (line.startsWith('@@')) return '<span class="diff-hdr">' + escHtml(line) + '</span>';
    if (line.startsWith('+')) return '<span class="diff-add">' + escHtml(line) + '</span>';
    if (line.startsWith('-')) return '<span class="diff-del">' + escHtml(line) + '</span>';
    return escHtml(line);
  }).join('\n');
}

// ---- Init ----
window.addEventListener('load', loadRuns);
window.addEventListener('resize', () => {
  if (treeData) {
    renderTree(treeData.tree, selectedProgramId);
    renderTimeline(treeData.timeline);
    renderPCA(treeData.pca);
  }
});
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# State registry (multiple runs)
# ---------------------------------------------------------------------------

_states: dict[str, EvolutionState] = {}
_states_lock = threading.Lock()


def get_state(run_id: str) -> EvolutionState | None:
    with _states_lock:
        return _states.get(run_id)


def register_dbs(results_root: Path):
    """Scan and register all available databases."""
    dbs = find_databases(results_root)
    with _states_lock:
        for db in dbs:
            run_id = db.parent.name
            if run_id not in _states:
                _states[run_id] = EvolutionState(db)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/runs")
def runs():
    register_dbs(RESULTS_ROOT)
    with _states_lock:
        run_list = sorted(_states.keys(), reverse=True)
    return jsonify([{"id": r, "name": r} for r in run_list])


@app.route("/charts")
def charts():
    run_id = request.args.get("run", "")
    state = get_state(run_id)
    if state is None:
        return jsonify({"error": "run not found"})
    state.refresh()
    programs = state.get_programs()
    meta = state.get_meta()

    valid = [p for p in programs if p["correct"]]
    best_score = max((p["score"] for p in valid), default=None)
    best_gen = None
    if best_score is not None:
        best_gen = next(p["generation"] for p in valid if p["score"] == best_score)
    max_gen = max((p["generation"] for p in programs), default=None)

    summary = {
        "total": len(programs),
        "correct": sum(1 for p in programs if p["correct"]),
        "best_score": best_score,
        "best_gen": best_gen,
        "max_gen": max_gen,
    }

    tree_fig = build_tree_plotly(programs)
    timeline_fig = build_score_timeline(programs)
    pca_fig = build_pca_scatter(programs)

    return jsonify({"tree": tree_fig, "timeline": timeline_fig, "pca": pca_fig, "summary": summary})


@app.route("/program")
def program():
    program_id = request.args.get("id", "")
    run_id = request.args.get("run", "")
    state = get_state(run_id)
    if state is None:
        return jsonify({"error": "run not found"})
    programs = state.get_programs()
    prog = next((p for p in programs if p["id"] == program_id), None)
    if prog is None:
        return jsonify({"error": "program not found"})
    # Don't send the full code over JSON (large); circuit is loaded separately
    return jsonify({k: v for k, v in prog.items() if k != "code" and k != "stdout_log"})


@app.route("/circuit")
def circuit():
    program_id = request.args.get("id", "")
    run_id = request.args.get("run", "")
    state = get_state(run_id)
    if state is None:
        return "<p>run not found</p>", 404
    programs = state.get_programs()
    prog = next((p for p in programs if p["id"] == program_id), None)
    if prog is None:
        return "<p>program not found</p>", 404
    if not prog["code"]:
        return "<p style='color:#888;padding:10px'>No code stored</p>"
    svg = render_circuit_svg(prog["code"], program_id)
    return Response(svg, mimetype="text/html")


@app.route("/sse")
def sse():
    run_id = request.args.get("run", "")
    state = get_state(run_id)

    def generate():
        if state is None:
            yield "data: error\n\n"
            return
        q: queue_module.Queue = queue_module.Queue(maxsize=10)
        state.subscribe(q)
        try:
            yield "data: connected\n\n"
            while True:
                try:
                    msg = q.get(timeout=30)
                    yield f"data: {msg}\n\n"
                except queue_module.Empty:
                    yield ": keepalive\n\n"
        except GeneratorExit:
            pass
        finally:
            state.unsubscribe(q)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global RESULTS_ROOT

    parser = argparse.ArgumentParser(description="ShinkaEvolve QML Evolution Dashboard")
    parser.add_argument("--results-dir", default=None,
                        help="Path to a specific results run directory (or the results root)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    if args.results_dir:
        p = Path(args.results_dir)
        if (p / "programs.sqlite").exists():
            RESULTS_ROOT = p.parent
        else:
            RESULTS_ROOT = p

    register_dbs(RESULTS_ROOT)

    if not _states:
        print(f"WARNING: No programs.sqlite found under {RESULTS_ROOT}")
    else:
        print(f"Loaded {len(_states)} run(s): {', '.join(sorted(_states.keys(), reverse=True)[:3])}")

    # Start background poller
    t = threading.Thread(target=_poll_loop, args=(list(_states.values())[0] if _states else None,), daemon=True)
    # Poll all states, not just first
    def poll_all():
        while True:
            time.sleep(POLL_INTERVAL)
            register_dbs(RESULTS_ROOT)
            for s in list(_states.values()):
                s.refresh()
    poller = threading.Thread(target=poll_all, daemon=True)
    poller.start()

    print(f"\nDashboard running at http://localhost:{args.port}\n")
    app.run(host=args.host, port=args.port, threaded=True, debug=False)


if __name__ == "__main__":
    main()
