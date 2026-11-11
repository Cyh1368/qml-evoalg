"""Candidate ansatz schema: validation, expansion, parameters, random search ops.

Schema (frozen, see research/core/INTERFACES.md)::

    {"id": "c0007", "n_qubits": 6,
     "block": [<gate entries>], "repeats": 2, "layers": 2,
     "param_names": ["t0", "t1", ...],
     "hypothesis": {"generators": [[1,0,2,3,4,5]], "output_action": "invariant"},
     "notes": "free text", "source": {"arm": "...", "model": "...", "parent": "c0002"}}

Gate entries inside ``block`` are the repository dict format::

    {"gate": G, "wire": i, "param": name}    G in RX, RY, RZ
    {"gate": G, "wire": i}                   G in H, X, Y, S, T
    {"gate": G, "wires": [a, b]}             G in CNOT, CZ
    {"gate": G, "wires": [a, b], "param": p} G in CRX, CRY, CRZ, RZZ

Only block gates carry trainable ``param`` names. The task feature map carries
fixed ``angle`` entries and is contributed by the task, never by a proposal, so
a ``block`` gate with an ``angle`` is a schema violation.

Full circuit gate list = ``layers x (feature_map(x) + repeats x block)``: the
feature map re-encodes the input before every block application (data
re-uploading), hence expansion is per-example (``expand_example``).

All randomness takes an explicit ``numpy.random.Generator`` (or an integer seed,
which is wrapped in ``default_rng``).
"""
import copy

import numpy as np

# ---------------------------------------------------------------- schema facts
ALLOWED_GATES = ("RX", "RY", "RZ", "CRX", "CRY", "CRZ", "CNOT", "CZ", "RZZ",
                 "H", "X", "Y", "S", "T")
SINGLE_ROTATIONS = ("RX", "RY", "RZ")
SINGLE_FIXED = ("H", "X", "Y", "S", "T")
TWO_FIXED = ("CNOT", "CZ")
TWO_ROTATIONS = ("CRX", "CRY", "CRZ", "RZZ")
PARAM_GATES = SINGLE_ROTATIONS + TWO_ROTATIONS
FIXED_GATES = SINGLE_FIXED + TWO_FIXED
TWO_QUBIT_GATES = TWO_FIXED + TWO_ROTATIONS

# Gate pool used by sample_random / mutate (per WP-CORE: rotations + CNOT/CZ).
RANDOM_GATES = ("RX", "RY", "RZ", "CNOT", "CZ", "CRX", "CRY", "CRZ")
RANDOM_PARAM_GATES = ("RX", "RY", "RZ", "CRX", "CRY", "CRZ")

MAX_BLOCK_GATES = 64          # hard cap enforced by validate()
MIN_PARAMS = 4                # sample_random / mutate keep 4..8 parameter names
MAX_PARAMS = 8
DEFAULT_LAYERS = 2            # fixed pipeline, matches search/prompts.py
DEFAULT_REPEATS = 2
OUTPUT_ACTIONS = ("invariant",)
REQUIRED_KEYS = ("block", "param_names", "n_qubits", "layers", "repeats")


class CandidateError(ValueError):
    """Raised for operations that cannot proceed on an invalid candidate."""


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def as_rng(rng):
    """Accept a Generator, an integer seed, or None; return a Generator."""
    if isinstance(rng, np.random.Generator):
        return rng
    return np.random.default_rng(rng)


def new_id(rng, prefix="c"):
    return "%s%04d" % (prefix, int(as_rng(rng).integers(0, 10 ** 4)))


# --------------------------------------------------------------- validation
def _gate_wires(entry):
    """Return the wire list of a gate entry ([] when absent/malformed)."""
    if not isinstance(entry, dict):
        return []
    if "wires" in entry:
        wires = entry["wires"]
        if isinstance(wires, (list, tuple)):
            return list(wires)
        return [wires]
    if "wire" in entry:
        return [entry["wire"]]
    return []


def _check_wires(wires, want, n, where, errors):
    if len(wires) != want:
        errors.append("%s: expected %d wire(s), got %r" % (where, want, wires))
        return False
    ok = True
    for w in wires:
        if not _is_int(w) or not 0 <= w < n:
            errors.append("%s: wire %r outside 0..%d" % (where, w, n - 1))
            ok = False
    if want == 2 and all(_is_int(w) for w in wires) and wires[0] == wires[1]:
        errors.append("%s: two-qubit gate repeats wire %r" % (where, wires[0]))
        ok = False
    return ok


def _check_gate(entry, index, n, errors, used):
    where = "block[%d]" % index
    if not isinstance(entry, dict):
        errors.append("%s: gate entry is not a JSON object" % where)
        return
    name = entry.get("gate")
    if name not in ALLOWED_GATES:
        errors.append("%s: unknown gate %r (allowed: %s)"
                      % (where, name, ", ".join(ALLOWED_GATES)))
        return
    if "angle" in entry:
        errors.append("%s: %s carries a fixed 'angle'; fixed-angle gates belong "
                      "to the task feature map, block gates must use 'param'"
                      % (where, name))
    extra = set(entry) - {"gate", "wire", "wires", "param", "angle"}
    if extra:
        errors.append("%s: unexpected key(s) %s" % (where, sorted(extra)))
    if name in TWO_QUBIT_GATES:
        if "wire" in entry or "wires" not in entry:
            errors.append("%s: %s needs \"wires\": [a, b]" % (where, name))
            return
        _check_wires(_gate_wires(entry), 2, n, where, errors)
    else:
        if "wires" in entry or "wire" not in entry:
            errors.append("%s: %s needs \"wire\": i" % (where, name))
            return
        _check_wires(_gate_wires(entry), 1, n, where, errors)
    if name in PARAM_GATES:
        param = entry.get("param")
        if not isinstance(param, str) or not param:
            errors.append("%s: %s needs a non-empty string 'param'" % (where, name))
        elif param not in used:
            used.append(param)
    elif "param" in entry:
        errors.append("%s: %s is a fixed gate and must not carry 'param'"
                      % (where, name))


def _check_hypothesis(hypothesis, n, errors):
    if hypothesis is None:
        return
    if not isinstance(hypothesis, dict):
        errors.append("hypothesis: must be null or an object")
        return
    if "generators" not in hypothesis:
        errors.append("hypothesis: missing 'generators'")
        return
    gens = hypothesis["generators"]
    if not isinstance(gens, list) or not gens:
        errors.append("hypothesis.generators: must be a non-empty list of "
                      "one-line permutations")
        return
    for i, gen in enumerate(gens):
        if not isinstance(gen, (list, tuple)):
            errors.append("hypothesis.generators[%d]: must be a list of %d "
                          "integers" % (i, n))
            continue
        if len(gen) != n:
            errors.append("hypothesis.generators[%d]: length %d != n_qubits %d"
                          % (i, len(gen), n))
            continue
        if not all(_is_int(v) for v in gen):
            errors.append("hypothesis.generators[%d]: entries must be integers" % i)
            continue
        if sorted(gen) != list(range(n)):
            errors.append("hypothesis.generators[%d]: %r is not a permutation of "
                          "range(%d)" % (i, list(gen), n))
    action = hypothesis.get("output_action", "invariant")
    if action not in OUTPUT_ACTIONS:
        errors.append("hypothesis.output_action: %r not in %s"
                      % (action, list(OUTPUT_ACTIONS)))


def validate(candidate, task=None):
    """Return a list of schema/consistency errors; an empty list means valid.

    ``task`` may be a TaskSpec (or anything exposing ``n_qubits``) or None, in
    which case the n_qubits cross-check against the task is skipped.
    """
    errors = []
    if not isinstance(candidate, dict):
        return ["candidate: not a JSON object (got %s)" % type(candidate).__name__]
    task_n = int(getattr(task, "n_qubits", 0) or 0) if task is not None else 0
    for key in REQUIRED_KEYS:
        if key not in candidate:
            errors.append("missing required key '%s'" % key)
    n = candidate.get("n_qubits")
    if "n_qubits" in candidate:
        if not _is_int(n) or n < 1:
            errors.append("n_qubits: must be an integer >= 1 (got %r)" % (n,))
            n = task_n
        elif task_n and int(n) != task_n:
            errors.append("n_qubits: candidate says %d, task %s has %d"
                          % (n, getattr(task, "name", "?"), task_n))
            n = task_n
    if not n:
        n = task_n
    if n < 1:
        errors.append("n_qubits: unknown (candidate and task both missing)")
    for key in ("layers", "repeats"):
        if key in candidate and (not _is_int(candidate[key]) or candidate[key] < 1):
            errors.append("%s: must be an integer >= 1 (got %r)"
                          % (key, candidate[key]))
    block = candidate.get("block")
    if block is None and "block" in candidate:
        errors.append("block: must be a list of gate entries (got %r)" % (block,))
        block = []
    if not isinstance(block, list):
        errors.append("block: must be a list of gate entries")
        block = []
    if len(block) > MAX_BLOCK_GATES:
        errors.append("block: %d gates exceeds the cap of %d"
                      % (len(block), MAX_BLOCK_GATES))
    names = candidate.get("param_names")
    if names is None and "param_names" in candidate:
        errors.append("param_names: must be a list of strings (got %r)" % (names,))
        names = []
    if not isinstance(names, list):
        errors.append("param_names: must be a list of strings")
        names = []
    if any(not isinstance(name, str) or not name for name in names):
        errors.append("param_names: every entry must be a non-empty string")
        names = [name for name in names if isinstance(name, str) and name]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        errors.append("param_names: duplicate name(s) %s" % duplicates)
    used = []
    for index, entry in enumerate(block):
        _check_gate(entry, index, int(n), errors, used)
    declared = set(names)
    undeclared = [name for name in used if name not in declared]
    if undeclared:
        errors.append("block uses parameter(s) %s not declared in param_names"
                      % undeclared)
    unused = [name for name in names if name not in set(used)]
    if unused:
        errors.append("param_names declares parameter(s) %s that no block gate "
                      "uses" % unused)
    _check_hypothesis(candidate.get("hypothesis"), int(n), errors)
    return errors


# --------------------------------------------------------------- expansion
def expand_example(candidate, task, x):
    """Full per-example gate list: layers x (feature_map(x) + repeats x block).

    Feature-map gates carry fixed ``angle`` entries; only block gates carry
    ``param``. Returns ``(gates, param_names)``.
    """
    if not isinstance(candidate, dict):
        raise CandidateError("candidate must be a dict")
    n = int(candidate.get("n_qubits") or getattr(task, "n_qubits"))
    layers = int(candidate.get("layers", DEFAULT_LAYERS))
    repeats = int(candidate.get("repeats", DEFAULT_REPEATS))
    if layers < 1 or repeats < 1:
        raise CandidateError("layers and repeats must be >= 1 (got %d, %d)"
                             % (layers, repeats))
    x = np.asarray(x)
    block = list(candidate.get("block") or [])
    gates = []
    for _ in range(layers):
        gates.extend(dict(entry) for entry in task.feature_map(x))
        for _ in range(repeats):
            gates.extend(dict(entry) for entry in block)
    del n  # n is informational here; the simulator takes it explicitly
    return gates, list(candidate.get("param_names") or [])


def expand(candidate, task, x=None):
    """Convenience wrapper: expand on one row (``task.x[0]`` when x is None).

    Expansion is per-example; use :func:`expand_example` in loops.
    """
    if x is None:
        rows = getattr(task, "x", None)
        if rows is None or len(rows) == 0:
            raise CandidateError("expand needs an input row: pass x explicitly")
        x = np.asarray(rows)[0]
    return expand_example(candidate, task, x)


# --------------------------------------------------------------- parameters
def param_names(candidate):
    return list(candidate.get("param_names") or [])


def n_params(candidate):
    return len(param_names(candidate))


def count_gates(candidate):
    """Number of gates in the proposed BLOCK (one repeat)."""
    return len(candidate.get("block") or [])


def param_vector(candidate, pdict):
    """Parameter dict -> vector ordered as ``candidate['param_names']``."""
    names = param_names(candidate)
    if not isinstance(pdict, dict):
        raise CandidateError("param_vector expects a dict of name -> value")
    missing = [name for name in names if name not in pdict]
    if missing:
        raise KeyError("missing parameter value(s) for %s" % missing)
    return np.array([float(pdict[name]) for name in names], dtype=float)


def param_dict(candidate, vec):
    """Vector -> dict aligned with ``candidate['param_names']``."""
    names = param_names(candidate)
    values = np.asarray(vec, dtype=float).reshape(-1)
    if values.size != len(names):
        raise ValueError("param_dict: got %d value(s) for %d parameter name(s)"
                         % (values.size, len(names)))
    return {name: float(value) for name, value in zip(names, values)}


# --------------------------------------------------------------- generation
def _used_params(block):
    used = []
    for entry in block:
        if isinstance(entry, dict):
            name = entry.get("param")
            if isinstance(name, str) and name and name not in used:
                used.append(name)
    return used


def _fresh_name(existing, rng):
    existing = set(existing)
    k = 0
    while ("t%d" % k) in existing:
        k += 1
    return "t%d" % k


def _make_gate(name, rng, n, param=None):
    name = str(name)
    if name in TWO_QUBIT_GATES:
        a = int(rng.integers(n))
        b = int(rng.integers(n - 1))
        b = b if b < a else b + 1
        entry = {"gate": name, "wires": [a, b]}
    else:
        entry = {"gate": name, "wire": int(rng.integers(n))}
    if name in PARAM_GATES:
        entry["param"] = param
    return entry


def _random_gate(rng, n, names, allow_new_name=True):
    name = str(rng.choice(RANDOM_GATES))
    param = None
    if name in PARAM_GATES and names:
        if allow_new_name and len(names) < MAX_PARAMS and rng.random() < 0.35:
            param = _fresh_name(names, rng)
        else:
            param = str(rng.choice(list(names)))
    elif name in PARAM_GATES:
        param = _fresh_name(names, rng)
    return _make_gate(name, rng, n, param=param)


def _reconcile_params(candidate, rng):
    """Make param_names and block usage consistent, keeping MIN..MAX names."""
    block = candidate["block"]
    param_slots = [i for i, g in enumerate(block)
                   if isinstance(g, dict) and g.get("gate") in PARAM_GATES]
    if block and not param_slots:  # keep at least one trainable gate
        index = int(rng.integers(len(block)))
        gate = str(rng.choice(SINGLE_ROTATIONS))
        entry = {"gate": gate, "wire": int(rng.integers(max(1, int(
            candidate.get("n_qubits") or 1))))}
        entry["param"] = _fresh_name(_used_params(block), rng)
        block[index] = entry
        param_slots = [index]
    used = _used_params(block)
    if len(used) > MAX_PARAMS:  # retie the overflow onto the kept names
        keep = used[:MAX_PARAMS]
        remap = {name: (name if i < MAX_PARAMS else str(rng.choice(keep)))
                 for i, name in enumerate(used)}
        for entry in block:
            if isinstance(entry, dict) and entry.get("param") in remap:
                entry["param"] = remap[entry["param"]]
        used = list(keep)
    while len(used) < MIN_PARAMS and param_slots:
        fresh = _fresh_name(used, rng)
        slot = int(param_slots[int(rng.integers(len(param_slots)))])
        block[slot]["param"] = fresh
        used.append(fresh)
    candidate["param_names"] = list(used)
    return candidate


def sample_random(rng, task, max_block=24):
    """Schema-valid random candidate: 4..max_block gates, 4..8 parameters."""
    rng = as_rng(rng)
    n = int(getattr(task, "n_qubits", 6))
    cap = int(max(1, min(int(max_block), MAX_BLOCK_GATES)))
    length = int(rng.integers(min(MIN_PARAMS, cap), cap + 1))
    names = ["t%d" % i for i in range(int(rng.integers(MIN_PARAMS, MAX_PARAMS + 1)))]
    block = []
    unused = list(names)
    for position in range(length):
        remaining = length - position - 1
        if len(unused) > remaining:  # a declared name must be consumed now
            gate = str(rng.choice(RANDOM_PARAM_GATES))
            param = unused.pop(int(rng.integers(len(unused))))
            block.append(_make_gate(gate, rng, n, param=param))
        else:
            block.append(_random_gate(rng, n, names, allow_new_name=False))
    candidate = {"id": new_id(rng), "n_qubits": n, "block": block,
                 "repeats": DEFAULT_REPEATS, "layers": DEFAULT_LAYERS,
                 "param_names": names, "hypothesis": None,
                 "notes": "random baseline candidate",
                 "source": {"arm": "random", "model": None, "parent": None}}
    if rng.random() < 0.5:  # random relabeling claim, never the true group
        generators = [[int(v) for v in rng.permutation(n)]
                      for _ in range(int(rng.integers(1, 3)))]
        candidate["hypothesis"] = {"generators": generators,
                                   "output_action": "invariant"}
    _reconcile_params(candidate, rng)
    return candidate


# --------------------------------------------------------------- mutation
MUTATIONS = ("point", "insert", "delete", "reorder", "retie")


def _mutate_once(candidate, rng, task):
    """One structural mutation; the result is reconciled but not yet checked."""
    n = int(getattr(task, "n_qubits", None) or candidate.get("n_qubits") or 1)
    child = copy.deepcopy(dict(candidate))
    child["n_qubits"] = n
    block = child.get("block")
    if not isinstance(block, list):
        block = []
    child["block"] = block
    ops = list(MUTATIONS)
    if len(block) <= 1:
        ops = [op for op in ops if op not in ("delete", "reorder")]
    if len(block) >= MAX_BLOCK_GATES:
        ops = [op for op in ops if op != "insert"]
    op = str(rng.choice(ops))
    names = [name for name in (child.get("param_names") or [])
             if isinstance(name, str) and name]
    if op == "point":
        index = int(rng.integers(len(block)))
        entry = block[index]
        two_qubit = isinstance(entry, dict) and entry.get("gate") in TWO_QUBIT_GATES
        if rng.random() < 0.5:  # swap the gate name, keep the arity
            pool = (TWO_ROTATIONS + TWO_FIXED if two_qubit
                    else SINGLE_ROTATIONS + SINGLE_FIXED)
            block[index] = _make_gate(str(rng.choice(pool)), rng, n,
                                      param=entry.get("param")
                                      if isinstance(entry, dict) else None)
        elif two_qubit and len(_gate_wires(entry)) == 2:  # perturb one wire
            a, b = _gate_wires(entry)
            if rng.random() < 0.5:
                a = int(rng.integers(n))
            else:
                b = int(rng.integers(n))
            if a == b:
                b = (int(b) + 1) % n
            entry["wires"] = [int(a), int(b)]
        else:
            entry["wire"] = int(rng.integers(n))
    elif op == "insert":
        block.insert(int(rng.integers(len(block) + 1)),
                     _random_gate(rng, n, names or None))
    elif op == "delete":
        del block[int(rng.integers(len(block)))]
    elif op == "reorder":
        source = int(rng.integers(len(block)))
        target = int(rng.integers(len(block)))
        block.insert(target, block.pop(source))
    else:  # retie: merge two parameter names, or untie one onto a fresh name
        used = _used_params(block)
        if len(used) > 1 and rng.random() < 0.6:
            source = str(rng.choice(used))
            target = str(rng.choice([name for name in used if name != source]))
        elif used:
            source = str(rng.choice(used))
            target = _fresh_name(used, rng)
        else:
            source = target = None
        if source is not None:
            for entry in block:
                if isinstance(entry, dict) and entry.get("param") == source:
                    entry["param"] = target
    _reconcile_params(child, rng)
    child["id"] = new_id(rng)
    parent = candidate.get("id")
    child["source"] = {"arm": "mutation-ea", "model": None,
                       "parent": parent if isinstance(parent, str) else None}
    return child


def mutate(candidate, rng, task, max_attempts=12):
    """Point / insert / delete / reorder / retie mutation.

    Always returns a schema-valid candidate: a mutation that fails
    :func:`validate` is retried, and after ``max_attempts`` failures the
    candidate is re-sampled with :func:`sample_random`.
    """
    rng = as_rng(rng)
    for _ in range(int(max_attempts)):
        child = _mutate_once(candidate, rng, task)
        if not validate(child, task):
            return child
    return sample_random(rng, task)
