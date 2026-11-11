# Claim ledger

| Claim | Current evidence | Allowed interpretation |
|---|---|---|
| Historical selection is test-independent | Refuted by evaluator audit | Treat old test as adaptively reused development data. |
| The supplied baseline is exactly S8 equivariant for all parameters | Refuted analytically and numerically | One-direction CRZ introduces nonuniform local Z coefficients. |
| Complete gate coverage guarantees equivariance | Refuted by ordered CRX counterexample | Verify semantics or prove commutation conditions. |
| A continuous symmetry diagnostic is available | Implemented and validated | Report channel defect, parameter sampling and supplied group separately. |
| Greater symmetry necessarily gives better prediction | Refuted without assumptions | Output averaging has a squared-risk guarantee only with invariant input measure and target; circuit repair has no general guarantee. |
| Verifier feedback improves LLM search | Confirmatory (n=12/family) shows NULL: dev-selected risk unchanged vs fitness (CI includes 0 on both families) | No verifier-feedback performance benefit at B=12; report as an implementation-reliability null. Larger budget / other tasks untested. |
| LLM search beats non-LLM search | Supported on `ring_n6` (vs mutation-ea and random, Holm p<0.001); NOT on `graphs_n6` (density shortcut dominates) | LLM advantage is task-dependent and disappears under a strong shortcut. |
| Analytic repair of an equivariance causally changes prediction | Supported, conditionally (WP-REPAIR, n=24, gate-count-matched control): repaired beats control at eta=0 (CI excludes 0) and loses at eta=1 (pinned at invariant floor) | Symmetry enforcement helps iff the target is invariant; the effect is attributable to symmetry, not gate count. Development-split evidence; holdout not read. |
| Inference-time output averaging (Reynolds) lowers risk on invariant targets | Pilot (n=3) positive but did NOT survive confirmatory (n=12, p_holm=0.61) | Not established at B=12; do not claim a confirmatory averaging benefit. |
| Greater symmetry necessarily gives better prediction | Refuted without assumptions (and now shown causally both directions) | Output averaging has a squared-risk guarantee only with invariant input measure and target; circuit repair helps only when the target is invariant. |
| Stronger LLMs obey a smooth symmetry-discovery scaling law | Unidentified by present design | Use individual-model treatments and measurable continuous interventions. |
| The new method is first-of-kind | Not established | Literature supports a candidate gap in verified implementation, repair and transfer; final priority review and empirical evidence are required. |

The mathematical tools are established. Potential novelty lies in the experimentally demonstrated behavior of the complete proposal–verification–repair search method, especially when group hypotheses are wrong and on held-out task families. A failed performance hypothesis can still yield an implementation-reliability study if its scope and baselines are rigorous.
