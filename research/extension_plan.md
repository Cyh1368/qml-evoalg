# Confirmatory extension program (executed)

Prospective plan written 2026-11-10 after the audit. Implements `experiment_plan.md`
through four work packages. All choices here were frozen before any new outcome was seen.

## Cluster note (supersedes the gpu_devel-only line in README.md)

The earlier protocol said "all cluster jobs must use `gpu_devel`". This is not executable
for this program: `gpu_devel` enforces `QOSMinGRES` (a GPU TRES is mandatory), and every
workload here (dense NumPy statevector simulation, training, LLM API calls) is CPU-only.
Attaching a GPU solely to satisfy the old wording would hold a GPU idle, which YCRC
idle-GPU/utilization policy prohibits, and YCRC policy takes precedence over project
instructions for cluster operations. Therefore: CPU batch jobs run on `day` (short smoke
tests on `devel`); `gpu_devel` is reserved for genuine GPU work, of which this program has
none. LLM calls run inside Slurm jobs with `module load ycrc-llm` per YCRC guidance.

## Software stack (frozen)

`module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a` (numpy 1.26.4,
scipy 1.13.1). LLM arms additionally `module load ycrc-llm/1.0`, model treatments
`ycrc-local` (reasoning_effort none / medium) and `ycrc-local-think` as categorical
treatments. No PennyLane, no conda env for batch jobs; stdlib + numpy + scipy only.

## Work packages

### WP-CORE — shared executable core (`research/core/`)

Dense statevector simulator over the repository gate-list format plus `RZZ`, with exact
reverse-mode parameter gradients, Adam training with orbit-disjoint train/dev splits,
candidate schema, and task adapters for `graphs_n6`, `ring_n6`, and the new
`tictactoe_n9` family. Interfaces frozen in `core/INTERFACES.md`; unit-tested.

### WP-TTT — third task family (`research/datasets/tictactoe/`)

Legal tic-tac-toe boards, D4 action on cells, scalar terminal/winner target, orbit-split
into dev/locked-holdout, plus a designated-cell counterfactual target that breaks D4.
Generated after this file is frozen; used only as the held-out transfer family.

### WP-REPAIR — decisive causal-repair experiment (`research/experiments/repair/`)

Implements the "next decisive test" of `training_review.md` on all three families:
`y_eta = h + eta*b` with `b` the group-centered, orbit-variance-normalized breaking
component and analytically known invariant-risk floor `eta^2 E[b^2]`; continuous circuit
breaking `H_eps = T_G(H) + eps (H - T_G(H))` with measured residual; gate-count-matched
equivalent control (repeated half-angle same-direction CRZ), the phase-shift sham,
increasing matched optimization budgets with common random numbers, >=8 paired optimizer
seeds per cell, >=3 frozen teacher draws, selection on train only, dev reported per
teacher/split, locked holdout evaluated exactly once after analysis choices are frozen.
Primary contrast: paired (train-fit) risk difference repaired vs original and vs
gate-matched control at eta=0 and eta=1, run/seed-level paired CIs.

### WP-SEARCH — matched-budget search comparison (`research/search/`)

Five arms at identical evaluated-candidate budget B=32 (pilot B=12):
`random`, `mutation-ea`, `llm-fitness`, `llm-verify` (adds executable equivariance
residual + label-preservation report for the proposal's own hypothesis and for the true
group), `llm-verify-repair` (compiles the Reynolds-repaired generator when the proposal's
hypothesis passes label preservation and the candidate residual exceeds tolerance).
Identical initial populations across arms; every proposal (including invalid) retained in
denominators; wall time, tokens, evaluator calls, and failures logged per run. Primary
endpoint: test risk of the dev-selected candidate at fixed budget, paired by seed between
arms. Pilot: 3 paired seeds x 3 model treatments x 2 development families. Confirmatory:
12 paired runs for the `llm-verify` vs `llm-fitness` contrast per family, frozen after the
pilot variance check. Locked holdouts evaluated once.

### WP-PAPER — analysis and manuscript

Predeclared analysis script, run-level bootstrap/hierarchical CIs, multiplicity
correction within secondary families, figures, `research/manuscript.md`, updated
`CLAIMS.md` reflecting only what the executed evidence supports.

## Integrity rules for all WPs

- `datasets/locked_holdout/` and `datasets/tictactoe/locked*` stay sealed until the
  single confirmatory evaluation; search code receives development artifacts only.
- No outcome is inspected before its protocol section is written to disk.
- Every persisted result JSON records seeds, module versions, git commit, and host.
- Negative and null results are reported as such; CLAIMS.md wording must not outrun
  the paired evidence.
