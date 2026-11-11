# Continuing a frontier discovery under a different ensemble (frw3)

Jobs 23103674-98 and 23104274-78, submitted 2026-08-22. Analysis script
`analyze_frw3.py`; run data in `results/2026-08-22/`.

## Design

`results_or_frontier_r1` is rewound to generation 3, the point where
gpt-5.6-sol proposed `shared_cube_mixer` (combined_score 0.44771504, 44 gates,
26 parameters). Generations 0-3 are kept intact, everything above is deleted
from `programs.sqlite`, the bandit state is dropped, and the run continues under
a **different** ensemble. The question is not whether an ensemble can make the
discovery, but whether it can carry one forward once handed it.

| arm | runs | roster | seeds |
|---|---|---|---|
| weak | 10 | gpt-5.4-nano, gemini-3.1-flash-lite, qwen3-coder | 301-310 |
| mid | 10 | gpt-5.4-mini, gemini-3-flash, claude-haiku-4.5 | 321-330 |
| frontier | 5 | gpt-5.6-sol, claude-opus-4.6, gemini-3.1-pro | 341-345 |
| frontier minus sol | 5 | claude-opus-4.6, gemini-3.1-pro | 361-365 |

The readout is `s8_parts()` from `build_run_metrics.py`: a circuit is
S_8-invariant only if every single-qubit block covers all 8 wires **and** every
two-qubit block covers all 28 edges of K8. The parent's cube entangler covers
12 of those 28 edges, so the discovery it represents is genuinely half-finished,
and completing it is a well-defined target.

## Two defects in the data, stated up front

**Four new generations, not five.** `num_generations` counts generation 0, so
the target of 8 produced generations 4-7. The weak and mid arms each got four
new generations rather than the intended five.

**The frontier arms are truncated by billing, not by the models.** The
OpenRouter account ran out of credits around 00:10 on 2026-08-22, mid-flight.
The weak and mid runs had already finished their generations (480 trailing 402s
each, all from proposals abandoned at shutdown). The frontier runs hit 402 from
00:12 and the minus-sol runs from 00:10, giving 1,721 to 5,172 failed calls per
run and 1-3 stored programs instead of 4. `frontabl_r5` never made a single
successful call: it retried 5,172 times over three hours and its database still
holds only generations 0-3.

So the weak and mid results below are sound. The frontier arm is a lower bound
(fewer proposals than intended, and what it did produce still shows the effect).
The minus-sol arm is **not interpretable as an ablation** at n=8 proposals; it is
reported here for completeness and needs rerunning once credits are restored.

## Results

| arm | runs | new programs | improved on 0.4477 | best | median run-best | ties 8 wires | K8 entangler | S_8-invariant |
|---|---|---|---|---|---|---|---|---|
| weak | 10 | 40 | 7/10 | 0.7682 | 0.4898 | 18/40 | **0/40** | **0/40** |
| mid | 10 | 40 | 6/10 | 0.8083 | 0.4721 | 15/40 | **0/40** | **0/40** |
| frontier | 5 | 16 | 4/5 | 0.9989 | 0.8069 | 9/16 | **6/16** | **6/16** |
| frontier minus sol | 5 | 8 | 2/4 | 0.6967 | 0.5511 | 1/8 | 0/8 | 0/8 |

### The weak and mid arms never touch the entangler

Of the 80 weak and mid proposals, 64 still cover exactly the parent's 12 pairs.
The widest coverage any of them reaches is 20 pairs, in a single program. None
reaches 28. Every one of the 80 has a two-qubit gate, so this is not the
vacuous case where an ansatz passes the test by having no entangler at all.

What they do instead is tie rotation families across all 8 wires, in 18/40 and
15/40 proposals and in 8/10 runs each. That is the cheap half of the symmetry,
and it is the half already present in what they were given. The search stays in
a recognisable neighbourhood: recurring patch names are parity, cube, bipartite,
collective, butterfly, hypercube, that is, structured partitions of the 8 wires
that are not the full orbit.

### The frontier arm completes it, and one model does the completing

Four proposals reach 28 pairs, all from gpt-5.6-sol:

| run | gen | patch | score | angles | gates |
|---|---|---|---|---|---|
| frontier_r2 | 6 | `complete_graph_symmetric_entangler` | 0.8069 | 4 | 60 (16 RY, 8 RZ, 8 RX, 28 CZ) |
| frontier_r3 | 5 | `s8_parity_lens` | 0.8867 | 4 | 60 (16 RY, 8 RZ, 8 RX, 28 CZ) |
| frontier_r3 | 6 | `permutation_twist` | 0.9989 | 3 | 52 (16 RY, 8 RZ, 28 CZ) |
| frontier_r5 | 7 | `permutation_twist_ansatz` | 0.9027 | 5 | 88 (16 RY, 8 RZ, 8 RX, 56 CRZ) |

Per-model attribution over all 104 proposals:

| arm | model | proposals | S_8-invariant | 28-pair entangler |
|---|---|---|---|---|
| frontier | gpt-5.6-sol | 5 | 5 | 4 |
| frontier | gemini-3.1-pro | 6 | 1 (vacuous, no entangler) | 0 |
| frontier | claude-opus-4.6 | 5 | 0 | 0 |
| minus sol | gemini-3.1-pro | 5 | 0 | 0 |
| minus sol | claude-opus-4.6 | 3 | 0 | 0 |
| mid | gpt-5.4-mini / gemini-3-flash / haiku-4.5 | 12 / 13 / 15 | 0 | 0 |
| weak | gpt-5.4-nano / flash-lite / qwen3-coder | 13 / 12 / 15 | 0 | 0 |

Every gpt-5.6-sol proposal is S_8-invariant, four of the five with a real K8
entangler. Its two frontier partners made 11 proposals between them and produced
one vacuously invariant circuit with no two-qubit gate at all. Inside the same
runs, drawing from the same archive, on the same parent.

This is the model-attribution question from `frontier-resume.md` answered from
within the control arm rather than from the ablation: the ablation lost its
credits, but the full-roster runs already show opus-4.6 and gemini-3.1-pro
declining to complete the entangler on 11 chances.

### Consistency across runs

Structurally the arms are highly consistent, and consistent in opposite
directions: 0/40 and 0/40 for weak and mid, 6/16 in 4 of 5 runs for frontier.
That matches the fresh-run counts in `RUN_METRICS.md` section 1C (weak 0, mid 0,
frontier 23), so being handed the discovery does not change which arm can finish
it.

By score the picture inverts. Weak and mid run-bests span 0.2091-0.7682 and
0.2567-0.8083 around a starting 0.4477; three weak and four mid runs end below
where they began. The two arms are indistinguishable (medians 0.4898 and
0.4721), well inside the 0.2987 detection threshold measured in `EXP1_RESULTS.md`.

Convergence, where it occurs, is to the parent or to a shared dead end. Of 103
proposals only 97 have distinct ansatz specs:

- Four runs (weak_r5 g5, mid_r5 g7, mid_r9 g5, mid_r10 g7) re-proposed the
  gen-3 parent's spec byte-for-byte, scoring exactly 0.447715 again.
- weak_r3 g7 and weak_r6 g5 independently produced the identical 44-gate circuit
  (16 RY, 8 RZ, 8 RX, 12 CRZ, 5 angles) at 0.7682, both from gpt-5.4-nano. It is
  the parent's cube with CZ swapped for parameterised CRZ: still 12 edges.
- weak_r1 g4 with weak_r4 g7, and weak_r4 g5 with weak_r5 g6, are two more
  identical-spec pairs at 0.2091.

### They mostly do not claim the symmetry here

Symmetry vocabulary appears in 0 of 40 weak patch notes and 3 of 40 mid ones,
against 5 of 16 in the frontier arm. That is far below the mid arm's 67% naming
rate on fresh runs (`SAY_VS_BUILD.md`). Being handed a strong parent appears to
shift the notes toward incremental description rather than symmetry claims, so
the say-vs-build gap does not reproduce in this setting; it is replaced by a
build-vs-build gap.

## What this supports

For the guideline in `202608-18-direction.md`, this is a clean case where score
agreement and structural agreement point opposite ways. A researcher watching
scores sees 13 of 20 cheap runs improve on a frontier-made discovery, and two
independent weak runs converge on the same circuit at 0.7682, which reads as
reproducibility confirming a real finding. The structural check says all 20 runs
left the symmetry exactly as incomplete as they found it, and that the only
model to complete it was the one that started it.

The practical form of the guideline: rerunning at multiple seeds is necessary
but not sufficient. Cross-run agreement on a *score* can be manufactured by an
ensemble converging on a shared wrong structure. Agreement has to be assessed on
the structure that is claimed, which on this task means checking both halves of
the invariance rather than the tied-8 proxy.

## Follow-ups

1. Restore OpenRouter credits, then rerun the frontier and minus-sol arms. The
   ablation is the actual test of whether opus-4.6 and gemini-3.1-pro can
   complete the entangler when sol is not there to do it first, and at 8
   proposals it has not been run.
2. Extend all runs by one generation (target 9) to deliver the intended five.
3. The weak and mid arms are already at their intended n and need no rerun; if
   anything they would benefit from more generations rather than more seeds,
   since the structural result is unanimous while the scores are noise.
