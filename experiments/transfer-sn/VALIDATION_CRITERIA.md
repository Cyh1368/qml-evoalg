# How to tell whether an evolved symmetry is real, without an answer key

A researcher running ShinkaEvolve on a genuinely unknown problem cannot check
the discovered structure against ground truth. This document tests which
observable criteria actually discriminate, using our 18 runs where the answer
*is* known (S_8 permutation invariance, built into the task, never revealed to
the evolution loop).

Every criterion below is computable from run artifacts alone. Each is scored
against whether the run's best program really has the S_8 orbit structure, and
marked WORKS, PARTIAL or FAILS. Several plausible criteria fail, including the
two most natural ones.

Data: weak n=10, mid n=5, frontier n=3 (`or_*_e1_*` plus `or_frontier_r1`).
Ground truth via `symmetry_analysis.py`: a fully tied family is one parameter
driving a single-qubit gate on all 8 wires.

## Summary

| # | criterion | verdict | evidence |
|---|---|---|---|
| 1 | Best score is high | **FAILS** | top 2 weak runs by score have the wrong structure |
| 2 | Proposer says "symmetry" in its patch notes | **FAILS** | P(builds \| says) = 22% mid vs 97% frontier |
| 3 | Proposer says it consistently across all runs | **FAILS** | mid says it in 5/5 runs, builds it in 1/5 |
| 4 | Score variance across reruns is low | **WORKS** | sd 0.054 frontier vs 0.222 mid, 0.239 weak |
| 5 | Structural motif recurs across independent runs | **WORKS** | 3/3 frontier vs 1/5 mid, 2/10 weak |
| 6 | Motif recurs *within* a run across many proposals | **WORKS** | 70% frontier vs 29-33% cheap arms |
| 7 | Several distinct models converge on the motif | **PARTIAL** | 2.67 frontier vs 2.00 mid, separates weak only |
| 8 | Parameter count collapses relative to the seed | **PARTIAL** | good precision, misses one true positive |
| 9 | Independent runs agree on raw structural features | **FAILS** | modal agreement 67% frontier vs 50% weak |

The reliable signals are all **recurrence** measures, within and across runs.
Everything based on a single run, on the score, or on the model's own
description is unreliable.

---

## 1. High score. FAILS.

The natural move is to take the best-scoring run and inspect what it found.
This is exactly wrong. Weak-arm runs ordered by score, with `max_family` (the
largest number of gates driven by one parameter; 8 means tied across all wires):

```
0.754(mf4)  0.639(mf4)  0.549(mf8)  0.520(mf8)  0.361(mf4)
0.329(mf4)  0.257(mf4)  0.166(mf2)  0.159(mf1)  0.000(mf1)
```

The two highest-scoring weak runs both have the wrong structure. The correct
structure appears at ranks 3 and 4. A researcher who ran the weak ensemble ten
times, took the 0.754 winner and studied it would conclude the wrong thing.

Score is not useless: across the full set it correlates with structure
(Spearman rho = +0.87 weak, +1.00 mid and frontier). But the correlation holds
in aggregate while the argmax is wrong, and the argmax is what people inspect.

**Rule: never select the run to inspect by score.**

## 2. The proposer says "symmetry". FAILS.

Matching symmetry vocabulary in LLM-authored patch names and descriptions, then
asking whether that proposal actually built a tied family:

| arm | P(builds \| says it) | P(builds \| doesn't) | mention rate |
|---|---|---|---|
| weak | 3/15 = 20.0% | 10.9% | 7.9% |
| mid | 8/36 = 22.2% | 18.6% | **37.9%** |
| frontier | 32/33 = **97.0%** | 53.7% | **37.9%** |

Mid and frontier mention symmetry at an identical 37.9% rate and build it at
22% versus 97%. The words are literally uninformative between those two arms.

Worst case: `mid_e1_r5` names symmetry in 12 of 19 proposals, the highest rate
of any 20-generation run, and its best program has 20 free parameters and zero
tied families.

Full detail in `SAY_VS_BUILD.md`.

## 3. The proposer says it in every run. FAILS.

Requiring consistency of the verbal claim does not repair criterion 2:

| arm | mentions in all runs | verdict | correct? |
|---|---|---|---|
| weak | 6/10 | reject | yes |
| mid | **5/5** | **accept** | **no** |
| frontier | 3/3 | accept | yes |

Mid satisfies it perfectly and is wrong in 4 runs out of 5. Repetition filters
sporadic claims; it cannot filter a systematic confabulation.

## 4. Low score variance across reruns. WORKS.

Rerun the identical configuration N times and measure the spread of the final
score:

| arm | n | mean | sd | CV |
|---|---|---|---|---|
| weak | 10 | 0.3733 | 0.2386 | 0.64 |
| mid | 8 | 0.3649 | 0.2221 | 0.61 |
| frontier | 3 | 0.9881 | **0.0542** | **0.05** |

A wide spread means the reported number is one draw from a broad distribution
and any single structure found is untrustworthy. Note this needs a *level* as
well as a spread: a searcher that reliably fails also has low variance
(`mid_e1_r2` finished at exactly 0.0000). Use it as "consistently high", which
in practice requires comparing at least two configurations.

Caveat: frontier sd comes from n=3, 95% CI roughly 0.03-0.16.

## 5. Structural motif recurs across independent runs. WORKS.

For each run take the best program, extract the parameter-sharing partition,
and ask whether a single parameter drives a single-qubit gate family across
*all* wires of the system. Then count how many independent runs show it:

| arm | runs whose best program has the motif |
|---|---|
| weak | 2/10 |
| mid | 1/5 |
| frontier | **3/3** |

Clean separation. This is the single best criterion in the set, and it is what
the "run it multiple times" intuition should be attached to.

The question "does one parameter tie across the full extent of the system" is
generic. It does not require knowing which symmetry to look for, only that you
are testing for *some* invariance over the system's degrees of freedom.

## 6. Motif recurs within a single run. WORKS.

Fraction of all proposals in a run that contain the motif, averaged per arm:

| arm | mean within-run recurrence |
|---|---|
| weak | 33.3% |
| mid | 29.4% |
| frontier | **69.7%** |

A real attractor is found repeatedly by the search; a fluke is found once. This
is valuable because it works on a **single run**, so it is the cheapest signal
available and the only one on this list that does not require reruns.

Per-model rates sharpen it further. In frontier runs, gpt-5.6-sol produces the
motif at 10/10, 7/9 and 20/20. No mid model exceeds 6/10 in any run. A maximum
per-model rate above roughly 70% picks out all 3 frontier runs and `weak_e1_r6`
(9/10), and rejects every mid run.

## 7. Several distinct models converge on it. PARTIAL.

Mean number of distinct models producing the motif at least once per run:
frontier 2.67, mid 2.00, weak 0.80. Separates weak cleanly, mid poorly.

The count is too coarse because one lucky proposal counts the same as
saturation. The per-model *rate* in criterion 6 is the better form of this
idea. Keep the underlying logic, which is sound and important: if only one
model ever produces the structure, you may be measuring that model's prior
rather than the problem's structure.

## 8. Parameter count collapses. PARTIAL.

The seed has 24 free parameters. Best-program parameter counts:

- frontier: 4, 2, 5
- mid: 5, 7, 7, 20, 24
- weak: 5, 7, 7, 8, 10, 11, 12, 12, 24, 24

A threshold of 5 or fewer selects all 3 frontier runs, `mid_e1_r3` and
`weak_e1_r6`, all of which genuinely have the motif. Precision is perfect here.
It misses `weak_e1_r5`, which has the motif at 7 parameters.

Useful as a fast screen, unreliable alone, and the threshold was chosen with
hindsight. Prefer the direct structural test in criterion 5.

## 9. Runs agree on raw structural features. FAILS.

Tempting to skip the interpretation and just ask whether runs agree with each
other. Modal agreement on the raw `max_family` value:

| arm | values | modal agreement |
|---|---|---|
| weak | 1,1,2,4,4,4,4,4,8,8 | 5/10 = 50% |
| mid | 1,2,4,4,8 | 2/5 = 40% |
| frontier | 8,8,16 | 2/3 = **67%** |

Not a usable separation. Frontier's runs *do* agree on the invariant but not on
its surface realization: 44, 60 and 76 gates, parameter counts 2, 4 and 5, two
runs using {RX,RY} and one adding RZ. The 16 is `or_frontier_r1`, which ran 50
generations rather than 20.

**The agreement has to be measured on the normalized invariant, not on raw
counts.** This is the difference between criterion 5 working and criterion 9
failing, and it is the main technical subtlety in the whole protocol.

---

## Recommended protocol

For a researcher with no answer key, in order of cost.

**Step 1, free, single run.** Compute the within-run motif recurrence
(criterion 6). Extract the structural regularity from every proposal, not just
the best one, and measure what fraction of proposals exhibit it. Below roughly
40%, treat the finding as a fluke and stop. Also record the per-model rate: if
one model produces it and the others never do, flag that the structure may be
that model's prior.

**Step 2, cheap.** Ignore the patch notes entirely when deciding whether a
discovery occurred (criteria 2 and 3). Read them for hypotheses about *what*
the structure means, never as evidence *that* it exists. Verify every verbal
claim against the extracted artifact.

**Step 3, the main test, N reruns.** Rerun the identical configuration at least
5 times, ideally 10. Then:

- Extract each run's best program and compute the parameter-sharing partition
  normalized to system size (criterion 5). Accept the structure only if it
  recurs in a large majority of runs. In this dataset the true case is 3/3 and
  the false cases are 1/5 and 2/10.
- Measure the score spread (criterion 4). A CV above roughly 0.5 means the
  instrument is not resolving anything and no single run should be reported.
- Do **not** select which run to inspect by score (criterion 1). Inspect all of
  them, or the modal structure.

**Step 4, confirmation.** If the structure implies an invariance, test it
behaviourally rather than structurally: apply the candidate transformation to
inputs and measure whether outputs are unchanged. `symmetry_analysis.py`
computes this equivariance error. Structural tying is a proxy; the behavioural
check is the real thing and does not depend on any fingerprint choice.

**Step 5, if the stakes are high.** Rerun with the model that produced the
structure removed. If the remaining models recover it, the structure is a
property of the problem. If only one model ever finds it, you have learned
something about the model, not necessarily about the problem. See
`DISCOVERY_ATTRIBUTION.md` for how this plays out here: gpt-5.6-sol produces the
motif on 18 of 20 cold-start attempts while opus and gemini manage 1 of 21
combined, Fisher p = 1.7e-8.

## Limits, and one real risk of circularity

**The fingerprint choice is not innocent.** Criterion 5 works with a strict
definition (a single-qubit family tied across all wires) and degrades badly
with a looser one (any parameter spanning 8 or more wires, including two-qubit
gates), which gives weak 6/10, mid 3/5, frontier 3/3. We chose the strict
definition knowing the answer. A researcher without an answer key has to commit
to a fingerprint before seeing which one separates, and a poor choice will
blunt the criterion. This is the weakest point in the protocol and the most
important thing to address before publishing it.

Mitigation: prefer the behavioural test in step 4, which has no fingerprint
free parameter, and pre-register the structural fingerprint before running.

**Other limits.** One task and one symmetry. Permutation invariance is a
natural, heavily pretrained concept, so the say-build gap and the discovery
rates may differ for less familiar structure. Frontier n=3. Vocabulary matching
counts a mention rather than an assertion of implementation. The score-variance
thresholds are calibrated on this problem's score scale and do not transfer
as absolute numbers; use the CV, not the sd.

## Reproducing

```
PY=viz/.venv_render/bin/python
$PY transfer-sn/symmetry_analysis.py --results-dir transfer-sn/results_or_frontier_e1_r1
$PY transfer-sn/analyze_symmetry_talk_vs_build.py transfer-sn/results_or_mid_e1_r5/programs.sqlite
```

Related: `EXP1B_RESULTS.md` (score variance), `SAY_VS_BUILD.md` (talk versus
build), `DISCOVERY_ATTRIBUTION.md` (who found it and whether selection explains
it), `RELATED_WORK.md` (prior art on rerun variance).
