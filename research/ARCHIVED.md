# What is archived here, and what must not be cited

**Project:** *Executable Verification and Analytic Repair in LLM-Guided Quantum Circuit Search*
**Final decision:** rejected, fifth round (`research/paper/REVIEW_ROUND5.md`, 12 Nov 2026). The
reviewer recommended against another rebuttal cycle and advised that a future submission be treated
as substantially new work.
**Redirection:** `reports/Certified symmetry decisions.md`. The new study lives in the `shotcert/`
package with its own data namespace; nothing in this directory is carried into it as evidence.

Hash manifest: `research/ARCHIVE_MANIFEST.md`. Split-consumption ledger:
`research/HOLDOUT_ACCESS*.json`, `research/HOLDOUT_DEPLOYED_ACCESS.json` (sealed splits were opened
once each; the ledger is the authority on that, not the digests).

## Claims that are SUPERSEDED or WITHDRAWN — do not cite

| # | claim | status | why |
|---|---|---|---|
| 1 | "Verification is a recall bottleneck, not a safety device" | **withdrawn** (round 3) | described a screen testing the wrong labels at zero tolerance; the corrected screen captures the full benefit |
| 2 | Verifier value is a function of P(wrong group) and P(Q ⊆ L_t) | **withdrawn** (A7) | the firing rule is a threshold on the posterior; the two probabilities enter only through it, together with screen sensitivity/specificity |
| 3 | A verifier-free defect gate recovers 79% of the benefit | **superseded** (A7.3) | the comparison lacked gate parity; with regime-specific groups and a frozen threshold it rejects only 4/58 harmful repairs |
| 4 | Empirical LLM proposal acceptance = 0.47 | **corrected** (A7.2) | pool mixed arms and both families and double-weighted selected candidates; defined properly it is 0.6250 (120/192) |
| 5 | The n=9 verifier is "provably non-discriminating" | **downgraded** (A7.1) | 0/400 bounds the rate at 0.00746 (one-sided 95%) for those Qs; a proposer concentrated on the 8 board symmetries would be accepted |
| 6 | `calib_harm` admits no tolerance, therefore harmful acceptance cannot be controlled | **withdrawn** (round 5 §1) | empty harmful panel in most regimes; in the mismatched regime 0/58 errors gives bound 0.0503 — a sample-size artifact, not a mechanism |
| 7 | `calib_exact` fails because label discrepancies exceed the tolerance | **withdrawn for declared/subgroup regimes** (round 5 §1) | the invalid-case panel is empty there, so the rule defaults to never firing; that is absence of calibration support, not evidence about discrepancies |
| 8 | No calibrated rule is best "on this continuum" | **narrowed** (round 5 §5) | the mixture table covers only declared and mismatched regimes, not the four approximate ones; and the graphs mixture used 0 as the risk of a regime that does not exist |
| 9 | q\* = 0.938 is the measured posterior threshold for label validity | **withdrawn** (round 5 §3) | B and H were estimated from sign-partitioned Δ, not from validity-conditioned effects; in the mismatched regime every group is invalid, including the two beneficial repairs |
| 10 | Holm-adjusted intervals, and "equivalent at the prespecified margin" | **removed** (round 5 §4) | widening a bootstrap interval by a normal quantile taken from an observed adjusted p-value is not an adjusted interval and not a TOST procedure |
| 11 | The edge-count rule beats LLM search | **reversed** (round 2) | its development advantage does not survive matched held-out rows |
| 12 | A symmetry-specific benefit at η = 0 | **not established** (round 1) | the gate-count-matched duplicate control closes most of the gap |

## What survives as a technical record (with its scope stated)

* **Enforcing equivariance has a robust cost when the target breaks the symmetry**: +0.03605,
  CI [+0.02998, +0.04210] under the primary estimand (fixed direction set, resampled optimiser
  seeds); four resampling schemes all exclude 0. Conditional on one dataset and one direction set.
* **Inference-time group averaging is the intervention that moved the deployed predictor** on
  `graphs_n6`: −0.04862 development, −0.02846 held-out (7/12 runs fired). Coverage-conditional.
* **A label-exactness screen and a beneficial-averaging decision are different objects**, and under
  approximate symmetry they disagree. This is the observation the new study starts from.
* **Corrected-feedback search runs**: ring candidate-risk effect +0.00039
  [−0.00016, +0.00093], descriptive band containment only; the deployed graphs contrast −0.07269
  [−0.12931, −0.02313] has unadjusted p = 0.0176 and does not survive Holm (0.158). Underpowered;
  a hypothesis for a better-powered follow-up, not a result.
* **Process record**: five rounds of defects found and fixed, including several found by the
  referee in our own analysis code (tie-breaking that manufactured a win, an invalid adjusted
  interval, conditioning mismatches). The lessons in `research/PROVENANCE.md` are the most
  transferable output of this project.

## Methodological lessons carried forward into `shotcert/`

1. Never let a calibration panel be empty and let the code return "no admissible setting" — that
   conflates *no evidence* with *evidence of failure*. Report panel support explicitly.
2. Calibrate on data that is independent of the data scoring the policy, and name the independence
   unit. Seed-vector bootstrap does not validate a binomial model inside a calibration step.
3. Keep estimand conditioning and estimator conditioning identical. A sign-partitioned mean is not a
   validity-conditioned mean.
4. Do not construct confidence sets from observed p-values. Use two one-sided tests, or a
   simultaneous bound with stated coverage.
5. A verdict computed from a table must not be broader than the table. Regimes absent from the
   mixture are not covered by the verdict.
6. Ties between policies are ties. Compare by regret against a stated baseline with paired
   uncertainty and a practical margin, not by unique argmin over names.
