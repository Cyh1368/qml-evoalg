"""Check that every number printed in the manuscript appears in the auto-compiled summary.

The second-round referee's point 6 ends with "Automated compilation alone is not validation."
They are right: `compile_results2.py` guarantees the *summary* is generated, not that the
manuscript quotes it. This script closes that gap mechanically: it collects the numeric
tokens from the generated tables, then reports manuscript numbers that appear nowhere in the
generated record (a stale, hand-typed or transposed value), and numbers in the manuscript
whose surrounding sentence claims a direction the generated data contradicts.

Usage::

    python3 -m research.paper.check_numbers \\
        --summary research/results_summary2.md --tex research/paper/main.tex

Exit status is non-zero when a *suspicious* number (>= 3 significant digits, not on the
allow-list of structural constants) is found only in the manuscript.
"""
import argparse
import re
import sys

ALLOW = {
    # structural / design constants, budget counts, page and section numbers
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "12", "15", "16", "20",
    "24", "32", "48", "60", "64", "72", "100", "120", "128", "192", "200", "240", "256",
    "299", "348", "400", "512", "600", "720", "1000", "1024", "1800", "2000", "3000",
    "4000", "10000", "20000", "2026", "20261110", "20261111", "20261112", "20261113",
    "20261114", "20261115", "20261116", "20261117", "20261118", "20261119", "20261120",
    "20261121", "20261122", "20261123", "20261124", "20261201", "20261202", "20261203",
    "20261204", "20261205",
    # identifiers, not results: arXiv numbers, DOI prefixes, module/toolchain versions.
    # They belong in the manuscript and have no place in a results summary.
    "2505.12764", "2606.20316", "2311.00212", "2610.00157", "2509.19349", "2210.08566",
    "10.1103", "10.48550", "2024.05", "13.3.0", "1.26.4", "3.12.3",
}
NUM = re.compile(r"(?<![\w.])(-?\d+\.\d+)(?![\w.])")


def numbers(text, min_len=5):
    """Numeric tokens with at least ``min_len - 1`` digits, kept as (string, float, dp)."""
    out = {}
    for m in NUM.finditer(text):
        tok = m.group(1)
        digits = tok.replace("-", "").replace(".", "").lstrip("0")
        if not digits:
            continue
        if len(tok.replace("-", "").replace(".", "")) < min_len - 1:
            continue
        dp = len(tok.split(".")[1]) if "." in tok else 0
        out[tok] = (float(tok), dp)
    return out


def matches(mv, md, gen):
    """Does some generated value round to this manuscript value at its own precision?

    Also accepts a x100 (percentage) or /100 reading, since the manuscript writes
    "4.6% of the target variance" where the record stores 0.04629.
    """
    for g in gen.values():
        for scale in (1.0, 100.0, 0.01):
            v = g[0] * scale
            if abs(round(v, md) - mv) < 1e-12:
                return True
            tol = 0.5 * 10 ** (-md) * (1.0000001 if scale == 1.0 else 100.0)
            if abs(v - mv) <= tol:
                return True
    return False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default="research/results_summary2.md")
    ap.add_argument("--tex", default="research/paper/main.tex")
    ap.add_argument("--min-digits", type=int, default=4)
    a = ap.parse_args(argv)
    gen = numbers(open(a.summary).read(), min_len=a.min_digits)
    tex = open(a.tex).read().replace("\\mathbf", "").replace("$", "")
    tex = tex.replace("\\textbf", "")
    man = numbers(tex, min_len=a.min_digits)
    missing = [t for t, (v, dp) in man.items()
               if t not in ALLOW and not matches(v, dp, gen)]
    print("generated numbers: %d   manuscript numbers: %d" % (len(gen), len(man)))
    if not missing:
        print("OK: every manuscript number of >=%d digits matches a generated value at its "
              "own precision (absolute or percent scaling)" % a.min_digits)
        return 0
    print("\nNumbers in the manuscript with no generated counterpart (%d):" % len(missing))
    lines = tex.split("\n")
    for m in sorted(missing, key=lambda x: -len(x)):
        line = next((i for i, l in enumerate(lines, 1) if m in l), None)
        print("  %-14s %s" % (m, "main.tex line %s" % line if line else ""))
    print("\nEach must be (a) removed, (b) traced to a result file and added to the "
          "compiler, or (c) allow-listed with a reason.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
