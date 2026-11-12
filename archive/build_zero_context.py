"""Build zero-context variants of the three ansatz-search tasks.

Research question: can the proposer identify a symmetry with NO context about the
problem? It must get there only by proposing circuits and reading the numbers.

Two leak channels are closed:
  1. the task message, rewritten to describe nothing but qubit count and gates;
  2. the seed program, which ShinkaEvolve embeds in the prompt IN FULL. All data
     loading, encoding, readout and training code moves into `_backend.py`, which
     is imported and therefore never shown.

What the proposer is left with: N qubits, the legal gate schema, the parameter
sharing mechanism, and per-generation numeric feedback. Nothing else.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ----------------------------------------------------------------- task table
TASKS = {
    "ttt": {
        "src": ROOT / "tic-tac-toe/shinka_cluster_motif_anon",
        "dst": ROOT / "zc-ttt",
        "n_qubits": 9,
        "extra": ["data_splits.npz", "permutation_meta.json", "motif_analysis.py"],
        "schema": """- Single-qubit parametrized gates:
  {"gate": "RX"|"RY"|"RZ", "wire": int 0..8, "param": "name"}
- Fixed two-qubit gates:
  {"gate": "CNOT"|"CZ", "wires": [first, second]}
- Parametrized controlled rotations:
  {"gate": "CRX"|"CRY"|"CRZ", "wires": [control, target], "param": "name"}
- Parametrized three-qubit interactions (any three distinct qubits 0..8):
  {"gate": "ZZZ", "wires": [a, b, c], "param": "name"}
  {"gate": "CCRZ", "wires": [control_1, control_2, target], "param": "name"}

Two-qubit gates are allowed only on these qubit pairs:
(0,2), (0,3), (0,7), (0,8), (1,3), (1,8),
(2,4), (2,6), (3,5), (4,8), (5,7), (6,7).
Three-qubit gates have no such restriction: any 3 distinct qubits.""",
        "quality": """Improve validation accuracy, reduce the train-test gap, reduce
L2 loss, use parameters efficiently, and converge in fewer steps.""",
    },
    "sn": {
        "src": ROOT / "transfer-sn",
        "dst": ROOT / "zc-sn",
        "n_qubits": 8,
        "extra": ["dataset.npz", "answer_key.json", "symmetry_analysis.py"],
        "schema": """- Single-qubit parametrized gates:
  {"gate": "RX"|"RY"|"RZ", "wire": int 0..7, "param": "name"}
- Fixed two-qubit gates:
  {"gate": "CNOT"|"CZ", "wires": [first, second]}
- Parametrized controlled rotations:
  {"gate": "CRX"|"CRY"|"CRZ", "wires": [control, target], "param": "name"}

Two-qubit gates may act on ANY pair of distinct qubits.""",
        "quality": """Improve validation accuracy, reduce the train-test gap, reduce
L2 loss, use parameters efficiently, and converge in fewer steps.""",
    },
    "su2": {
        "src": ROOT / "transfer-su2",
        "dst": ROOT / "zc-su2",
        "n_qubits": 8,
        # Local-only artifacts (answer_key.json, symmetry_analysis.py,
        # make_dataset.py) are deliberately NOT listed: the evolve block is
        # arbitrary Python, so anything in the task dir is reachable at eval
        # time. Only the opaque dataset ships.
        "extra": ["dataset.npz"],
        "schema": """- Single-qubit parametrized gates:
  {"gate": "RX"|"RY"|"RZ", "wire": int 0..7, "param": "name"}
- Fixed two-qubit gates:
  {"gate": "CNOT"|"CZ", "wires": [first, second]}
- Parametrized two-qubit gates:
  {"gate": "CRX"|"CRY"|"CRZ", "wires": [control, target], "param": "name"}
  {"gate": "XX"|"YY"|"ZZ", "wires": [a, b], "param": "name"}

Two-qubit gates may act on ANY pair of distinct qubits.""",
        "quality": """The score is dominated by ROBUST SEPARATION: validation samples
are grouped by hidden difficulty, and the largest score term is the margin of
the WORST group, so the classifier must separate the hardest samples, not just
the average ones. The training set is very small, and held-out behaviour is the
only thing that counts: fitting the training set is a poor predictor of the
score, so structures that generalize from few examples win. Parameter economy
matters at every count: fewer distinct trainable parameter names ALWAYS scores
higher, with no point of diminishing returns. Also reduce the train-test gap and
converge in fewer steps.""",
    },
}

REPEAT_NOTES = {
    "ttt": "with independent parameter copies per repetition.",
    "sn": "with independent parameter copies per repetition.",
    "su2": ("with the SAME parameter values in every repetition: the trainable "
            "parameter count equals the number of distinct param names."),
}

PROMPT = """
You are optimizing a parametrized quantum circuit.

Goal:
Evolve the ANSATZ_SPEC below. Fixed code trains each candidate and returns
numeric feedback. You are NOT told what the data is, what the inputs represent,
what the labels mean, or how the inputs are encoded into the circuit, and you do
not need to know any of it. Your only guide is the feedback you receive.

Fixed architecture:
- {n} qubits, indexed 0..{last}.
- The input encoding, the readout, the training loop and the metrics are fixed
  and are implemented outside this file.
- The candidate ansatz block is applied a fixed number of times, {repeat_note}

Only edit the EVOLVE-BLOCK, that is ANSATZ_SPEC. Nothing else is editable.

Formal ANSATZ_SPEC schema:
{schema}

Parameter sharing:
Reusing the same param string shares that parameter within one ansatz block.
Use sharing deliberately: it is the only way to reduce the parameter count
without removing gates.

Candidate quality:
{quality}

Invalid candidates are rejected for unsupported gates, bad wires, non-finite
metrics, or too many parameters.
"""

SEED_DOC = '''"""Seed program. Only ANSATZ_SPEC inside the EVOLVE-BLOCK is evolved.

Everything else about the task, that is how inputs are encoded, how the circuit
is measured, how training works and how metrics are computed, is fixed and lives
in a module that is not reproduced here. No information about the data is
available in this file.
"""
'''


def split_seed(src_seed: Path) -> tuple[str, str]:
    """Return (backend_source, evolve_block_source)."""
    text = src_seed.read_text()
    m = re.search(r"# EVOLVE-BLOCK-START\n(.*?)# EVOLVE-BLOCK-END\n", text, re.S)
    if not m:
        raise SystemExit(f"no evolve block in {src_seed}")
    block = m.group(1)

    backend = text[: m.start()] + text[m.end():]

    # The spec-derived module globals must become rebindable, since the spec now
    # arrives as an argument rather than being defined in this file. Seeds differ
    # in exactly which N_* constants they derive, so take the whole run of
    # consecutive assignments that follows and replay it inside bind_spec().
    anchor = "SPEC_ERRORS, PARAMETER_KEYS_PER_BLOCK = validate_ansatz_spec(ANSATZ_SPEC)\n"
    start = backend.find(anchor)
    if start < 0:
        raise SystemExit(f"could not find the spec-binding anchor in {src_seed}")
    lines = backend[start:].split("\n")
    assign = re.compile(r"^([A-Z_][A-Z0-9_]*(?:, [A-Z_][A-Z0-9_]*)*) = ")
    taken, names = [], ["ANSATZ_SPEC"]
    for line in lines:
        m2 = assign.match(line)
        if not m2:
            break
        taken.append(line)
        names += [n.strip() for n in m2.group(1).split(",")]
    end = start + len(("\n".join(taken) + "\n"))

    body = "\n".join("    " + t for t in taken)
    body = body.replace("validate_ansatz_spec(ANSATZ_SPEC)", "validate_ansatz_spec(spec)")
    uniq = list(dict.fromkeys(names))
    replacement = (
        "ANSATZ_SPEC: list = []\n"
        "SPEC_ERRORS: list = []\n"
        "PARAMETER_KEYS_PER_BLOCK: list = []\n"
        + "".join(f"{n} = 0\n" for n in uniq
                  if n not in ("ANSATZ_SPEC", "SPEC_ERRORS", "PARAMETER_KEYS_PER_BLOCK"))
        + "\n\n"
        "def bind_spec(spec):\n"
        '    """Install the candidate spec and recompute the derived sizes."""\n'
        + "".join(f"    global {n}\n" for n in uniq)
        + "    ANSATZ_SPEC = spec\n"
        + body + "\n")
    backend = backend[:start] + replacement + backend[end:]

    # run_experiment now takes the spec first and binds it before doing anything.
    backend = backend.replace(
        "def run_experiment(\n    seed: int = 0,",
        "def run_experiment(\n    spec,\n    seed: int = 0,", 1)
    backend = backend.replace(
        '    """Train the candidate ansatz and return ShinkaEvolve metrics."""\n',
        '    """Train the candidate ansatz and return ShinkaEvolve metrics."""\n'
        "    bind_spec(spec)\n", 1)
    return backend, block


def build(tag: str, cfg: dict) -> None:
    src, dst = cfg["src"], cfg["dst"]
    dst.mkdir(parents=True, exist_ok=True)
    backend, block = split_seed(src / "initial_program.py")
    (dst / "_backend.py").write_text(backend)

    n = cfg["n_qubits"]
    seed = (SEED_DOC
            + "\nfrom _backend import run_experiment as _run\n\n"
            + f"N_QUBITS = {n}\n"
            + 'ALLOWED_SINGLE_QUBIT_GATES = {"RX", "RY", "RZ"}\n'
            + 'ALLOWED_TWO_QUBIT_GATES = {"CNOT", "CZ"}\n'
            + 'ALLOWED_PARAM_TWO_QUBIT_GATES = {"CRX", "CRY", "CRZ"}\n'
            + ("ALLOWED_ISING_GATES = {\"XX\", \"YY\", \"ZZ\"}\n" if tag == "su2" else "")
            + ('ALLOWED_THREE_QUBIT_GATES = {"ZZZ", "CCRZ"}\n' if tag == "ttt" else "")
            + "\n\n# EVOLVE-BLOCK-START\n" + block + "# EVOLVE-BLOCK-END\n\n\n"
            + "def run_experiment(**kwargs):\n"
            + "    return _run(ANSATZ_SPEC, **kwargs)\n")
    (dst / "initial_program.py").write_text(seed)

    for name in ["evaluate.py", "launch_shinka_cluster.py"] + cfg["extra"]:
        p = src / name
        if p.exists():
            shutil.copy2(p, dst / name)

    prompt = PROMPT.format(n=n, last=n - 1, schema=cfg["schema"],
                           quality=cfg["quality"], repeat_note=REPEAT_NOTES[tag])
    base_cfg = sorted(src.glob("shinka_config*.json"))[0]
    conf = json.loads(base_cfg.read_text())
    conf["evo"]["task_sys_msg"] = prompt
    for model, fname in [("openrouter/anthropic/claude-haiku-4.5", "haiku"),
                         ("openrouter/anthropic/claude-sonnet-5", "sonnet"),
                         ("openrouter/openai/gpt-5.6-sol", "gpt56sol")]:
        c = json.loads(json.dumps(conf))
        c["evo"]["llm_models"] = [model]
        c["evo"]["max_api_costs"] = 12.0
        (dst / f"shinka_config_{fname}.json").write_text(json.dumps(c, indent=2))

    print(f"built {dst.name}: backend {len(backend.splitlines())} lines, "
          f"visible seed {len(seed.splitlines())} lines")


for tag, cfg in TASKS.items():
    build(tag, cfg)
