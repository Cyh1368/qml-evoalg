# Results summary (auto-compiled; do not hand-edit numbers)

## WP-REPAIR — causal symmetry repair (family `ring_n6`)

- group order 12; arms original,repaired,control; etas [0.0, 0.5, 1.0]; teacher draws [101, 202, 303]; opt seeds 8; budgets [200]
- Scope: development only; locked holdout never read

| eta | steps | contrast | n | mean diff (a-b) | 95% CI | frac a better |
|---|---|---|---|---|---|---|
| 0.0 | 200 | repaired vs control | 24 | -0.00093 | [-0.00160, -0.00036] | 0.62 |
| 0.0 | 200 | repaired vs original | 24 | -0.00201 | [-0.00308, -0.00095] | 0.88 |
| 0.0 | 200 | control vs original | 24 | -0.00107 | [-0.00203, -0.00017] | 0.62 |
| 0.5 | 200 | repaired vs control | 24 | +0.01817 | [+0.01320, +0.02307] | 0.17 |
| 0.5 | 200 | repaired vs original | 24 | +0.01690 | [+0.01259, +0.02112] | 0.17 |
| 0.5 | 200 | control vs original | 24 | -0.00127 | [-0.00544, +0.00286] | 0.46 |
| 1.0 | 200 | repaired vs control | 24 | +0.04523 | [+0.03231, +0.05758] | 0.04 |
| 1.0 | 200 | repaired vs original | 24 | +0.04319 | [+0.03493, +0.05139] | 0.00 |
| 1.0 | 200 | control vs original | 24 | -0.00204 | [-0.01338, +0.00898] | 0.42 |

_Negative mean diff => arm `a` has lower dev risk (better). Expected: repaired beats gate-count-matched `control` at eta=0; control beats repaired at eta=1 (repaired is pinned at the invariant floor eta^2 E[b^2])._

## WP-SEARCH — matched-budget search arms

- runs 120; families ['graphs_n6', 'ring_n6']; treatments [['ycrc-local', 'none']]

### Arm summary (mean dev risk / invalid / tokens)
| family | arm | n | mean dev risk | mean invalid | mean tokens |
|---|---|---|---|---|---|
| graphs_n6 | llm-fitness | 12 | 0.56572 | 0.2 | 18480 |
| graphs_n6 | llm-verify | 12 | 0.55158 | 0.1 | 18868 |
| graphs_n6 | llm-verify-repair | 12 | 0.55250 | 0.2 | 19437 |
| graphs_n6 | mutation-ea | 12 | 0.53930 | 0.0 | 0 |
| graphs_n6 | random | 12 | 0.53782 | 0.0 | 0 |
| ring_n6 | llm-fitness | 12 | 0.00651 | 0.0 | 16425 |
| ring_n6 | llm-verify | 12 | 0.00709 | 0.1 | 17494 |
| ring_n6 | llm-verify-repair | 12 | 0.00664 | 0.0 | 17199 |
| ring_n6 | mutation-ea | 12 | 0.01022 | 0.0 | 0 |
| ring_n6 | random | 12 | 0.01013 | 0.0 | 0 |

### Primary contrast: llm-verify - llm-fitness (negative => verifier helps)
| family | treatment | n | mean diff | 95% CI | p | frac verify better |
|---|---|---|---|---|---|---|
| graphs_n6 | ycrc-local/none | 12 | -0.01414 | [-0.05914, +0.02837] | 0.516 | 0.42 |
| ring_n6 | ycrc-local/none | 12 | +0.00058 | [-0.00025, +0.00139] | 0.162 | 0.25 |

### Secondary contrasts (Holm-adjusted within family)
| family | a vs b | n | mean diff | p_holm |
|---|---|---|---|---|
| graphs_n6 | llm-verify-repair vs llm-verify | 12 | +0.00092 | 1.000 |
| graphs_n6 | llm-fitness vs mutation-ea | 12 | +0.02642 | 0.854 |
| graphs_n6 | mutation-ea vs random | 12 | +0.00148 | 1.000 |
| graphs_n6 | llm-verify vs random | 12 | +0.01376 | 1.000 |
| ring_n6 | llm-verify-repair vs llm-verify | 12 | -0.00046 | 0.614 |
| ring_n6 | llm-fitness vs mutation-ea | 12 | -0.00371 | 0.000 |
| ring_n6 | mutation-ea vs random | 12 | +0.00009 | 0.614 |
| ring_n6 | llm-verify vs random | 12 | -0.00304 | 0.000 |
