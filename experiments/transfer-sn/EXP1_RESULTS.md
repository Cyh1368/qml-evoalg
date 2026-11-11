# Experiment 1: the noise floor

Ten runs of the cheap ensemble, byte-identical configs (single md5), 20
generations, bandit seed fixed at 1. Jobs 22190763-72, submitted and completed
2026-08-14, 58-99 min each. Only the models' own sampling was free to vary.
Analysis: `analyze_exp1.py` → `exp1_metrics.json`.

## Result

| run | best @gen20 | cost $ |
|---|---|---|
| r9 | 0.7540 | 0.615 |
| r7 | 0.6392 | 0.639 |
| r5 | 0.5487 | 0.663 |
| r6 | 0.5201 | 0.611 |
| r3 | 0.3607 | 0.656 |
| r1 | 0.3294 | 0.614 |
| r10 | 0.2566 | 0.649 |
| r2 | 0.1655 | 0.618 |
| r4 | 0.1588 | 0.674 |
| r8 | 0.0000 | 0.674 |

mean 0.3733, **sd 0.2386**, median 0.3451, IQR 0.3533,
**best-worst gap 0.7540**. Ten distinct values from ten identical
configurations. Total spend $6.41.

The gap between the luckiest and unluckiest run is 0.754, which is larger than
the entire mean score. Run r8 evaluated 20 candidates and every one was worse
than the starting circuit, so it finished with no improvement at all: **1 run
in 10 produces nothing**. Run r9 nearly reached the 0.834 that `weak_r1` hit in
50 generations, in 20.

## The bandit seed does nothing

| | sd at gen 20 | range |
|---|---|---|
| fixed seed (new, n=10) | 0.2386 | [0.0000, 0.7540] |
| varying seed (old, n=5) | 0.2235 | [0.0000, 0.4920] |

Brown-Forsythe W = 0.089 (df 1,13), nowhere near the ~4.5 needed to claim a
difference. Holding the seed fixed did not reduce the spread by any detectable
amount.

This settles an open question. The 0.3085 sd previously reported across
`weak_r1..r5` and attributed to the seed was **entirely model sampling
randomness**. The seed only ever fed the UCB1 bandit RNG, and that contributes
nothing measurable. Every variance number in `PHASE23_FINDINGS.md` should be
read as LLM nondeterminism, not seed sensitivity.

## Spread against generation budget

Truncating the same runs, free from stored trajectories:

| gens | mean | sd | min | max | gap | mean $ |
|---|---|---|---|---|---|---|
| 5 | 0.0686 | 0.0856 | 0.0000 | 0.2239 | 0.224 | 0.098 |
| 10 | 0.1954 | 0.1916 | 0.0000 | 0.5374 | 0.537 | 0.233 |
| 15 | 0.3428 | 0.2262 | 0.0000 | 0.7540 | 0.754 | 0.440 |
| 20 | 0.3733 | 0.2386 | 0.0000 | 0.7540 | 0.754 | 0.641 |

Noise grows with the score and does not settle. Running longer buys a higher
mean but not a steadier number, so a longer protocol will not rescue
reliability.

## Verdict against the pre-registered thresholds

**Noise floor sd = 0.2386, against a FAIL line of 0.25.** Technically below it,
so the formal verdict is MARGINAL rather than FAIL, but only just, and nothing
about that margin is reassuring.

Practical consequence: with n=10 per arm, two ensembles must differ by
**0.2987** before the difference is detectable. That threshold is most of the
usable score range. Against it:

| | score at gen 20 | vs weak |
|---|---|---|
| weak (this experiment, n=10) | 0.3733 | — |
| mid (existing, n=3) | 0.3108 | -0.06, **far below threshold** |
| frontier (existing, n=1) | 0.9832 | +0.61, **above threshold** |

The mid ensemble again scores *below* the cheap one, now at generation 20 as
well as generation 50. Weak-vs-mid remains unresolvable and not worth funding.

Frontier's lead of 0.61 clears the detection threshold, and would still clear
it at n=4 frontier vs n=10 weak (threshold 0.395 under that split), assuming
frontier's spread resembles weak's. So the instrument can separate frontier
from the rest, and cannot do anything finer.

## Budget correction

Runs cost **$0.64 each, not the $0.41 projected** from the older runs'
cumulative spend at generation 19: a 1.56x underestimate, because these runs
issue more proposals per generation. Applying that factor to the rest of the
plan:

| | planned | corrected |
|---|---|---|
| Exp 1 (weak, n=10) | $4.10 | $6.41 actual |
| Exp 2 (mid, n=10) | $10.10 | ~$15.80 |
| Exp 3 (frontier, n=4) | $30.88 | **~$48.20** |
| total | $45.08 | **~$70** |

**Experiments 2 and 3 as specified no longer fit the $50 budget**, and
frontier alone would nearly exhaust it. Options, none yet chosen:

1. Skip Exp 2 entirely. Weak-vs-mid is already shown to be unresolvable, so
   the $15.80 buys a noise-floor estimate for an arm we cannot use anyway.
   Spend on frontier: n=4 at ~$48 fits, with Exp 1 already banked.
2. Cut the frontier protocol to 10 generations (~$6/run at the observed rate,
   since frontier reached 0.983 by generation 14 and 0.887 by generation 9).
   n=6 for ~$36, leaving room for Exp 2 at reduced n.
3. Lower frontier `reasoning_efforts` from `xhigh`. Cheaper, but changes the
   ensemble definition and breaks comparability with `frontier_r1`.

Option 2 is the most informative per dollar: Phase 0 showed frontier's signal
saturates early, so a 10-generation frontier protocol keeps the separation
while roughly quartering the cost.

## What this means for the benchmark hypothesis

A single ShinkaEvolve run does not measure an ensemble. Ten identical attempts
returned ten different numbers spanning 0.00 to 0.75, one of which was a total
failure. Any single-run score, including the 0.834 and 1.100 headline numbers,
is one draw from a distribution this wide.

A benchmark is still possible, but only in coarse form and only with repeats:
roughly 10 runs per ensemble to resolve differences of ~0.3, which is enough to
say "frontier beats the rest" and not enough to rank anything within a tier.
Whether frontier's own spread is small enough to preserve even that separation
is exactly what Experiment 3 would test, and is now the only question in the
plan worth the remaining money.
