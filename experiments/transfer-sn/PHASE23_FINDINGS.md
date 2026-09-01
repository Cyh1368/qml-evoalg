# Phase 2/3: does any single model in the ensemble actually matter?

Cluster runs on Bouchet, submitted 2026-08-13, all 22 jobs `COMPLETED`
(job IDs 22097373-94, 42-111 min each). Analysis script:
`analyze_phase23.py`; machine-readable output: `phase23_metrics.json`.

Phase 1 attributed credit within a single ShinkaEvolve run by asking which
model authored the record-setting generations. That attribution is only
meaningful if the answer would change when you remove the credited model.
These runs test that directly, and the answer is that it does not change:
seed-to-seed variation is roughly two orders of magnitude larger than the
effect of deleting a model from the ensemble.

## What was run

**Phase 2, seed replication.** The `weak` arm (gpt-5.4-nano,
gemini-3.1-flash-lite, qwen3-coder) was run at 5 independent seeds and the
`mid` arm (gpt-5.4-mini, gemini-3-flash, claude-haiku-4.5) at 3, each to a
target of 50 generations. Nothing varies but the seed.

**Phase 3, rewind ablations.** A completed `weak` run was rewound to
generation *k* and continued to generation 50 under two conditions, 4 seeds
per condition:

| Experiment | Rewind gen | Control ensemble | Ablation removes |
|---|---|---|---|
| `rw13` | 13 | nano + flash-lite + qwen | `qwen3-coder` |
| `rw20` | 20 | nano + flash-lite + qwen | `gemini-3.1-flash-lite` |

Both arms of a pair inherit a byte-identical prefix, so everything after
gen *k* is attributable to ensemble composition plus seed. The rewind
procedure is the one verified on 2026-08-13 (delete rows with
`generation > k`, prune archive, recompute `children_count` and
`metadata_store`, drop `bandit_state.pkl`).

## Phase 2: the seed is the dominant variable

| Run | Best | Gen | Author | Cost $ |
|---|---|---|---|---|
| `weak_r1` | 0.8344 | 38 | qwen3-coder | 0.57 |
| `weak_r2` | 0.5097 | 28 | gpt-5.4-nano | 0.26 |
| `weak_r3` | 0.0962 | 48 | gpt-5.4-nano | 0.10 |
| `weak_r4` | 0.5516 | 47 | qwen3-coder | 0.33 |
| `weak_r5` | 0.1391 | 12 | gpt-5.4-nano | 0.16 |

mean 0.4262, sd **0.3085**, range [0.0962, 0.8344], spread 0.7382.

| Run | Best | Gen | Author | Cost $ |
|---|---|---|---|---|
| `mid_r1` | 0.2725 | 20 | gpt-5.4-mini | 1.99 |
| `mid_r2` | 0.4443 | 38 | gpt-5.4-mini | 1.48 |
| `mid_r3` | 0.4338 | 47 | gemini-3-flash | 0.79 |

mean 0.3836, sd 0.0963, range [0.2725, 0.4443].

The `weak` arm's best score spans nearly the entire achievable range purely
on seed. `weak_r1` at 0.8344, the run Phase 1 analyzed, is the best of five
and about 1.3 sd above the arm mean: it is an outlier, not a typical run.
Any narrative built on which model authored `weak_r1`'s records is a
narrative about one draw from a very wide distribution.

The `mid` arm is markedly tighter (sd 0.0963 vs 0.3085) at 3-6x the cost.
With n=3 vs n=5 this is suggestive rather than established, but the direction
is that stronger ensembles buy consistency rather than a higher ceiling:
`mid`'s best run (0.4443) is well below `weak`'s best (0.8344).

## Phase 3: removing a model changes nothing measurable

Both experiments inherited the same prefix best of **0.4920** at their
respective rewind points, which is itself a finding: generations 14-20 of the
parent run produced no improvement at all, so rewinding at 13 and at 20 start
from the same score.

### rw13, ablating qwen3-coder

| Run | Base | Best | Gain | Gens to beat base |
|---|---|---|---|---|
| `ctl_r1` | 0.4920 | 0.4920 | 0.0000 | never |
| `ctl_r2` | 0.4920 | 0.6249 | 0.1329 | 7 |
| `ctl_r3` | 0.4920 | 0.6308 | 0.1388 | 11 |
| `ctl_r4` | 0.4920 | 0.5926 | 0.1006 | 36 |
| `abl_r1` | 0.4920 | 0.4920 | 0.0000 | never |
| `abl_r2` | 0.4920 | 0.6107 | 0.1187 | 7 |
| `abl_r3` | 0.4920 | 0.5511 | 0.0591 | 2 |
| `abl_r4` | 0.4920 | 0.6508 | 0.1587 | 2 |

control gain 0.0931 ± 0.0643, ablation gain 0.0841 ± 0.0694, difference
**+0.0090**. Welch t=0.19, df=5.96, p=0.86; Mann-Whitney U=8.5, p=0.89.

`qwen3-coder` set **zero** post-rewind records in the control arm across all
four seeds. The control-arm records came from gemini-3.1-flash-lite (2
records, +0.2335) and gpt-5.4-nano (1 record, +0.1388). Deleting a model that
contributed nothing changed nothing, which is the expected direction but also
means `rw13` is a weak test: it ablated an idle model.

### rw20, ablating gemini-3.1-flash-lite

| Run | Base | Best | Gain | Gens to beat base |
|---|---|---|---|---|
| `ctl_r1` | 0.4920 | 0.4920 | 0.0000 | never |
| `ctl_r2` | 0.4920 | 0.6176 | 0.1255 | 2 |
| `ctl_r3` | 0.4920 | 0.5511 | 0.0591 | 3 |
| `ctl_r4` | 0.4920 | 0.5511 | 0.0591 | 4 |
| `abl_r1` | 0.4920 | 0.5511 | 0.0591 | 7 |
| `abl_r2` | 0.4920 | 0.4920 | 0.0000 | never |
| `abl_r3` | 0.4920 | 0.5511 | 0.0591 | 10 |
| `abl_r4` | 0.4920 | 0.6410 | 0.1490 | 3 |

control gain 0.0609 ± 0.0513, ablation gain 0.0668 ± 0.0615, difference
**-0.0059**: the ablation arm did marginally *better*. Welch t=-0.15,
df=5.81, p=0.89; Mann-Whitney U=7.5, p=0.89.

Here the ablated model was not idle: gemini-3.1-flash-lite authored 1 of 4
control-arm records (+0.0591 of +0.2437 total gain). Removing a model that
was contributing still produced no detectable degradation, because the other
models pick up the slack.

## Effect size versus noise

| | rw13 | rw20 |
|---|---|---|
| observed \|difference\| | 0.0090 | 0.0059 |
| pooled sd | 0.0669 | 0.0566 |
| MDE at 80% power, n=4/arm | 0.1555 | 0.1316 |
| observed / MDE | 0.06 | 0.04 |
| seeds per arm to detect observed difference | ~875 | ~1465 |
| difference as % of Phase-2 seed sd (0.3085) | 2.9% | 1.9% |

These are not underpowered-but-promising results. The observed differences
are 4-6% of the smallest effect this design could have detected, and would
need roughly a thousand seeds per arm to resolve. The honest reading is that
the ensemble-composition effect is bounded well below the seed effect, not
that it is unmeasured.

## Caveats

**One control run was accidentally an ablation.** In `rw20_ctl_r4` the bandit
never sampled gemini-3.1-flash-lite in any post-rewind generation (proposals:
gpt-5.4-nano 9, qwen3-coder 4, gemini 0). That run is nominally control but
functionally identical to the ablation condition, which biases the rw20
comparison toward the null. Since rw20 already shows the ablation arm
slightly ahead, correcting this cannot rescue a control advantage, but the
rw20 numbers should be quoted with this noted.

**The post-rewind budget is small.** Each rewind run produced only 11-22
programs after the rewind point (target 50 generations, ~30 stored programs
total). Model-level differences have few draws in which to show up.

**Scores are strongly quantized.** Across the 8 rewind runs there are 187
distinct correct-score values, but the mass concentrates on a few attractors:
0.4920 (33 hits), 0.4095 (27), 0.1903 (24), 0.5511 (17). Several runs land on
exactly 0.5511 or never leave 0.4920. Gains are therefore near-discrete
jumps between plateaus, which makes means over 4 seeds coarse and inflates
apparent variance.

**Cost is not the differentiator.** All 16 rewind runs cost $0.25-0.38; the
arms are indistinguishable on spend, so the null result is not a
control-arm-ran-out-of-budget artifact.

## What this means for the paper

The Phase-1 per-model credit metrics measure authorship, not necessity. A
model can author every record in a run and still be removable without cost,
because the remaining models explore the same space and reach the same
plateaus. Any claim of the form "model X drove this run" needs the
counterfactual to back it, and here the counterfactual comes back null.

The result worth reporting is the variance result: on this task a single
ShinkaEvolve run tells you very little, the `weak` arm's outcome ranges over
0.096-0.834 on seed alone, and the headline `weak_r1` run at 0.8344 is the
top of five draws. Reporting single-run numbers, ours or anyone's, without
seed replication substantially overstates what was found.

## Suggested next runs

1. Replicate `mid` to n=5 to confirm the variance-reduction effect, which is
   currently the most interesting live hypothesis and rests on n=3.
2. Ablate to a *single* model rather than 3→2. If 3→2 is null, the
   interesting question is whether ensemble diversity matters at all.
3. Fix the bandit-coverage leak: either force a minimum sampling rate per
   model in control arms, or record and report realized sampling so runs like
   `rw20_ctl_r4` can be excluded by a pre-registered rule.
4. Raise the post-rewind budget, or rewind earlier, so each run has more than
   ~15 proposals in which to differentiate.
