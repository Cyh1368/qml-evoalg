# Related work: rerun variance in LLM-driven evolutionary search

Collected 2026-08-17 while assessing the hypothesis in `EXP1B_RESULTS.md`
("Open question"): that low run-to-run variance at a high score is a
ground-truth-free signal that an evolutionary search found real structure.

**Verification status matters here.** Most entries below were found by web
search and are recorded at the resolution I actually confirmed. Several arXiv
PDFs did not extract cleanly, so their claims are quoted from search snippets
rather than from the papers. Anything marked SNIPPET must be read properly
before being cited in a writeup.

| status | meaning |
|---|---|
| SNIPPET | claim seen only in a search result summary, not verified against the paper |
| FETCHED | retrieved the document, but extraction was partial or hedged |
| KNOWN | established work, claim is standard and not in doubt |

## The gap this project sits in

Nothing found treats rerun variance as a *diagnostic for whether a discovery is
real* in LLM-driven scientific search, and nothing found reports that variance
shrinks with proposer model capability. The existing literature treats variance
as noise to be reported honestly or averaged away. Using it as signal, and
validating that use against a task with a known hidden symmetry, appears open.

Two things would have to hold for the contribution to survive contact with
this literature: the criterion needs a level as well as a spread (a reliably
stalling searcher also has low variance), and the proposers in an ensemble
share pretraining, so their agreement is not independent evidence.

## Closest prior work

**What Do Evolutionary Coding Agents Evolve?** (arXiv:2605.20086) — SNIPPET
<https://arxiv.org/pdf/2605.20086>

The nearest thing found to our frontier result. Reported finding: breakthrough
events are not crisp, repeatable artifacts. Same-prompt replays almost never
reproduce the original program byte-for-byte, yet typically recover a
substantial fraction of its score from a different program. Framed as "the
trajectory carries the structural gain, while the specific program is one draw
from a wider distribution."

That is close to what the three frontier runs do here: all find the S_8 tying,
none by the same circuit (44, 60, 76 gates). Introduces tooling named EvoTrace
and EvoReplay.

Caveat: the PDF did not extract cleanly and the fetched summary was hedged and
non-specific. Read this one properly before positioning against it. It is the
paper most likely to have scooped part of the structural claim.

## The best-of-N reporting problem

**Compute Allocation in Evolutionary Search: From Depth-Breadth to Multi-Armed
Bandits** (arXiv:2605.29268) — SNIPPET
<https://arxiv.org/html/2605.29268v1>

Source of the clearest statement of the methodological complaint: the dominant
convention in LLM-guided evolutionary search is to report only the best of an
unspecified number of runs, and few systems report the run-to-run distribution
behind those headline numbers.

Directly supports the framing that our exp1/exp1b numbers are unusual in being
reported as distributions at all.

**TurboEvolve: Towards Fast and Robust LLM-Driven Program Evolution**
(arXiv:2604.18607) — FETCHED, unhelpful
<https://arxiv.org/html/2604.18607v1>

Runs three independent trials per setting, arguing that improvements over the
OpenEvolve baseline are robust rather than "a single lucky run." Establishes
n=3 as a defensible floor in this literature, which is relevant since our
frontier arm is at n=3.

Direct PDF fetch returned only structural metadata, no usable text. The n=3
claim is from a search snippet.

**AlphaEvolve** — SNIPPET
<https://sakana.ai/shinka-evolve/>

Reports intra-target standard deviation averaged over three independent runs
initialized with different random seeds. Precedent for reporting spread, but
spread is treated as an error bar, not as an inferential quantity.

**QuantaAlpha: An Evolutionary Framework for LLM-Driven Alpha Mining**
(arXiv:2602.07085) — SNIPPET

Reports sd of IC and Rank IC (0.0021, 0.0024) explicitly to argue performance
"is not driven by a fortuitously selected seed set." This is the closest
existing use of low variance as an argument for validity, though it argues
against seed-luck rather than for structural correctness.

**Multimodal LLM-assisted Evolutionary Search** (arXiv:2508.05433) — SNIPPET

Repeats each experiment five times for robustness, and notes lower variance
across runs than PPO on a hard task. Variance used as a quality property of the
method, which is one step toward our framing.

## Variance as inference without ground truth

**Stability selection** (Meinshausen & Bühlmann, JRSS-B 2010) — KNOWN
<https://people.math.ethz.ch/~nicolai/stability.pdf>

The statistical foundation for the hypothesis. Core argument is the one we
need: variance is estimable whereas bias generally is not, and there is no
notion of approximating the truth, so the model is not required to be correct.
Selects structure by how consistently it reappears across perturbed or
resampled fits.

The analogy to our setting is close but not exact. Stability selection
perturbs the *data* and holds the algorithm fixed; we hold data and config
fixed and let LLM sampling supply the randomness. Worth stating explicitly if
we build on this, since it changes what the stability is evidence *about*.

See also Shah & Samworth on error control for stability selection
(<https://statistique.cuso.ch/fileadmin/statistique/SamworthSlides.pdf>) and
"A General Stability Approach to False Discovery Rate Control"
(arXiv:2512.17401), if we ever want a calibrated threshold rather than a
qualitative comparison between arms.

**Variance-Bounded Evaluation without Ground Truth: VB-Score**
(arXiv:2509.22751) — SNIPPET
<https://arxiv.org/html/2509.22751v1>

Applies resampling-style reasoning to evaluation with no ground-truth labels,
inferring robustness from a distribution of perturbed interpretations rather
than a single run. Same family of argument, different domain.

## Background

**ShinkaEvolve: Towards Open-Ended and Sample-Efficient Program Evolution**
(arXiv:2509.19349) — KNOWN
<https://github.com/SakanaAI/ShinkaEvolve> / <https://arxiv.org/pdf/2509.19349>

The system under test. Weighted parent sampling, code novelty rejection
sampling, bandit-based LLM ensemble selection. Note for our purposes that the
bandit seed was measured in exp1 to contribute no variance, so the sampling
nondeterminism is upstream of all of this.

## Searches run

Queries used, for reproducibility:

- ShinkaEvolve multiple runs variance reproducibility evolutionary LLM program search
- alphaxiv LLM evolutionary search seed variance multiple runs report mean standard deviation
- variance across independent restarts as evidence solution is correct without ground truth stability selection multi-start convergence criterion
- best-of-N reporting convention LLM program evolution run-to-run distribution not reported AlphaEvolve OpenEvolve variance critique (restricted to alphaxiv.org, arxiv.org)

Not yet searched, and worth doing before writing: quantum ansatz / VQE
architecture search reproducibility, equivariance discovery in neural
architecture search, and whether anyone reports capability-dependent variance
in agentic search more broadly.
