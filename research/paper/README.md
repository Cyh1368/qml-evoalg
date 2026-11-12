# Paper — NeurIPS format (revised after three referee rounds, 12 Nov 2026)

`main.tex` is the revised paper in **NeurIPS 2024 format**
(`\documentclass{neurips_2024}`). `REVIEW.md`, `REVIEW_ROUND2.md` and `REVIEW_ROUND3.md` are the
referee reports; **`REBUTTAL.md`**, **`REBUTTAL_ROUND2.md`** and **`REBUTTAL_ROUND3.md`** are the
point-by-point author responses. Every number in the manuscript and in any response is generated,
not hand-typed. Two instruments enforce that, at different strengths, and the difference between
them matters:

* `python3 -m research.paper.check_numbers` is a **numeric-token lint**: every manuscript number
  of at least four digits must appear in the generated summary at its own precision. A green run
  shows no number was invented; it does **not** show a number sits in the right claim, because the
  check does not bind value to arm, endpoint or split.
* `python3 -m research.paper.claim_bind` is the **claim-level** layer: headline values are
  recomputed from structured result keys and must appear in a context window carrying that claim's
  arm/endpoint/split tokens. The instrument tests itself against deliberate mutations (sign, arm,
  split, order-of-magnitude, endpoint) and reports its own rates, on the manuscript and on a second
  artifact (`research/CLAIMS.md`); degenerate mutations, which leave the printed token unchanged,
  are excluded from the rate and listed. See `claim_binding_report.md`.

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
Last verified preview: 26 pages, zero errors, zero undefined references, no overfull box (job 33055110).

## Numbers
`python3 -m research.compile_results2 --out research/results_summary2.md` regenerates every
table from the result JSONs; the manuscript transcribes that file, and
`python3 -m research.paper.check_numbers` verifies it:

| manuscript object | generated from |
|---|---|
| Table "repair v1 recomputed" | `research/experiments/repair/repair_v1_reanalysis.json` |
| Table "WP-REPAIR-2" + four-estimand sensitivity (A5.1) | `research/experiments/repair/repair2_analysis.json` |
| Table "search estimands" | `research/search/confirm_analysis2.json` |
| baselines, selectivity, density bands, refit check | `research/search/dev_analysis.json` |
| breaking-target selectivity (Addendum A1) | `research/search/breaking_target.json` |
| label-symmetry groups, taxonomy, fixed panel (A5.2/A5.3) | `research/search/verify_semantics.json` |
| decision-rule ablation R0–R4 (A5.4) | `research/search/decision_rules.json` |
| one-shot sealed / fresh holdout (candidate endpoint) | `research/HOLDOUT_RESULTS.json` + `HOLDOUT_ACCESS.json` |
| E-R4' corrected untouched-input repair evaluation | `research/HOLDOUT_RESULTS_v4.json` |
| E-S7 vs-random contrast matrix | `research/holdout_search_contrasts.py` (from the stored record) |
| deployed endpoint + matched-split baselines (A5.5) | `research/HOLDOUT_DEPLOYED.json` + `HOLDOUT_DEPLOYED_ACCESS.json` |
| corrected-gate decision comparison, 7 rules x 5 regimes (A6.2/A6.3/A6.4) | `research/search/decision_rules2.json` |
| accept probability by proposal distribution, exact label groups, tolerance sweep, n=9 case (A6.5/A6.6) | `research/search/corrected_gate.json` |
| corrected-feedback matched search runs (A6.7) | `research/search/corrected_search.json` |
| claim-binding and mutation-detection report (A6.8) | `python3 -m research.paper.claim_bind` -> `claim_binding_report.md` |
| bibliography corrections | `paper/REFERENCES_AUDIT.md` (arXiv API / Crossref / PMLR / APS) |
| artifact manifest, split-consumption ledger | `python3 -m research.build_manifest` → `research/MANIFEST.md` |

## Documents that bound the claims
* `research/REVISED_PROTOCOL.md` — frozen protocol (units, estimands E-R1…E-R4 /
  E-S1…E-S7, inference, margins, one-shot holdout policy) plus Addendum A1 (breaking-target
  test), A2 (density-matched contrasts), A3 (projection-identity sign correction), A4 (the
  one-shot defect that invalidated the first E-R4), and **A5** (committed 22:32Z, before any
  second-round analysis): A5.1 estimand-appropriate inference, A5.2 hypothesis taxonomy,
  A5.3 fixed-panel selectivity, A5.4 verification as a decision rule, A5.5 deployed endpoint,
  A5.6 reporting policy.
* `research/CLAIMS.md` — claim ledger: what each claim may say, with its interval.
* `research/PROVENANCE.md` — dated chain, model identity, budgets, the two provenance defects
  in the project's own earlier records, the authorised graphs second read, and the aborted
  one-shot attempt.
* `research/MANIFEST.md` — every manuscript table mapped to analysis code (with commit),
  result file (with sha256 and size), endpoint, split, amendment and status, including
  `invalid` and `superseded` entries.
* `research/paper/REFERENCES_AUDIT.md` — every reference checked against a primary record,
  including the retracted round-1 claim about Meyer et al. (now quoted from the primary text).

Claims are scoped by the ledger; negative and null results are reported as "difference not
detected" with intervals, and equivalence is claimed only against a prespecified margin.
Do not add a claim that outruns the paired evidence.
