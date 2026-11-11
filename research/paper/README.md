# Paper — NeurIPS format (revised after referee report, 11 Nov 2026)

`main.tex` is the revised paper in **NeurIPS 2024 format**
(`\documentclass{neurips_2024}`). `REVIEW.md` is the referee report;
**`REBUTTAL.md` is the point-by-point author response**, and every number quoted in either
document is generated, not hand-typed (see "Numbers" below).

## Build (final, official style)
1. Download the official **NeurIPS 2024 author kit** from the NeurIPS 2024
   author-guidelines page and copy `neurips_2024.sty` into this directory.
2. On Bouchet:
   ```bash
   module load texlive/20240312-GCC-13.3.0
   pdflatex main && bibtex main && pdflatex main && pdflatex main
   ```
   (References use an embedded `thebibliography`; `bibtex` is a no-op but harmless.)

## Preview without the style file
`preview_article.pdf` is the same content compiled with `article`+`geometry`, used to
verify that body/tables/math/references are valid LaTeX when the NeurIPS style is
unavailable. It is **not** the submission format. Rebuild it with
`sbatch --output logs/preview-%j.out research/paper/job_preview.sh` (a short `devel` job that
loads `texlive/20240312-GCC-13.3.0`, substitutes an `article` preamble, and compiles twice).

## Numbers
`python3 -m research.compile_results2 --out research/results_summary2.md` regenerates every
table from the result JSONs; the manuscript transcribes that file:

| manuscript object | generated from |
|---|---|
| Table "repair v1 recomputed" | `research/experiments/repair/repair_v1_reanalysis.json` |
| Table "WP-REPAIR-2" | `research/experiments/repair/repair2_analysis.json` |
| Table "search estimands" | `research/search/confirm_analysis2.json` |
| baselines, selectivity, density bands | `research/search/dev_analysis.json` |
| breaking-target selectivity | `research/search/breaking_target.json` |
| one-shot sealed / fresh holdout | `research/HOLDOUT_RESULTS.json` + `HOLDOUT_ACCESS.json` |
| bibliography corrections | `paper/REFERENCES_AUDIT.md` (arXiv API / Crossref / PMLR) |

## Documents that bound the claims
* `research/REVISED_PROTOCOL.md` — frozen protocol (units, estimands E-R1…E-R4 /
  E-S1…E-S7, inference, margins, one-shot holdout policy, Addendum A1 breaking-target test,
  Addendum A2 density-matched contrasts). Committed before the experiments ran.
* `research/CLAIMS.md` — claim ledger: what each claim may say.
* `research/PROVENANCE.md` — dated chain, model identity, budgets, and the two provenance
  defects found in the project's own earlier run records.
* `research/paper/REFERENCES_AUDIT.md` — every reference checked against a primary record.

Claims are scoped by the ledger; negative and null results are reported as "difference not
detected" with intervals, and equivalence is claimed only against a prespecified margin.
Do not add a claim that outruns the paired evidence.
