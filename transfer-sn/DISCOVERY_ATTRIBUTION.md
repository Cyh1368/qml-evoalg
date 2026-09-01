# Who actually made the discovery, and was it an artifact of model selection?

Analysis of the three frontier runs (`or_frontier_r1` at 50 generations,
`or_frontier_e1_r1/r2` at 20), 2026-08-17. No new runs were submitted; every
number here comes from databases already on disk.

## The discovery is a single event at generation 3

Best-so-far lineage of `or_frontier_r1`, with the structural metrics from
`symmetry_analysis.py`:

| gen | score | free params | fully-tied 1q families | author |
|---|---|---|---|---|
| 0 | 0.0000 | 24 | 0 | seed |
| **3** | **0.4477** | **4** | **4** | **gpt-5.6-sol** |
| 5 | 0.7840 | 3 | 3 | gpt-5.6-sol |
| 9 | 0.8867 | 4 | 4 | gpt-5.6-sol |
| 14 | 0.9832 | 4 | 4 | gpt-5.6-sol |
| 22 | 1.0687 | 6 | 6 | claude-opus-4.6 |
| 39 | 1.1002 | 5 | 6 | gpt-5.6-sol |

Parameters collapse from 24 to 4 in one step at generation 3. Every later jump
is refinement inside the already-symmetric family, not a new discovery. The
S_8 structure is found once, at generation 3, by gpt-5.6-sol.

This matters for experiment design: only a rewind to generation 2 tests
discovery. Rewinds to 4, 8, 13 or 21 start from a circuit that already encodes
the answer and test refinement instead.

## Selection bias does not explain generation 3

gpt-5.6-sol draws 41-53% of proposals across the three runs, well above the
33% an even split would give, because UCB1 rewards it for succeeding. That
compounding is real, but it operates *after* the model starts winning, so it
cannot explain the first discovery.

UCB1 initialises by round-robin, and the schedule is identical in all three
runs:

| gen | model | parent | inspirations | score (r1 / e1_r1 / e1_r2) |
|---|---|---|---|---|
| 1 | claude-opus-4.6 | gen 0 (seed) | none | -0.96 / -2.10 / -0.96 |
| 2 | gemini-3.1-pro | gen 0 (seed) | none | -1.76 / -1.62 / -2.19 |
| 3 | **gpt-5.6-sol** | gen 0 (seed) | none | **+0.45 / +0.78 / +0.33** |

Same parent, no inspirations, one attempt each, fixed order, replicated three
times. Generations 1-3 are already a matched three-way head-to-head:
**opus 0/3, gemini 0/3, gpt 3/3.** The bandit had no meaningful data to
exploit at that point, so nothing about the generation-3 result is attributable
to selection.

Where the selection confound does live is later in the run, which is exactly
where the rewind ablations at generations 8, 13 and 21 would probe. Those test
refinement rather than discovery.

## Per-attempt discovery rate from cold starts

Counting every proposal made from a pre-discovery parent (parent score < 0.40)
across all three frontier runs, and asking whether the proposed ANSATZ_SPEC
contains at least one fully tied 8-wire family:

| model | attempts | produced a symmetric circuit |
|---|---|---|
| gpt-5.6-sol | 20 | **18 (90%)** |
| claude-opus-4.6 | 12 | 1 (8%) |
| gemini-3.1-pro | 9 | 0 (0%) |

gpt against the other two pooled: 18/20 versus 1/21, **Fisher exact two-sided
p = 1.7e-8**.

This is not one lucky draw. gpt finds the symmetry on nine attempts in ten from
cold starts; the other two frontier models essentially never do, across 21
attempts at equal or better opportunity.

## Consequences

The discovery question is answered observationally, at no cost, and the planned
rewind ablation is no longer the main event. Two caveats keep it from being
fully settled:

1. **Archive contamination.** In the existing runs, opus and gemini proposed
   into an archive that already contained gpt's symmetric circuits. Some of
   their 21 attempts could see the answer and still did not use it. This biases
   *against* them relative to a true cold start, so the observational gap may
   overstate their weakness.
2. **Observational, not interventional.** Removing gpt entirely and letting
   opus and gemini run alone would keep the archive gpt-free and give each
   roughly six dedicated attempts from the pre-discovery state.

A rewind-at-generation-2 ablation (opus + gemini, no gpt) remains worth running
as confirmation, reframed as removing the contamination confound rather than as
correcting a selection bias. It is no longer the primary evidence.

## Reproducing

```
python transfer-sn/symmetry_analysis.py --results-dir transfer-sn/results_or_frontier_r1
```

Per-model cold-start counts and the Fisher test are computed inline; see
`SAY_VS_BUILD.md` for the related talk-versus-build analysis.
