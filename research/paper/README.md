# Paper — NeurIPS format

`main.tex` is the paper in **NeurIPS 2024 format** (`\documentclass{neurips_2024}`).

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
`preview_article.pdf` is the same content compiled with `article`+`geometry`
(used to verify the body/tables/math/references are valid LaTeX when the
NeurIPS style is unavailable). It is **not** the submission format; use the
official `.sty` for the real PDF.

## Content / provenance
All numbers are the executed results, compiled by `research/compile_results.py`
into `research/results_summary.md` and transcribed here:
- WP-REPAIR: `research/experiments/repair/repair_results.json` (n=24 paired).
- WP-SEARCH confirmatory: `research/search/confirm_analysis.json` (n=12/family).
- Audit: `research/audit.md`.
Claims are scoped in `research/CLAIMS.md`; negative/null results are reported as
such. Do not add a claim that outruns the paired evidence.
