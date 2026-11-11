# Extended L/P Sweep — Accuracy Ceiling of the Cemoid QML Class

**Date:** 2026-06-29
**Cluster job:** SLURM array `16560387` (Yale Bouchet, `day` partition) — 153 tasks, all `COMPLETED`
**Data:** `paper-replication/histories/history_l{1..10}_p{1..10}.json` (100 cells)
**Question addressed:** Does this cemoid model class have an upper bound on classification
accuracy on the 3-class tic-tac-toe task, or does some (possibly low-depth) circuit reach
perfect (≈1.0) classification?

---

## Methods

I trained the cemoid variational classifier on a full **10×10 grid** of architecture sizes,
sweeping the number of circuit layers **L ∈ {1..10}** against the parameter-repeat factor
**P ∈ {1..10}**, for 100 distinct (L, P) configurations spanning **9 to 900 trainable
parameters**. This extends the original 7×7 sweep (`SWEEP_LP_REPORT.md`) by 51 new frontier
cells (every cell with L ≥ 8 or P ≥ 8), submitted heaviest-first as a SLURM array on the
Bouchet `day` partition; the 49 cached 7×7 cells were reused unchanged. Every cell was trained
under the identical **converged protocol** used throughout the cemoid replication: class-balanced
splits of 450 train / 300 validation / 600 test, Adam optimizer at learning rate 0.03, and
**validation-loss early stopping** (patience 75, min_delta 1e-4, restore-best-weights) with a
hard cap of 1000 epochs. Each cell wrote a history record with `final_test_accuracy`,
validation accuracy, best/stopped epoch, and the full val-loss trajectory. Convergence was
genuine, not cap-limited: **98 of 100 cells halted on early stopping** (mean stopped epoch 379,
range 122–756), so reported accuracies reflect converged optima rather than a fixed epoch budget.
I then quantified the size–accuracy relationship with Spearman rank correlation (parameter count
vs. converged test accuracy) and a Pearson correlation on log-parameters, and compared the new
frontier region (L > 7 or P > 7) against the original 7×7 region to test whether accuracy keeps
climbing toward 1.0 or saturates.

## Results

**Accuracy saturates near ~0.90 and does not approach perfect classification.** The single best
configuration over the entire extended grid is **L8P5 = 0.8983** (360 params), statistically
indistinguishable from the original 7×7 champion **L7P6 = 0.8950** (378 params); the frontier
region adds only **+0.0033** absolute accuracy over the old grid's best (0.8983 vs. 0.8950)
despite reaching 900 parameters. Scaling further actively stops helping — the ten heaviest cells
(params ≥ 600) average just **0.846** (max 0.890), no better than the mid-grid, and the entire
band of params ≥ 300 plateaus at mean **0.852** (37 cells, never exceeding 0.898). Size still
correlates with accuracy overall (Spearman ρ = **0.734**, p = 3.5e-18; Pearson on log-params
0.817), but the correlation is **weaker than on the 7×7 grid** (ρ was 0.896) — the curve has
flattened into a ceiling rather than continuing to climb. The gains are concentrated entirely at
the small end: accuracy rises steeply from the floor (L1P1 = 0.563, L2P1 = 0.562) up to ~100
parameters (params ≥ 100 mean 0.835) and then flattens, with essentially **zero marginal return
past ~300 parameters**. **Conclusion: the cemoid class has a hard accuracy ceiling around
0.89–0.90 on tic-tac-toe; no circuit in the 10×10 grid — low-depth or high-capacity —
approaches 1.0.** This is consistent with an intrinsic model-capacity / data-encoding limit
rather than an optimization or undertraining artifact.

---

## Appendix A — Converged test accuracy by (L, P)

| L\P | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 |
|---|---|---|---|---|---|---|---|---|---|---|
| **L1** | 0.563 | 0.593 | 0.692 | 0.620 | 0.660 | 0.695 | 0.683 | 0.670 | 0.702 | 0.718 |
| **L2** | 0.562 | 0.690 | 0.763 | 0.710 | 0.677 | 0.638 | 0.782 | 0.677 | 0.768 | 0.785 |
| **L3** | 0.593 | 0.693 | 0.762 | 0.793 | 0.770 | 0.858 | 0.817 | 0.832 | 0.740 | 0.797 |
| **L4** | 0.680 | 0.770 | 0.772 | 0.793 | 0.775 | 0.828 | 0.842 | 0.878 | 0.823 | 0.773 |
| **L5** | 0.690 | 0.747 | 0.852 | 0.833 | 0.828 | 0.878 | 0.828 | 0.850 | 0.893 | 0.815 |
| **L6** | 0.738 | 0.792 | 0.848 | 0.873 | 0.830 | 0.867 | 0.872 | 0.828 | 0.895 | 0.852 |
| **L7** | 0.692 | 0.882 | 0.830 | 0.853 | 0.858 | 0.895 | 0.885 | 0.802 | 0.757 | 0.860 |
| **L8** | 0.752 | 0.805 | 0.868 | 0.853 | **0.898** | 0.893 | 0.838 | 0.862 | 0.885 | 0.868 |
| **L9** | 0.777 | 0.838 | 0.877 | 0.858 | 0.895 | 0.832 | 0.863 | 0.890 | 0.732 | 0.837 |
| **L10** | 0.748 | 0.858 | 0.865 | 0.868 | 0.862 | 0.887 | 0.867 | 0.860 | 0.888 | 0.768 |

Parameter count per cell = 9 · L · P.

## Appendix B — Accuracy vs. parameter budget

| Param budget | # cells | mean acc | max acc | min acc |
|---|---|---|---|---|
| ≥ 50 | 90 | 0.8135 | 0.8983 | 0.6383 |
| ≥ 100 | 73 | 0.8345 | 0.8983 | 0.6383 |
| ≥ 200 | 52 | 0.8490 | 0.8983 | 0.7317 |
| ≥ 300 | 37 | 0.8515 | 0.8983 | 0.7317 |
| ≥ 400 | 26 | 0.8505 | 0.8950 | 0.7317 |
| ≥ 600 | 10 | 0.8455 | 0.8900 | 0.7317 |

## Appendix C — Top 10 and bottom 5 configurations

| Rank | Config | Params | Test acc |
|---|---|---|---|
| 1 | L8P5 | 360 | 0.8983 |
| 2 | L7P6 | 378 | 0.8950 |
| 2 | L9P5 | 405 | 0.8950 |
| 2 | L6P9 | 486 | 0.8950 |
| 5 | L8P6 | 432 | 0.8933 |
| 5 | L5P9 | 405 | 0.8933 |
| 7 | L9P8 | 648 | 0.8900 |
| 8 | L10P9 | 810 | 0.8883 |
| 9 | L10P6 | 540 | 0.8867 |
| 10 | L8P9 | 648 | 0.8850 |

| Bottom | Config | Params | Test acc |
|---|---|---|---|
| 1 | L2P1 | 18 | 0.5617 |
| 2 | L1P1 | 9 | 0.5633 |
| 3 | L3P1 | 27 | 0.5933 |
| 3 | L1P2 | 18 | 0.5933 |
| 5 | L1P4 | 36 | 0.6200 |

**Summary statistics:** original 7×7 region — max 0.8950, mean 0.7642; extended frontier
(L > 7 or P > 7) — max 0.8983, mean 0.8257. Spearman ρ(params, acc) = 0.734 (p = 3.5e-18).
98/100 cells converged via early stopping (mean stopped epoch 379).
