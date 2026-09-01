# Plan: is the ShinkaEvolve score a usable benchmark instrument?

Drafted 2026-08-14 in response to `2026-08-14-direction.md`. Awaiting approval.
Budget ceiling $50. Nothing submitted yet.

## The hypothesis, restated as a measurement problem

The proposal is to benchmark model ensembles by how well they do on the graph
connectedness problem under ShinkaEvolve. That only works if the score behaves
like an instrument: rerun the same ensemble and get a similar number, run a
better ensemble and get a reliably higher one. Two quantities decide it:

- **noise floor**: the spread of the score when nothing changes but LLM
  sampling. Call it `sd_within`.
- **signal**: the gap between ensembles we believe differ in capability.

The benchmark is viable iff signal exceeds noise by enough that a practical
number of repeats separates tiers. Everything below is built to measure those
two numbers before spending anything on ablations.

## Phase 0 (already done, $0): what the 25 existing runs say

Best-so-far by generation, mean ± sd across existing runs, with cumulative cost:

| gen | weak (n=5) | mid (n=3) | frontier (n=1) | weak $ | mid $ | front $ |
|---|---|---|---|---|---|---|
| 9  | 0.202 ± 0.224 | 0.311 ± 0.087 | 0.887 | 0.25 | 0.60 | 3.36 |
| 14 | 0.250 ± 0.224 | 0.311 ± 0.087 | 0.983 | 0.37 | 0.89 | 5.51 |
| 19 | 0.250 ± 0.224 | 0.311 ± 0.087 | 0.983 | 0.41 | 1.01 | 7.72 |
| 24 | 0.288 ± 0.230 | 0.366 ± 0.081 | 1.069 | 0.46 | 1.19 | 8.92 |
| 49 | 0.426 ± 0.309 | 0.384 ± 0.096 | 1.100 | 0.99 | 2.29 | 19.58 |

Three consequences, all of which change the design:

**1. weak and mid are not distinguishable and testing them is a waste.**
At gen 49 the gap is +0.043 with pooled sd 0.229, Cohen d = 0.19. Separating
that needs ~63 runs per arm. Note the sign: `weak` scores *higher* than `mid`
on average while costing a third as much. Any benchmark claim that these two
tiers are ordered is not supported.

**2. frontier separates from both, hugely.** It sits 2.18 weak-sd above weak
and 7.44 mid-sd above mid, and its worst generation-9 score (0.887) already
exceeds the best score any weak or mid run reached in 50 generations (0.834).
At d of this size, n=3-4 per arm suffices. The whole discriminative signal in
this benchmark is frontier-vs-rest.

**3. The signal arrives early, and that is the budget lever.** Frontier is at
0.887 by generation 9 and 0.983 by generation 14, against a final 1.100. Weak
and mid crawl for 50 generations and never approach it. Truncating the
protocol at generation 20 keeps essentially all of the discriminative signal
at **40% of the cost** ($7.72 vs $19.58 for frontier).

Cost was previously understated in `PHASE23_FINDINGS.md`: those figures
counted only `api_costs` and omitted `meta_cost`, `novelty_cost` and
`embed_cost`. True totals are 2-6x higher. Frontier is dominated by proposer
spend ($18.31 of $19.58) at `reasoning_efforts: xhigh`.

## The protocol

**Fixed for every run: 20 generations, config otherwise byte-identical within
an arm, bandit seed fixed at 1.** Full trajectories are stored, so the score
at any k ≤ 20 can be recovered without rerunning. Primary metric is
best-so-far at generation 20; robustness checks at k = 10 and 15 come free.

Holding the bandit seed fixed makes each arm's spread a clean estimate of LLM
nondeterminism. The existing r1-r5 runs varied that seed, so a Levene test of
new-vs-existing weak runs tells us whether the seed contributes variance at
all. If it does not, the existing runs pool in as extra draws for free.

## Gate 1 + Gate 2: noise floor and tier separation

These are the same runs: repeats within an arm give `sd_within`, and the arm
means give the separation.

| Arm | Ensemble | n | $/run @20 gen | Subtotal |
|---|---|---|---|---|
| weak | nano + flash-lite + qwen3-coder | 10 | 0.41 | $4.10 |
| mid | gpt-5.4-mini + gemini-3-flash + haiku-4.5 | 10 | 1.01 | $10.10 |
| frontier | gpt-5.6-sol + opus-4.6 + gemini-3.1-pro | 4 | 7.72 | $30.88 |
| | | | **expected** | **$45.08** |

Hard ceiling enforced per run via `max_api_costs` (frontier 9.0, mid 1.6,
weak 0.8), capping worst-case exposure at **$49.6**. Runs are cheap and
parallel; wall clock roughly 1-2 hours as before.

Why frontier gets n=4 while the cheap arms get n=10: frontier is 19x the cost
per run, and the effect it must resolve is enormous (d > 2), so n=4 is ample
for *separation*. Its `sd_within` estimate will be poor (95% CI on an sd from
n=4 spans roughly 0.6-2.2x the point estimate) and will be reported as a bound,
not a measurement. The cheap arms carry the precise noise-floor estimate.

### Decision rules, fixed in advance

Let `sd_within` be the pooled within-arm sd at generation 20.

- **PASS** if frontier's mean exceeds mid's by more than 3x `sd_within` and no
  frontier run overlaps the mid range. The instrument discriminates, and
  ablation work is justified.
- **MARGINAL** if the gap is 1-3x `sd_within`. Usable only with several repeats
  per measurement; report the required n.
- **FAIL** if the gap is under 1x `sd_within`, or if `sd_within` for the weak
  arm exceeds ~0.25 (i.e. reruns of an identical config span most of the
  achievable range). Then a single number does not characterise an ensemble
  and the benchmark idea does not survive in this form.

Also recorded regardless of outcome: whether within-arm sd differs from the
existing between-seed sd (Levene), and the number of repeats needed for a
one-model change to be detectable, which sizes any future ablation.

## Gate 3: the rediscovery experiment (conditional, NOT in this budget)

Only run if Gate 1/2 returns PASS or MARGINAL. Designed here so the analysis
is fixed before data exists; costed separately below.

The previous Phase 3 ablations had two defects that this design corrects:

1. **They ablated the wrong models.** rw13 removed qwen3-coder, which authored
   0% of that arm's gains; rw20 removed gemini-flash-lite at 24%. The dominant
   contributor (gpt-5.4-nano at 76%, gemini at 63%) was never removed.
2. **They had no power.** With n=4/arm the smallest detectable difference was
   0.156, while the entire gain available to destroy was 0.093. Even total
   elimination of all progress could not have reached significance. The null
   was uninformative by construction.

Corrected design: identify a run containing a genuine discovery (a single
generation producing a large score jump), rewind to the generation before it,
and continue with and without **the model that authored it**, at an n set by
Gate 1's noise floor so that the max possible effect sits well above the
detection floor.

**Outcome classification.** The direction doc's key point is that recovering
the score is not the same as recovering the discovery. Each ablation run is
classified on two axes:

| | same structure | different structure |
|---|---|---|
| **score recovered** | rediscovered: the model was not special | convergent alternative: a different route to equal score |
| **score not recovered** | — | discoverer was essential |

Structure is fingerprinted from `ANSATZ_SPEC`: gate-type multiset, two-qubit
connectivity graph, parameter-sharing partition (the tied-family measure
`symmetry_analysis.py` already computes), depth and parameter count, plus the
embeddings already stored in `programs.sqlite`.

The threshold for "same structure" is not chosen by hand. Control-arm reruns
supply the null distribution: two control runs that both find the discovery
show how different two instances of the *same* discovery look. An ablation run
is "different structure" only if it exceeds that spread. This calibration is
why the control arm must be rerun rather than reused from a single run.

Estimated cost, weak arm at 20 generations, n=12 per arm: **~$10**. Frontier,
if the discovery worth studying only occurs there: n=12 x 2 arms x $7.72 =
**~$185**, which would need its own budget conversation.

## What I recommend

Approve Gate 1+2 as specified: **$45 expected, $49.6 hard-capped**, 24 runs.
It answers the question the direction doc puts first, and it is the
prerequisite for everything after. Do not fund weak-vs-mid discrimination; the
existing data already shows d = 0.19 there.

The likeliest outcome, given weak's existing sd of 0.309 against a mean of
0.426, is MARGINAL or FAIL for the cheap tiers and PASS for frontier-vs-rest.
If that happens, the honest form of the benchmark is coarse: it separates
frontier from non-frontier and cannot rank ensembles more finely than that.
That is still a publishable negative result about evolutionary-search
benchmarks, and it is worth knowing before building anything on top.
