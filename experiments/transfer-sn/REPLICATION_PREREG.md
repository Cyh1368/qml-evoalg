# Replication experiment: same seed, run it again

Submitted 2026-08-14, job IDs 22190471-83. Manifest on the cluster:
`~/project/replication_jobs.txt`. Written before any results came back.

## The question

Every LLM call is nondeterministic. Rerunning the identical config will not
reproduce a run exactly, but if the pipeline is worth anything the reruns
should land in a similar place. That is what replication means here, and it
has not been tested.

## Why the earlier Phase 2 did not answer this

Phase 2 varied `seed` across runs and found a spread of 0.096-0.834 in the
weak arm. That was read as a seed effect. It is not, for two reasons:

1. `seed` is threaded to exactly one place, `llm_dynamic_selection_kwargs`,
   which seeds the UCB1 bandit RNG in `shinka/llm/prioritization.py`. Parent
   selection, archive/island logic and everything else run unseeded.
2. `llm_kwargs.temperatures = [1.0]` and no seed is passed to OpenRouter, so
   the proposer models are free-running regardless.

So the Phase 2 runs differed in bandit seed *and* LLM sampling *and* unseeded
selection simultaneously. The 0.31 spread cannot be attributed to the seed.

## What was submitted

Configs are byte-identical copies of the originals, seed left at 1
(md5 `c84eb51e...` for weak, `d900a014...` for mid). Nothing varies. All
variation observed is the pipeline's intrinsic nondeterminism.

| Arm | Config source | Repeats | Results dirs |
|---|---|---|---|
| weak | `shinka_config_or_weak_r1.json` | 8 | `results_or_weak_rep1..8` |
| mid | `shinka_config_or_mid_r1.json` | 5 | `results_or_mid_rep1..5` |

The original `weak_r1` (0.8344) and `mid_r1` (0.2725) are additional draws
from the same distribution, giving effective n=9 and n=6.

## Predictions, recorded in advance

**Primary.** Within-seed spread of the weak arm's best score will be large,
comparable to the 0.3085 sd measured across seeds. If so, the bandit seed
contributes little or nothing and the earlier Phase 2 "seed sensitivity"
finding should be restated as pipeline nondeterminism.

**On the headline run.** `weak_r1` scored 0.8344, the best of five. If the
8 reruns at the same seed cluster well below it, that score is a lucky draw
from a wide distribution rather than a property of seed 1. Concretely: fewer
than 2 of 8 reruns reaching 0.75+ would mean 0.8344 should not be quoted as
a representative result.

**Secondary.** The mid arm's tighter between-seed spread (sd 0.0963, n=3)
predicts a tighter within-seed spread too. If mid replicates tightly while
weak does not, "stronger models buy consistency" survives as a claim; if both
are wide, it does not.

## Decision rules, fixed now

- Compare within-seed sd to between-seed sd per arm (Levene on the two sets).
  Ratio near 1 means the seed is doing nothing.
- Report the full min-max range of reruns alongside any single-run number.
- If within-seed sd exceeds ~0.15 in the weak arm, no single weak-arm run is
  reportable on its own and every downstream weak-arm claim, including the
  Phase 3 ablation gains, needs restating with rerun error bars.

## Consequence for the Phase 3 ablations

The rewind ablations used 4 seeds per arm and found differences of 0.009 and
-0.006. Those arms also differ only in bandit seed, so their within-arm
scatter is the same nondeterminism measured here. This experiment supplies
the correct noise floor for that comparison; the ablation conclusion (no
detectable effect) is expected to hold or strengthen, but its stated error
bars were derived from a mislabeled source of variance and will be redone.
