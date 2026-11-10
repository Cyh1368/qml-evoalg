# Development-only training pilot

Reproduce: `OPENBLAS_NUM_THREADS=1 python3 research/metrics/training_pilot.py`.

Eight paired random-search seeds evaluate 128 parameter proposals per architecture, selecting by training MSE. Whole S3 input orbits are split into 20 training, 10 development and 5 unevaluated holdout orbits. Three target mixtures interpolate between repaired and original circuit teachers. This is parameter optimization, not LLM architecture search.

| Target mixture eta | Original minus repaired development MSE | Seeds improved | Original minus sham MSE |
|---|---:|---:|---:|
| 0 (invariant teacher) | 0.001554 | 6/8 | 0.003693 |
| 0.5 | 0.001280 | 6/8 | 0.002780 |
| 1 (original teacher) | 0.001007 | 6/8 | 0.001735 |

Positive differences favor the intervention. These small development results do not isolate a symmetry benefit: the sham's mean improvement is larger, and all conditions share the same data and seed proposals. Repair changes gate count from 9 to 12 while preserving three trainable parameters. The target teacher belongs to the compared hypothesis families. The sham shifts a shared rotation angle and changes the finite set of sampled functions; it is an optimization-variability control, not a fully matched causal intervention.

Next experiment: use independent targets from the ring dataset, equal-cost circuit representations, increasing optimization budgets, and several independently sampled train/development orbit splits. Include exact output averaging separately from architectural repair. Predefine the paired primary contrast before inspecting fresh holdout risk. Only after stability across these checks should verifier-assisted LLM search be compared with scalar-feedback and non-LLM search.

No final holdout prediction was computed. No cluster resources or paid APIs were used.
