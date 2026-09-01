"""Decompose every evolved ANSATZ_SPEC into layers and label each layer's symmetry.

Reads the viz run dumps (viz/data/run_*.js), extracts ANSATZ_SPEC from each
program's source, splits it into layers, and labels each layer.  Writes
analysis/labelling/labels.json.

Layer rule
----------
ANSATZ_SPEC is an ordered gate list.  Each gate gets a key:
    1-qubit  RX/RY/RZ      -> ("1q", gate, param_family)
    2-qubit  CZ/CNOT       -> ("2q", gate, "")
    2-qubit  CRX/CRY/CRZ   -> ("2q", gate, param_family)
where param_family strips trailing numeric indices ("ry_3" -> "ry",
"ent_0_1" -> "ent").  A layer is a maximal run of consecutive gates with the
same key.  A second pass merges windows of >=4 consecutive short segments
(<=2 gates each) drawing on <=3 distinct keys, so a per-wire interleaved
pattern like RY,RZ,RY,RZ,... is treated as one layer rather than many.
"""
from __future__ import annotations

import ast
import json
import os
import re
import glob
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NQ = 8
ONEQ = {"RX", "RY", "RZ"}
TWOQ_CONST = {"CZ", "CNOT"}
TWOQ_PARAM = {"CRX", "CRY", "CRZ"}
ALL_PAIRS = frozenset(frozenset((i, j)) for i in range(NQ) for j in range(i + 1, NQ))


def load_run(path):
    s = open(path).read()
    i = s.index('{"run_id"')
    return json.loads(s[i:].rstrip().rstrip(";"))


def _spec_from_source(src):
    """Literal ANSATZ_SPEC if possible, else execute the source and read it."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    found = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "ANSATZ_SPEC":
                    found = node.value
    if found is None:
        return None
    try:
        lit = ast.literal_eval(found)
        if isinstance(lit, list) and lit:
            return lit
    except (ValueError, SyntaxError, TypeError):
        pass
    # built programmatically (loops / comprehensions): execute the block
    import itertools, math
    import numpy as _np
    ns = {"__builtins__": __builtins__, "np": _np, "numpy": _np,
          "itertools": itertools, "math": math, "N_QUBITS": NQ,
          "N_UPLOADS": 3, "N_REPEATS": 2,
          "ALLOWED_SINGLE_QUBIT_GATES": set(ONEQ),
          "ALLOWED_TWO_QUBIT_GATES": set(TWOQ_CONST),
          "ALLOWED_PARAM_TWO_QUBIT_GATES": set(TWOQ_PARAM)}
    try:
        exec(compile(tree, "<ansatz>", "exec"), ns)
    except Exception:
        return None
    v = ns.get("ANSATZ_SPEC")
    return v if isinstance(v, list) else None


def extract_spec(code):
    """Prefer the EVOLVE-BLOCK alone: stored sources sometimes carry a stray
    diff marker further down that makes the whole file unparseable."""
    if not code:
        return None
    i = code.find("EVOLVE-BLOCK-START")
    if i >= 0:
        body = code[i + len("EVOLVE-BLOCK-START"):]
        for stop in ("EVOLVE-BLOCK-END", "\n=======", "\n<<<<<<<", "\n>>>>>>>"):
            j = body.find(stop)
            if j >= 0:
                body = body[:j]
        body = re.sub(r"^\s*#.*$", "", body, flags=re.M)
        spec = _spec_from_source(body)
        if spec:
            return spec
    return _spec_from_source(code)


def fam(p):
    if not isinstance(p, str):
        return ""
    f = re.sub(r"(_?\d+)+$", "", p)
    return f or p


def norm(spec):
    """Normalise to a list of dicts: kind, gate, wires (tuple), param, fam."""
    out = []
    for it in spec:
        if not isinstance(it, dict):
            return None
        g = str(it.get("gate", "")).upper()
        if g in ONEQ:
            w = it.get("wire")
            if not isinstance(w, int):
                return None
            out.append({"kind": "1q", "gate": g, "wires": (w,),
                        "param": it.get("param"), "fam": fam(it.get("param"))})
        elif g in TWOQ_CONST | TWOQ_PARAM:
            ws = it.get("wires")
            if not isinstance(ws, (list, tuple)) or len(ws) != 2:
                return None
            p = it.get("param") if g in TWOQ_PARAM else None
            out.append({"kind": "2q", "gate": g, "wires": tuple(int(x) for x in ws),
                        "param": p, "fam": fam(p) if p else ""})
        else:
            return None
    return out


def key(g):
    return (g["kind"], g["gate"], g["fam"])


def segment(gates):
    segs, cur = [], []
    for g in gates:
        if cur and key(g) != key(cur[-1]):
            segs.append(cur)
            cur = []
        cur.append(g)
    if cur:
        segs.append(cur)
    # merge interleaved short segments
    merged, i = [], 0
    while i < len(segs):
        j = i
        while j < len(segs) and len(segs[j]) <= 2:
            j += 1
        window = segs[i:j]
        if len(window) >= 4 and len({key(s[0]) for s in window}) <= 3:
            merged.append([g for s in window for g in s])
            i = j
        else:
            merged.append(segs[i])
            i += 1
    return merged


def label_layer(layer):
    one = [g for g in layer if g["kind"] == "1q"]
    two = [g for g in layer if g["kind"] == "2q"]

    # --- 1-qubit structure
    per_wire = defaultdict(list)
    for g in one:
        per_wire[g["wire_"] if False else g["wires"][0]].append(g["gate"])
    sig1 = {w: tuple(sorted(v)) for w, v in per_wire.items()}
    params1 = {g["param"] for g in one}
    all_singular = bool(one) and len(sig1) == NQ and len(set(sig1.values())) == 1
    singular_tied = all_singular and len(params1) == 1

    # --- 2-qubit structure
    per_pair = defaultdict(list)
    for g in two:
        per_pair[frozenset(g["wires"])].append(g["gate"])
    sig2 = {p: tuple(sorted(v)) for p, v in per_pair.items()}
    params2 = {g["param"] for g in two if g["param"]}
    pairs = set(sig2)
    all_double = bool(two) and pairs == set(ALL_PAIRS) and len(set(sig2.values())) == 1
    double_tied = all_double and len(params2) == 1

    labels = set()
    if all_singular:
        labels.add("all-singular")
        if singular_tied:
            labels.add("all-singular-tied")
    if all_double:
        labels.add("all-double")
        if double_tied:
            labels.add("all-double-tied")
        # Exactly S_8-invariant: CZ is symmetric in its two wires, so one CZ on
        # each of the 28 pairs is invariant on its own.  A controlled rotation is
        # directed, so it is invariant only if every pair carries the same angle
        # in both directions.
        gate_set = {g["gate"] for g in two}
        if gate_set == {"CZ"} and len(two) == 28:
            labels.add("all-double-exact")
        elif gate_set <= TWOQ_PARAM and len(params2) == 1:
            dirs = Counter(g["wires"] for g in two)
            if all(dirs[(a, b)] == dirs[(b, a)] for (a, b) in list(dirs)):
                labels.add("all-double-exact")

    # linear chain / ring on the 2-qubit part
    chain = {frozenset((i, i + 1)) for i in range(NQ - 1)}
    ring = chain | {frozenset((NQ - 1, 0))}
    if two and pairs == chain:
        labels.add("linear-chain")
    if two and pairs == ring:
        labels.add("ring")

    # mirror i -> 7-i and cyclic i -> i+1 (mod 8), only if not already S_8-uniform
    def refl(w):
        return NQ - 1 - w

    def shift(w):
        return (w + 1) % NQ

    def invariant(m, f):
        if not m:
            return False
        try:
            return {(frozenset(f(x) for x in k) if isinstance(k, frozenset) else f(k)): v
                    for k, v in m.items()} == m
        except TypeError:
            return False

    if not (all_singular or all_double):
        mir = (invariant(sig2, refl) if two else True) and (invariant(sig1, refl) if one else True)
        cyc = (invariant(sig2, shift) if two else True) and (invariant(sig1, shift) if one else True)
        if (one or two) and mir:
            labels.add("mirror")
        if (one or two) and cyc and "ring" not in labels:
            labels.add("cyclic")
    if not labels:
        labels.add("none")

    return {
        "n_gates": len(layer),
        "gates": sorted({g["gate"] for g in layer}),
        "n_1q": len(one),
        "n_2q": len(two),
        "n_wires": len(sig1),
        "n_pairs": len(pairs),
        "pair_coverage": len(pairs) / 28.0 if two else 0.0,
        "n_params": len(params1 | params2),
        "labels": sorted(labels),
    }


def label_circuit(spec):
    gates = norm(spec)
    if gates is None or not gates:
        return None
    layers = [label_layer(l) for l in segment(gates)]
    lab = set()
    for l in layers:
        lab |= set(l["labels"])
    lab.discard("none")
    if not lab:
        lab.add("none")
    return {
        "n_gates": len(gates),
        "n_layers": len(layers),
        "max_pair_coverage": max((l["pair_coverage"] for l in layers), default=0.0),
        "layers": layers,
        "labels": sorted(lab),
    }


ARMS = {"weak": "weak", "mid": "mid", "frontier": "frontier", "frontabl": "frontier-no-gpt"}


def classify(rid):
    """(setting, arm) or None if the run is out of scope."""
    m = re.match(r"sn-transfer-or_(weak|mid|frontier)(_e1)?_r\d+$", rid)
    if m:
        return ("scratch", m.group(1), 20 if m.group(2) else 50)
    m = re.match(r"sn-transfer-frw3_(weak|mid|frontier|frontabl)_r\d+$", rid)
    if m:
        return ("continue", ARMS[m.group(1)], 4)
    return None


def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "viz/data/run_sn-transfer-*.js"))):
        rid = os.path.basename(f)[4:-3]
        c = classify(rid)
        if not c:
            continue
        setting, arm, budget = c
        run = load_run(f)
        for p in run["programs"]:
            gen = p["generation"]
            # in continuation runs, generations 0-3 are the inherited frontier
            # ancestry; only gen >= 4 was proposed by this run's ensemble.
            own = (gen >= 4) if setting == "continue" else (gen >= 1)
            lc = label_circuit(extract_spec(p.get("code")) or [])
            rows.append({
                "run_id": rid, "setting": setting, "arm": arm, "budget": budget,
                "program_id": p["id"], "generation": gen,
                "score": p["combined_score"], "correct": p.get("correct"),
                "model": p.get("model_name"), "own": own,
                "parsed": lc is not None,
                **({"circuit": lc} if lc else {}),
            })
    out = os.path.join(HERE, "labels.json")
    json.dump(rows, open(out, "w"))
    print("programs:", len(rows), "parsed:", sum(r["parsed"] for r in rows))
    print("runs:", len({r["run_id"] for r in rows}))


if __name__ == "__main__":
    main()
