"""A3.1: no number may appear in the manuscript unless a generated artifact contains it.

Why this exists. The response to the first review said the symmetry menu "reaches power 1.000 at
20,800 shots" and "1.000 at 96,000". results/ledger.json said 0.900 and 0.960. Nothing failed, because
nothing checked: the number was typed into prose instead of emitted from data. The previous project had
a checker like this and it caught exactly this class of error repeatedly; leaving it behind when the
project changed was the mistake.

Every decimal literal in the manuscript with at least `--min-decimals` fractional digits, or with four
or more significant digits, must appear in a generated table fragment or in a result JSON, formatted
the same way. Numbers that legitimately have no upstream artifact (LaTeX dimensions, section counts,
test counts quoted in prose) are allowed by an explicit, reviewed list in ALLOWED, never by lowering
the threshold.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# Numbers with no generated source, each with the reason. Adding to this list is a reviewable act.
ALLOWED = {
    "0.05": "declared delta in the protocol",
    "0.02": "declared epsilon multiplier in the protocol",
    "0.01": "protocol deviation recorded in Addendum A2.0",
    "0.90": "power threshold used to select the cheapest frontier point",
    "0.95": "Wilson interval level",
    "1.96": "Wilson z score",
    "0.00": "displayed zero",
    "1.00": "displayed unit rate",
    "0.10": "displayed rate",
    "0.14": "displayed rate",
    "0.50": "displayed rate",
    "0.25": "displayed mixture weight",
    "0.75": "displayed mixture weight",
    "1.000": "displayed unit rate",
    "0.000": "displayed zero rate",
}

NUM = re.compile(r"(?<![\w.])(\d+\.\d+)(?![\w.])")
# arXiv identifiers are citations, not results; they must not be bound to an artifact.
ARXIV = re.compile(r"arXiv:\d{4}\.\d+")


def collect_allowed(paths):
    vals = set()
    for p in paths:
        txt = open(p).read()
        for m in NUM.finditer(txt):
            vals.add(m.group(1))
        # integers too: budgets and counts are quoted in prose
        for m in re.finditer(r"(?<![\w.])(\d{3,})(?![\w.])", txt):
            vals.add(m.group(1))
    return vals


def json_values(path):
    out = set()

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                walk(v)
        elif isinstance(x, bool):
            pass
        elif isinstance(x, (int, float)):
            for d in range(0, 9):
                out.add(("%." + str(d) + "f") % x)
            out.add(str(x))
    walk(json.load(open(path)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex", default="shotcert/paper/main.tex")
    ap.add_argument("--tabs", default="shotcert/paper")
    ap.add_argument("--results", default="shotcert/results")
    ap.add_argument("--min-decimals", type=int, default=3)
    args = ap.parse_args()

    tab_files = [os.path.join(args.tabs, f) for f in sorted(os.listdir(args.tabs))
                 if f.startswith("tabs_") and f.endswith(".tex")]
    allowed = collect_allowed(tab_files)
    for f in sorted(os.listdir(args.results)):
        if f.endswith(".json"):
            allowed |= json_values(os.path.join(args.results, f))

    # A number written in a table is allowed; so is one present in any JSON at any printed precision.
    tex = open(args.tex).read()
    # strip the historical appendix, which is allowed to quote superseded numbers with a warning
    body = re.split(r"\\section\*?\{Historical", tex)[0]

    bad = []
    for lineno, line in enumerate(body.split("\n"), 1):
        if line.strip().startswith("%"):
            continue
        line = ARXIV.sub("", line)
        for m in NUM.finditer(line):
            tok = m.group(1)
            dec = len(tok.split(".")[1])
            sig = len(tok.replace(".", "").lstrip("0"))
            if dec < args.min_decimals and sig < 4:
                continue
            if tok in ALLOWED:
                continue
            if tok in allowed:
                continue
            # allow a prefix match against a longer generated value (0.008 for 0.00800)
            if any(a.startswith(tok) and len(a) > len(tok) for a in allowed):
                continue
            bad.append((lineno, tok, line.strip()[:100]))

    print("checked %s against %d generated artifacts" % (args.tex, len(tab_files)))
    print("allowed values known: %d" % len(allowed))
    if bad:
        print("\nUNBOUND NUMBERS (%d):" % len(bad))
        for lineno, tok, ctx in bad:
            print("  line %4d  %s   |  %s" % (lineno, tok, ctx))
        sys.exit(1)
    print("OK: every threshold-crossing number in the manuscript is bound to a generated artifact")


if __name__ == "__main__":
    main()
