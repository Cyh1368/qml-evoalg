# Mathematical audit and continuous measurements

These metrics are established representation-theoretic diagnostics, not a novelty claim. The research opportunity is their use to verify LLM claims and experimentally intervene on implementation errors. Primary foundations: [Meyer et al.](https://arxiv.org/abs/2205.06217), [Larocca et al.](https://arxiv.org/abs/2205.02261), and [Nguyen et al.](https://arxiv.org/abs/2210.08566). Their frameworks motivate explicit representations and separate circuit equivariance from output invariance.

Let P_g be a specified unitary representation and U a circuit at fixed numerical parameters, dimension d. Define strict residual D_U(g)=||U-P_g U P_g†||_F²/(2d). It lies in [0,2]. For a uniform finite group, its mean is ||U-T_G(U)||_F²/d, since the Reynolds operator T_G is an orthogonal projection. This identity requires averaging the full group (or an unbiased Monte Carlo estimator), not only generators. T_G(U) generally is not unitary and must not be substituted as a circuit.

For physical unitary channels define D_C(g)=1-|Tr(U†P_g U P_g†)/d|². This is half the squared Hilbert–Schmidt distance between normalized pure Choi states and lies in [0,1]. It vanishes exactly when conjugation differs by global phase. Unlike strict commutation it respects physical channel equivalence. For example Z anticommutes with X, giving strict residual 2 but channel residual zero. No dense d² by d² channel matrix is required.

Adjacent transpositions generate S_n. Zero residual on all generators certifies the corresponding exact symmetry at those parameters. Nonzero mean generator residual is a useful continuous diagnostic, but does not equal full-group twirl distance. Numerical zeros at sampled angles are evidence, not proof of architecture-wide symmetry. Use repeated seeded parameter draws with a declared distribution, report maxima and means, and distinguish these from metrics at trained parameters. A single counterexample disproves architecture-wide equivariance.

For predictions f and complete uniformly weighted orbits define D_f=E_x Var_g f(gx). Equivalently D_f=E_{x,g,h}(f(gx)-f(hx))²/2. It is output-scale dependent. On a group-invariant input distribution with invariant regression target y, the squared-loss identity is R(f)=R(T_G f)+E[(f-T_G f)²]. This follows by orthogonal projection: the cross term vanishes. It need not hold for a non-invariant sampling distribution. Constant predictors have zero defect, so always report predictive risk and output variance too. Channel/circuit equivariance is sufficient for output invariance only with compatible encoding, initialization and invariant readout; it is not necessary.

# A specific controlled-rotation failure

Under CRZ(theta)=exp[-i theta (I-Z_control)Z_target/4], the complete one-direction list i<j has commuting generator

H = (sum_j j Z_j - sum_{i<j} Z_i Z_j)/4,

where j=0,...,n-1. The pairwise term is permutation invariant; the local coefficients are not. Thus covering every unordered pair and sharing the angle does not certify symmetry. Summing both directions, with theta/2 on each direction, gives

H_repaired = ((n-1)/2 sum_j Z_j - sum_{i<j} Z_i Z_j)/4.

This preserves the original ZZ coefficient and equalizes local Z coefficients. It is an exact repair because all these generators commute. Bidirectional CRX/CRY products cannot use this argument: shared endpoints can produce noncommuting terms, and changing gate order changes the product. The executable validation demonstrates this counterexample.

# Reproduction and scope

Run `OPENBLAS_NUM_THREADS=1 python3 research/metrics/validate.py` for unitarity, exact full-group twirl identity, commuting versus noncommuting ordered-gate checks and the global-phase counterexample. Run `OPENBLAS_NUM_THREADS=1 python3 research/metrics/pilot.py` for three random-parameter draws on each gallery circuit plus continuous breaking of a collective rotation by untying angles. Projecting the latter angles onto their mean restores exact symmetry. This is a mathematical intervention, not evidence of improved prediction or a causal explanation of prior model performance. Follow-up training must compare repaired circuits with equal-budget sham changes and evaluate untouched orbit-disjoint test data.

The actual baseline numerical check (`baseline_check.py`, persisted `baseline_check.json`) uses ry=0.31, rz=-0.23, crz=0.7 on all eight qubits. Its mean adjacent-transposition channel defect is 0.0597083702; the bidirectional half-angle repair gives 1.47e-14 (floating-point roundoff), with strict residual 3.83e-32. This is a counterexample to the baseline file's architecture-wide equivariance claim; it does not determine the defect of its trained predictor.

# Controlled predictive-risk experiment

`risk_pilot.py` evaluates eight paired random circuit parameter seeds on all 27 three-qubit product states drawn from three Bloch angles. This input set is exactly closed under S3. For each seed it interpolates the original one-direction CRZ layer (epsilon=1) to the bidirectional half-angle repair (epsilon=0), preserving the ZZ coefficient and changing only the asymmetric local-Z contribution. A final collective RY makes phase differences observable. Targets interpolate from a nonconstant invariant quantum predictor to a target with a precisely centered asymmetric component (eta=0, .25, .5, 1). All 160 combinations verify the exact identity

R_eta(f)-R_eta(Tf) = D_f - 2 eta E[(f-Tf)y_asym].

For eta=0 this verifies the invariant-target risk projection identity to 1e-12. The maximum observed output defect is 0.000395818. A deliberately mismatched negative-control target equal to an asymmetric circuit's prediction has raw risk zero and averaged risk 0.000244086: enforcing output invariance can hurt when the target violates it. These are finite-distribution controlled demonstrations, not generalization results or evidence about LLM search. Circuit repair (epsilon=0) and averaging predictions (Tf) are distinct interventions; only output averaging has the stated unconditional squared-risk guarantee. The JSON retains the risk of every repaired and original circuit for paired comparisons.

In the eight paired fixed-parameter invariant-target comparisons, exact circuit repair improves risk for two seeds and worsens it for six. This confirms the need to distinguish circuit repair from output averaging and to retrain under matched budgets before asserting predictive benefit. The paired differences R(original)-R(repaired) range from -0.0183091 to +0.00175712.
