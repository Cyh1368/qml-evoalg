# Identifying Symmetries in Quantum Machine Learning Problems with Evolutionary Algorithms

This document is the compilation of ideas that I have for the paper. It will contain mostly what will go into the introduction. It will contain a lot of background about the tools that we use and existing work and it will gradually build to the importance of artwork..

## Our Work, in Brief
All the data that is relevant is available locally. I'm mostly referring to the three previous ShinkaEvolve runs where we used different ensembles at different strengths and tackled the same graph problem. In my work, I've used a quantum computing circuit on a graph connectedness problem with 8 qubits. I run it with three different ensembles categorized by model strength. The optimal solution ties every pair of the 8 qubits with CZ gates, and this permutation invariant solution is only found in. the Frontier Ensemble. The other ensembles sometimes identify symmetry, or sometimes did not identify symmetry, identify the wrong symmetry. It soon became apparent that GPT models are excelling at symmetry identification compared to Claude or Gemini. Thus, I believe it is necessary to propose a benchmark that assesses the ability of LLMs in identifying symmetries in an evolutionary harness for quantum machine learning problems, but this may as well scale up to other fields.

## To-do
Our priority right now is to determine how we can evaluate LLMs in a Shinka Evolve run. So, intuitively, if one single LOM continues proposing the best so far candidates, then that LOM could be said to be the best in the Ensemble while the others are worse. But if an AOM generates a lot of bad generations and occasionally happens to have a good one, then we also shouldn't only care about the good one. We should also think about the number of failures it used, right? There are other things that we can take into account, including the novelty score, the diversity score in the Shinka Evolve. framework so we can utilize the existing items in the harness to build our evaluation matrix metric.

You will have more context about this when read our meeting notes. I think one key thing we should be doing is to rewind the evolutionto right before a key jumpand then remove the model that made the key jumpand see how the other models will be able to replicate that if they will. when doing this we also need to make sure that when we run the evolution at the original settings after the rewind that critical jump will still happen that is I want to make sure that the evolution is at least somewhat reproducible so that if we remove the key model and then the evolution doesn't happen, then we can say with confidence that the such model is essential in the discovery of the solution.

I believe the best way to determine the capability of a model in ShinkaEvolve is to run different controlled experiments by using different models as ensembles. But again, I'm also interested in whether an evolutionary run is reproducible or not.

## ShinkaEvolve

### How ShinkaEvolve is not just a loop
- The Best-of-N baseline ignores evolutionary history entirely, always using the initial program as parent with no feedback
- Hill Climbing greedily selects the highest-performing program found so far as the parent for the next mutation. Hill climbing is precisely "call the agent again on its best past solution."

## Relevant Work

https://www.alphaxiv.org/abs/2512.15567?chatId=019feeb6-3a80-794e-af66-057a0bb44a3e

Most of the tasks here are simply Q&A. There are some tasks that require the LOM to continue proposing new solutions, and the LOM will receive what score it got on the previous solution. And I think this is very similar to Shinka Evolve, but there are many caveats. First of all, we're only using one model, and also there isn't a selection framework for selecting generations. So this is just a simple agentic loop. So we still have an edge if we make a benchmark on ShinkaEvolve. Also, the scope of this paper is very broad. It does not cover very specific things like identifying symmetries in quantum machine learning.

> The question-level portion contains 1,012 questions in total, including 163 physics questions. These are mainly multiple-choice or short-answer tasks covering areas such as quantum information, cosmology, condensed matter, probability and statistics, and computational physics. Mathematical answers may be checked for symbolic equivalence rather than exact string matching.

https://www.alphaxiv.org/abs/2606.05080?chatId=019feebf-1996-75d5-84d6-3a1604cdcdb2

> AUTOLAB creates 36 executable, multi-hour optimization tasks, but it does not include a dedicated physics category. Its closest physics-adjacent tasks are low-level numerical computing, CUDA kernels, scientific-model development, and systems optimization. The four categories are system optimization (15 tasks), puzzle and challenge (10), model development (7), and CUDA optimization (4). 

This benchmark is mostly focused on numerical analyses.

AutoLab gives the model a task that it will run for several hours, gives it a deadline, and observes how it performs experiments. So it's a measure of how good it is at auto research.

> AUTOLAB is therefore primarily a benchmark of model-and-agent behavior. It asks: Does the model start experimenting quickly? Does it continue after a promising result? Does it notice when a change made performance worse? Does it submit before the deadline? Does its harness encourage enough iteration?

> A fixed development episode means AUTOLAB gives an agent one task, one starting codebase, and one finite working session—for example, a two-hour CUDA optimization problem—and evaluates the solution produced at the end of that session. The agent is not running an open-ended population search across thousands of independent candidates. 

https://www.alphaxiv.org/abs/2606.07591?chatId=019feeec-6fea-752f-b433-543a379d747f

> it is primarily a hidden-paper re-discovery benchmark for autonomous research agents, with an additional attempt to measure whether they go beyond the paper rather than merely reproduce it. esearchClawBench tests whether autonomous research agents can re-discover the central results of a hidden paper from its research question, related literature, raw data, and an executable environment, without being shown the target paper itself.

### Appendix: Summary and notes from our latest meeting

```
similar benchmarks:

- GPQA
- humanity last exam
- ArcAGI: hidden rules in the system

increase in raw model capability can override the effect of harness engineering — the LLM itself is more important.

ex. Opus and Fable 5 reduced system prompts. the system prompts now look like restrictions to what the model can do! i.e. harnesses are imposing restrictions on the decision space for the models.

if model is very capable, but harness is not 

Anthropic paper: J-space, try to extract info from this space that is not reflected in the final output.

»

They're they're not committed as first choice tokens at all. Instead, they are just, like, lost in the sea of still, it is useful look at the entire probability distribution of of next token generation. And and see what what what the candidates are the diversity of candidates, the relevance of these, So these are all things that you can't you can't explicitly so you can't implicitly do when you just look at the model as a black box and analyze its performance on aggregate benchmarks.

«

https://www.anthropic.com/research/global-workspace

Identify share of models along a path (track models along a path?). For each improvement a model makes, there are several things that quantify the importance of that generation — if the model makes many tries but only one shadows everyone else, the cost to generate the "suboptimal" ones should be included. 

Another thing that is easy to measure is to measure how good your new solution is compared to others; also, the shinka-generated novelty score compared to other solutions. Run through many iterations  / historically look at how good solutions happen one after another → identify continuous chunks of these nodes that are generated by one single model → indicates the strength of the ensemble. e.g. if the best-so-far is all gpt then the ensemble is not balanced and favors GPT. however if claude gpt switches then it means its balanced.

*rewind solution to right before a KEY EVOLUTION GEN and remove the model that did it. Then see if the rest of the models are able to make the breakthroughs.

Fine-tuning the relevance of these statistics may be the challenges.

# Experiment Results: Symmetry Identification Across Model Tiers

- GPT 5.6 (extra-high reasoning) generated equivariant circuits within the first few generations
  - Consistent across three runs: GPT always best at identifying permutation-invariant symmetry
  - Concern raised: possible memorization, but Allen considers this non-alarming given Shinka Evolve’s reliance on pretrained model knowledge
- Mid-tier models (GPT 5.4) also identified the correct symmetry; weaker ensembles did not
  - Weaker models identified mirror symmetry instead, implemented it, but it underperformed
  - Mid-tier models named the wrong symmetry; frontier models named and built the correct one
- Non-GPT models tend toward circuit complexity, control gates, or connectivity reasoning rather than symmetry
  - GPT generations consistently reference parameter sharing or parameter efficiency, likely deducing symmetry from there
- Frontier ensemble: best-so-far chain is a long GPT run followed by one Opus contribution, then GPT again
  - Supports Allen’s earlier point: diverse model families offer complementary coverage

# Benchmarking and Ensemble Analysis

- Proposed framing: symmetry identification in QML problems (not a universal Shinka Evolve benchmark yet)
  - Scope can broaden if an effective metric is established
- Adjacent benchmarks for reference:
  - GPQA, Humanity’s Last Exam (reasoning-heavy)
  - ARC-AGI: closest match, tests hidden rules within a system; three generations, frontier models still struggle with ARC-AGI 3 (~1.86%)
- Metrics for evaluating model contribution along the evolutionary path:
  - Share of models in the path toward the best solution
  - Relative improvement size of each contribution (1% vs. meaningful jump)
  - Shinka-generated novelty score vs. prior solutions
  - Contiguous chunk analysis: long GPT-only runs suggest ensemble imbalance; interlaced GPT/Claude switches suggest genuine complementarity
- Key ablation idea: rewind to just before a key breakthrough generation, remove that model, and test if others can bridge the gap
  - Weaker models may cover regions outside the stronger model’s reach
- Challenge: fine-tuning the relevance of these statistics, not measurement itself

# Harness Engineering vs. Raw Model Capability

- Raw model capability increasingly overrides harness engineering
  - Opus and Fable 5 reduced system prompt length by ~two-thirds
  - System prompts now act as restrictions on the model’s decision space rather than guides
- Harnesses down-project the model’s decision space to lower dimensions
  - Useful when search heuristics in high-dimensional space are weak
  - But restrict expressivity when the model is highly capable
- Anthropic paper on J-space: extracts internal representations not reflected in final output
  - Many candidate tokens never committed as first-choice tokens, lost before chain-of-thought
  - Useful to examine the full next-token probability distribution, not just black-box aggregate benchmarks
  - https://www.anthropic.com/research/global-workspace

# Next Steps

- **Summarize all results and identify gaps in preparation for a draft skeleton**
- **Review Anthropic J-space paper (Allen)**
- **Meet again next Monday (17th August) at the same time**

---

Chat with meeting transcript: https://notes.granola.ai/t/11c8e393-8ee4-4868-a30f-23001ddbf068
```