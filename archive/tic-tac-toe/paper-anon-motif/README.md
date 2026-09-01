# Discovery or Recall? — paper build

Paper on whether LLM-driven evolutionary search discovers the tic-tac-toe winning
lines or recalls them, comparing the leaky run (2026-07-18) against the
anonymized re-run (2026-07-24/25).

## Files

- `paper.tex` / `paper.pdf` — the paper (build: `tectonic paper.tex`)
- `figs/` — all figures, generated (do not hand-edit)

## Headline numbers

| | leaky (given) | Haiku 4.5 | Sonnet 5 | GPT-5.6-sol |
|---|---|---|---|---|
| generations | 100 | 30 | 30 | 30 |
| gates on winning lines | 916/916 (100%) | 35/89 (39%) | 0/46 (0%) | 7/95 (7.4%) |
| distinct lines found | 8/8 | 3/8 | 0/8 | 0/8 |
| **hidden lines found** | **2/2** | **0/2** | **0/2** | **0/2** |
| proposals naming the game | 92% | 10% | 27% | 30% |
| best validation accuracy | 82.7% | 67.7% | 72.0% | **82.3%** |
| best test accuracy | 78.2% | 65.5% | 65.7% | **77.8%** |

Two nulls are reported throughout: the uniform 8/84 = 0.095, and the
connectivity-matched 6/22 = 0.273. The second is the honest one, because 6 of the
8 winning lines are exactly the triples carrying two hardware links. Using it
moves the Haiku arm from p = 6.7e-14 to p = 9.1e-3.

## Second experiment: the symmetry tasks (positive result)

`transfer_sn` (networks on 8 nodes, label is an S_8 graph invariant) and
`transfer_su2` (8-qubit spin-singlet states). Neither names a symmetry anywhere,
verified by grep of prompt + seed + evaluator; both allow gates on any pair so
there is no connectivity confound.

| arm | test acc | params | equivariance |
|---|---|---|---|
| seed | 86.7% | 146 | 0.15 |
| Sonnet 5 | 92.0% | 98 | 0.18 |
| Haiku 4.5 | 92.0% | 38 | 0.66 |
| **GPT-5.6-sol** | **96.0%** | **26** | **0.96** |

GPT-5.6-sol derived permutation symmetry at gen 33 (`permutation_equivariant_ansatz`,
reasoning explicitly from 28 = C(8,2)). Mean equivariance across proposals jumps
0.154 -> 0.946 at that generation; mean score 0.821 -> 0.932.

`transfer_su2` is uninformative: all arms hit 100% accuracy by gen 2-9. Needs to be
made harder before it tests anything. Analysis scripts: `sym_analysis.py`,
`equivariance_test.py`, `sym_reasoning.py`, `verify_sym.py`, `make_figs3.py`.

## The three findings that carry the paper

1. **Connectivity is grid adjacency**, so the 6 rows/columns each contain exactly
   2 permitted pairs while the 2 diagonals contain none. The diagonals are the
   "hidden lines": the only ones unreachable by following visible wiring.
2. **GPT-5.6-sol matched the leaked run's accuracy using zero winning lines**
   (82.3% vs 82.7% validation), so the motif is not necessary for the accuracy the
   original result was built on.
3. **The recall test.** GPT-5.6-sol inferred the domain despite anonymization
   ("the eight winning lines of a 3x3 board") and at gens 3/7/8/9/10 placed 8/8
   gates on the *unpermuted* lines, 1/8 on the true ones. Those attempts scored
   0.546-0.578 against its own earlier 0.725, and it abandoned them. Recall
   falsified by measurement.

## Rebuilding

Scripts live in the session scratchpad (copy them here if they need to persist):

1. `extract_all.py` — run on Bouchet, dumps every run's programs to `rundata.json`.
   Reads local-disk copies in `/tmp/anon_dbs/` because the live DBs sit on NFS and
   throw `locking protocol` while an orchestrator holds them.
2. `stats.py` — computes both nulls, trajectories, and per-arm statistics into
   `stats.json`.
3. `make_figs.py` — writes all six figures into `figs/`.
4. `tectonic paper.tex`

All four runs are complete and included. `reasoning.py` extracts each proposal's
natural-language description; `recall_test.py` runs the remembered-vs-true line
comparison; `make_figs2.py` builds the two reasoning figures.

## Caveats stated in the paper

- The leaky run used 100 generations and a 3-model bandit; the anonymized arms
  used 30 generations and a single model each. The comparison is between
  protocols, not matched models.
- 30 generations rules out *fast* discovery, not slow discovery.
