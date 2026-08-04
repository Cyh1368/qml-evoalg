#!/usr/bin/env python3
"""Batch circuit renderer, run inside a PennyLane-capable venv as a subprocess
of build_data.py.

Protocol: reads a single JSON object from stdin:
    {"items": [{"id": "<program id>", "code": "<full candidate source>"}, ...]}
Writes a single JSON object to stdout:
    {"results": {"<id>": {"circuit_svg": str|null, "circuit_text": str|null,
                           "error": str|null}, ...}}

Design notes (see viz/build_data.py for the caller):
  - We do NOT exec() the full candidate file (which may `import` arbitrary
    modules such as `_backend`, unavailable here). Instead we extract just the
    `# EVOLVE-BLOCK-START ... # EVOLVE-BLOCK-END` region -- a static
    ANSATZ_SPEC = [ {"gate": ..., "wire"/"wires": ..., "param": ...}, ... ]
    list literal -- and exec that under a restricted builtins/globals set.
    This is the same trick tic-tac-toe/make_ansatz_report.py uses, and it
    generalizes across tasks (ttt/su2/sn all share this ANSATZ_SPEC shape).
  - From the spec we build a generic PennyLane circuit (one gate call per
    spec item) and render it with qml.draw_mpl -> SVG. On any failure we
    retry with the plain-text qml.draw drawer. On total failure both fields
    are null and `error` is set.
  - A SIGALRM-based per-item timeout (~20s) guards against a stuck render;
    since we never execute arbitrary top-level candidate code (only the
    static EVOLVE-BLOCK), a genuine hang here is very unlikely, but the
    timeout is kept for defense in depth as requested.
"""
from __future__ import annotations

import io
import json
import re
import signal
import sys
import warnings

warnings.filterwarnings("ignore")

_real_stdout = sys.stdout
sys.stdout = io.StringIO()  # swallow noisy import-time prints/warnings

import matplotlib  # noqa: E402

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"  # keep SVGs small: no embedded glyph paths
import matplotlib.pyplot as plt  # noqa: E402
import pennylane as qml  # noqa: E402
from pennylane.drawer import draw_mpl  # noqa: E402

sys.stdout = _real_stdout

EVOLVE_START = "# EVOLVE-BLOCK-START"
EVOLVE_END = "# EVOLVE-BLOCK-END"
N_QUBITS_RE = re.compile(r"^\s*N_QUBITS\s*=\s*(\d+)", re.MULTILINE)
TIMEOUT_SECONDS = 20

SAFE_BUILTINS = {
    "dict": dict, "enumerate": enumerate, "int": int, "len": len,
    "list": list, "range": range, "str": str, "tuple": tuple,
    "float": float, "bool": bool, "min": min, "max": max, "sum": sum,
    "abs": abs, "sorted": sorted, "zip": zip, "round": round, "set": set,
    "frozenset": frozenset, "map": map, "filter": filter, "any": any,
    "all": all, "reversed": reversed,
}
# Constants a handful of tic-tac-toe evolve-blocks reference by name when
# building ANSATZ_SPEC programmatically (grid geometry of the frozen task).
TTT_GRID_EDGES = ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 0),
                   (1, 8), (3, 8), (5, 8), (7, 8))
EXTRA_GLOBALS = {
    "CORNERS": (0, 2, 4, 6),
    "EDGES": (1, 3, 5, 7),
    "CENTER": 8,
    "GRID_EDGES": TTT_GRID_EDGES,
    "GRID_EDGE_SET": {tuple(sorted(e)) for e in TTT_GRID_EDGES},
}

GATE_1Q = {"RX": qml.RX, "RY": qml.RY, "RZ": qml.RZ}
GATE_2Q_FIXED = {"CNOT": qml.CNOT, "CZ": qml.CZ}
GATE_2Q_PARAM = {"CRX": qml.CRX, "CRY": qml.CRY, "CRZ": qml.CRZ,
                  "XX": qml.IsingXX, "YY": qml.IsingYY, "ZZ": qml.IsingZZ}


class RenderTimeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise RenderTimeout(f"render exceeded {TIMEOUT_SECONDS}s")


class _alarm_guard:
    """SIGALRM-based timeout; no-op on platforms without SIGALRM."""

    def __enter__(self):
        self._have_alarm = hasattr(signal, "SIGALRM")
        if self._have_alarm:
            self._prev = signal.signal(signal.SIGALRM, _alarm_handler)
            signal.alarm(TIMEOUT_SECONDS)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._have_alarm:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, self._prev)
        return False


def extract_evolve_block(code: str) -> str:
    start = code.find(EVOLVE_START)
    end = code.find(EVOLVE_END)
    if start == -1 or end == -1 or end <= start:
        raise ValueError("EVOLVE-BLOCK markers not found")
    start = code.find("\n", start)
    if start == -1:
        raise ValueError("EVOLVE-BLOCK start marker has no following source")
    return code[start + 1:end]


def extract_ansatz_spec(code: str) -> list:
    block = extract_evolve_block(code)
    env = {"__builtins__": SAFE_BUILTINS, **EXTRA_GLOBALS}
    m = N_QUBITS_RE.search(code)
    if m:
        env["N_QUBITS"] = int(m.group(1))
    exec(compile(block, "<evolve_block>", "exec"), env, env)
    spec = env.get("ANSATZ_SPEC")
    if not isinstance(spec, list) or not spec:
        raise ValueError("ANSATZ_SPEC did not evaluate to a non-empty list")
    for i, item in enumerate(spec):
        if not isinstance(item, dict):
            raise ValueError(f"ANSATZ_SPEC[{i}] is {type(item).__name__}, expected dict")
    n_qubits = env.get("N_QUBITS")
    return spec, n_qubits


def spec_wires(item: dict) -> list[int]:
    if item.get("wires") is not None:
        return [int(w) for w in item["wires"]]
    if item.get("wire") is not None:
        return [int(item["wire"])]
    raise ValueError(f"ANSATZ_SPEC item missing wire/wires: {item!r}")


def param_value_table(spec: list) -> dict:
    order = []
    for item in spec:
        p = item.get("param")
        if isinstance(p, str) and p and p not in order:
            order.append(p)
    return {p: round(0.15 + 0.083 * i, 3) for i, p in enumerate(order)}


# While True (the mpl drawer), parameter names are appended on a second line
# inside the gate box; the text drawer chokes on newlines, so it gets an
# inline "RZ(rz_3)" form instead.
_MULTILINE_LABELS = True

# Synthetic angle value -> parameter name for the circuit currently being
# drawn. The drawer pipeline rebuilds ops (map_wires on controlled gates),
# so per-instance label overrides get lost; the parameter VALUE survives any
# rebuild, and param_value_table() makes it unique per name. Class-level
# label patches below use this map.
_VALUE2NAME: dict = {}


def _value_key(op):
    try:
        if op.parameters:
            return round(float(op.parameters[0]), 6)
    except Exception:
        pass
    return None


def _install_label_patches() -> None:
    """Patch label() on our gate classes to append the parameter name
    (angles here are synthetic placeholders, so names — i.e. which gates
    share a parameter — are the only meaningful thing to display)."""
    from pennylane.ops.op_math.controlled import Controlled

    classes = set(GATE_1Q.values()) | set(GATE_2Q_PARAM.values())
    classes |= {qml.MultiRZ, Controlled}
    for cls in classes:
        if "_viz_patched" in cls.__dict__:  # own-dict check: subclasses of a
            continue                        # patched class still need their own wrap
        orig = cls.label

        def label(self, decimals=None, base_label=None, cache=None, _orig=orig):
            base = _orig(self, decimals=None, base_label=base_label, cache=cache)
            name = _VALUE2NAME.get(_value_key(self))
            if not name or name in base:  # 'in base': Controlled delegates to
                return base               # its base op, which is also patched
            return f"{base}\n{name}" if _MULTILINE_LABELS else f"{base}({name})"

        cls.label = label
        cls._viz_patched = True  # noqa: B010 — must land in cls.__dict__


def apply_spec(spec: list, values: dict) -> None:
    for item in spec:
        gate = str(item.get("gate", "")).strip().upper()
        wires = spec_wires(item)
        param = item.get("param")
        angle = values.get(param, 0.5) if isinstance(param, str) else 0.5
        if gate in GATE_1Q:
            op = GATE_1Q[gate](angle, wires=wires[0])
        elif gate in GATE_2Q_FIXED:
            op = GATE_2Q_FIXED[gate](wires=wires)
        elif gate in GATE_2Q_PARAM:
            op = GATE_2Q_PARAM[gate](angle, wires=wires)
        elif gate == "ZZZ":
            op = qml.MultiRZ(angle, wires=wires)
        elif gate == "CCRZ":
            op = qml.ctrl(qml.RZ, control=wires[:2])(angle, wires=wires[2])
        else:
            raise ValueError(f"unsupported gate type {gate!r}")
        del op  # labels come from _VALUE2NAME via the class-level patches


def build_qnode(spec: list, n_qubits: int | None):
    max_wire = max(w for item in spec for w in spec_wires(item))
    n_wires = max(int(n_qubits or 0), max_wire + 1)
    dev = qml.device("default.qubit", wires=n_wires, shots=None)
    values = param_value_table(spec)
    _install_label_patches()
    _VALUE2NAME.clear()
    _VALUE2NAME.update({round(v, 6): p for p, v in values.items()})

    @qml.qnode(dev)
    def circuit():
        apply_spec(spec, values)
        return [qml.expval(qml.PauliZ(w)) for w in range(n_wires)]

    return circuit


def strip_svg_prologue(svg: str) -> str:
    svg = re.sub(r"<\?xml[^>]+\?>", "", svg)
    svg = re.sub(r"<!DOCTYPE[^>]+>", "", svg)
    svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.S)  # RDF/license boilerplate
    return svg.strip()


def render_one(code: str) -> dict:
    try:
        with _alarm_guard():
            spec, n_qubits = extract_ansatz_spec(code)
            circuit = build_qnode(spec, n_qubits)
    except Exception as exc:  # extraction failed: nothing else to try
        return {"circuit_svg": None, "circuit_text": None,
                "error": f"{type(exc).__name__}: {exc}"}

    svg_error = None
    global _MULTILINE_LABELS
    _MULTILINE_LABELS = True
    try:
        with _alarm_guard():
            fig, _ax = draw_mpl(circuit)()
            buf = io.BytesIO()
            fig.savefig(buf, format="svg", bbox_inches="tight")
            plt.close(fig)
            svg = strip_svg_prologue(buf.getvalue().decode("utf-8"))
        return {"circuit_svg": svg, "circuit_text": None, "error": None}
    except Exception as exc:
        svg_error = f"{type(exc).__name__}: {exc}"
        try:
            plt.close("all")
        except Exception:
            pass

    try:
        _MULTILINE_LABELS = False
        with _alarm_guard():
            text = qml.draw(circuit, max_length=200)()
        return {"circuit_svg": None, "circuit_text": text,
                "error": f"svg failed ({svg_error}); used text fallback"}
    except Exception as exc:
        return {"circuit_svg": None, "circuit_text": None,
                "error": f"svg failed ({svg_error}); text also failed "
                         f"({type(exc).__name__}: {exc})"}


def main() -> None:
    payload = json.loads(sys.stdin.read())
    items = payload.get("items", [])
    results = {}
    for item in items:
        pid = item["id"]
        try:
            results[pid] = render_one(item["code"])
        except RenderTimeout as exc:
            results[pid] = {"circuit_svg": None, "circuit_text": None,
                             "error": f"timeout: {exc}"}
        except Exception as exc:  # belt-and-suspenders: never abort the batch
            results[pid] = {"circuit_svg": None, "circuit_text": None,
                             "error": f"worker error: {type(exc).__name__}: {exc}"}
    json.dump({"results": results}, sys.stdout)


if __name__ == "__main__":
    main()
