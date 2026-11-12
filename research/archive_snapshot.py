"""Immutable snapshot manifest for the fifth-round-terminated project (2026-11-12).

The redirection memo requires an archivable record before a new study starts: manuscript,
reviews, rebuttals, protocol amendments, result records, the split-consumption ledger, and a hash
manifest, with a README naming what is exploratory or superseded.

This walks an explicit allow-list of record classes (not the whole repository: the repository also
holds unrelated historical projects) and writes sha256 digests plus sizes. It is a *record of what
the bytes were at the snapshot*, not a claim that any conclusion stands.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os

# Record classes, in the order a reader should meet them.
CLASSES = [
    ("decision", ["research/paper/REVIEW.md", "research/paper/REVIEW_ROUND2.md",
                  "research/paper/REVIEW_ROUND3.md", "research/paper/REVIEW_ROUND4.md",
                  "research/paper/REVIEW_ROUND5.md",
                  "reports/Certified symmetry decisions.md"]),
    ("manuscript", ["research/paper/main.tex", "research/paper/preview_article.pdf"]),
    ("responses", ["research/paper/REBUTTAL.md", "research/paper/REBUTTAL_ROUND2.md",
                   "research/paper/REBUTTAL_ROUND3.md", "research/paper/REBUTTAL_ROUND4.md"]),
    ("protocol", ["research/REVISED_PROTOCOL.md", "research/CLAIMS.md",
                  "research/MANIFEST.md", "research/PROVENANCE.md", "HANDOFF.md"]),
    ("ledgers", ["research/HOLDOUT_ACCESS.json", "research/HOLDOUT_ACCESS_v4.json",
                 "research/HOLDOUT_DEPLOYED_ACCESS.json", "research/HOLDOUT_RESULTS.json",
                 "research/HOLDOUT_RESULTS_v4.json", "research/HOLDOUT_DEPLOYED.json"]),
    ("result-records", []),          # filled by glob below
    ("compiled-summary", ["research/results_summary2.md",
                          "research/paper/claim_binding_report.md",
                          "research/paper/REFERENCES_AUDIT.md"]),
]

GLOBS = [("result-records", "research/search/*.json"),
         ("result-records", "research/experiments/repair/*.json"),
         ("result-records", "research/core/*.json")]


def sha256(path, limit=None):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="research/ARCHIVE_MANIFEST.md")
    ap.add_argument("--tag", default="")
    a = ap.parse_args(argv)
    import glob as _g
    buckets = {k: [] for k, _ in CLASSES}
    for _k, files in CLASSES:
        buckets[_k].extend(files)
    for kind, pat in GLOBS:
        buckets[kind].extend(sorted(p for p in _g.glob(pat)))
    seen, rows = set(), []
    for kind, _ in CLASSES:
        for p in buckets[kind]:
            if p in seen or not os.path.isfile(p):
                continue
            seen.add(p)
            rows.append((kind, p, os.path.getsize(p), sha256(p)))
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = ["# Archive manifest: terminated submission (fifth-round reject)\n",
           "Generated %s by `research/archive_snapshot.py`. Tag: `%s`.\n" % (stamp, a.tag or "none"),
           "**Status of everything hashed here.** The fifth-round review "
           "(`research/paper/REVIEW_ROUND5.md`) rejected the submission and recommended against "
           "another rebuttal cycle. Items marked superseded below are retained for provenance and "
           "must not be cited as findings; `research/ARCHIVED.md` lists them one by one.\n",
           "| class | path | bytes | sha256 |", "|---|---|---|---|"]
    for kind, p, size, d in rows:
        out.append("| %s | `%s` | %d | `%s` |" % (kind, p, size, d[:16]))
    out.append("\n%d files, %d bytes total.\n" % (len(rows), sum(r[2] for r in rows)))
    with open(a.out, "w") as fh:
        fh.write("\n".join(out) + "\n")
    print("wrote %s: %d files" % (a.out, len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
