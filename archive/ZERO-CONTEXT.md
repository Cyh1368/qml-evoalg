# Zero-context symmetry-discovery runs

Launched 2026-07-25 on Bouchet. Research question: **can an LLM-driven search
identify a symmetry with no context about the problem at all?** The proposer must
get there only by proposing circuits and reading the numbers that come back.

## Why the previous runs did not answer this

The graph run's winning proposal reasoned:

> "Exploit the likely graph structure of the 28 binary features, which correspond
> exactly to all unordered pairs of eight qubits."

It could say that because the task message *told* it the features map onto qubit
pairs, and the seed program's docstring repeated it (`FEATURE_PAIRS[k]`). Given
28 = C(8,2), permutation symmetry follows by deduction. That is inference from
supplied structure, not discovery from data.

## What changed

Two leak channels were closed. ShinkaEvolve embeds the **entire seed file** in the
prompt (`prompts_base.py`: `program_str += f"```{lang}\n{program.code}\n```"`), so
sanitising the task message alone is not enough.

1. **Task message** rewritten to state only: qubit count, the legal gate schema,
   the parameter-sharing mechanism, and what the score rewards. It explicitly says
   the model is not told what the data is or how it is encoded.
2. **Seed program** split. Everything about data loading, encoding, readout,
   training and metrics moved into `_backend.py`, which is imported and therefore
   never shown. The visible seed is ~55 lines: a docstring that describes nothing,
   `N_QUBITS`, the gate vocabulary, the evolve block, and a one-line delegation.

`evaluate.py` is *not* shown to the proposer (`evaluate_str` is written to disk for
execution only), so the scoring formula stays hidden.

## Tasks

| dir | qubits | hidden truth | what discovery looks like |
|---|---|---|---|
| `zc-sn` | 8 | label is an S_8 graph invariant (connectedness) | one shared angle across all 8 wires, pair-set closed under relabelling |
| `zc-su2` | 8 | states are spin singlets of a bond-alternating Heisenberg ring | XX+YY+ZZ on a pair with ONE shared angle, no single-qubit rotations |
| `zc-ttt` | 9 | 8 winning lines under a secret qubit permutation | three-qubit gates on the true permuted lines |

## SU(2) reward redesign

The old fitness saturated: `param_eff = min(1, acc*146/(4*n))` hit 1.0 at ~36
parameters, so every candidate below that scored identically and the pressure
vanished exactly where the interesting structures live. GPT-5.6-sol stopped at 14
parameters with no incentive to go further, and never found the isotropic coupling.

Two changes, neither of which names a symmetry:

- divisor 4 -> 36, so the score keeps discriminating down to ~4 parameters
  (146 params -> 0.028, 14 -> 0.290, 8 -> 0.507, 4 -> 1.000)
- weights `0.30 acc + 0.40 param_eff + 0.20 gap + 0.10 convergence`
- `TRAIN_SIZE` 450 -> **24**. Few-shot generalisation is the legitimate metric that
  the correct symmetry wins on, and it makes accuracy discriminative again rather
  than saturated.

## Runs

9 arms = 3 tasks x {haiku-4.5, sonnet-5, gpt-5.6-sol}, 80 generations, $15 cap each
($135 worst case; `OPENROUTER_API_KEY_3` held $298 at launch). Launcher:
`~/project/orch_zc.sbatch`, results in `~/project/zc_<task>/results_<model>/`.

## Gotcha fixed during launch

`TTT_LOG_DIR` was relative (`logs/training`). Eval jobs run from a generation
directory, so training logs went nowhere and every evaluation failed with a missing
file or a stale NFS handle. It is now absolute and created by the activation script.
First launch was cancelled and the results wiped before relaunch.

## Build

`python3 build_zero_context.py && python3 write_activate.py`, then rsync each
`zc-<task>/` to `~/project/zc_<task>/`.

## su2 v2 (2026-07-28)

The v1 su2 runs ended in a flat fitness: every 1-name circuit (trivial or
equivariant) scored an identical 0.8027, accuracy was 100% from generation 0,
and TRAIN_SIZE=24 was exported but never read. Full diagnosis and redesign in
`../context/zc-su2-scoring-redesign-2026-07-28.md`. v2: no re-uploading,
N_REPEATS=3 with parameters SHARED across repeats (count = distinct names),
TRAIN_SIZE=16 actually honored, dataset j in [0.80, 0.97] with 40% disorder +
difficulty groups, scoring led by worst-group clipped margin (0.45) with a
strictly monotone no-saturation economy term exp(-names/6)*acc (0.20).
answer_key.json / symmetry_analysis.py no longer ship to the cluster. Deployed
to `~/project/zc_su2_v2/`; v1 results untouched in `~/project/zc_su2/`.
