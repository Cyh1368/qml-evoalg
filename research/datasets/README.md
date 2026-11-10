# Fresh prospective datasets

Run `python3 research/datasets/generate.py` then `python3 research/datasets/validate.py` from the repository root. NumPy is the only dependency. `manifest.json` records the seed, definitions, split sizes and SHA-256 hashes; `validation.json` records completed checks.

Only `development/*.npz` may enter search. They contain training and validation arrays, never test arrays. `locked_holdout/*.npz` is for final assessment after architecture, optimizer, seeds and analysis choices are frozen. This directory naming is an experimental access contract, not a filesystem security barrier. Labels were inspected only by deterministic integrity checks; no model has been selected against this holdout.

`graphs_n6` exhaustively contains all 32,768 labeled simple graphs on six vertices. Exact canonical IDs are minimum adjacency-bit integers over all 720 vertex permutations. The 156 isomorphism classes are shuffled once and allocated 93/31/32 to train/validation/test. Splits contain 19,739/6,217/6,812 labeled examples. Connectivity and triangle-existence tasks share inputs and split; report their dependence. Each split weights labeled graphs uniformly, so larger orbits receive more weight. Report an additional orbit-balanced metric (average loss within orbit, then over orbits) and cluster uncertainty by orbit. Classes are naturally imbalanced; use balanced accuracy and a majority baseline. Any training subsample must preserve the fixed split and record its seed and selected indices. This task is small enough for exhaustive correctness checks, not evidence of computational quantum advantage.

`ring_n6` contains 1,200 six-dimensional continuous inputs, with 720/240/240 examples split by exact D6 orbits. Targets are

    y_alpha(x) = mean_i x_i x_(i+1) + alpha (x_0 - mean_i x_i)

for alpha in {0, .1, .25, .5, 1}. Alpha=0 is D6 invariant. The symmetry-breaking component has zero group average, so the squared group-averaged target defect scales exactly as alpha². This provides an interpretable continuous control variable independent of subjective LLM capability rankings. The transformed target must be recomputed when measuring equivariance for alpha>0; assigning unchanged labels after transformation would be incorrect. Report regression MSE and group defect jointly. All alpha conditions share samples and must be analyzed as paired conditions.

Validation independently traverses graph connectivity, checks triangles, checks all adjacent-transposition generator edges of the canonicalization map, verifies split orbit disjointness and checks all 12 D6 transforms and the alpha² law. These checks cover correctness of the generated artifacts; they are not downstream research performance results.
