# Claim ledger (revised 2026-11-11, after the referee report)

Rules: a claim may not exceed the paired evidence; endpoints are named **development**,
**sealed test** or **fresh holdout** (`REVISED_PROTOCOL.md` section 0); a CI containing 0 is
"difference not detected", never "no effect"; equivalence requires the whole CI inside the
prespecified margin. Numbers come from `research/results_summary2.md`
(`python3 -m research.compile_results2`), which is generated from the result JSONs.

| Claim | Current evidence | Allowed interpretation |
|---|---|---|
| Historical selection is test-independent | **Refuted** by executing the historical evaluator's own AST (`research/audit.py`) | Treat the old "test" as an adaptively reused development set. |
| The supplied baseline is exactly S8-equivariant for all parameters | **Refuted** analytically and numerically (channel defect 0.0597; repair to 1.5e-14) | One-direction CRZ introduces non-uniform local Z fields (Appendix A identity). |
| Complete gate coverage guarantees equivariance | **Refuted** by the ordered-CRX counterexample | Verify semantics or prove commutation conditions. |
| A continuous symmetry diagnostic is available | Implemented and unit-tested | Report channel defect, parameter sampling, supplied vs true group separately. |
| Enforcing equivariance causally improves risk when the target is invariant | **Not established.** The v1 record's 24 eta=0 rows are **8 units**; recomputed: repaired−control −0.00093, CI [−0.00217,−0.00002], p_boot 0.083, p_flip 0.125. WP-REPAIR-2 (24 units at eta=0) is the confirmatory test | Report as "not established in the v1 record"; state WP-REPAIR-2's result as measured, with its own interval. No "iff". |
| Enforcing equivariance causally hurts when the target breaks symmetry | **Supported** (v1, 24 units: +0.04523, CI [+0.03225,+0.05773], p<1e-4; WP-REPAIR-2 confirms) | The cost of enforced invariance is large and robust at the tested mismatch level. |
| Control validates the gate-count account | **Weakened.** `control_dup` is the original interaction at 2b (verified), initial operator differs (distance 1.37); `control_matched` (identical initial operator) and `control_rand` added | Controls match gate count and reachable family, not optimisation geometry. No symmetry-only attribution. |
| Inference-time Reynolds averaging lowers risk on the deployed predictor | **Supported on graphs** (E-S1 −0.04862, CI [−0.07083,−0.02839], sign-flip p 0.0156, 7/12 runs); **no data on ring** (4 attempted, 0 fired). E-S5b: the same tool helps every arm, including non-LLM arms | Coverage-conditional; the gain belongs to the analytic tool, not to the LLM. Not an intention-to-treat effect. |
| Verifier feedback improves search | **Not established** (E-S3 undetected on both families; CIs wider than the equivalence margin) | "Difference not detected". No equivalence claim. |
| Verification identifies the symmetry group | **Refuted as implemented**: graphs 10/299 correct groups, 289 wrong-group proposals pass label preservation; ring 0/192 correct, 7 pass | The label gate is a soundness filter: every subgroup of a label symmetry passes by construction. Identification needs a different instrument. |
| LLM search beats non-LLM search | **Task-dependent and weak.** On ring the LLM arms beat random/mutation-ea, but the constructive equivariant architecture beats every arm (arms +0.0060 to +0.0097 worse, p<1e-4) | No general LLM-advantage claim; constructive design wins at matched budget on the ring. |
| LLM search beats classical task-aware rules on graphs | **Refuted**: edge-count threshold (train-only, k=6) dev risk 0.351 / acc 0.912 vs arms 0.538–0.566 | The graphs task is shortcut-dominated; do not use it as evidence about quantum search. |
| A density shortcut explains the graphs null | **Not established causally.** Stratified risks (band 0–5: 1.39 vs band 8–9: 0.14) are consistent with it | Describe as shortcut-dominated; a density-matched intervention is required for a causal statement. |
| Greater symmetry necessarily gives better prediction | **Refuted** without assumptions; the floor constrains only invariant predictors | Population floor vs MC estimate vs exact finite-orbit floor must be separated. |
| Repaired arm is "pinned near the invariant floor" | **Restated numerically**: per-unit floor 0.866–1.059 (mean 0.948) at eta=1; repaired excess +0.0228; asymmetric arms −0.020/−0.022 (below the floor) | Report excess risk with intervals; drop the phrase. |
| Stronger LLMs obey a smooth symmetry-discovery scaling law | Unidentified by this design | Individual-model treatments only; no continuous predictor. |
| The method is first of its kind | **Not claimed.** Closest predecessors compared in `paper/REFERENCES_AUDIT.md` and related work | Empirical, narrow contribution: where executable verification changes behaviour. |
| Results are prospective and pre-declared | **Partly.** The 120-run search study's plan first appears in git after the runs (protocol-consistent, not verifiably pre-registered). The repair-2 / dev-analysis / one-shot-holdout chain is verifiably pre-registered (protocol commit `ecd1be72`, 16:20:02Z, before job submission) | State which chain has dated evidence; do not blanket-claim pre-registration. |
| Run records pin the code that produced them | **Refuted for the old records** (`git_commit=a37fc2d6` does not contain the code); true for the new chain | Disclosed in `PROVENANCE.md`; new jobs record commits containing their code. |
| Quantum advantage | Not claimed, and the classical baseline is stronger on the historical task | Never claim it. |
