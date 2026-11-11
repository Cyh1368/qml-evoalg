# Verified symmetry hypotheses and causal repair in LLM-guided quantum circuit search

*Draft manuscript (WP-PAPER). Method, protocol, and related work are fixed; the
Results and Discussion sections are populated from `results_summary.md` once the
confirmatory runs finish. Claims are scoped to the paired evidence per
`CLAIMS.md` — this document does not assert more than the executed experiments
support.*

## Abstract

We study how large language models (LLMs) turn *symmetry hypotheses* into
*executable* quantum models, and whether an executable verifier and an analytic
repair step causally improve that process under matched evaluation budgets. The
mathematical tools we use — group twirls, channel/predictor equivariance
residuals, and an orthogonal-projection risk identity — are established; our
object of study is behavioural: the gap between a model *proposing* a correct
transformation, *implementing* it correctly, and *obtaining useful task
performance*. We (i) audit a prior LLM-evolutionary QML study and show its
selection leaked test data and its equivariance claims were partly false; (ii)
build a matched-budget, single-model search harness with verifier-feedback and
repair arms; and (iii) run a confound-free causal-repair experiment with an
analytically known invariant-risk floor and a gate-count-matched control. We
report what these interventions do — including null and negative results — with
run-level paired uncertainty.

## 1. Introduction

Symmetry is a first-class inductive bias in quantum machine learning (QML): a
circuit that commutes with a representation of the data's symmetry group yields
invariant predictions under a compatible readout. A tempting hypothesis is that
an LLM asked to design such circuits will both *state* the right symmetry and
*build* it. This paper treats that hypothesis as measurable rather than
anecdotal.

Three levels must be separated (and are conflated in casual "symmetry-aware
LLM" claims):

1. **Proposing** a transformation (a stated group hypothesis).
2. **Implementing** it (the circuit actually commutes with the representation).
3. **Performing** (the trained predictor generalises on held-out data).

Our contributions:

- **A reproducibility audit** of a prior ShinkaEvolve-based study: test-set
  leakage in selection, a refuted architecture-wide equivariance claim, and a
  proposal-level (not run-level) significance error. These bound what the old
  numbers can mean.
- **A matched-budget search harness** comparing random, mutation-only,
  LLM-fitness, LLM-verify (adds executable equivariance + label-preservation
  feedback), and LLM-verify-repair arms, with identical initial populations,
  every invalid proposal retained, and a sealed-holdout guard.
- **A causal repair experiment** on a real benchmark with confound-free targets
  `y_eta = h + eta*b`, an analytic invariant-risk floor `eta^2 E[b^2]`, and a
  gate-count-matched asymmetric control that isolates the symmetry effect from
  expressivity.

## 2. Related work

See `literature.md` for the full table. In brief: representation-based gate
symmetrisation and invariant re-uploading (Meyer et al. 2023); constructive
equivariant unitary layers/channels (Nguyen et al. 2024); permutation-invariant
QML for graph properties including approximate symmetry (Mansky et al. 2025);
task-aligned interactions where symmetry alone does not fix a useful architecture
(Baumann & Linnhoff-Popien 2026); averaging-operator generalisation theory
(Elesedy & Zaidi 2021); Lie-derivative symmetry promotion (Otto et al. 2023);
finite-measurement task-level symmetry inference and projection bias (Chen 2026,
preprint); and ShinkaEvolve's parent sampling / novelty rejection / bandit model
selection (Lange et al. 2026). The tools are therefore not the novelty; the
behavioural, intervention-based study of the propose-verify-implement-perform gap
is the candidate contribution, and priority still requires a final broader review.

## 3. Method

### 3.1 Continuous symmetry diagnostics (established)

For a fixed-parameter circuit unitary `U` and representation `P_g`, the strict
residual `D_U(g)=||U-P_g U P_g^†||_F^2/(2d)` and the physical channel residual
`D_C(g)=1-|Tr(U^† P_g U P_g^†)/d|^2` distinguish exact commutation from
global-phase equivalence. Zero residual on adjacent transpositions certifies
`S_n` symmetry at those parameters; a random-parameter zero is evidence, not an
architecture-wide proof. For predictions on complete orbits,
`D_f = E_x Var_g f(gx)`, and under a group-invariant input measure with an
invariant target the squared-risk projection identity
`R(f)=R(T_G f)+E[(f-T_G f)^2]` holds. Constant predictors are perfectly
invariant, so risk and output variance are always reported alongside invariance.
Details and counterexamples: `mathematics.md`.

### 3.2 Confound-free causal repair (WP-REPAIR)

Targets are `y_eta = h + eta*b` where `h` is the benchmark's ground-truth
invariant oracle and `b` is a group-centred, variance-normalised breaking
component (Reynolds projection via the explicit group closure). No invariant
predictor can beat the analytic floor `eta^2 E[b^2]`. Three ansatz arms with
equal parameter count are trained with a **fixed symmetric readout** (so an
equivariant block yields an invariant predictor): `original` (one-direction CRZ,
asymmetric), `repaired` (bidirectional shared-angle CRZ, exactly equivariant),
and `control` (repeated same-direction CRZ — asymmetric, operator-family-
equivalent to `original`, with the *same gate count as* `repaired`). The decisive
contrast is `repaired` vs `control`: they differ only in symmetry.

### 3.3 Matched-budget search (WP-SEARCH)

Five arms at an identical evaluated-candidate budget, identical seed-derived
initial populations, invalid proposals kept in denominators, and per-run cost
accounting (tokens, evaluator calls, wall time). Model identity and reasoning
effort are fixed categorical treatments (no adaptive bandit), so capability is
not confounded with cost or exposure. Development selection only; the locked
holdout is never read by search.

## 4. Protocol, integrity, and analysis

Prospective and pre-declared (`extension_plan.md`). Orbit-disjoint splits;
sealed holdouts evaluated once; run-level paired bootstrap CIs; Holm correction
within secondary families; every result JSON stamped with seeds, module versions,
git commit, and host. Negative and null results are reported as such.

## 5. Results

*WP-REPAIR and WP-SEARCH confirmatory results are in `results_summary.md` and
folded into 5.1/5.2. The pilot (`pilot_analysis.json`, n=3) is retained for
variance/runtime only; the confirmatory run is `confirm_analysis.json` (n=12).*

### 5.1 WP-REPAIR (decisive, n = 24 paired draws = 3 teachers x 8 optimiser seeds)

Targets `y_eta = h + eta*b` on `ring_n6` (D6, order 12); `h` is the ground-truth
invariant oracle, `b` a group-centred frozen breaking direction; the analytic
invariant-risk floor is `eta^2 E[b^2]` (verified equal to the empirical
orbit-mean floor). Arms share parameter count and a fixed symmetric readout;
`repaired` is exactly equivariant (measured channel residual `0.0`), `original`
and the gate-count-matched `control` are asymmetric (residual ~0.6-0.8).

| eta | floor | repaired vs control (mean diff, 95% CI) | verdict |
|---|---|---|---|
| 0.0 | 0.000 | **-0.00093 [-0.00160, -0.00036]** | repaired better |
| 0.5 | 0.217 | +0.01817 [+0.01320, +0.02307] | repaired worse |
| 1.0 | 0.866 | +0.04523 [+0.03231, +0.05758] | repaired worse |

Mean dev risk at eta=1: repaired 0.971 (pinned near the 0.866 invariant floor +
approximation error), control 0.926, original 0.928; `control vs original` is
null at every eta (CI includes 0), confirming the control isolates gate count /
expressivity from symmetry. **Finding:** enforcing equivariance causally improves
held-out risk exactly when the target is invariant, and causally hurts when the
target breaks symmetry — against a control matched in gate count, so the effect
is attributable to symmetry, not capacity. This is a development-split result;
the locked holdout was not read.

### 5.2 WP-SEARCH (confirmatory, n = 12 paired seeds per family)

119 runs, 5 arms, families `ring_n6`/`graphs_n6`, one model treatment
(`ycrc-local`/none), matched budget B=12, fixed treatment filenames. Run-level
paired bootstrap CIs; Holm correction within family.

- **Primary — verifier feedback vs fitness: NULL.** Dev-selected risk is not
  significantly changed: graphs `-0.014 [-0.059, +0.028]` (p=0.52), ring
  `+0.0006 [-0.0003, +0.0014]` (p=0.16); CIs include 0 on both families. This is
  the protocol's anticipated "changes the measured residual but not the
  predictive risk" branch — an implementation-reliability result, not a
  performance win.
- **LLM search beats non-LLM baselines only when the task is not shortcut-
  dominated.** On `ring_n6`, `llm-fitness` beats `mutation-ea`
  (`-0.0037`, p_holm<0.001) and `llm-verify` beats `random` (`-0.0030`,
  p_holm<0.001). On `graphs_n6` no arm separates from random/mutation-ea
  (a density shortcut dominates, as the audit predicted).
- **Inference-time Reynolds averaging (verify-repair vs verify)** did not survive
  to n=12 (`-0.0005`, p_holm=0.61); the n=3 pilot signal was not confirmatory.

Together with WP-REPAIR, the picture is consistent: symmetry is a real, causally
verifiable inductive bias when the target is invariant (WP-REPAIR), but bolting a
verifier onto fixed-budget LLM search did not, by itself, improve held-out risk
here, and any LLM advantage is task-dependent and vanishes under a strong
shortcut.

## 6. Discussion

Interpretation is written only after the paired contrasts are in. The design
anticipates three outcomes and treats each as informative: (i) verifier feedback
improves held-out risk at fixed budget; (ii) it changes the measured residual but
not risk (an implementation-reliability result); or (iii) repair helps only with a
supplied group and not under wrong-group or symmetry-breaking conditions (no
unknown-symmetry discovery claim). If results vanish under orbit splitting or
budget matching, the central claim is revised rather than the analysis.

## 7. Limitations

Small dense statevector simulation; no quantum-advantage claim (a trivial
edge-count baseline is strong on the historical task); a single local model
family, so results are not comparable to the prior commercial-ensemble numbers;
and the held-out task family is a transfer test, not a claim of open-ended
discovery.
