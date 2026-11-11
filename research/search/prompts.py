"""Prompt builders and strict JSON extraction for the LLM search arms.

The task description block is REDACTED CONTEXT: it describes the data and the
question but never names the transformation group the task happens to admit.
The verifier report embedded for the llm-verify arms reports residuals of the
model's OWN claimed hypothesis only; the true task group never appears in any
prompt.
"""
import json
import re

ALLOWED_GATES = ("RX", "RY", "RZ", "CRX", "CRY", "CRZ", "CNOT", "CZ", "RZZ",
                 "H", "X", "Y", "S", "T")

# Case-insensitive audit tokens for the redacted task-description block.
REDACTED_FORBIDDEN_TOKENS = ("S6", "S_6", "permutation", "symmetry", "D6", "D4")

# Fixed pipeline (frozen for all arms; the model only designs the block).
DEFAULT_LAYERS = 2
DEFAULT_REPEATS = 2

SYSTEM_PROMPT = (
    "You are a quantum ansatz designer in an evolutionary search. You design "
    "the trainable ansatz BLOCK for one fixed QML pipeline. Reply with exactly "
    "one JSON object and nothing else. The JSON object must have the keys "
    "\"block\" (list of gate entries), \"param_names\" (list of parameter "
    "name strings), \"hypothesis\" (a structured claim about a relabeling "
    "invariance of your block, or null), and \"notes\" (a short patch note "
    "explaining your design reasoning). Do not wrap the JSON in markdown "
    "fences and do not add prose before or after it."
)

# Redacted per-family descriptions. Wording rule: never name or hint at a
# transformation group; describe data and question only.
_TASK_DESCRIPTIONS = {
    "graphs_n6": (
        "TASK DESCRIPTION (redacted context)\n"
        "Consider six nodes in a graph, where each pair of nodes can either be "
        "disconnected or connected. You can travel from one node to another if "
        "and only if they are connected. Each input example is a vector of 15 "
        "binary features, one for each of the 15 possible pairings of the six "
        "nodes, listed in lexicographic order of node pairs: (0,1), (0,2), "
        "(0,3), (0,4), (0,5), (1,2), (1,3), (1,4), (1,5), (2,3), (2,4), (2,5), "
        "(3,4), (3,5), (4,5). A feature is 1 when that pair of nodes is "
        "connected and 0 otherwise. The question to answer: are the six nodes "
        "fully connected, i.e. is it possible to travel from any node to any "
        "other node? The dataset supplies the numeric target labels for this "
        "question; the label mapping rule is withheld."
    ),
    "ring_n6": (
        "TASK DESCRIPTION (redacted context)\n"
        "Each input example is a vector of six real numbers x_0, ..., x_5, "
        "each in [0, 2*pi), measured at six indexed sites of a fixed "
        "experimental setup. The dataset supplies two real-valued regression "
        "targets per example, named alpha_0 and alpha_1, each computed from "
        "the input by a fixed analytic formula that is withheld. Predict both "
        "targets from the input; the loss is mean squared error over both "
        "targets."
    ),
    "tictactoe_n9": (
        "TASK DESCRIPTION (redacted context)\n"
        "Each input example describes a 3x3 board of cells read left-to-right, "
        "top-to-bottom, so cell index c in 0..8 is row c//3, column c%3. Each "
        "cell is empty, marked O, or marked X; the input encodes each cell as "
        "an angle in {0, pi/2, pi}. Only terminal positions occur: a position "
        "where one side has three marks in a line, or the board is full. The "
        "target is +1 when X has achieved a line of three, -1 when O has, and "
        "0 for a full board with no line."
    ),
}


def task_description(task):
    """Redacted task-description text for a family name or a TaskSpec-like object."""
    name = getattr(task, "name", task)
    text = _TASK_DESCRIPTIONS.get(str(name))
    if text is not None:
        return text
    n = getattr(task, "n_qubits", None)
    return ("TASK DESCRIPTION (redacted context)\n"
            "Task family %r over %s qubits. Each input example is a fixed-size "
            "feature vector; the dataset supplies the target values. Predict "
            "the targets from the inputs." % (str(name), str(n)))


def audit_redaction(task):
    """Return list of forbidden tokens found in the redacted block (empty = clean)."""
    text = task_description(task).lower()
    return [tok for tok in REDACTED_FORBIDDEN_TOKENS if tok.lower() in text]


def pipeline_facts(task, layers=DEFAULT_LAYERS, repeats=DEFAULT_REPEATS):
    n = getattr(task, "n_qubits", 6)
    n_obs = len(getattr(task, "observables", [])) or (n + n * (n - 1) // 2)
    return (
        "FIXED PIPELINE (not editable; you only design the ansatz block)\n"
        "- n_qubits = %d.\n"
        "- The full circuit gate list is: %d layers of ( task feature map, then "
        "your block repeated %d times ). The feature map re-encodes the input "
        "before every block application (data re-uploading); its gates carry "
        "fixed angles and are NOT part of your proposal.\n"
        "- Readout: for each of the %d fixed diagonal observables (single Z_i "
        "and pairwise Z_iZ_j expectation values), take the matrix element of "
        "the full circuit state; a trainable classical linear layer "
        "f = w . <O> + b maps them to the scalar output. Block gate parameters "
        "and (w, b) are trained jointly; you only propose the block.\n"
        "- Set \"layers\": %d and \"repeats\": %d in your JSON; they are fixed."
        % (n, layers, repeats, n_obs, layers, repeats)
    )


def schema_facts(task):
    n = getattr(task, "n_qubits", 6)
    gates = ", ".join('"%s"' % g for g in ALLOWED_GATES)
    return (
        "CANDIDATE JSON SCHEMA (exactly these gate entries)\n"
        "- Single-qubit gate: {\"gate\": G, \"wire\": i, \"param\": name} for "
        "rotations G in RX/RY/RZ, or {\"gate\": G, \"wire\": i} for fixed "
        "gates H, X, Y, S, T.\n"
        "- Two-qubit gate: {\"gate\": G, \"wires\": [a, b]} for CNOT, CZ; "
        "{\"gate\": G, \"wires\": [a, b], \"param\": name} for CRX, CRY, CRZ; "
        "{\"gate\": \"RZZ\", \"wires\": [a, b], \"param\": name}.\n"
        "- Allowed gate names: %s. Wires a, b are integers in 0..%d, a != b. "
        "\"param\" is a string naming a trainable parameter; the same name may "
        "be reused by many gates (tied parameter).\n"
        "- Top-level keys: \"block\": list of the gate entries above (at most "
        "24 entries); \"param_names\": list of every parameter name used; "
        "\"hypothesis\": either null or {\"generators\": [p1, p2, ...], "
        "\"output_action\": \"invariant\"} where each pi is a list of the "
        "integers 0..%d in some order, one line per generator, describing a "
        "site relabeling your block is claimed to be invariant under (the "
        "group is generated by closing these under composition); \"notes\": "
        "your patch note string; \"layers\": %d; \"repeats\": %d; "
        "\"n_qubits\": %d.\n"
        "- Every name in the block must appear in param_names and vice versa."
        % (gates, n - 1, n - 1, DEFAULT_LAYERS, DEFAULT_REPEATS, n)
    )


def structural_summary(candidate):
    """Short structural digest of a proposal; never mentions any group name."""
    try:
        block = candidate.get("block") or []
        counts = {}
        for g in block:
            counts[g.get("gate", "?")] = counts.get(g.get("gate", "?"), 0) + 1
        kinds = ", ".join("%s:%d" % kv for kv in sorted(counts.items()))
        npar = len(candidate.get("param_names") or [])
        hyp = candidate.get("hypothesis")
        hyp_txt = ("no hypothesis" if not hyp else
                   "hypothesis with %d generator(s)" % len(hyp.get("generators", [])))
        return "%d gates (%s), %d params, %s" % (len(block), kinds or "none",
                                                 npar, hyp_txt)
    except Exception:
        return "unparseable proposal"


def history_block(history, max_rows=12):
    """history: list of dicts with id, summary, dev_risk (float or None), valid."""
    rows = [h for h in history if h.get("valid")][-max_rows:]
    if not rows:
        return "PRIOR PROPOSALS\nNo valid prior proposals yet."
    lines = ["PRIOR PROPOSALS (id | structure | development risk; lower is better)"]
    for h in rows:
        risk = h.get("dev_risk")
        risk_txt = "n/a" if risk is None else ("%.4f" % risk)
        lines.append("- %s | %s | dev risk %s"
                     % (h.get("id", "?"), h.get("summary", ""), risk_txt))
    invalid = sum(1 for h in history if not h.get("valid"))
    if invalid:
        lines.append("(%d earlier proposals were rejected as invalid JSON/schema)"
                     % invalid)
    return "\n".join(lines)


def verifier_report_block(report):
    """Format the verifier report of the model's OWN last hypothesis.

    Only the model's claimed hypothesis is ever mentioned; the true task group
    is never computed for, or named in, a prompt.
    """
    if report is None:
        return ""
    if report.get("status") == "no_hypothesis":
        return ("VERIFIER REPORT for your last proposal: you supplied no "
                "hypothesis, so nothing could be verified. Supply a "
                "hypothesis (generators + output_action invariant) to get "
                "executable feedback.")
    lines = [
        "VERIFIER REPORT for your last proposal (checks ONLY the hypothesis "
        "you yourself claimed; it is not a hint about any other structure)",
        "- your claimed relabeling group order: %s" % report.get("group_order"),
        "- mean channel residual of your expanded circuit over %s random "
        "parameter draws: %.3e" % (report.get("parameter_samples", "?"),
                                   report.get("mean_channel_residual", float("nan"))),
        "- max channel residual: %.3e" % report.get("max_channel_residual", float("nan")),
        "- equivariance pass at tolerance %.1e: %s"
        % (report.get("tolerance", 1e-10), report.get("sampled_pass", False)),
        "- label-preservation of your hypothesis on training rows: mean abs "
        "discrepancy %.3e, max %.3e, violated fraction %.3f"
        % (report.get("label_mean_abs_discrepancy", float("nan")),
           report.get("label_max_discrepancy", float("nan")),
           report.get("label_violated_fraction", float("nan"))),
        "Interpretation: a large channel residual means your gate list does not "
        "actually realize the invariance you claimed; a nonzero violated "
        "label fraction means the task targets are not invariant under your "
        "claimed relabeling.",
    ]
    return "\n".join(lines)


def build_prompt(task, history=None, verifier_report=None,
                 layers=DEFAULT_LAYERS, repeats=DEFAULT_REPEATS):
    """Return (system, user) prompt strings for one proposal request."""
    parts = [task_description(task), "", pipeline_facts(task, layers, repeats),
             "", schema_facts(task), "", history_block(history or [])]
    vrb = verifier_report_block(verifier_report)
    if vrb:
        parts += ["", vrb]
    parts += ["", "Propose ONE improved candidate now: reply with exactly one "
                  "JSON object (block, param_names, hypothesis, notes) and "
                  "nothing else."]
    return SYSTEM_PROMPT, "\n".join(parts)


# --------------------------------------------------------------------------
# Strict JSON extraction with repair of common failures.

_FENCE_RE = re.compile(r"```(?:json|javascript|python)?\s*(\{.*?\})\s*```", re.S)


def _balanced_object(text):
    """First balanced {...} span, string/escape aware; None if unbalanced."""
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start:i + 1]
        start = text.find("{", start + 1)
    return None


def extract_json_object(text):
    """Best-effort recovery of one JSON object from an LLM reply."""
    if not isinstance(text, str) or not text.strip():
        return None
    attempts = [text.strip()]
    attempts += [m.strip() for m in _FENCE_RE.findall(text)]
    obj = _balanced_object(text)
    if obj:
        attempts.append(obj)
    for cand in attempts:
        for variant in (cand, re.sub(r",(\s*[}\]])", r"\1", cand)):
            try:
                parsed = json.loads(variant)
            except (ValueError, TypeError):
                continue
            if isinstance(parsed, dict):
                return parsed
    return None


def extract_candidate(content):
    """Extract (candidate_dict_or_None, patch_note, errors).

    Never raises: an unrecoverable reply yields candidate None (the harness
    records it as an invalid proposal, counted in proposals_total only).
    """
    errors = []
    obj = extract_json_object(content)
    if obj is None:
        note = (content or "").strip()[:2000]
        return None, note, ["no JSON object found in reply"]
    note = str(obj.get("notes") or obj.get("patch_note") or "")[:4000]
    if not isinstance(obj.get("block"), list):
        errors.append("missing or non-list 'block'")
    if not errors:
        allowed = set(ALLOWED_GATES)
        for i, g in enumerate(obj["block"]):
            if not isinstance(g, dict) or g.get("gate") not in allowed:
                errors.append("gate entry %d has an unsupported gate name" % i)
    return (obj if not errors else None), note, errors
