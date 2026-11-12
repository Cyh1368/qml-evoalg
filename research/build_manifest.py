"""Generate `research/MANIFEST.md`: one row per manuscript table (Addendum A5.6 / A5.8).

The second-round referee's point 8 asked for "a final artifact manifest mapping each
manuscript table to its code revision, result file, endpoint, split ID, seed, digest,
protocol/amendment, and status", with obsolete and invalid artefacts marked explicitly.
Hand-maintaining such a table guarantees it drifts, so the digests, sizes, modification
times and the git revision at which each analysis file last changed are read here at
generation time.

Usage::

    python3 -m research.build_manifest --out research/MANIFEST.md
"""
import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (manuscript location, analysis code, result file, endpoint, split / seed, protocol, status)
ROWS = [
    ("Table 1 contribution summary", "research/compile_results2.py", "research/results_summary2.md",
     "mixed (labelled per row)", "n/a", "sections 1-4 + A1-A5", "current"),
    ("S-self-audit, audit table", "research/audit.py", "research/audit.md",
     "historical v2 scoring path", "prior study's split", "section 0 (audit)", "current"),
    ("WP-REPAIR v1 reanalysis table", "research/experiments/repair/analyze_repair.py",
     "research/experiments/repair/repair_v1_reanalysis.json",
     "development risk", "development validation; 8 units at eta=0",
     "sections 1-4", "current (supersedes the v1 paper table)"),
    ("WP-REPAIR-2 primary contrasts (E-A)", "research/experiments/repair/analyze_repair.py",
     "research/experiments/repair/repair2_analysis.json",
     "development risk", "8 directions x 24 optimiser seeds; seed 20261110+; job 32982225",
     "sections 1-4 + A1 (units) + A5.1 (estimands)", "current"),
    ("WP-REPAIR-2 estimand sensitivity (E-A/B/C/D)", "research/experiments/repair/analyze_repair.py",
     "research/experiments/repair/repair2_analysis.json",
     "development risk", "same design", "A5.1", "current"),
    ("WP-REPAIR-2 floor accounting + E-R1", "research/experiments/repair/analyze_repair.py",
     "research/experiments/repair/repair2_results.json",
     "development risk, orbit-completed risk", "same design",
     "sections 1-4 + A3 (identity sign)", "current"),
    ("Budget-sensitivity table", "research/experiments/repair/analyze_repair.py",
     "research/experiments/repair/repair2_analysis.json",
     "development risk", "200 / 600 / 1800 steps", "section 3", "current"),
    ("WP-SEARCH E-S1/E-S2/E-S3 table", "research/search/analyze2.py",
     "research/search/confirm_analysis2.json",
     "development risk, candidate + deployed endpoints", "120 frozen runs, seeds 20261110-21",
     "section 2 (search)", "current"),
    ("WP-DEV E-S4b/E-S4c/E-S5/E-S5b/E-S5c/E-S6", "research/search/dev_analysis.py",
     "research/search/dev_analysis.json",
     "development risk (validation split; NOT held out)", "120 frozen runs",
     "section 2 + A2 (density-matched)", "current"),
    ("Breaking-target table (A1)", "research/search/analyze_breaking.py",
     "research/search/breaking_target.json",
     "development risk on the breaking target", "60 runs, ring target alpha_0.5",
     "A1", "current"),
    ("Verifier-semantics tables (A5.2/A5.3)", "research/search/verify_semantics.py",
     "research/search/verify_semantics.json",
     "label-preservation decisions on development rows + independent probe",
     "probe seed 777, panel seed 4242; 120 frozen runs", "A5.2, A5.3", "current"),
    ("Decision-rule tables (A5.4)", "research/search/decision_rules.py",
     "research/search/decision_rules.json",
     "development risk, paired per candidate", "120 frozen runs; MC seed 90210",
     "A5.4", "current"),
    ("Corrected-gate decision tables (A6.2/A6.3)", "research/search/decision_rules2.py",
     "research/search/decision_rules2.json",
     "development risk, paired per candidate, per-rule firing masks, measured costs",
     "120 frozen candidates; 7 rules x 5 regimes; horizons 1/10/100/1000; w grid",
     "A6.2, A6.3, A6.4", "current"),
    ("Corrected-gate semantics tables (A6.5/A6.6)", "research/search/corrected_gate.py",
     "research/search/corrected_gate.json",
     "accept probability under four proposal distributions, exact label groups, panel units, "
     "tolerance sweep",
     "400 MC draws, probe 256 rows seed 777, gate 64 rows, closure cap 2000; job 33053412",
     "A6.5, A6.6", "current; supersedes corrected_gate_driftedpanel.json (local panel copy drift)"),
    ("Corrected-feedback search study (A6.7)", "research/search/analyze_corrected.py",
     "research/search/corrected_search.json",
     "development-selected risk, paired by seed",
     "72 new runs, label_mode=corrected, budget 32, 200 steps, max_train 256",
     "A6.7", "see record"),
    ("Claim-binding report (A6.8)", "research/paper/claim_bind.py",
     "research/paper/claim_binding_report.md",
     "binding of manuscript values to result keys, plus mutation testing of the instrument",
     "22 manuscript bindings, 7 external bindings on research/CLAIMS.md",
     "A6.8", "current"),
    ("E-S7 sealed-test candidate table", "research/holdout_oneshot.py",
     "research/HOLDOUT_RESULTS.json",
     "sealed-test risk, CANDIDATE endpoint only", "v1 sealed split (consumed)",
     "section 5", "current, but candidate endpoint only - see A5.5"),
    ("E-S7 arm-vs-random contrasts", "research/holdout_search_contrasts.py",
     "research/HOLDOUT_SEARCH_CONTRASTS.json",
     "sealed-test risk, candidate endpoint", "recomputed from the consumed v1 record",
     "section 5 + A5.6", "current"),
    ("E-R4 first one-shot repair table", "research/holdout_oneshot.py",
     "research/HOLDOUT_RESULTS.json",
     "sealed / fresh risk", "v1 + v2 splits (both consumed)",
     "section 5", "INVALID for eta>0 (A4): all eta scored against one alpha_0 label"),
    ("E-R4' corrected fresh-input repair table", "research/holdout_oneshot.py",
     "research/HOLDOUT_RESULTS_v4.json",
     "fresh-input risk, targets rebuilt from the trusted oracle",
     "v4 inputs-only holdout, seed 20261204 (consumed)", "A4", "current"),
    ("Deployed-endpoint tables (A5.5)", "research/holdout_deployed.py",
     "research/HOLDOUT_DEPLOYED.json",
     "candidate AND deployed endpoints + matched test-split baselines",
     "ring: v5 fresh inputs seed 20261205; graphs: v1 sealed split, SECOND READ (post hoc)",
     "A5.5", "current"),
    ("References", "research/paper/REFERENCES_AUDIT.md", "research/paper/REFERENCES_AUDIT.md",
     "bibliographic records", "Crossref / arXiv / PMLR lookups", "A5 round-2 re-check",
     "current; one round-1 audit conclusion was itself wrong and is withdrawn"),
]

CONSUMED = [
    ("research/datasets/locked_holdout/", "v1 sealed test (ring + graphs)",
     "consumed by the E-S7 / first E-R4 run; the evaluator refuses it"),
    ("research/datasets/locked_holdout_v2/", "v2 fresh split",
     "consumed by the defective first E-R4 run; refused"),
    ("research/datasets/locked_holdout_v3/", "v3 inputs-only holdout",
     "opened by a job whose self-check ran too late (A4); inputs only, so no label was "
     "exposed; treated as consumed and refused"),
    ("research/datasets/locked_holdout_v4/", "v4 inputs-only holdout",
     "consumed by the reported E-R4' run (one read, gate passed first)"),
    ("research/datasets/locked_holdout_v5/", "v5 inputs-only holdout",
     "ring half consumed by the A5.5 deployed-endpoint run; graphs half does not exist "
     "(no unseen isomorphism classes remain)"),
]


def sha256(path):
    p = REPO / path
    if not p.exists():
        return "MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def git_rev(path):
    try:
        out = subprocess.run(["git", "-C", str(REPO), "log", "-1", "--format=%h %ad",
                              "--date=format:%Y-%m-%dT%H:%MZ", "--", path],
                             capture_output=True, text=True, timeout=30)
        return out.stdout.strip() or "untracked"
    except Exception as exc:
        return "git error: %s" % exc


def file_stat(path):
    p = REPO / path
    if not p.is_dir():
        return "%d B" % p.stat().st_size if p.exists() else "missing"
    n = sum(1 for _ in p.rglob("*") if _.is_file())
    return "%d files" % n


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="research/MANIFEST.md")
    a = ap.parse_args(argv)
    head = ["# Artifact manifest (generated; do not hand-edit digests)\n",
            "Generated by `python3 -m research.build_manifest` at %s from git %s.\n"
            % (time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()),
               subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True).stdout.strip()),
            "Digests are truncated sha256 (16 hex). `code rev` is the last commit that "
            "touched the analysis file, which is the strongest statement git can make "
            "here: it is a documented chronology, **not** an independently certified "
            "preregistration service (see `research/PROVENANCE.md`).\n",
            "| manuscript location | analysis code (rev) | result file (sha256, size) | "
            "endpoint | split / seed | protocol | status |",
            "|---|---|---|---|---|---|---|"]
    for loc, code, res, endpoint, split, proto, status in ROWS:
        head.append("| %s | `%s` (%s) | `%s` (`%s`, %s) | %s | %s | %s | %s |"
                    % (loc, code, git_rev(code), res, sha256(res), file_stat(res),
                       endpoint, split, proto, status))
    head.append("\n## Split consumption ledger\n")
    head.append("| path | what it is | state |")
    head.append("|---|---|---|")
    for path, what, state in CONSUMED:
        head.append("| `%s` | %s | %s |" % (path, what, state))
    head.append("""
## What digests and permissions do and do not prove

A digest recorded before and after a read shows the **bytes did not change**: the file was
not modified or truncated while we read it. It does **not** show the file was never opened
before, and it is not an access-control mechanism. The controls that actually restrict
access here are (a) `0444` permissions, (b) the evaluator's refusal to open a split listed
as consumed, and (c) this ledger. Those are procedural guards against our own drift, not
isolation against a determined reader, and the manuscript says so.

## Reproduction (current path; no command here opens a consumed split)

```bash
module reset && module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
export OPENBLAS_NUM_THREADS=1
export LD_LIBRARY_PATH=/apps/software/2024a/software/Python/3.12.3-GCCcore-13.3.0/lib:$LD_LIBRARY_PATH

# development analyses (no sealed read)
python3 -m research.experiments.repair.analyze_repair \\
  --in research/experiments/repair/repair2_results.json \\
  --out research/experiments/repair/repair2_analysis.json
python3 -m research.search.verify_semantics --runs logs/runs_confirm \\
  --out research/search/verify_semantics.json
sbatch research/search/job_decision.sh
python3 -m research.search.dev_analysis --dir logs/runs_confirm

# one-shot evaluations (each refuses a consumed split; run once)
python3 -m research.holdout_oneshot --splits dev --selfcheck \\
  research/experiments/repair/repair2_results.json        # gate only, no read
python3 -m research.holdout_oneshot --splits fresh_v4 \\
  --out research/HOLDOUT_RESULTS_v4.json                  # E-R4', one read
DRY_RUN=1 sbatch research/job_deployed.sh                 # gate first, opens nothing
sbatch research/job_deployed.sh                           # A5.5, one read

# tables and consistency
python3 -m research.compile_results2 --out research/results_summary2.md
python3 -m research.holdout_search_contrasts
python3 -m research.paper.check_numbers                   # must print OK
python3 -m research.build_manifest --out research/MANIFEST.md
```
""")
    with open(a.out, "w") as fh:
        fh.write("\n".join(head) + "\n")
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
