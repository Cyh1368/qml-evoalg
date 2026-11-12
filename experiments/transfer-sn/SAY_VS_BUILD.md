# Does naming the symmetry mean finding it?

Test of the hypothesis that a researcher reading ShinkaEvolve's patch notes can
be fooled: weak and mid models talk about the symmetry as if they found it,
while the circuits they actually build do not have it. Proposed remedy was to
run repeatedly and accept a claimed symmetry only when it is claimed
consistently across runs.

Analysis 2026-08-17 over 15 runs already on disk (weak n=10, mid n=5, frontier
n=3). No new runs. Scripts: `analyze_symmetry_language.py`,
`analyze_symmetry_talk_vs_build.py`, `symmetry_analysis.py`.

Method: "SAYS" means the LLM-authored patch name or description matches
`symmetr|equivariant|permutation|invarian|orbit|S_?8|exchangeab|relabel`. Only
LLM-authored fields are searched, never evaluator feedback. "BUILDS" means the
proposed ANSATZ_SPEC contains at least one family of 8 single-qubit gates
driven by one parameter, which is what an S_8 orbit requires.

## The core result: the same words mean different things

Per-proposal, pooled within each arm:

| arm | P(builds \| says it) | P(builds \| does not say it) | lift |
|---|---|---|---|
| weak | 3/15 = **20.0%** | 19/175 = 10.9% | +9.1 pts |
| mid | 8/36 = **22.2%** | 11/59 = 18.6% | +3.6 pts |
| frontier | 32/33 = **97.0%** | 29/54 = 53.7% | +43.3 pts |

When the frontier ensemble says "symmetry" it has built the symmetry 97% of the
time. When mid says the same word it has built it 22% of the time, and the
statement carries almost no information: mid's proposals are barely more likely
to be symmetric when it names the concept than when it does not.

The overall mention rates make this sharper. Mid mentions symmetry in **36 of
95** proposals (37.9%). Frontier mentions it in **33 of 87** (37.9%). The two
arms talk about symmetry at an identical rate and build it at 22% versus 97%.
Mention frequency does not separate them at all.

## The hypothesis is confirmed

Run-level view, with the structure of each run's final best program:

| arm | runs mentioning symmetry | runs whose best program is symmetric |
|---|---|---|
| weak | 6/10 | 2/10 |
| mid | **5/5** | **1/5** |
| frontier | 3/3 | 3/3 |

Mid names the symmetry in **every single run** and produces a symmetric final
circuit in **one**. A researcher reading only the patch notes across five mid
runs would see the symmetry claimed every time and conclude it was found.

The single clearest case is `mid_e1_r5`: it mentions symmetry in 12 of 19
proposals, the highest rate of any 20-generation run in the dataset, and its
best program has 20 free parameters and zero tied families. It talks about the
symmetry more than any frontier run and builds nothing.

The converse also occurs. `weak_e1_r9` scores 0.7540, the best weak run, with
zero mentions and zero tied families: a high score by a structurally wrong
route, claimed by nobody.

## The proposed remedy does not work as stated

The specific criterion, accept the symmetry only when the model says it
consistently across all runs, **produces a false positive on mid**:

| arm | says it in all runs? | verdict under the criterion | correct? |
|---|---|---|---|
| weak | 6/10, no | reject | correct |
| mid | **5/5, yes** | **accept** | **wrong** |
| frontier | 3/3, yes | accept | correct |

Mid satisfies the criterion completely and its circuits are unsymmetric in four
runs out of five. Requiring consistency does not rescue the signal, because
mid's talk is consistently present and consistently wrong.

## The criterion works when applied to what is built

Substituting the structural check for the verbal claim, and keeping the
repeated-runs logic unchanged:

| arm | runs whose best program is symmetric | verdict | correct? |
|---|---|---|---|
| weak | 2/10 | reject | correct |
| mid | 1/5 | reject | correct |
| frontier | 3/3 | accept | correct |

Clean separation. The repeated-runs intuition is right; the observable was
wrong. Consistency across reruns is the correct decision procedure, but it has
to be applied to the artifact the search produced, not to the model's
description of it.

This is checkable without an answer key. Counting distinct parameter names and
tied gate families is a property of the evolved code alone. A researcher who
does not know the true symmetry can still ask whether independent runs keep
converging on the same structural regularity, which is the ground-truth-free
criterion from `EXP1B_RESULTS.md` applied to structure rather than score.

## Limits

- Vocabulary matching is crude. It counts a mention, not whether the model
  claimed to have *implemented* the symmetry, so some frontier mentions are
  probably discussion rather than assertion. This cuts against frontier, whose
  97% is measured despite the noise, and does not rescue mid.
- "Fully tied 8-wire family" is a sufficient condition for the S_8 orbit
  structure but is checked structurally, not behaviourally. The equivariance
  error in `symmetry_analysis.py` would confirm it; it has not been run per
  proposal.
- One task, one symmetry. Permutation invariance is a natural, heavily
  represented concept, so the say-build gap may differ for less familiar
  structure.
- Frontier n=3 runs, 87 proposals. The per-proposal counts are reasonable; the
  run-level 3/3 is thin.

## Consequence for the benchmark claim

Two independent readouts now separate frontier from the cheap arms, and neither
requires knowing the answer: score variance across reruns (`EXP1B_RESULTS.md`,
sd 0.054 versus 0.22) and structural consistency across reruns (3/3 versus 1/5
and 2/10). The model's own account of what it did separates nothing, and is
actively misleading for mid.

Practical rule for anyone running ShinkaEvolve on a problem with unknown
structure: never take the proposer's description as evidence of a discovery,
extract the structural invariant from the evolved artifact, and require it to
recur across independent runs.

## Reproducing

```
PY=viz/.venv_render/bin/python
$PY transfer-sn/analyze_symmetry_talk_vs_build.py transfer-sn/results_or_mid_e1_r5/programs.sqlite
$PY transfer-sn/symmetry_analysis.py --results-dir transfer-sn/results_or_mid_e1_r5
```

`analyze_symmetry_language.py` and `analyze_symmetry_talk_vs_build.py` need
numpy, which is not on the bare python3; use the `viz/.venv_render` interpreter.
