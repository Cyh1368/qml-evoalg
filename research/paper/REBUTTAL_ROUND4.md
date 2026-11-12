# Response to the fourth-round review

**Manuscript:** Executable Verification and Analytic Repair in LLM-Guided Quantum Circuit Search
**Responding to:** `REVIEW_ROUND4.md` (12 November 2026)
**Protocol amendment under which this work was done:** Addendum A7 (plus A7.5a), commit
`73a95d77`, written **before** any A7 analysis or recomputation.

We accept all seven blockers. Each of the four code-level claims was checked in source before we
acted on it, and all four were correct as stated; none is disputed below. Two of them changed
reported numbers, one of them substantially (the empirical proposal pool: the ring acceptance rate
is **0.6250**, not the 0.47 we printed). We also accept the novelty judgment in substance: the
two-probability characterization we proposed in the third-round rebuttal is wrong, and we now say
so in the manuscript and replace it with the decision model the referee specified.

What this round produced, in order of the referee's list:

| # | requirement | what we did | artifact |
|---|---|---|---|
| 1 | correctly specified decision model, or descriptive accounting | model written with the referee's estimand, losses and costs; the withdrawn claim is retracted in text and refuted by a tested counterexample; measured thresholds | `research/search/decision_model.py`, `decision_model.json`, `test_decision_model.py` (11 tests) |
| 2 | sample inside the proposed subgroup; report zero-acceptance with a bound; separate proof / exhaustive / finite-probe | fallback now enumerates words in the proposed subgroup; three-level certification vocabulary; `certifies_soundness` deleted; 0/400 reported with a Clopper--Pearson bound | `corrected_gate.py` (`closure_capped`, `cp_upper_95`, `scope`), `corrected_gate_a7.json` |
| 3 | define $Q$, filter it, deduplicate, separate pool error from run uncertainty, recompute ratios | $Q$ defined before measurement (LLM arms, own family, one entry per proposal, no selected-best duplicate); finite pools enumerated exactly | `empirical_pool`, `accept_pool_exact`, `corrected_gate_a7.json` |
| 4 | identical regime-specific groups to all gates; frozen threshold or relabel the quantile rule | both gates and the channel condition now take the current regime's group and target; `defect_q1_frozen` and `defect_q1_within` reported as different policies | `decision_rules3.py`, `decision_rules3.json`, `analyze_decision3.py` |
| 5 | never-repair baseline, stated information set, mixture over regimes, measured vs extrapolated timings | `never_repair` added; policies scored under a pre-declared mixture; costs split into search-time and deployed components; all timings measured, repeated three times | `decision_rules3.py` (`cost_v3`, mixture block), `analyze_decision3.py` |
| 6 | equivalence wording, multiplicity before verdicts, deployed contrast from stored diagnostics | Holm now precedes verdicts; vocabulary split; deployed-endpoint contrasts added as separate rows | `analyze_corrected.py` (`assign_verdict`, `_adjusted_interval`, `deployed_risk`) |
| 7 | one coherent manuscript; no external-validation claim for self-tests | three live contradictions removed; superseded material moved to the audit appendix; checker scope paragraph added | `main.tex` (abstract, §`sec:corrected`, Discussion, §`sec:repro`) |

Plus the contribution the referee asked us to choose: **a sharply scoped negative result** (the
third of the three routes offered), reported under verdict categories fixed in advance.

---

## 1. The two-probability characterization is withdrawn and replaced

The referee is right that our characterization was incomplete, and right about the reason: the two
probabilities are inputs to the decision, not a description of it. We now write the model the
review gave us.

With $\Delta$ = repaired risk minus unrepaired risk, $A$ the firing decision, $c_{gate}$ the
screening cost and $c_{rep}$ the repair-and-serve cost, the value of a policy relative to never
repairing is $V(A) = E[A\Delta] + w\,E[c_{gate} + A c_{rep}]$. Writing $B = -E[\Delta\mid
\text{valid}] > 0$ and $H = E[\Delta \mid \text{invalid}] > 0$, firing is preferred exactly when

$$q \;>\; q^*(w) \;=\; \frac{H + w\,c_{rep}}{B + H},\qquad
  q = P(\text{supplied group is a label symmetry} \mid A = 1) = \frac{\pi s}{\pi s + (1-\pi)(1-f)} .$$

Three things follow, and we state them as the paper's position.

* **The two probabilities enter only through the posterior $q$, and only together with the
  screen's own sensitivity $s$ and specificity $f$.** They are not a characterization on their own.
* **The threshold is set by effect magnitudes and costs, which the two probabilities cannot
  express.** This is not a hypothetical: `test_decision_model.py` builds two worlds with *identical*
  $P(\text{valid})$, identical sensitivity (0.8) and identical specificity (0.6) — hence an
  identical induced posterior $q = 0.6\overline{6}$ — and opposite optimal policies, because
  $(B,H) = (10^{-4}, 5{\times}10^{-5})$ in one and $(10^{-3}, 4{\times}10^{-3})$ in the other. The
  test asserts the decisions differ. That is the referee's counterexample, instantiated.
* **The measured thresholds move over a range the withdrawn claim cannot represent.** From the
  parity run: on the ring, $q^* = 0$ in the declared, subgroup and all four approximate regimes
  (no candidate was harmed there, $H = 0$), and $q^* = 0.938$, CI $[0.933, 1.000]$, in the
  mismatched regime ($B = 0.00018$ from two beneficial repairs, $H = 0.00276$ from 58 harmful ones).
  A 94-point swing in the decision boundary, with the proposal distribution unchanged.

**Where the model fails, and why we report that rather than hide it.** The threshold rule is
correct, but its natural argument is $E[\Delta \mid \text{evidence}]$, and *label validity is a poor
proxy for the sign of* $\Delta$. In the four approximate-symmetry regimes the supplied group is not
a label symmetry of the perturbed target ($\pi = 0$, so the rule says never fire), yet all 60
repairs help, by $-0.00334$ to $-0.00343$. The proxy does not merely misestimate; on this continuum
it inverts. That is the referee's point demonstrated on our own data, and it is now stated in the
manuscript instead of being worked around.

We do not claim this as a new theorem. The threshold algebra is elementary; what we offer is that
it is *measured* here — $B$, $H$, $s$, $f$ and $q^*$ per regime, with intervals — and that the
measurement shows the exactness event is the wrong state variable under approximate symmetry.

## 2. The third task: subgroup sampling fixed, and the claim downgraded to a bound

**The code defect was real.** `label_test`'s capped fallback drew `rng.permutation(n)` — arbitrary
elements of $S_n$. A violation at a permutation outside the proposed subgroup refutes nothing about
that subgroup. It is replaced by `closure_capped(gens, n, cap)`, the same breadth-first search over
generator products as `closure`, returning the elements found instead of raising. Every returned
element is a word in the proposed generators. `test_capped_return_is_always_subgroup_words` asserts
that the capped set is a subset of the fully enumerated subgroup and that every element is a
bijection; the un-enumerable case ($\langle\text{9-cycle}, \text{transposition}\rangle = S_9$) is
asserted to report `complete=False`.

**Certification language is now three-level and machine-recorded.** `certifies_soundness` is
deleted. Each test result carries `scope` $\in$ {`exhaustive_subgroup_on_probe_set`,
`inconclusive`}, plus `refutation_is_conclusive: true` and `acceptance_is_conclusive` (true only
when the subgroup was fully enumerated). Panel entries whose subgroup exceeds the cap carry
`scope: "inconclusive"` at the point where the number is read. In the $n=9$ record, **3 of 9 panel
entries are now inconclusive** — `full_symmetric`, `random_permutations`, `single_transpositions`,
exactly the capped ones. Nothing in the paper calls a finite-probe result a proof of the population
label-symmetry group any more; the exhaustive $n\le 6$ checks are described as exhaustive over the
finite input domain.

**Zero acceptances are reported with a bound.** For `tictactoe_n9`, each of the three uniform
models gives 0 acceptances in 400 draws, reported with a one-sided Clopper--Pearson upper bound of
**0.00746**. The claim in the paper is now "acceptance rate at most 0.0075 at 95% confidence under
these $Q$s", not "provably non-discriminating". We agree with the referee that the eight
square-board symmetries are valid and that a proposal distribution concentrated on them would be
accepted; the $n=9$ result bounds the *uniform-model* acceptance rate and says nothing about an
adapted proposer. As for exact cardinalities: we do not claim $|L_t|$ for $n=9$ by exhaustive
checking, and we have not added the analytic derivations the referee sketches (connectedness for
graphs, quadratic form for the ring); the paper claims exhaustive-over-$S_n$ results only at
$n \le 6$, where `exact_L` enumerates all $720$ permutations and verifies the result is a group.

## 3. The empirical proposal distribution: the pool was wrong, and the number changed

All three defects confirmed and fixed. The old `_empirical_hypotheses` read every `run_*.json` in
the directory (mock and non-LLM arms mixed with LLM arms, both six-qubit families mixed together),
appended each run's selected best hypothesis *in addition to* its occurrence among proposals, and
the call site computed a filtered `emp_here` and then passed the unfiltered `emp`. The deprecated
pool held **819** entries.

$Q$ is now defined before it is measured: proposals from the named LLM arms, on the family's own
runs, one entry per proposal, selected-best duplicate removed, mock runs excluded, and frozen-mode
runs kept separate from corrected-mode runs. Because the pool is finite and fully stored, its rate
is computed by **exact enumeration**, with no Monte-Carlo layer:

| $Q$ | kind | $n$ | accepted | rate |
|---|---|---|---|---|
| `llm_ring_n6` | exact over stored pool | 192 | 120 | **0.6250** |
| `uniform_single` ($S_6$) | Monte Carlo, 400 draws | 400 | 9 | 0.0225 |
| `uniform_pair` ($k=2$) | Monte Carlo, 400 draws | 400 | 1 | 0.0025 |
| `uniform_triple` ($k=3$) | Monte Carlo, 400 draws | 400 | 0 | 0, bound 0.00746 |
| `llm_graphs_n6` | exact over stored pool | 304 | 304 | 1.0000 |

Recomputed ratios against the **exact** group sizes rather than noisy MC draws
($|L_{\alpha_0}| = 12$ of $720 = 0.016667$; two-generator model $0.000278$): the ring LLM pool
accepts **37.5×** more often than a uniform single permutation and **2248×** more often than a
two-generator proposal. We are dropping the "three orders of magnitude" framing entirely: the
honest statement is that the empirical pool is far from uniform, that the pool's rate carries no
Monte-Carlo error but *also no uncertainty about the LLM process that produced it*, and that
between-run spread is now reported separately (`proposals_with_hypothesis_per_run`, ranging 0 to 11
per run on the ring). A write-time assertion now refuses to emit the record if a family with a
non-empty pool lacks its exact-pool entry — this patch silently failed to apply once during this
round, and the record looked complete.

## 4. Gate parity restored, and the two threshold designs separated

Both defects confirmed: `lab_d` received `gens_declared` in every regime, and `chan` was computed
once with `group="true"` outside the regime loop. In the mismatched and approximate regimes the
"defective" and "corrected" gates were therefore testing different repairs, and the channel
condition was not the channel condition of the repair under discussion.

`decision_rules3.py` is a new module rather than an edit, so the A6 record stays as the audited
artifact of what was actually run; it imports the shared structures from `decision_rules2` rather
than re-implementing them. Now: every gate receives the current regime's group and target; the
channel residual is recomputed per regime with the regime's group; and the two threshold designs
are separate policies with separate names — `defect_q1_frozen` (numeric threshold computed once on
the declared regime, applied unchanged elsewhere) and `defect_q1_within` (recomputed per regime,
which preserves a selection fraction by construction and is labelled within-regime quantile
selection, not transfer).

The parity fix changes the mismatched-regime picture, and not in our favour. With the regime's own
group, the frozen-threshold defect rule fires **56/60** and rejects only **4 of 58** harmful
repairs (risk 0.01064 against never's 0.00812) — the earlier comparison flattered it. The corrected
label gate rejects **58/58** harmful repairs and the 2 beneficial ones with them (risk 0.00812,
identical to never-repair).

## 5. A complete decision problem: never-repair, an information set, and a mixture

`never_repair` is now an explicit zero-cost policy, and we agree with the referee's consequence: in
the mismatched regime, where every corrected decision rejects, never-repair has the same realized
risk (0.00812) and no gate cost, so the corrected gate is **not** optimal there for $w > 0$ — it is
weakly dominated. We no longer claim otherwise. Its value is insurance under regime uncertainty,
which is now the thing actually evaluated: a policy is a function of the candidate and the supplied
group only, the regime is not observed at decision time, and policies are scored under the
pre-declared mixture $\pi \in \{0, 0.25, 0.5, 0.75, 1\}$.

Ring argmin by mixture and cost weight (risk plus $w(\text{search seconds} + H\times\text{deployed
seconds per prediction})$, $H = 10^3$):

| $\pi$(declared) | argmin at $w=0$ | argmin at $w=10^{-2}$ |
|---|---|---|
| 0.00 | `never_repair` | `never_repair` |
| 0.25 | `corrected_label` | `never_repair` |
| 0.50 | `corrected_label` | `never_repair` |
| 0.75 | `corrected_label` | `never_repair` |
| 1.00 | `always_repair` | `never_repair` |

On graphs, `always_repair` wins for every $\pi \ge 0.25$ at $w=0$ (risk 0.46087 against never's
0.54479) and `never_repair` wins at $w = 10^{-2}$. Costs are decomposed rather than merged:
`search_seconds_per_candidate` (gate + one-off averaging) and `deployed_seconds_per_prediction`
(measured averaged-inference time minus raw, times $H$), with the record stating that risk is a
per-prediction MSE (a rate) while the horizon term is cumulative. Averaged time is a timed call over
the twirl elements, not raw time $\times$ group order; the measured overhead factor is reported
per candidate (ring declared regime: median **10.17**, range 9.28–12.19, against a group order of 12 —
so the raw-time × group-order extrapolation was close on average but wrong per candidate), every timing is the median of three repeats with min/max stored, and all timings are
tagged `measured`.

## 6. The calibrated screen: the pre-declared negative result

The referee named the interesting question — whether a calibrated, statistically justified screen
chooses beneficial repairs under approximate symmetry better than the simple policies — and we ran
it, with the verdict categories fixed in A7.5 before the data existed. Two honest amendments to our
own pre-declaration are recorded first: A7.5 as first written calibrated against a "null panel of
exactly symmetric targets", where accepting is correct at every tolerance and the constrained error
is identically zero. A7.5a names the error each rule controls (`calib_exact`: accepting a
non-symmetry; `calib_harm`: accepting a repair that actually harms), each choosing the largest
tolerance on a scale-free grid whose one-sided 95% bound is at most $\alpha = 0.05$.

Result, both families, under the mechanical verdict rule in `analyze_decision3.py`:

> **Scoped negative.** No calibrated rule is the strictly unique best policy at any
> (mixture, cost-weight) cell on this continuum.

The mechanism is worth stating because it is stronger than a null. `calib_exact` selects the largest
admissible tolerance, $t = 0.03 \times \mathrm{sd}(y)$, and **still fires 0/60 in every regime**:
the label violations under a wrong or perturbed group are larger than 3% of the target's own
spread, so a tolerance constrained at $\alpha = 0.05$ cannot reach them. The calibrated exactness
screen therefore collapses onto `never_repair` — numerically identical risk in all seven regimes.
`calib_harm` returns **no admissible tolerance anywhere**: no tolerance on the grid keeps the
harmful-accept rate's upper bound at or below 0.05. And the uncalibrated exactness screen forfeits
the entire benefit on the continuum: at $\varepsilon = 0.40\,\mathrm{sd}(y)$, always-repair reaches
0.00621 while the screen leaves 0.00955.

One methodological note, because it matters for how much weight to put on the word "wins". Our first
pass reported `calib_exact` as the winner at $\pi = 0, w = 0$. That was an artifact: objectives tie
exactly when both policies fire nothing, and an alphabetical `min` returned the calibrated name. The
analysis now compares with a strict-improvement tolerance and breaks ties toward the simpler policy,
and reports `strictly_unique` per cell. With that in place the win disappears. We are reporting this
because a reviewer reasonably asked us not to overstate, and the failure mode was in our own
analysis code, not in the referee's reading of it.

## 7. Feedback endpoint: multiplicity first, and the deployed contrast

`analyze_corrected.py` now applies Holm **before** assigning verdicts, and "significant" for verdict
purposes means the **adjusted** $p < 0.05$; the unadjusted sign-flip $p$ is recorded alongside. The
vocabulary is split into `bounded within prespecified band (descriptive)` and
`equivalent at the prespecified margin (Holm-adjusted TOST)`, and the two are not interchangeable.
Applying that rule to our own headline: the ring candidate contrast $+0.00039$, CI
$[-0.00016, +0.00093]$ has its unadjusted interval inside the $\pm 0.002$ band, but the
Holm-adjusted interval $[-0.00624, +0.00690]$ does not, so **we do not claim equivalence** — the
paper says the interval lies inside the band descriptively, and nothing stronger.

Why 0.002: it is a third of the $0.006$ gap between the LLM arms and the constructive equivariant
block on the ring invariant floor, which is the smallest existing contrast in this benchmark that a
practitioner would act on. It is not comparable to the repair-side margins ($0.002$ absolute risk on
a floor of $0.0047$ is a 43% relative effect; the repair effects there are $0.028$--$0.049$), and the
paper now says so rather than implying one scale.

The deployed contrast the referee said was computable from stored diagnostics with no further
holdout read is now computed, as its own row per contrast, with non-firing runs contributing their
candidate risk:

| family | endpoint | contrast | mean | 95% CI | sign-flip $p$ | Holm $p$ | verdict |
|---|---|---|---|---|---|---|---|
| ring | candidate | verify-corrected $-$ fitness | +0.00039 | [−0.00016, +0.00093] | 0.203 | 1.000 | bounded within band (descriptive) |
| ring | deployed | verify-repair-corrected $-$ fitness | −0.00026 | [−0.00121, +0.00060] | 0.593 | 1.000 | bounded within band (descriptive) |
| graphs | candidate | verify-repair-corrected $-$ fitness | −0.02249 | [−0.07236, +0.01926] | 0.684 | 1.000 | difference not detected |
| graphs | **deployed** | verify-repair-corrected $-$ fitness | **−0.07269** | [−0.12931, −0.02313] | **0.0176** | **0.158** | difference not detected |

We follow the referee's instruction on interpretation precisely. The candidate-endpoint bound is
restricted to development-selected risk on one dataset, one model, one budget; the causal reading
rests on the contemporaneous corrected-versus-corrected comparison, and the corrected-versus-old-gate
rows are labelled as differing in run time and possibly serving state. "The trajectory outcome did
not move" is no longer used; the sentence is now that the mean effect on this endpoint is bounded
inside the band, and that on graphs the deployed contrast moves by $-0.07269$ with an unadjusted
$p = 0.0176$ that does not survive adjustment ($0.158$) — a hypothesis for a larger study, listed in
"What would change these conclusions", not a result. The coverage-conditional three-run estimate
($-0.00300$, CI $[-0.00416, -0.00195]$, conditional on firing) is labelled as conditional.

## 8. Coherence, and the checkers' status

The three contradictions were live and are fixed: the abstract no longer presents the defect gate's
79% recovery as a present-tense conclusion (it states the corrected screen's result and points to the
audit appendix for the superseded comparison); the A5 decision material is in the appendix with its
provenance rather than in the results; and the Discussion's "What would change these conclusions"
no longer says corrected-feedback runs were not performed — it now describes them. The
$\texttt{tictactoe\_n9}$ limitation is corrected too: its label-symmetry structure *has* been
measured (that needs no circuit simulation); what remains unrun is the search/repair benchmark.

We accept the referee's point about the checkers. `check_numbers.py` and `claim_bind.py` are now
described in §Reproducibility as self-checks on documents this project produced, useful for catching
transcription errors and stale numbers, with no claim resting on them passing, and with the explicit
admission that context-token matching is not semantic reconciliation — the fourth-round review found
live contradictions they did not, which is precisely their limit. They stay as supporting software
and are removed from anything resembling a contribution list.

---

## What we now offer as the contribution

We take the third route the referee offered — a sharply scoped negative study — and we state its
scope in the title of the section rather than in a footnote:

> **A label-exactness screen is the wrong instrument for approximately symmetric targets, and the
> failure is measurable rather than rhetorical.** On a pre-declared perturbation continuum, a
> tolerance calibrated to keep the false-accept rate's 95% upper bound at $\alpha = 0.05$ still
> rejects every candidate (0/60 in all seven regimes), collapsing the screen onto never-repair;
> no tolerance at all controls the *harmful*-accept rate at that level; and the exactness event
> inverts as a state variable for the sign of $\Delta$ ($\pi = 0$ while all 60 repairs help). The
> correct instrument is a threshold on $E[\Delta \mid \text{evidence}]$, and the measured threshold
> itself swings from $0$ to $0.938$ across regimes the two-probability story treats as identical.

What this does **not** claim, stated in the paper: that any real task has this shape (the continuum
is synthetic and controlled); that the threshold algebra is new; that a calibrated screen ever beats
the simple policies (it does not, in any cell we tested); or anything about LLMs beyond the local
setting. We agree with the referee that the general components are expected from definitions plus
bias--variance and decision reasoning. Our position is that the *measurement* is the contribution:
the failure is quantified against a calibrated comparator rather than asserted, on a frozen
predictor panel with paired inference, and it disconfirms a claim we ourselves made two rounds ago.

If the referee judges that a quantified negative on a synthetic continuum, against pre-declared
categories, with the boundary case measured rather than asserted, still does not clear the bar for
this venue, we would accept that as a scope judgment about the venue rather than a defect in the
evidence — and we would ask only that the assessment say so in those terms, since every concrete
error the referee identified has now been corrected, several at the cost of removing our own
favourable numbers.

## Residual limitations we are not resolving this round

* The approximate-symmetry continuum is synthetic. The referee is right that adding a non-invariant
  perturbation creates an approximately symmetric target, and right that what is missing is
  independently validated, task-relevant approximate symmetry. We have not produced that, and we
  have stopped claiming that "no approximately symmetric target exists in our set" — the corrected
  sentence is that no *task-relevant* one does.
* One model, one serving alias with no immutable checkpoint revision, two six-qubit families, and a
  third family used only for label-structure measurement.
* The deployed graphs contrast ($p = 0.0176$ unadjusted, $0.158$ adjusted) is the most promising
  open thread and is underpowered at 12 seeds; resolving it needs more seeds, not another holdout.
* Repair-side inference still conditions on one dataset and one direction set; no interval here
  covers newly sampled datasets or families.
