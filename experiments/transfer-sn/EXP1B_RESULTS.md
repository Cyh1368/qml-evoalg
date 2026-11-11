# Experiment 1b: the noise floor across all three arms

Five runs of the mid ensemble and two of the frontier ensemble, byte-identical
configs within each arm (mid md5 `cb481de6...`, frontier `a8053aca...`), 20
generations, bandit seed fixed at 1. Same protocol as exp1, only the roster
changed. Jobs 22391337-43, submitted and completed 2026-08-16, 1h30-2h28 each,
all COMPLETED with exit 0 and no API errors. Total spend $19.41.

The verdict against `BENCHMARK_PLAN.md`'s pre-registered thresholds is
deliberately **not** recorded here. See "Open question" below.

## Result

| arm | n | mean @gen20 | sd | CV | min | max |
|---|---|---|---|---|---|---|
| weak (exp1) | 10 | 0.3733 | 0.2386 | 0.64 | 0.0000 | 0.7540 |
| mid (new) | 5 | 0.3974 | 0.2811 | 0.71 | 0.0000 | 0.6888 |
| mid (pooled with r1-r3) | 8 | 0.3649 | 0.2221 | 0.61 | 0.0000 | 0.6888 |
| frontier | 3 | 0.9881 | 0.0542 | 0.05 | 0.9365 | 1.0445 |

Individual runs, best-so-far at generation 20:

| run | @10 | @15 | @20 | cost $ | top-scoring program authored by |
|---|---|---|---|---|---|
| mid_e1_r1 | 0.3245 | 0.3414 | 0.3482 | 1.16 | gemini-3-flash |
| mid_e1_r2 | 0.0000 | 0.0000 | 0.0000 | 1.22 | (none: seed never beaten) |
| mid_e1_r3 | 0.6888 | 0.6888 | 0.6888 | 1.19 | claude-haiku-4.5 |
| mid_e1_r4 | 0.2156 | 0.5385 | 0.6464 | 1.35 | gemini-3-flash |
| mid_e1_r5 | 0.0795 | 0.1582 | 0.3036 | 1.17 | gemini-3-flash |
| frontier_e1_r1 | 0.8867 | 0.8867 | 0.9365 | 7.12 | gemini-3.1-pro |
| frontier_e1_r2 | 0.3342 | 1.0445 | 1.0445 | 6.20 | gpt-5.6-sol |

The frontier n=3 pools these two with the existing `or_frontier_r1` (0.9832 at
generation 20), valid because exp1 showed the bandit seed contributes no
measurable variance. The mid n=8 pools in `or_mid_r1..r3` (0.2287, 0.4025,
0.3012) on the same grounds.

## Mid is no more reproducible than weak

sd 0.2811 across the five new mid runs, slightly worse than weak's 0.2386, and
`mid_e1_r2` evaluated 20 candidates without ever beating the seed circuit,
finishing at exactly 0.0000. That is the second total failure in 15 runs across
the two cheap arms. Pooling to n=8 gives sd 0.2221.

This kills the one encouraging signal in the earlier data. The sd of 0.088
across `mid_r1..r3` that suggested mid might be tighter than weak was a
small-sample artifact; at n=8 the mid spread is indistinguishable from weak's.

Mid also does not outscore weak: the pooled difference is -0.0084, confirming
`BENCHMARK_PLAN.md`'s decision to cut weak-vs-mid discrimination from the
design.

## Frontier is a qualitatively different instrument

sd 0.0542 against 0.2221 for mid, and a coefficient of variation of 0.05
against 0.61. In absolute terms roughly 4x tighter; relative to its own mean,
13x tighter. Every frontier run lands in [0.937, 1.044] while the cheap arms
scatter across [0.000, 0.754].

Reproducibility here tracks model capability, not merely score level. Nothing
in the plan predicted this; it was designed to measure separation between arm
means, and the within-arm spread turned out to be the more informative
quantity.

**This sd is a bound, not a measurement.** From n=3 its 95% CI spans roughly
0.03-0.16. Even the upper end sits well below the cheap arms, so the direction
is safe, but the magnitude needs more runs before it can be quoted.

## Structure: what the runs actually found

`symmetry_analysis.py` computes parameter-sharing uniformity against the answer
key. A gate family is "fully tied" when one parameter covers all 8 wires, which
is what S_8 permutation invariance requires. The task was built with this
symmetry; the evolution loop is never told it exists.

| run | score | unique params | fully-tied 1q families |
|---|---|---|---|
| frontier_e1_r2 | 1.0445 | 2 | 2 |
| frontier_r1 | 1.1002 | 5 | 6 |
| frontier_e1_r1 | 0.9365 | 4 | 4 |
| mid_e1_r3 | 0.6888 | 5 | 3 |
| mid_e1_r4 | 0.6464 | 7 | 0 |
| mid_e1_r1 | 0.3482 | 7 | 0 |
| mid_e1_r5 | 0.3036 | 20 | 0 |
| mid_e1_r2 | 0.0000 | 24 | 0 |
| weak_e1_r9 | 0.7540 | 7 | 0 |
| weak_e1_r7 | 0.6392 | 8 | 0 |
| weak_e1_r5 | 0.5487 | 7 | 4 |
| weak_e1_r1 | 0.3294 | 11 | 0 |

Two findings.

**All three frontier runs found the symmetry, by different circuits.** Every
one collapses to 2-5 free parameters with fully tied rotation families, against
24 in the untied seed. They do not agree on the realization: 44, 60 and 76
gates, using {RX,RY}, {RX,RY} and {RX,RY,RZ} respectively. Same invariant,
three different circuits expressing it. In the outcome grid of
`BENCHMARK_PLAN.md` Gate 3 this is the "convergent alternative" cell, reached
independently rather than under ablation.

**The best weak run scores 0.7540 without the symmetry.** `weak_e1_r9` has 7
free parameters and zero fully-tied families. It reaches three quarters of the
frontier score by a structurally wrong route. `weak_e1_r5` is a partial
exception, with 4 tied families at 0.5487, so tying is not strictly absent from
the cheap arms, but no cheap run combines tying with a frontier-level score.

## Open question: is run-to-run variance a ground-truth-free validity signal?

Raised 2026-08-17, not yet adjudicated, and the reason the pre-registered
verdict is being held.

A researcher running ShinkaEvolve on a real problem does not have an answer
key. Looking at `weak_e1_r9` alone, they would see 0.7540 and conclude the
evolved structure captured something real about the problem. It did not. That
error is invisible from a single run and invisible from the score alone.

The proposal is that the within-arm spread supplies the missing signal without
ground truth. High variance across identical reruns means the score is a draw
from a wide distribution and any single structure found is not trustworthy. Low
variance at a high score means independent searches keep arriving at the same
place, which is evidence that the place is real.

The structural table above is a direct test of this on a problem where the
answer is known, and it comes out in favor: the arms with sd ~0.22 produce
structurally wrong solutions that sometimes score well, and the arm with sd
0.054 finds the true invariant in all three runs. The criterion would have
reached the right conclusion using only the reruns.

Reasons this is not yet settled are recorded in the analysis notes, chiefly:
low variance is also produced by a searcher that reliably stalls, so the
criterion needs a level as well as a spread; the three frontier proposers share
pretraining and are not independent searchers; and n=3 is thin. Resolving these
determines whether Gate 3 is worth funding and in what form.

## Reproducing

```
python transfer-sn/analyze_exp1.py                       # weak arm, exp1
python transfer-sn/symmetry_analysis.py --results-dir transfer-sn/results_or_frontier_e1_r1
```

Note that `programs.sqlite` cannot be read over NFS from the Bouchet login node
while a run is live; it raises `sqlite3.OperationalError: locking protocol`.
Copy the database locally first, or read progress from `evolution_run.log`.
