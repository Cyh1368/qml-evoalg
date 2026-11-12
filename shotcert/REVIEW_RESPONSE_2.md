# Response to the second referee report

**Summary.** The referee is right on all six concerns. Each was verified in our source before being
accepted. Two of them are errors we introduced while fixing the first round; one is a numerical
statement in our own response that does not match our own JSON.

The most important consequence is not a wording change. Once the comparator's measurement cost is
charged honestly — one record per distinct circuit, with every deterministic policy evaluated from it at
zero additional shots — **the advantage we reported disappears and reverses**. The group-free arm reaches
the power threshold at *half* the total cost of the group arm on six of seven tasks, including both
physical mechanisms. Our own frozen stop criterion (A2.7, applied where it says it applies) therefore
**fails**, and the paper now reports the scoped negative as its operational finding. The referee's
characterisation — that our positive result "mainly contrasts different policy menus on constructed
controls" — was correct, and the corrected experiment is what settles it rather than argument.

All changes were pre-declared in `docs/PROTOCOL.md` **Addendum A3** (commit `e529e0b5`), before any A3
analysis was run.

---

## 1. The manuscript still published withdrawn results — **confirmed, removed**

Verified: the abstract still quoted the pre-A2 frontier (`power 0.000 up to n=200 and 1.000 at n=400`,
the `B=1600` allocation comparison), Section 4 still `\input`-ed `tabs_frontier.tex` and
`tabs_bound.tex`, the first term of Eq. (1) was still labelled `bias^2`, and the access section still
said "one labelled state preparation per calibration instance" while the ledger intended the opposite.
Mixing an invalid distribution-free frontier with a new Studentised sweep and calling both the study's
evidence is exactly the defect described.

**Fix.** All pre-A2 certificate material — the old frontier, the old bound comparison, and the
withdrawal subsection that quoted them — is moved to `\section*{Historical (superseded) results}`, which
opens with "Nothing in this appendix supports any claim in this paper" and states why each number is
invalid. The main argument now contains zero references to those tables (verified mechanically:
`tabs_frontier` and `tabs_bound` appear only after the appendix marker). The abstract, contribution list
and access model are rewritten; the first term is now the integrated squared discrepancy $D_a$.

**Structural fix.** A checker that verifies each number appears *somewhere* cannot catch a number paired
with the wrong quantity — `"power 1.000 at 20,800 shots"` quoted a power that exists in the data and a
budget that exists in the data, at points that do not belong together. So `paper/make_claims.py` now
emits the manuscript's quantitative **sentences** from `results/matched.json`, and `main.tex` inputs
them. `paper/check_numbers.py` (absent when the last error slipped through) additionally fails the build
on any threshold-crossing number not bound to a generated artifact; arXiv identifiers are excluded by
pattern, and every other exemption is an explicit reviewed entry in `ALLOWED`. Current status: OK.

## 2. Reported selection rates were not certified at the advertised level — **confirmed, language corrected**

Correct: the 108-point sweep called `certify(..., bound="normal")`, a normal-quantile approximation, and
the paper used the word "certifies". Wilson intervals on simulated violation frequency quantify
Monte-Carlo uncertainty in these regimes and do not confer $1-\delta$ validity on a future task.

**Fix.** Three selectors are now defined by name and used consistently: **certified** (Maurer–Pontil,
finite-sample guarantee), **plug-in** (generic paired calibration, no guarantee), and **Studentised**
(descriptive simulation evidence only). "Certifies" is reserved for the first. The
`n_required_mp` figure is described as the cost of that particular conservative bound — explicitly "not
a lower bound for the statistical problem and not a measurement-complexity result", since a sharper
inequality or one exploiting paired structure beyond the contrast range would move it.

## 3. The comparator did not isolate a method advantage — **confirmed; corrected comparison reverses the claim**

All three sub-points are right, including the arithmetic.

**(a) The comparator was underpowered by construction.** Shrinkage toward a declared constant was the
only group-free class, and the controls were designed so orbit averaging reduces bias. We now report
the two questions separately, as pre-declared in A3.4: (a) what the group buys — same selector,
different candidate sets, matched resources; (b) what certification buys — **the same symmetry menu**,
generic plug-in selection versus the certified rule. The expectation was stated before running: our
certificate *is* generic paired certification, so (b) should show no symmetry-specific method advantage.
It does not: the plug-in rule matches the Studentised selector wherever either reaches high power and
dominates the certified rule, which almost never fires.

**(b) The comparator's cost was avoidably inflated.** Every shrinkage level is a deterministic rescaling
of the same raw batch, and we resampled and charged a batch per level. A3.3 replaces this with a shared
record: $s$ shots per **distinct circuit** per instance, all deterministic policies evaluated from it at
zero additional shot cost, dependence across policies handled by the simultaneous bound (valid under
arbitrary dependence; the paired contrast remains an average over independent instances). The same
sharing is applied to the symmetry arm, whose honest price is exactly $|G|$ circuits.

One subtlety we had to get right: policies that allocate shots per *draw* (`orbit_k`, mixtures) would
gain shots they do not pay for under sharing while being scored by their deployed risk — an estimator
compared against a different estimand. They are excluded from the shared-record comparison and studied
in the deployed-cost experiment, which is stated in the paper.

**(c) The numbers were wrong.** Our response and Section 4.1 said power **1.000** at 20,800 shots
(`control_help`) and **1.000** at 96,000 (`control_interior`). `results/ledger.json` says **0.900** and
**0.960**; power 1.000 needs 59,200 and 160,000. "Never certifies" was also wrong for arms with
non-zero power. Both are corrected, and the sentences are now generated rather than typed.

**Result of the corrected comparison** (200 repetitions, $\delta=0.05$, $\epsilon$ per the frozen rule,
total shots including a declared 1,000-prediction deployment):

| task | grp $\Delta_{\text{best}}$ | group-free $\Delta_{\text{best}}$ | $\epsilon$ | grp cost | group-free cost | verdict |
|---|---|---|---|---|---|---|
| `control_help` | −0.03186 | −0.00645 | 0.00000 | 17,600 | **8,800** | group-free cheaper |
| `control_interior` | −0.00884 | −0.00363 | 0.00000 | 17,600 | **8,800** | group-free cheaper |
| `control_hurt` | +0.07367 | +0.00650 | 0.00000 | none | none | neither reaches |
| `heisenberg_even_n6` | −0.00854 | **−0.04795** | 0.00217 | 17,600 | **8,800** | group-free cheaper |
| `heisenberg_raw_n6` | +0.00122 | **−0.04371** | 0.00217 | 17,600 | **8,800** | group-free cheaper |
| `cluster_even_n7` | −0.00229 | −0.01396 | 0.00386 | 17,600 | **8,800** | group-free cheaper |
| `cluster_raw_n7` | −0.00229 | −0.01396 | 0.00386 | 17,600 | **8,800** | group-free cheaper |

The group arm's cost is exactly $2\times$ the group-free arm's because it must measure a second circuit,
and at these budgets its bias gain does not repay that. On the physical mechanisms the group-free arm is
also *better*, not merely cheaper: shrinkage by ten per cent gains $-0.04795$ on `heisenberg_even_n6`
where full orbit averaging gains $-0.00854$.

Assembling this table caught a third instance of the same error class. An initial reading pooled
$\min_s \Delta_{\text{best}}$ across each arm's whole sweep, which compares unequal deployments and
reported the Heisenberg group-free gain as $-0.00206$ (taken from its $s=64$ row) instead of $-0.04795$
at matched $s=8$. The generator now quotes both arms at a common shots-per-circuit and says so in the
caption. Since the referee rejected the previous submission partly for a number taken from the wrong
point of a sweep, we would rather report finding it a third time than have it survive a fourth.

## 4. The ledger still miscounted preparations and compilations — **confirmed, corrected and pinned by tests**

`calib_ledger()` set `preparations_total = n × policy_batches` — 400 preparations for 3,200 shots —
contradicting its own docstring, which said every repeated shot needs a fresh state copy. Compilations
summed `p.circuits` over policies, charging 12 for a two-element group. Switches were summed over
candidates that were never executed.

**Fix.** Preparations equal shots under single-copy destructive measurement; compilations are the
**distinct** circuits across the menu ($|G|$ for a group menu, 1 for the group-free menu); switches come
from the executed schedule. `Policy.circuit_ids` gives circuit identity so sharing is computed rather
than assumed. Four new unit tests pin all four conventions, including that shared shots are strictly
below the naive per-policy sum. Suite: 24 tests, all passing.

## 5. The study did not pass its own physical-task stop gate — **confirmed; the gate now runs and fails**

Correct: the A2 ledger covered only the three synthetic controls. A3.5 runs the matched-resource
comparison, with the A3.2 ledger and A3.3 sharing, on the Heisenberg and cluster mechanisms. The verdict
is emitted from the JSON by `make_claims.py` rather than asserted:

> Under shared measurement records and matched total resources, the group-free arm reaches the 0.9 power
> threshold at lower total cost than the group arm on 6 of 7 tasks, including both physical mechanisms.
> The frozen A2.7/A3.5 stop gate therefore FAILS, and the scoped negative is the finding.

The paper's contribution list now leads with the scoped negative, and advantage language is removed from
the abstract and the principal-contribution section. The two acknowledged scope facts are kept in the
limitations and are consistent with the claim: the cluster task's even and raw targets are nearly
identical, so it does not test the sign-reversal mechanism; and the Heisenberg input flip is a paired
control transformation, not a symmetry of the deployed experiment.

## 6. Theoretical contribution — **accepted; the paper no longer claims otherwise**

We agree. Eq. (1) is a conditional bias–variance decomposition, the calibration split is the law of total
variance, the bound is a known result applied to a fixed finite menu, the minimum-$n$ figure
characterises that conservative bound, and the per-switch optimum is schedule-dependent and prices a
schedule the predictor need not use. No theorem is offered as a contribution. What the paper offers is a
measurement-shared, matched-resource negative result, a corrected accounting, and a documented record of
two claims this study had and lost — which we regard as the honest residual for this venue, and we state
in the limitations that it is a control study with no device evidence, no new measurement primitive, and
no allocation rule.

---

## Current state

- `paper/main.tex`: pre-A2 material confined to `\label{sec:historical}`; abstract and contribution list
  rewritten around the scoped negative; terminology and access model fixed.
- New artifacts: `experiments/exp_matched.py` (shared-record, matched-resource, both mechanisms, three
  selectors), `results/matched.json`, `paper/check_numbers.py`, `paper/make_claims.py`,
  `paper/tabs_matched.tex`, `paper/claims_matched.tex`.
- 24 unit tests pass, including the four new ledger conventions and the independent-enumeration
  agreement.
- `check_numbers.py`: OK — every threshold-crossing number in the manuscript is bound to a generated
  artifact, and the sentences quoting the headline numbers are generated from the JSONs.

## What we would still like to know, and do not claim

The group arm's factor-$|G|$ price is a property of *this* comparison, where the group's only benefit is
a bias reduction of order $10^{-3}$ to $10^{-2}$ at $s$ shots per circuit. Whether a task family exists
where that repays the second circuit at matched total resources is open, and answering it would require
mechanisms with much larger odd components than the two we have. We do not claim the negative generalises
beyond the two mechanisms and three controls we tested, and we do not claim a lower bound for the
statistical problem.
