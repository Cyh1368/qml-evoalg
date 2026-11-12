# Anonymized Motif-Discovery Experiment: Pre-Registration (2026-07-24)

**Author:** Banana Labs (via Claude Code), for Cheng-You / the Yale QI project.
**Status:** written BEFORE launch, as a pre-registration of design and predictions.
**Companion:** `context/motif-discovery-validity-audit-2026-07-24.md` (why the first
run's discovery claim failed) and this experiment's code in
`qml-ea/tic-tac-toe/shinka_cluster_motif_anon/`.

---

## 1. Why we are running this

The first motif-discovery run (`~/project/motif_discovery`, 2026-07-18) appeared to
show evolution "discovering" the eight tic-tac-toe winning lines: the best lineage put
12 of 12 three-qubit gates on winning lines, binomial p = 5.6e-13. The validity audit
showed that result is not discovery. The winning lines were handed to the model through
three channels: the prompt named the task "tic-tac-toe" and gave the board geometry, the
seed source literally defined `WIN_LINES`, `CORNERS`, and `CENTER` as constants above the
editable block, and the proposer models know tic-tac-toe as common knowledge. The tell:
the first mutation that ever added three-qubit gates placed 10 of 10 on winning lines
with essentially no score gain, and its own rationale said it was "leveraging domain
knowledge." That is recall, not search.

This experiment removes every prior-knowledge channel so that the only way to identify
the structure-bearing qubit triples is the training signal. It answers the question the
first run could not: **can LLM-driven evolution discover a task's higher-order motif when
it is given no semantic hint about what that motif is?** This is the question that matters
for real science, where the correct symmetry or motif is usually unknown in advance.

## 2. What we changed (the anonymization)

The underlying learning problem is unchanged: the same 9-qubit, 3-class classifier over
the same board states with the same labels, so results stay comparable to the leaky run
(the seed still scores about 0.58, confirmed by a local smoke test). We removed all
information that reveals which triples are winning lines:

1. **No semantics in the prompt.** The task is described as an abstract 9-qubit, 3-class
   classification problem. The words "tic-tac-toe", "board", "winning line", "corner",
   "edge", "center", "row", "column", "diagonal", "symmetry", and "motif" do not appear.
   The earlier "symmetry-inspired motifs" nudge in the prompt and evaluator feedback is
   also gone.
2. **No constants in the seed.** `WIN_LINES`, `CORNERS`, `EDGES`, `CENTER`, `PAPER_GRID`,
   the ASCII board diagram, and the board-enumeration/labeling code are removed from the
   file the model sees. Labels are precomputed offline into `data_splits.npz`; the seed
   only loads arrays. Class names are `class_0/1/2`, not cross/circle/draw.
3. **A secret qubit-label permutation.** A fixed permutation pi (build seed 777, held
   secret in `permutation_meta.json`) relabels the nine qubits everywhere: feature map,
   two-qubit connectivity, and readout. The problem is an exact relabeling of the original
   (isomorphic, identical optimal accuracy), but the winning-line triples become
   pi(WIN_LINES) = {(0,1,6),(0,2,3),(0,4,5),(0,7,8),(1,3,5),(1,4,8),(2,4,6),(5,6,7)}, an
   apparently arbitrary set of 8 triples out of the C(9,3)=84 possible. No board geometry
   is recoverable from the permuted coordinates.

**What structure remains available, by design.** The readout still groups qubits into
sets of {4,4,1}, which corresponds to the known corner/edge/center orbit partition. This
is deliberate: in the real scientific setting you typically know the basic symmetry but
not the higher-order motif. So the "known symmetry" is available and only the winning-line
motif is hidden. This is the correct experimental condition, not a leak.

**A built-in control (the graph-invisible lines).** Two of the eight permuted winning
lines, (0,1,6) and (0,4,5) (the images of the two board diagonals), have none of their
qubit pairs among the hardware-native two-qubit edges. They are invisible to any reasoning
about the wiring graph or the readout partition. They can only be found by the accuracy
signal. If evolution places three-qubit gates on these two triples, that is decisive
evidence of genuine, score-driven discovery rather than clever structural guessing.

## 3. What we run

Three independent runs, identical in every respect except the proposer model, so the
comparison isolates the model's contribution:

| tag | proposer model | run dir on Bouchet |
|---|---|---|
| haiku | `anthropic/claude-haiku-4.5` | `~/project/motif_anon_haiku` |
| sonnet | `anthropic/claude-sonnet-5` | `~/project/motif_anon_sonnet` |
| gpt56sol | `openai/gpt-5.6-sol` | `~/project/motif_anon_gpt56sol` |

Fixed across all three: 100 generations, converged eval protocol (validation-loss early
stopping, patience 75, restore-best-weights), NUM_RUNS=1 per candidate, UCB1 selection
over the single model, the same helper models for meta-recommendation and novelty
(`o4-mini`) and embeddings (`text-embedding-3-small`), and a per-run cost cap of $15.
The cost cap is a safety limit: cheaper models should reach 100 generations, while pricier
models (Sonnet in particular) may stop earlier on cost. Because the deliverable is the
per-generation trajectory, a run that stops at, say, generation 60 is still informative.

## 4. Predictions (pre-registered)

We register these before seeing results so that outcomes are evidence, not hindsight.

**If the pipeline genuinely discovers the motif:**
- Enrichment of three-qubit gates on the permuted winning lines rises **gradually** and
  **later** than in the leaky run, tracking score improvements, rather than appearing
  fully formed on the first triple-adding mutation.
- The best-so-far lineage's winning-line fraction ends well above the chance rate
  (8/84 = 0.095), with a significant binomial tail.
- At least one of the two graph-invisible lines, (0,1,6) or (0,4,5), is used. This is the
  strongest single signal.

**If the pipeline cannot discover it without hints (the null):**
- Three-qubit gates, if used at all, are spread roughly uniformly over triples; the
  winning-line fraction stays near 0.095 and the binomial test is non-significant.
- The graph-invisible lines are not found.
- Accuracy still improves through generic circuit tuning (more entanglement, parameter
  sharing on the readout-implied orbit groups), but not via the specific motif.

**Cross-model prediction.** If motif discovery depends on model capability, we expect an
ordering in discovery strength and speed, plausibly stronger for the larger reasoning
models (Sonnet 5, GPT-5.6-sol) than for Haiku. A flat result across all three (all null)
would suggest the motif is simply not recoverable from this training signal at this
compute budget; a positive result concentrated in one model localizes the capability.

Either outcome is publishable. A positive result is the first clean demonstration that
the pipeline discovers unknown higher-order structure. A null result honestly bounds what
LLM-driven evolution can find without domain hints, and reframes the leaky run as a
cautionary tale about contamination in LLM-in-the-loop discovery claims.

## 5. Analysis plan

For each run: `motif_analysis.py --results-dir <run> --meta permutation_meta.json`. It
reads the secret permuted lines, reports the best-so-far lineage trajectory (generation,
score, triples placed, triples on lines, lines covered), the exact binomial tail on the
final best program, and explicitly whether either graph-invisible line was found. Primary
comparison across the three models is the trajectory of winning-line fraction vs
generation, plus whether and when the graph-invisible lines appear.

## 6. Compute and cost

Reference: the leaky run did 100 generations in about 10 hours of wall clock with 6-8
concurrent SLURM eval jobs. These runs use the same training cost per candidate. Running
all three concurrently with 6 eval jobs each (18 total) should complete in roughly 10-16
hours depending on scheduler load and proposer latency, with pricier proposers possibly
ending earlier on the $15 cap. Worst-case total API spend is about $45. Eval jobs run on
the CPU `day` partition and never call the API; only the three login-node orchestrators
use the OpenRouter key.
