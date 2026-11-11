# Results summary (auto-compiled; do not hand-edit numbers)

_WP-REPAIR results not available yet._


## WP-SEARCH — matched-budget search arms

- runs 22; families ['graphs_n6', 'ring_n6']; treatments [['ycrc-local', 'none'], ['ycrc-local-think', 'medium']]

### Arm summary (mean dev risk / invalid / tokens)
| family | arm | n | mean dev risk | mean invalid | mean tokens |
|---|---|---|---|---|---|
| graphs_n6 | mutation-ea | 1 | 0.51691 | 0.0 | 0 |
| graphs_n6 | random | 1 | 0.51691 | 0.0 | 0 |
| ring_n6 | llm-fitness | 4 | 0.00521 | 0.2 | 22252 |
| ring_n6 | llm-verify | 5 | 0.00764 | 0.0 | 24990 |
| ring_n6 | llm-verify-repair | 5 | 0.00597 | 0.0 | 26116 |
| ring_n6 | mutation-ea | 3 | 0.00913 | 0.0 | 0 |
| ring_n6 | random | 3 | 0.00895 | 0.0 | 0 |

### Primary contrast: llm-verify - llm-fitness (negative => verifier helps)
| family | treatment | n | mean diff | 95% CI | p | frac verify better |
|---|---|---|---|---|---|---|
| graphs_n6 | ycrc-local/none | 0 | n/a | [n/a, n/a] | n/a | 0.00 |
| graphs_n6 | ycrc-local-think/medium | 0 | n/a | [n/a, n/a] | n/a | 0.00 |
| ring_n6 | ycrc-local/none | 3 | +0.00202 | [+0.00060, +0.00325] | 0.000 | 0.00 |
| ring_n6 | ycrc-local-think/medium | 1 | +0.00462 | [+0.00462, +0.00462] | 0.000 | 0.00 |

### Secondary contrasts (Holm-adjusted within family)
| family | a vs b | n | mean diff | p_holm |
|---|---|---|---|---|
| graphs_n6 | llm-verify-repair vs llm-verify | 0 | n/a | 1.000 |
| graphs_n6 | llm-fitness vs mutation-ea | 0 | n/a | 1.000 |
| graphs_n6 | mutation-ea vs random | 1 | +0.00000 | 1.000 |
| graphs_n6 | llm-verify vs random | 0 | n/a | 1.000 |
| ring_n6 | llm-verify-repair vs llm-verify | 3 | -0.00207 | 0.000 |
| ring_n6 | llm-fitness vs mutation-ea | 0 | n/a | 1.000 |
| ring_n6 | mutation-ea vs random | 3 | +0.00017 | 1.000 |
| ring_n6 | llm-verify vs random | 0 | n/a | 1.000 |
