# Evolved Ansatz Re-Run — ShinkaEvolve under the Converged Objective

**Date:** 2026-06-29
**Run:** `cemoid_ea_converged` (Yale Bouchet), 100 generations, completed 2026-06-28 20:56
**Data:** `paper-replication/ea_converged_result/programs.sqlite` (99 scored programs)
**Best program id:** `b6ba28a0-c603-4aa9-802b-3501115b3967` (generation 16)
**Motivation:** Earlier ShinkaEvolve runs selected ansätze under a *flawed* fixed-3-epoch
objective, so they were ranked on undertrained accuracy. This run re-evolves the circuit
under the **correct converged objective** identical to the cemoid replication, then
characterizes the best evolved ansatz.

---

## Methods

I re-ran ShinkaEvolve (evolutionary neural-architecture search over the cemoid ansatz) for
**100 generations** with each candidate scored under the **converged evaluation protocol** —
the same one used in the cemoid replication and the extended L/P sweep: class-balanced
450/300/600 splits, Adam at lr 0.03, validation-loss early stopping (patience 75, min_delta
1e-4, restore-best-weights, 1000-epoch cap). Candidates were ranked by a `combined_score`
computed from converged validation accuracy with a parameter-efficiency regularizer (the
score does **not** peek at the test set; `score_uses_test = false`), correcting the earlier
runs that ranked on a fixed 3-epoch accuracy. The orchestrator ran on a Bouchet login node
(for outbound OpenRouter LLM access) and farmed each candidate evaluation out as an
independent SLURM job on the CPU `day` partition; the per-evaluation circuit was the
batch-broadcast statevector implementation (a provably-identical 7× speedup over the original
per-sample QNode loop). After the run finished, I selected the top program from
`programs.sqlite` by `combined_score`, extracted its `ANSATZ_SPEC` from the evolve-block,
tallied its gate composition and weight-sharing structure, and reconstructed the
running-best score trajectory across all 100 generations to measure the improvement over the
seed circuit.

## Results

The search produced a best ansatz at **generation 16** with **combined_score 0.7393** and a
mean **test accuracy of 0.7867** (train 0.8067, validation 0.8267, generalization gap only
**0.02**, test loss 1.898) — a large, genuine gain over the seed circuit (combined_score
0.5812, test accuracy 0.5917), i.e. **+0.20 absolute test accuracy / +27% relative score**.
The running-best trajectory shows steady, converging progress —
0.5812 (gen 0) → 0.6811 (gen 2) → 0.7184 (gen 9) → **0.7393 (gen 16)** — after which the score
**plateaued for the remaining 84 generations**: the identical 0.7393 optimum was rediscovered
independently at generations 16, 26, 27, 48, 49, 65, 72, 73, and 74, indicating the EA settled
into a robust attractor rather than a lucky one-off. The winning block — patch
`symmetry_grouped_rotations_and_crx_hub` — is built on **board-symmetry weight sharing**: full
RX, RY, and RZ single-qubit layers whose 27 rotation gates collapse to **9 free angles** by
tying the four corners (wires 0/2/4/6), the four edges (1/3/5/7), and the center (8) together,
plus a parametrized **CRZ nearest-neighbour ring** over the 8 outer qubits (one shared angle
`crz_outer`) and a 4-gate **CRX hub** coupling each edge to the center (one shared angle
`crx_inner`). This yields just **11 unique parameters per block**; tiled into the full 6-block
circuit it gives **66 free parameters at depth 70 / 261 gates**. Crucially, the EA *reduced*
parameters relative to the seed (162 → 66 free params at the same depth/gate count) **while
raising accuracy**, demonstrating that the improvement came from smarter symmetry-aware weight
sharing — not from added capacity. Read alongside the extended L/P sweep (see
`SWEEP_LP_EXTENDED_REPORT.md`), the evolved circuit reaches **0.787 test accuracy with only 66
free parameters**, far more parameter-efficient than the brute-force sweep, which needs ~360
untied parameters (L8P5) to reach its 0.898 ceiling.

---

## Appendix A — Best program metrics (generation 16)

| Metric | Value |
|---|---|
| combined_score | 0.7393 |
| train accuracy | 0.8067 |
| validation accuracy | 0.8267 |
| **test accuracy** | **0.7867** |
| generalization gap | 0.020 |
| validation loss | 1.786 |
| test loss | 1.898 |
| free parameters | 66 |
| circuit depth | 70 |
| gate count | 261 |
| parameter efficiency | 0.0119 |
| island | 0 |

**Seed (generation 0):** combined_score 0.5812, test accuracy 0.5917, 162 free params,
depth 70, 261 gates.

## Appendix B — Running-best trajectory and top-score ties

Running-best improvement steps (generation, combined_score):
`(0, 0.5812) → (2, 0.6811) → (9, 0.7184) → (16, 0.7393)`.

Generations that (re)achieve the top score 0.7393: **16, 26, 27, 48, 49, 65, 72, 73, 74**
(9 independent programs converge to the same optimum).

## Appendix C — Gate composition of the evolved block

| Gate | Count | Role | Shared params |
|---|---|---|---|
| RX | 9 | SU(2)-like rotation layer | rx_corner, rx_edge, rx_center |
| RY | 9 | SU(2)-like rotation layer | ry_corner, ry_edge, ry_center |
| CRZ | 8 | nearest-neighbour ring (outer 8 qubits) | crz_outer |
| CRX | 4 | edge→center hub | crx_inner |
| RZ | 9 | final local rotation layer | rz_corner, rz_edge, rz_center |

**11 unique parameters per block** (39 gate instances). Symmetry groups: corners = wires
{0, 2, 4, 6}, edges = {1, 3, 5, 7}, center = {8}.

## Appendix D — Best `ANSATZ_SPEC`

```python
ANSATZ_SPEC = [
    # Symmetry-grouped RX+RY rotations (SU2-like)
    {"gate": "RX", "wire": 0, "param": "rx_corner"},
    {"gate": "RX", "wire": 2, "param": "rx_corner"},
    {"gate": "RX", "wire": 4, "param": "rx_corner"},
    {"gate": "RX", "wire": 6, "param": "rx_corner"},
    {"gate": "RX", "wire": 1, "param": "rx_edge"},
    {"gate": "RX", "wire": 3, "param": "rx_edge"},
    {"gate": "RX", "wire": 5, "param": "rx_edge"},
    {"gate": "RX", "wire": 7, "param": "rx_edge"},
    {"gate": "RX", "wire": 8, "param": "rx_center"},
    {"gate": "RY", "wire": 0, "param": "ry_corner"},
    {"gate": "RY", "wire": 2, "param": "ry_corner"},
    {"gate": "RY", "wire": 4, "param": "ry_corner"},
    {"gate": "RY", "wire": 6, "param": "ry_corner"},
    {"gate": "RY", "wire": 1, "param": "ry_edge"},
    {"gate": "RY", "wire": 3, "param": "ry_edge"},
    {"gate": "RY", "wire": 5, "param": "ry_edge"},
    {"gate": "RY", "wire": 7, "param": "ry_edge"},
    {"gate": "RY", "wire": 8, "param": "ry_center"},
    # Parametrized entanglement: CRZ nearest-neighbour ring (outer 8 qubits)
    {"gate": "CRZ", "wires": [0, 1], "param": "crz_outer"},
    {"gate": "CRZ", "wires": [1, 2], "param": "crz_outer"},
    {"gate": "CRZ", "wires": [2, 3], "param": "crz_outer"},
    {"gate": "CRZ", "wires": [3, 4], "param": "crz_outer"},
    {"gate": "CRZ", "wires": [4, 5], "param": "crz_outer"},
    {"gate": "CRZ", "wires": [5, 6], "param": "crz_outer"},
    {"gate": "CRZ", "wires": [6, 7], "param": "crz_outer"},
    {"gate": "CRZ", "wires": [7, 0], "param": "crz_outer"},
    # CRX hub: each edge qubit -> center
    {"gate": "CRX", "wires": [1, 8], "param": "crx_inner"},
    {"gate": "CRX", "wires": [3, 8], "param": "crx_inner"},
    {"gate": "CRX", "wires": [5, 8], "param": "crx_inner"},
    {"gate": "CRX", "wires": [7, 8], "param": "crx_inner"},
    # Final local RZ layer
    {"gate": "RZ", "wire": 0, "param": "rz_corner"},
    {"gate": "RZ", "wire": 2, "param": "rz_corner"},
    {"gate": "RZ", "wire": 4, "param": "rz_corner"},
    {"gate": "RZ", "wire": 6, "param": "rz_corner"},
    {"gate": "RZ", "wire": 1, "param": "rz_edge"},
    {"gate": "RZ", "wire": 3, "param": "rz_edge"},
    {"gate": "RZ", "wire": 5, "param": "rz_edge"},
    {"gate": "RZ", "wire": 7, "param": "rz_edge"},
    {"gate": "RZ", "wire": 8, "param": "rz_center"},
]
```
