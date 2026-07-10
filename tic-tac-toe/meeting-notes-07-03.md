latent space — high dimensional space which the solutions occupy. the solution space is high dimensional but we can project it to lower dimensions

principle component analysis.

what are the rotation angles of the original gates? what is the order of magnitude, like 0.0005 rad or 0.5 rad?

joint: compare drift not only with original frozen weights

training until covergeence could still mean that the loss on validation set could rise due to overfitting → we need to know whether this perceived drift is attributed to inserted gates or merely an artifact of training more rounds on the weights.

baseline of comparison: original parameters unfrozen, train additional

next step: insert gates with (1) completely random angles vs (2) close to zero rotations. → see if my optimization scheme is able to pull back from the noise. observe phenomena from different randomization / pertubation. (3) adding randomized delta weights without new gates and see convergence.

it is possible to see same accuracy but diffeeereent set of weights — this means weights are not stable. by decreasing thee delta we emay observe a ball around the convergeence and anything in the ball converges.

over-constraining: there are overlapping parameters

under-constraining: amount of weights are not enough to nail down one config. 

joint pertubation of 2 weights → they converge veery artibrarily → these are degeeneratee dimensions, they are not that important. For complex optimizations we don't really know how to narrow down dimentions. e.g. (a+b) * c, a b are dgenerate. If we identify these parameters the solution may converge to an even smaller ball.

Test everything with small perturbation.

----

### Latent Space and Solution Stability

- Latent space: the high-dimensional space in which solutions (gate parameters) reside
  - Can project down to lower dimensions using Principal Component Analysis (PCA)
  - PCA finds the best canonical orthonormal directions for projection
- Next step: visualize how starting configurations and converged configurations differ in this projected space

### Rotation Angle Baseline

- Need to check the rotation angles of the original (pre-insertion) gates
  - What is the order of magnitude: ~0.0005 rad or ~0.5 rad?
  - Contextualizes whether a 0.05 rad drift from inserted gates is significant
- Observation so far: even in joint optimization, inserted gates do not move significantly away from zero rotation

### Joint Optimization and Overfitting Risk

- Current joint results appear to contradict last session’s results
  - Last time: gates initialized with random parameters
  - This time: gates initialized at optimal rotation angles, hence different behavior
- Training until convergence does not guarantee stability on test data
  - Additional training rounds can cause validation/test loss to rise due to overfitting
  - Perceived drift may be an artifact of training more rounds, not the inserted gates themselves
- Adequate baseline for joint case: take original circuit with unfrozen parameters, train for the same number of additional steps as when gates are inserted, then compare

### Perturbation Analysis and Stability Region

- Three perturbation experiments to run:
  1. Insert gates at fully random rotation angles
  2. Insert gates at angles close to zero (e.g. ±0.1 or ±0.2 rad)
  3. Add small randomized delta weights to converged parameters without new gates
- Goal: determine whether the optimization scheme can pull injected noise back toward the no-op (zero rotation) optimum
- As the perturbation range decreases, an epsilon-ball stability region around the converged point may emerge
  - Anything within the ball converges back to the original solution
- Same accuracy with different weights indicates instability in the weight configuration
- Weights are cyclic (2π + x = x), which affects how deltas shift the optimization landscape

### Degeneracy in Parameters

- Over-constraining: overlapping/redundant parameters that can trade off without affecting accuracy
- Under-constraining: insufficient weights to nail down a single optimal configuration
- Example: in (a + b) × c = r, a and b are degenerate axes; their sum is fixed but individual values are arbitrary
- For complex optimizations, degeneracy structure is not known analytically
  - Perturbation analysis can reveal degenerate dimensions empirically
  - Jointly perturbing all weights with small deltas (many Monte Carlo samples) and observing convergence geometry reveals symmetries and degeneracies
  - Converged geometry may be a smaller or oddly shaped ball within the starting perturbation ball
- Testing all pairs of weights is exponential; use Monte Carlo joint perturbation instead

### Next Steps

- **Check rotation angle magnitudes of original circuit gates** (Cheng-You)
  - Needed to contextualize whether observed drift from inserted gates is meaningful.
- **Run joint optimization baseline with original unfrozen parameters** (Cheng-You)
  - Train original circuit for the same number of additional steps as the gate-insertion runs to isolate overfitting artifact from gate-insertion effect.
- **Run perturbation experiments (random angles, near-zero angles, delta weights)** (Cheng-You)
  - Test all three variants and observe whether optimization pulls injected noise back to the no-op optimum; vary perturbation range to map the stability region.
- **Run Monte Carlo joint perturbations to identify degenerate dimensions** (Cheng-You)
  - Perturb all weights jointly with small deltas from the converged solution and analyze the resulting convergence geometry.

---

Chat with meeting transcript: https://notes.granola.ai/t/423bc956-6fab-45fc-8e45-8a4b6420b8e4