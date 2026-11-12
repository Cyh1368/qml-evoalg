# Corrected results summary (auto-compiled; do not hand-edit numbers)

Endpoints follow `research/REVISED_PROTOCOL.md` section 0. Development risk is **not** held-out risk: the validation split is used by candidate selection, by the search feedback loop and by the verifier.

Inference conventions: `research/core/paired.py` (percentile bootstrap over *units*, null-centred bootstrap p, sign-flip p with its symmetry assumption stated, p floors reported, Holm within declared families, equivalence only against a prespecified margin).

## WP-REPAIR v1 record, recomputed with correct replication units

- input: `research/experiments/repair/repair_v1_reanalysis.json`  units rule: REVISED_PROTOCOL sections 1-4
- units per eta (rows vs units after collapsing exact repeats): {"0.0": {"rows": 72, "units": 8}, "0.5": {"rows": 72, "units": 24}, "1.0": {"rows": 72, "units": 24}}

Headline columns use the **primary estimand** of Addendum A5.1: at `eta = 0` the 24 optimiser seeds; at `eta > 0` the 24 seed vectors after averaging the 8 frozen breaking directions within each seed (E-A). The cell-level interval is listed separately as sensitivity E-D.

| eta | steps | contrast | rows | units (estimand) | mean diff (a-b) | 95% CI (primary) | frac a better | p_shift-boot | p_signflip | p_holm | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 200 | repaired vs control | 24 | 8 (E-0: optimiser seeds, direction-free target) | -0.00093 | [-0.00217, -0.00002] | 0.62 | 0.0832 | 0.125 | 0.166 | difference not detected after multiplicity adjustment (adjusted p > 0.05; raw CI excludes 0 but is not a protocol verdict) |
| 0.0 | 200 | repaired vs original | 24 | 8 (E-0: optimiser seeds, direction-free target) | -0.00201 | [-0.00394, -0.00021] | 0.88 | 0.03435 | 0.125 | 0.103 | difference not detected after multiplicity adjustment (adjusted p > 0.05; raw CI excludes 0 but is not a protocol verdict) |
| 0.0 | 200 | control vs original | 24 | 8 (E-0: optimiser seeds, direction-free target) | -0.00107 | [-0.00277, +0.00041] | 0.62 | 0.1912 | 0.3203 | 0.191 | difference not detected (CI includes 0; NOT evidence of no effect) |
| 0.5 | 200 | repaired vs control | 24 | 8 (E-A) | +0.01817 | [+0.01402, +0.02214] | 0.17 | 5e-05 (floor < 5e-05) | 1.5e-05 | 0.00015 | a worse (raw CI excludes 0 on the positive side) |
| 0.5 | 200 | repaired vs original | 24 | 8 (E-A) | +0.01690 | [+0.01260, +0.02118] | 0.17 | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | 0.00015 | a worse (raw CI excludes 0 on the positive side) |
| 0.5 | 200 | control vs original | 24 | 8 (E-A) | -0.00127 | [-0.00541, +0.00295] | 0.46 | 0.5488 | 0.5636 | 0.554 | difference not detected (CI includes 0; NOT evidence of no effect) |
| 1.0 | 200 | repaired vs control | 24 | 8 (E-A) | +0.04523 | [+0.03458, +0.05538] | 0.04 | 5e-05 (floor < 5e-05) | 1e-05 | 0.00015 | a worse (raw CI excludes 0 on the positive side) |
| 1.0 | 200 | repaired vs original | 24 | 8 (E-A) | +0.04319 | [+0.03425, +0.05184] | 0.00 | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | 0.00015 | a worse (raw CI excludes 0 on the positive side) |
| 1.0 | 200 | control vs original | 24 | 8 (E-A) | -0.00204 | [-0.01327, +0.00868] | 0.42 | 0.7211 | 0.7294 | 0.721 | difference not detected (CI includes 0; NOT evidence of no effect) |

### Estimand sensitivity at eta > 0 (A5.1)

| eta | contrast | E-A seeds (primary) | E-B directions | E-C crossed | E-D cells (legacy) | direction-specific means |
|---|---|---|---|---|---|---|
| 0.5 | repaired vs control | [+0.01402, +0.02214] | [+0.01042, +0.02414] | [+0.00898, +0.02601] | [+0.01317, +0.02305] | +0.01042 … +0.02414 |
| 0.5 | repaired vs original | [+0.01260, +0.02118] | [+0.01212, +0.02136] | [+0.00959, +0.02381] | [+0.01250, +0.02112] | +0.01212 … +0.02136 |
| 0.5 | control vs original | [-0.00541, +0.00295] | [-0.00691, +0.00170] | [-0.00831, +0.00555] | [-0.00546, +0.00289] | -0.00691 … +0.00170 |
| 1.0 | repaired vs control | [+0.03458, +0.05538] | [+0.02589, +0.06036] | [+0.02146, +0.06461] | [+0.03225, +0.05773] | +0.02589 … +0.06036 |
| 1.0 | repaired vs original | [+0.03425, +0.05184] | [+0.03126, +0.05595] | [+0.02691, +0.05805] | [+0.03491, +0.05130] | +0.03126 … +0.05595 |
| 1.0 | control vs original | [-0.01327, +0.00868] | [-0.00709, +0.00536] | [-0.01825, +0.01281] | [-0.01346, +0.00903] | -0.00709 … +0.00536 |

*All four intervals condition on one dataset and one task family; none quantifies newly sampled training datasets or task families.*

### Floor accounting (population / MC / exact finite-orbit)

| eta | arm | units | dev risk | floor (rep MC) | floor (exact orbit) | orb risk | orb risk after projection | excess over orbit floor | excess over rep-MC floor | channel residual |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | control | 8 | 0.01404 | 0.00000 | n/a | n/a | n/a | n/a | +0.01404 | 7.32e-01 |
| 0.0 | original | 8 | 0.01511 | 0.00000 | n/a | n/a | n/a | n/a | +0.01511 | 5.61e-01 |
| 0.0 | repaired | 8 | 0.01311 | 0.00000 | n/a | n/a | n/a | n/a | +0.01311 | 8.65e-16 |
| 0.5 | control | 24 | 0.23715 | 0.23710 | n/a | n/a | n/a | n/a | +0.00005 | 7.75e-01 |
| 0.5 | original | 24 | 0.23842 | 0.23710 | n/a | n/a | n/a | n/a | +0.00132 | 7.58e-01 |
| 0.5 | repaired | 24 | 0.25532 | 0.23710 | n/a | n/a | n/a | n/a | +0.01822 | 6.56e-16 |
| 1.0 | control | 24 | 0.92591 | 0.94838 | n/a | n/a | n/a | n/a | -0.02247 | 7.52e-01 |
| 1.0 | original | 24 | 0.92796 | 0.94838 | n/a | n/a | n/a | n/a | -0.02042 | 7.57e-01 |
| 1.0 | repaired | 24 | 0.97114 | 0.94838 | n/a | n/a | n/a | n/a | +0.02276 | 1.38e-15 |

### E-R1 function-space contrast (same fitted predictor)

| eta | arm | units | R_orb(f) - R_orb(P f) | E[(f-P f)^2] | cross term | no-cross-term gap | full A3 gap |
|---|---|---|---|---|---|---|---|

## WP-REPAIR-2 (corrected design)

- input: `research/experiments/repair/repair2_analysis.json`  units rule: REVISED_PROTOCOL sections 1-4
- units per eta (rows vs units after collapsing exact repeats): {"0.0": {"rows": 120, "units": 24}, "0.5": {"rows": 960, "units": 192}, "1.0": {"rows": 960, "units": 192}}

Headline columns use the **primary estimand** of Addendum A5.1: at `eta = 0` the 24 optimiser seeds; at `eta > 0` the 24 seed vectors after averaging the 8 frozen breaking directions within each seed (E-A). The cell-level interval is listed separately as sensitivity E-D.

| eta | steps | contrast | rows | units (estimand) | mean diff (a-b) | 95% CI (primary) | frac a better | p_shift-boot | p_signflip | p_holm | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 200 | repaired vs control_dup | 24 | 24 (E-0: optimiser seeds, direction-free target) | -0.00060 | [-0.00135, +0.00019] | 0.75 | 0.1229 | 0.1495 | 0.246 | difference not detected (CI includes 0; NOT evidence of no effect) |
| 0.0 | 200 | repaired vs control_rand | 24 | 24 (E-0: optimiser seeds, direction-free target) | -0.00171 | [-0.00276, -0.00080] | 0.88 | 0.00115 | 0.000375 | 0.00575 | a better (raw CI excludes 0 on the negative side) |
| 0.0 | 200 | repaired vs original | 24 | 24 (E-0: optimiser seeds, direction-free target) | -0.00134 | [-0.00237, -0.00031] | 0.79 | 0.01075 | 0.01811 | 0.043 | a better (raw CI excludes 0 on the negative side) |
| 0.0 | 200 | control_dup vs original | 24 | 24 (E-0: optimiser seeds, direction-free target) | -0.00074 | [-0.00166, +0.00002] | 0.46 | 0.08195 | 0.133 | 0.246 | difference not detected (CI includes 0; NOT evidence of no effect) |
| 0.0 | 200 | control_matched vs original | 24 | 24 (E-0: optimiser seeds, direction-free target) | +0.00003 | [-0.00033, +0.00053] | 0.46 | 0.875 | 0.9374 | 0.875 | difference not detected (CI includes 0; NOT evidence of no effect) |
| 0.5 | 200 | repaired vs control_dup | 192 | 24 (E-A) | +0.01142 | [+0.00887, +0.01394] | 0.23 | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | 0.00025 | a worse (raw CI excludes 0 on the positive side) |
| 0.5 | 200 | repaired vs control_rand | 192 | 24 (E-A) | +0.00935 | [+0.00642, +0.01234] | 0.30 | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | 0.00025 | a worse (raw CI excludes 0 on the positive side) |
| 0.5 | 200 | repaired vs original | 192 | 24 (E-A) | +0.00879 | [+0.00682, +0.01066] | 0.30 | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | 0.00025 | a worse (raw CI excludes 0 on the positive side) |
| 0.5 | 200 | control_dup vs original | 192 | 24 (E-A) | -0.00263 | [-0.00465, -0.00054] | 0.61 | 0.0083 | 0.008065 | 0.0277 | a better (raw CI excludes 0 on the negative side) |
| 0.5 | 200 | control_matched vs original | 192 | 24 (E-A) | -0.00043 | [-0.00116, +0.00025] | 0.49 | 0.2759 | 0.2953 | 0.226 | difference not detected (CI includes 0; NOT evidence of no effect) |
| 1.0 | 200 | repaired vs control_dup | 192 | 24 (E-A) | +0.03605 | [+0.02998, +0.04210] | 0.15 | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | 0.00025 | a worse (raw CI excludes 0 on the positive side) |
| 1.0 | 200 | repaired vs control_rand | 192 | 24 (E-A) | +0.02797 | [+0.01974, +0.03644] | 0.19 | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | 0.00025 | a worse (raw CI excludes 0 on the positive side) |
| 1.0 | 200 | repaired vs original | 192 | 24 (E-A) | +0.02526 | [+0.02039, +0.02995] | 0.18 | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | 0.00025 | a worse (raw CI excludes 0 on the positive side) |
| 1.0 | 200 | control_dup vs original | 192 | 24 (E-A) | -0.01080 | [-0.01450, -0.00724] | 0.59 | 5e-05 (floor < 5e-05) | 2e-05 | 0.00025 | a better (raw CI excludes 0 on the negative side) |
| 1.0 | 200 | control_matched vs original | 192 | 24 (E-A) | -0.00234 | [-0.00435, -0.00051] | 0.48 | 0.02055 | 0.02048 | 0.0169 | a better (raw CI excludes 0 on the negative side) |

### Estimand sensitivity at eta > 0 (A5.1)

| eta | contrast | E-A seeds (primary) | E-B directions | E-C crossed | E-D cells (legacy) | direction-specific means |
|---|---|---|---|---|---|---|
| 0.5 | repaired vs control_dup | [+0.00887, +0.01394] | [+0.00869, +0.01443] | [+0.00743, +0.01567] | [+0.00958, +0.01329] | +0.00622 … +0.01936 |
| 0.5 | repaired vs control_rand | [+0.00642, +0.01234] | [+0.00547, +0.01433] | [+0.00456, +0.01551] | [+0.00746, +0.01129] | +0.00223 … +0.02420 |
| 0.5 | repaired vs original | [+0.00682, +0.01066] | [+0.00403, +0.01391] | [+0.00358, +0.01451] | [+0.00719, +0.01043] | -0.00061 … +0.02123 |
| 0.5 | control_dup vs original | [-0.00465, -0.00054] | [-0.00570, +0.00068] | [-0.00681, +0.00166] | [-0.00457, -0.00069] | -0.01009 … +0.00617 |
| 0.5 | control_matched vs original | [-0.00116, +0.00025] | [-0.00140, +0.00053] | [-0.00196, +0.00089] | [-0.00124, +0.00032] | -0.00234 … +0.00180 |
| 1.0 | repaired vs control_dup | [+0.02998, +0.04210] | [+0.02610, +0.04597] | [+0.02366, +0.04828] | [+0.03134, +0.04087] | +0.01579 … +0.05443 |
| 1.0 | repaired vs control_rand | [+0.01974, +0.03644] | [+0.01755, +0.04057] | [+0.01523, +0.04410] | [+0.02296, +0.03316] | +0.00947 … +0.06426 |
| 1.0 | repaired vs original | [+0.02039, +0.02995] | [+0.01360, +0.03769] | [+0.01262, +0.03911] | [+0.02135, +0.02920] | +0.00381 … +0.05764 |
| 1.0 | control_dup vs original | [-0.01450, -0.00724] | [-0.01695, -0.00430] | [-0.01942, -0.00224] | [-0.01545, -0.00620] | -0.02388 … +0.00372 |
| 1.0 | control_matched vs original | [-0.00435, -0.00051] | [-0.00408, -0.00065] | [-0.00570, +0.00065] | [-0.00439, -0.00043] | -0.00613 … +0.00116 |

*All four intervals condition on one dataset and one task family; none quantifies newly sampled training datasets or task families.*

### Floor accounting (population / MC / exact finite-orbit)

| eta | arm | units | dev risk | floor (rep MC) | floor (exact orbit) | orb risk | orb risk after projection | excess over orbit floor | excess over rep-MC floor | channel residual |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | control_dup | 24 | 0.01397 | 0.00000 | 0.00000 | 0.01399 | 0.01395 | +0.01399 | +0.01397 | 6.41e-01 |
| 0.0 | control_matched | 24 | 0.01475 | 0.00000 | 0.00000 | 0.01477 | 0.01459 | +0.01477 | +0.01475 | 6.19e-01 |
| 0.0 | control_rand | 24 | 0.01508 | 0.00000 | 0.00000 | 0.01509 | 0.01499 | +0.01509 | +0.01508 | 5.77e-01 |
| 0.0 | original | 24 | 0.01471 | 0.00000 | 0.00000 | 0.01473 | 0.01460 | +0.01473 | +0.01471 | 5.73e-01 |
| 0.0 | repaired | 24 | 0.01337 | 0.00000 | 0.00000 | 0.01337 | 0.01337 | +0.01337 | +0.01337 | 1.26e-15 |
| 0.5 | control_dup | 192 | 0.23900 | 0.23613 | 0.24021 | 0.24289 | 0.26105 | +0.00268 | +0.00287 | 7.51e-01 |
| 0.5 | control_matched | 192 | 0.24121 | 0.23613 | 0.24021 | 0.24561 | 0.25953 | +0.00540 | +0.00507 | 7.02e-01 |
| 0.5 | control_rand | 192 | 0.24107 | 0.23613 | 0.24021 | 0.24670 | 0.26046 | +0.00649 | +0.00494 | 6.41e-01 |
| 0.5 | original | 192 | 0.24164 | 0.23613 | 0.24021 | 0.24612 | 0.25921 | +0.00591 | +0.00550 | 6.83e-01 |
| 0.5 | repaired | 192 | 0.25042 | 0.23613 | 0.24021 | 0.25587 | 0.25587 | +0.01565 | +0.01429 | 9.88e-16 |
| 1.0 | control_dup | 192 | 0.92486 | 0.94453 | 0.96085 | 0.94043 | 0.98741 | -0.02042 | -0.01967 | 7.68e-01 |
| 1.0 | control_matched | 192 | 0.93332 | 0.94453 | 0.96085 | 0.95003 | 0.98521 | -0.01082 | -0.01121 | 7.32e-01 |
| 1.0 | control_rand | 192 | 0.93294 | 0.94453 | 0.96085 | 0.95224 | 0.98612 | -0.00861 | -0.01159 | 6.68e-01 |
| 1.0 | original | 192 | 0.93566 | 0.94453 | 0.96085 | 0.95210 | 0.98484 | -0.00875 | -0.00887 | 7.07e-01 |
| 1.0 | repaired | 192 | 0.96091 | 0.94453 | 0.96085 | 0.98029 | 0.98029 | +0.01944 | +0.01638 | 1.21e-15 |

### E-R1 function-space contrast (same fitted predictor)

| eta | arm | units | R_orb(f) - R_orb(P f) | E[(f-P f)^2] | cross term | no-cross-term gap | full A3 gap |
|---|---|---|---|---|---|---|---|
| 0.0 | control_dup | 24 | +0.00004 | 0.000041 | +7.268e-22 | 5.0e-18 | 5.0e-18 |
| 0.0 | control_matched | 24 | +0.00018 | 0.000176 | +1.084e-21 | 4.7e-18 | 4.7e-18 |
| 0.0 | control_rand | 24 | +0.00010 | 0.000099 | -1.301e-22 | 5.5e-18 | 5.5e-18 |
| 0.0 | original | 24 | +0.00014 | 0.000139 | +8.637e-22 | 3.8e-18 | 3.8e-18 |
| 0.0 | repaired | 24 | -0.00000 | 0.000000 | -1.376e-36 | 3.5e-18 | 3.5e-18 |
| 0.5 | control_dup | 192 | -0.01815 | 0.001971 | +1.006e-02 | 9.1e-02 | 1.1e-16 |
| 0.5 | control_matched | 192 | -0.01392 | 0.001445 | +7.685e-03 | 6.8e-02 | 8.0e-17 |
| 0.5 | control_rand | 192 | -0.01376 | 0.001461 | +7.611e-03 | 9.5e-02 | 8.2e-17 |
| 0.5 | original | 192 | -0.01309 | 0.001370 | +7.228e-03 | 5.3e-02 | 1.0e-16 |
| 0.5 | repaired | 192 | +0.00000 | 0.000000 | +1.455e-20 | 1.1e-16 | 1.1e-16 |
| 1.0 | control_dup | 192 | -0.04698 | 0.002817 | +2.490e-02 | 2.0e-01 | 3.7e-16 |
| 1.0 | control_matched | 192 | -0.03518 | 0.001968 | +1.857e-02 | 1.6e-01 | 3.3e-16 |
| 1.0 | control_rand | 192 | -0.03388 | 0.002021 | +1.795e-02 | 2.1e-01 | 3.2e-16 |
| 1.0 | original | 192 | -0.03274 | 0.001799 | +1.727e-02 | 1.2e-01 | 3.1e-16 |
| 1.0 | repaired | 192 | +0.00000 | 0.000000 | +2.701e-20 | 3.3e-16 | 3.3e-16 |

### Optimiser-budget sensitivity

| eta | steps | contrast | units | mean diff | 95% CI | verdict |
|---|---|---|---|---|---|---|
| 0.0 | 600 | repaired vs control_dup | 6 | -0.00135 | [-0.00316, +0.00006] | difference not detected (CI includes 0; NOT evidence of no effect) |
| 0.0 | 600 | control_dup vs original | 6 | -0.00169 | [-0.00349, +0.00008] | difference not detected (CI includes 0; NOT evidence of no effect) |
| 0.5 | 600 | repaired vs control_dup | 12 | +0.01987 | [+0.01503, +0.02428] | a worse (raw CI excludes 0 on the positive side) |
| 0.5 | 600 | control_dup vs original | 12 | -0.00509 | [-0.01183, +0.00182] | difference not detected (CI includes 0; NOT evidence of no effect) |
| 1.0 | 600 | repaired vs control_dup | 12 | +0.05117 | [+0.03699, +0.06387] | a worse (raw CI excludes 0 on the positive side) |
| 1.0 | 600 | control_dup vs original | 12 | -0.00735 | [-0.01999, +0.00517] | difference not detected (CI includes 0; NOT evidence of no effect) |
| 0.0 | 1800 | repaired vs control_dup | 6 | -0.00111 | [-0.00288, +0.00014] | difference not detected (CI includes 0; NOT evidence of no effect) |
| 0.0 | 1800 | control_dup vs original | 6 | +0.00011 | [-0.00266, +0.00302] | difference not detected (CI includes 0; NOT evidence of no effect) |
| 0.5 | 1800 | repaired vs control_dup | 12 | +0.02202 | [+0.01654, +0.02714] | a worse (raw CI excludes 0 on the positive side) |
| 0.5 | 1800 | control_dup vs original | 12 | -0.00585 | [-0.01439, +0.00215] | difference not detected (CI includes 0; NOT evidence of no effect) |
| 1.0 | 1800 | repaired vs control_dup | 12 | +0.05659 | [+0.04337, +0.06778] | a worse (raw CI excludes 0 on the positive side) |
| 1.0 | 1800 | control_dup vs original | 12 | -0.00638 | [-0.01889, +0.00641] | difference not detected (CI includes 0; NOT evidence of no effect) |

## WP-SEARCH reanalysis (frozen 120-run record, development endpoints)

- runs 120; families graphs_n6, ring_n6; endpoint: **development risk** (validation split used by selection and feedback)

### E-S3 primary (verify - fitness)

| family | n | mean diff | 95% CI | p_shift-boot | p_signflip | p_holm (A) | margin | verdict |
|---|---|---|---|---|---|---|---|---|
| graphs_n6 | 12 | -0.01414 | [-0.05855, +0.02837] | 0.516 | 0.5312 | 0.516 | 0.03274 | difference not detected (CI includes 0; NOT evidence of no effect) |
| ring_n6 | 12 | +0.00058 | [-0.00024, +0.00140] | 0.1621 | 0.2061 | 0.324 | 0.00097 | difference not detected (CI includes 0; NOT evidence of no effect) |

### E-S1 inference-time Reynolds averaging on the frozen candidate

| family | coverage | n fired | mean diff (averaged - candidate) | 95% CI | p_shift-boot | p_signflip | verdict |
|---|---|---|---|---|---|---|---|
| graphs_n6 | {"n_runs": 12, "attempted (best candidate carried a hypothesis)": 7, "fired (label preservation passed and residual > tolerance)": 7} | 7 | -0.04862 | [-0.07083, -0.02839] | 5e-05 (floor < 5e-05) | 0.01562 | a better (CI excludes 0 on the negative side) |
| ring_n6 | {"n_runs": 12, "attempted (best candidate carried a hypothesis)": 4, "fired (label preservation passed and residual > tolerance)": 0} | 0 | n/a | n/a | 1 | 1 | no data |

### Secondary contrasts (candidate endpoint vs deployed endpoint)

| family | endpoint | contrast | n | mean diff | 95% CI | p_holm (D) |
|---|---|---|---|---|---|---|
| graphs_n6 | candidate | llm-verify-repair vs llm-verify | 12 | +0.00092 | [-0.01457, +0.02417] | 1 |
| graphs_n6 | deployed | llm-verify-repair vs llm-verify | 12 | -0.02744 | [-0.05401, +0.00519] | 0.614 |
| graphs_n6 | candidate | llm-fitness vs mutation-ea | 12 | +0.02642 | [-0.01772, +0.06524] | 1 |
| graphs_n6 | deployed | llm-fitness vs mutation-ea | 12 | +0.02642 | [-0.01772, +0.06524] | 1 |
| graphs_n6 | candidate | mutation-ea vs random | 12 | +0.00148 | [-0.01554, +0.02098] | 1 |
| graphs_n6 | deployed | mutation-ea vs random | 12 | +0.00148 | [-0.01554, +0.02098] | 1 |
| graphs_n6 | candidate | llm-verify vs random | 12 | +0.01376 | [-0.02361, +0.05026] | 1 |
| graphs_n6 | deployed | llm-verify vs random | 12 | +0.01376 | [-0.02361, +0.05026] | 1 |
| graphs_n6 | candidate | llm-verify-repair vs llm-fitness | 12 | -0.01322 | [-0.06242, +0.03188] | 1 |
| graphs_n6 | deployed | llm-verify-repair vs llm-fitness | 12 | -0.04158 | [-0.08572, -0.00566] | 0.406 |
| ring_n6 | candidate | llm-verify-repair vs llm-verify | 12 | -0.00046 | [-0.00127, +0.00045] | 1 |
| ring_n6 | deployed | llm-verify-repair vs llm-verify | 12 | -0.00046 | [-0.00127, +0.00045] | 1 |
| ring_n6 | candidate | llm-fitness vs mutation-ea | 12 | -0.00371 | [-0.00423, -0.00326] | 0.0005 |
| ring_n6 | deployed | llm-fitness vs mutation-ea | 12 | -0.00371 | [-0.00423, -0.00326] | 0.0005 |
| ring_n6 | candidate | mutation-ea vs random | 12 | +0.00009 | [-0.00009, +0.00031] | 1 |
| ring_n6 | deployed | mutation-ea vs random | 12 | +0.00009 | [-0.00009, +0.00031] | 1 |
| ring_n6 | candidate | llm-verify vs random | 12 | -0.00304 | [-0.00390, -0.00215] | 0.0005 |
| ring_n6 | deployed | llm-verify vs random | 12 | -0.00304 | [-0.00390, -0.00215] | 0.0005 |
| ring_n6 | candidate | llm-verify-repair vs llm-fitness | 12 | +0.00013 | [-0.00050, +0.00080] | 1 |
| ring_n6 | deployed | llm-verify-repair vs llm-fitness | 12 | +0.00013 | [-0.00050, +0.00080] | 1 |

### E-S4 reliability (per arm, development record)

| family | arm | runs | invalid rate | hypothesis rate | tokens | wall s | mean dev risk |
|---|---|---|---|---|---|---|---|
| graphs_n6 | llm-fitness | 12 | 0.018 | 0.764 | 18480 | 796 | 0.56572 |
| graphs_n6 | llm-verify | 12 | 0.006 | 0.632 | 18868 | 400 | 0.55158 |
| graphs_n6 | llm-verify-repair | 12 | 0.018 | 0.681 | 19437 | 445 | 0.55250 |
| graphs_n6 | mutation-ea | 12 | 0.000 | 0.486 | 0 | 832 | 0.53930 |
| graphs_n6 | random | 12 | 0.000 | 0.479 | 0 | 794 | 0.53782 |
| ring_n6 | llm-fitness | 12 | 0.000 | 0.292 | 16425 | 583 | 0.00651 |
| ring_n6 | llm-verify | 12 | 0.006 | 0.535 | 17494 | 243 | 0.00709 |
| ring_n6 | llm-verify-repair | 12 | 0.000 | 0.507 | 17199 | 229 | 0.00664 |
| ring_n6 | mutation-ea | 12 | 0.000 | 0.451 | 0 | 580 | 0.01022 |
| ring_n6 | random | 12 | 0.000 | 0.479 | 0 | 521 | 0.01013 |

### E-S4 paired reliability contrasts (verify - fitness)

| family | metric | n | mean diff | 95% CI | p_shift-boot | verdict |
|---|---|---|---|---|---|---|
| graphs_n6 | invalid | 12 | -0.01190 | [-0.04304, +0.01282] | 0.4646 | difference not detected (CI includes 0; NOT evidence of no effect) |
| graphs_n6 | n_hypothesis | 12 | -0.13194 | [-0.18056, -0.08333] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| ring_n6 | invalid | 12 | +0.00641 | [+0.00000, +0.01923] | 0.4234 | difference not detected (CI includes 0; NOT evidence of no effect) |
| ring_n6 | n_hypothesis | 12 | +0.24306 | [+0.09722, +0.36111] | 0.00075 | b worse (CI excludes 0 on the positive side) |

## WP-DEV analyses (refit-verified, development endpoints)

- deterministic refit reproduced the logged dev risk exactly for 120/120 runs (max abs diff 1.73e-18)

### E-S5b declared-group twirl applied to every arm's selected predictor

| family | arm | n | mean diff (after - before) | 95% CI | p_shift-boot | verdict |
|---|---|---|---|---|---|---|
| graphs_n6 | llm-fitness | 12 | -0.06392 | [-0.08907, -0.04144] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| graphs_n6 | llm-verify | 12 | -0.07948 | [-0.10948, -0.05306] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| graphs_n6 | llm-verify-repair | 12 | -0.07869 | [-0.10460, -0.05235] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| graphs_n6 | mutation-ea | 12 | -0.08532 | [-0.12407, -0.05581] | 0.00025 | a better (CI excludes 0 on the negative side) |
| graphs_n6 | random | 12 | -0.11143 | [-0.14808, -0.07881] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| ring_n6 | llm-fitness | 12 | -0.00307 | [-0.00336, -0.00282] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| ring_n6 | llm-verify | 12 | -0.00326 | [-0.00365, -0.00291] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| ring_n6 | llm-verify-repair | 12 | -0.00308 | [-0.00347, -0.00271] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| ring_n6 | mutation-ea | 12 | -0.00390 | [-0.00443, -0.00339] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| ring_n6 | random | 12 | -0.00393 | [-0.00444, -0.00341] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |

### E-S6 matched-budget baselines

- constructive equivariant architecture, `graphs_n6`: channel residual 4.11e-15, mean dev risk 0.66724 over 12 seeds
- constructive equivariant architecture, `ring_n6`: channel residual 4.20e-15, mean dev risk 0.00055 over 12 seeds
- edge-count threshold rule, `graphs_n6` (target `connected`): threshold 6 fitted on train only, dev risk 0.35129, dev accuracy 0.9122
- best constant predictor, `graphs_n6`: dev risk 0.65667
- invariant oracle, `ring_n6`: dev risk 0.00000 (0 by construction)
- best constant predictor, `ring_n6`: dev risk 0.01951

### E-S6 arm selected predictor vs constructive equivariant baseline

| family | arm | n | mean diff (arm - constructive) | 95% CI | p_shift-boot | verdict |
|---|---|---|---|---|---|---|
| graphs_n6 | llm-fitness | 12 | -0.10152 | [-0.14456, -0.06974] | 0.0001 | a better (CI excludes 0 on the negative side) |
| graphs_n6 | llm-verify | 12 | -0.11566 | [-0.15704, -0.08022] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| graphs_n6 | llm-verify-repair | 12 | -0.11474 | [-0.15535, -0.08395] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| graphs_n6 | mutation-ea | 12 | -0.12794 | [-0.14798, -0.11108] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| graphs_n6 | random | 12 | -0.12943 | [-0.14807, -0.11205] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| ring_n6 | llm-fitness | 12 | +0.00596 | [+0.00548, +0.00640] | 5e-05 (floor < 5e-05) | b worse (CI excludes 0 on the positive side) |
| ring_n6 | llm-verify | 12 | +0.00655 | [+0.00573, +0.00737] | 5e-05 (floor < 5e-05) | b worse (CI excludes 0 on the positive side) |
| ring_n6 | llm-verify-repair | 12 | +0.00609 | [+0.00546, +0.00681] | 5e-05 (floor < 5e-05) | b worse (CI excludes 0 on the positive side) |
| ring_n6 | mutation-ea | 12 | +0.00967 | [+0.00908, +0.01034] | 5e-05 (floor < 5e-05) | b worse (CI excludes 0 on the positive side) |
| ring_n6 | random | 12 | +0.00959 | [+0.00903, +0.01017] | 5e-05 (floor < 5e-05) | b worse (CI excludes 0 on the positive side) |

### E-S4c verifier selectivity (wrong hypothesis group passing label preservation)

| family | arm | runs | proposals with hypothesis | group == task group | label-preserving | wrong group AND label-preserving |
|---|---|---|---|---|---|---|
| graphs_n6 | llm-fitness | 12 | 110 | 3 | 110 | 107 |
| graphs_n6 | llm-verify | 12 | 91 | 2 | 91 | 89 |
| graphs_n6 | llm-verify-repair | 12 | 98 | 5 | 98 | 93 |
| ring_n6 | llm-fitness | 12 | 42 | 0 | 0 | 0 |
| ring_n6 | llm-verify | 12 | 77 | 0 | 3 | 3 |
| ring_n6 | llm-verify-repair | 12 | 73 | 0 | 4 | 4 |

### E-S5 density (edge-count) band risks, graphs_n6 (mean over runs per arm)

| arm | band 0-5 (risk / n) | band 6-7 (risk / n) | band 8-9 (risk / n) | band 10-11 (risk / n) | band 12-15 (risk / n) |
|---|---|---|---|---|---|
| llm-fitness | 1.5225 / 1696 | 0.2721 / 1860 | 0.1520 / 2145 | 0.1990 / 516 | n/a |
| llm-verify | 1.4795 / 1696 | 0.2657 / 1860 | 0.1529 / 2145 | 0.1897 / 516 | n/a |
| llm-verify-repair | 1.4444 / 1696 | 0.2719 / 1860 | 0.1765 / 2145 | 0.1952 / 516 | n/a |
| mutation-ea | 1.3725 / 1696 | 0.2916 / 1860 | 0.1795 / 2145 | 0.1892 / 516 | n/a |
| random | 1.3750 / 1696 | 0.2867 / 1860 | 0.1759 / 2145 | 0.1957 / 516 | n/a |

### Nonconstant-output check (deployed predictor, dev rows)

| family | arm | runs | min pred std | frac nonconstant |
|---|---|---|---|---|
| graphs_n6 | llm-fitness | 12 | 0.1660 | 1.00 |
| graphs_n6 | llm-verify | 12 | 0.2036 | 1.00 |
| graphs_n6 | llm-verify-repair | 12 | 0.2036 | 1.00 |
| graphs_n6 | mutation-ea | 12 | 0.2630 | 1.00 |
| graphs_n6 | random | 12 | 0.2630 | 1.00 |
| ring_n6 | llm-fitness | 12 | 0.1110 | 1.00 |
| ring_n6 | llm-verify | 12 | 0.1102 | 1.00 |
| ring_n6 | llm-verify-repair | 12 | 0.1032 | 1.00 |
| ring_n6 | mutation-ea | 12 | 0.0893 | 1.00 |
| ring_n6 | random | 12 | 0.0893 | 1.00 |

## One-shot sealed / fresh holdout evaluation

- sealed digests unchanged across the evaluation: **True**; access record: `research/HOLDOUT_ACCESS.json`; started 2026-11-11T17:39:50.445346+00:00, finished 2026-11-11T18:01:38.656698+00:00

- **E-R4' supersedes the E-R4 table of the first one-shot run**, whose `eta > 0` rows scored every arm against a single invariant label (REVISED_PROTOCOL Addendum A4). Self-check: PASS (216 units compared, max |dev diff| 0.0); digests unchanged: True; access record: `research/HOLDOUT_ACCESS_v4.json`

### E-S7 sealed-test risk of the frozen candidates (candidate endpoint)

*Endpoint note: these are the refitted **candidates**. The deployed repaired predictor is measured separately (A5.5, `research/holdout_deployed.py`); `test_risk_averaged_diagnostic` was never computed in this run.*

| family | arm | n | mean dev risk | mean sealed-test risk |
|---|---|---|---|---|
| ring_n6 | llm-fitness | 12 | 0.00651 | 0.00639 |
| ring_n6 | llm-verify | 12 | 0.00709 | 0.00711 |
| ring_n6 | llm-verify-repair | 12 | 0.00664 | 0.00697 |
| ring_n6 | mutation-ea | 12 | 0.01022 | 0.01025 |
| ring_n6 | random | 12 | 0.01013 | 0.00995 |
| graphs_n6 | llm-fitness | 12 | 0.56572 | 0.51806 |
| graphs_n6 | llm-verify | 12 | 0.55158 | 0.49272 |
| graphs_n6 | llm-verify-repair | 12 | 0.55250 | 0.50674 |
| graphs_n6 | mutation-ea | 12 | 0.53930 | 0.49753 |
| graphs_n6 | random | 12 | 0.53782 | 0.48704 |

| family | contrast | pairs | mean diff | 95% CI | p_shift-boot | verdict |
|---|---|---|---|---|---|---|
| ring_n6 | llm-verify vs llm-fitness | 12 | +0.00072 | [-0.00039, +0.00186] | 0.2182 | difference not detected (CI includes 0; NOT evidence of no effect) |
| ring_n6 | llm-verify-repair vs llm-verify | 12 | -0.00014 | [-0.00148, +0.00123] | 0.8395 | difference not detected (CI includes 0; NOT evidence of no effect) |
| ring_n6 | llm-fitness vs mutation-ea | 12 | -0.00386 | [-0.00491, -0.00277] | 5e-05 (floor < 5e-05) | a better (CI excludes 0 on the negative side) |
| ring_n6 | llm-verify vs random | 12 | -0.00284 | [-0.00442, -0.00117] | 0.0004 | a better (CI excludes 0 on the negative side) |
| graphs_n6 | llm-verify vs llm-fitness | 12 | -0.02534 | [-0.11142, +0.05299] | 0.5362 | difference not detected (CI includes 0; NOT evidence of no effect) |
| graphs_n6 | llm-verify-repair vs llm-verify | 12 | +0.01401 | [-0.02964, +0.06451] | 0.5673 | difference not detected (CI includes 0; NOT evidence of no effect) |
| graphs_n6 | llm-fitness vs mutation-ea | 12 | +0.02053 | [-0.04866, +0.07697] | 0.5324 | difference not detected (CI includes 0; NOT evidence of no effect) |
| graphs_n6 | llm-verify vs random | 12 | +0.00568 | [-0.04052, +0.05050] | 0.8028 | difference not detected (CI includes 0; NOT evidence of no effect) |

### E-S7 paired against the `random` arm (regenerated from the stored per-run record; no new sealed read)

| family | arm | vs | pairs | mean diff | 95% CI | p_shift-boot | p_signflip | verdict |
|---|---|---|---|---|---|---|---|---|
| graphs_n6 | llm-fitness | random | 12 | +0.03102 | [-0.04167, +0.09514] | 0.369 | 0.4219 | difference not detected (CI includes 0; NOT evidence of no effect) |
| graphs_n6 | llm-verify | random | 12 | +0.00568 | [-0.04052, +0.05050] | 0.8028 | 0.8125 | difference not detected (CI includes 0; NOT evidence of no effect) |
| graphs_n6 | llm-verify-repair | random | 12 | +0.01970 | [-0.00448, +0.05037] | 0.1629 | 0.2344 | difference not detected (CI includes 0; NOT evidence of no effect) |
| graphs_n6 | mutation-ea | random | 12 | +0.01049 | [-0.01082, +0.03816] | 0.4141 | 0.4844 | difference not detected (CI includes 0; NOT evidence of no effect) |
| ring_n6 | llm-fitness | random | 12 | -0.00356 | [-0.00469, -0.00239] | 5e-05 (floor < 5e-05) | 0.0009766 | a better (raw CI excludes 0 on the negative side) |
| ring_n6 | llm-verify | random | 12 | -0.00284 | [-0.00442, -0.00117] | 0.0004 | 0.009277 | a better (raw CI excludes 0 on the negative side) |
| ring_n6 | llm-verify-repair | random | 12 | -0.00298 | [-0.00452, -0.00154] | 0.00015 | 0.00293 | a better (raw CI excludes 0 on the negative side) |
| ring_n6 | mutation-ea | random | 12 | +0.00030 | [-0.00009, +0.00090] | 0.2714 | 0.375 | difference not detected (CI includes 0; NOT evidence of no effect) |

### E-R4 repair arms on untouched data

| split | eta | contrast | units | mean diff | 95% CI | p_shift-boot | p_signflip | verdict |
|---|---|---|---|---|---|---|---|---|
| dev | 0.0 | repaired vs control_dup | 8 | -0.00083 | [-0.00225, +0.00024] | 0.185 | 0.2656 | difference not detected (CI includes 0; NOT evidence of no effect) |
| dev | 0.0 | repaired vs original | 8 | -0.00233 | [-0.00417, -0.00057] | 0.009 | 0.04688 | a better (CI excludes 0 on the negative side) |
| dev | 0.0 | control_dup vs original | 8 | -0.00150 | [-0.00351, +0.00024] | 0.1223 | 0.25 | difference not detected (CI includes 0; NOT evidence of no effect) |
| dev | 0.5 | repaired vs control_dup | 32 | +0.01757 | [+0.01326, +0.02180] | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | b worse (CI excludes 0 on the positive side) |
| dev | 0.5 | repaired vs original | 32 | +0.01265 | [+0.00875, +0.01658] | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | b worse (CI excludes 0 on the positive side) |
| dev | 0.5 | control_dup vs original | 32 | -0.00492 | [-0.00955, -0.00033] | 0.03645 | 0.04931 | a better (CI excludes 0 on the negative side) |
| dev | 1.0 | repaired vs control_dup | 32 | +0.05138 | [+0.04083, +0.06123] | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | b worse (CI excludes 0 on the positive side) |
| dev | 1.0 | repaired vs original | 32 | +0.03440 | [+0.02521, +0.04384] | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | b worse (CI excludes 0 on the positive side) |
| dev | 1.0 | control_dup vs original | 32 | -0.01697 | [-0.02978, -0.00450] | 0.0075 | 0.01453 | a better (CI excludes 0 on the negative side) |
| fresh_v4 | 0.0 | repaired vs control_dup | 8 | -0.00057 | [-0.00176, +0.00028] | 0.277 | 0.4844 | difference not detected (CI includes 0; NOT evidence of no effect) |
| fresh_v4 | 0.0 | repaired vs original | 8 | -0.00174 | [-0.00309, -0.00051] | 0.00595 | 0.04688 | a better (CI excludes 0 on the negative side) |
| fresh_v4 | 0.0 | control_dup vs original | 8 | -0.00117 | [-0.00279, +0.00015] | 0.1249 | 0.2734 | difference not detected (CI includes 0; NOT evidence of no effect) |
| fresh_v4 | 0.5 | repaired vs control_dup | 32 | +0.01551 | [+0.01106, +0.02011] | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | b worse (CI excludes 0 on the positive side) |
| fresh_v4 | 0.5 | repaired vs original | 32 | +0.01153 | [+0.00804, +0.01501] | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | b worse (CI excludes 0 on the positive side) |
| fresh_v4 | 0.5 | control_dup vs original | 32 | -0.00399 | [-0.00853, +0.00043] | 0.0817 | 0.09941 | difference not detected (CI includes 0; NOT evidence of no effect) |
| fresh_v4 | 1.0 | repaired vs control_dup | 32 | +0.04629 | [+0.03613, +0.05670] | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | b worse (CI excludes 0 on the positive side) |
| fresh_v4 | 1.0 | repaired vs original | 32 | +0.03067 | [+0.02227, +0.03906] | 5e-05 (floor < 5e-05) | 5e-06 (floor < 5e-06) | b worse (CI excludes 0 on the positive side) |
| fresh_v4 | 1.0 | control_dup vs original | 32 | -0.01561 | [-0.02814, -0.00358] | 0.01205 | 0.0203 | a better (CI excludes 0 on the negative side) |

### E-S7 search arms on the sealed test split

| family | arm | runs | mean dev risk | mean sealed-test risk |
|---|---|---|---|---|
| ring_n6 | llm-fitness | 12 | 0.00651 | 0.00639 |
| ring_n6 | llm-verify | 12 | 0.00709 | 0.00711 |
| ring_n6 | llm-verify-repair | 12 | 0.00664 | 0.00697 |
| ring_n6 | mutation-ea | 12 | 0.01022 | 0.01025 |
| ring_n6 | random | 12 | 0.01013 | 0.00995 |
| graphs_n6 | llm-fitness | 12 | 0.56572 | 0.51806 |
| graphs_n6 | llm-verify | 12 | 0.55158 | 0.49272 |
| graphs_n6 | llm-verify-repair | 12 | 0.55250 | 0.50674 |
| graphs_n6 | mutation-ea | 12 | 0.53930 | 0.49753 |
| graphs_n6 | random | 12 | 0.53782 | 0.48704 |

| family | contrast | n | mean diff | 95% CI | p_shift-boot | p_signflip | verdict |
|---|---|---|---|---|---|---|---|
| ring_n6 | llm-verify vs llm-fitness | 12 | +0.00072 | [-0.00039, +0.00186] | 0.2182 | 0.2622 | difference not detected (CI includes 0; NOT evidence of no effect) |
| ring_n6 | llm-verify-repair vs llm-verify | 12 | -0.00014 | [-0.00148, +0.00123] | 0.8395 | 0.8408 | difference not detected (CI includes 0; NOT evidence of no effect) |
| ring_n6 | llm-fitness vs mutation-ea | 12 | -0.00386 | [-0.00491, -0.00277] | 5e-05 (floor < 5e-05) | 0.0004883 | a better (CI excludes 0 on the negative side) |
| ring_n6 | llm-verify vs random | 12 | -0.00284 | [-0.00442, -0.00117] | 0.0004 | 0.009277 | a better (CI excludes 0 on the negative side) |
| graphs_n6 | llm-verify vs llm-fitness | 12 | -0.02534 | [-0.11142, +0.05299] | 0.5362 | 0.5625 | difference not detected (CI includes 0; NOT evidence of no effect) |
| graphs_n6 | llm-verify-repair vs llm-verify | 12 | +0.01401 | [-0.02964, +0.06451] | 0.5673 | 0.5312 | difference not detected (CI includes 0; NOT evidence of no effect) |
| graphs_n6 | llm-fitness vs mutation-ea | 12 | +0.02053 | [-0.04866, +0.07697] | 0.5324 | 0.5723 | difference not detected (CI includes 0; NOT evidence of no effect) |
| graphs_n6 | llm-verify vs random | 12 | +0.00568 | [-0.04052, +0.05050] | 0.8028 | 0.8125 | difference not detected (CI includes 0; NOT evidence of no effect) |

## Breaking-target selectivity test (protocol Addendum A1)

Family `ring_n6`, target `alpha_1` (the declared group is **not** a label symmetry here). Development risk on each run's own validation split. Declared prediction: if the verifier's benefit came from pushing toward the declared group, it must turn negative on this target.

| arm | runs | mean dev risk | accuracy | nonconstant | repair fired/attempted | hyp. | hyp. pass gate | hyp. = task group |
|---|---|---|---|---|---|---|---|---|
| llm-fitness | 12 | 0.04049 | 0.91181 | 12/12 | 0/0 | 56 | 0 | 0 |
| llm-verify | 12 | 0.03699 | 0.91632 | 12/12 | 0/0 | 73 | 4 | 0 |
| llm-verify-repair | 12 | 0.04106 | 0.91701 | 12/12 | 0/6 | 71 | 4 | 0 |
| mutation-ea | 12 | 0.04123 | 0.91528 | 12/12 | 0/0 | 79 | 0 | 0 |
| random | 12 | 0.04122 | 0.91215 | 12/12 | 0/0 | 69 | 0 | 0 |

| contrast | n | mean diff | 95% CI | p_shift-boot | p_signflip | p_holm (E) | verdict |
|---|---|---|---|---|---|---|---|
| llm-verify vs llm-fitness | 12 | -0.00350 | [-0.00963, +0.00198] | 0.2462 | 0.3594 | 0.7386 | difference not detected (CI includes 0; NOT evidence of no effect) |
| llm-verify-repair vs llm-verify | 12 | +0.00407 | [-0.00069, +0.00984] | 0.1338 | 0.2207 | 0.6692 | difference not detected (CI includes 0; NOT evidence of no effect) |
| llm-verify-repair vs llm-fitness | 12 | +0.00058 | [-0.00535, +0.00649] | 0.848 | 0.8613 | 1 | difference not detected (CI includes 0; NOT evidence of no effect) |
| mutation-ea vs random | 12 | +0.00001 | [-0.00280, +0.00311] | 0.9942 | 0.9844 | 1 | difference not detected (CI includes 0; NOT evidence of no effect) |
| llm-verify vs random | 12 | -0.00423 | [-0.01027, +0.00135] | 0.1545 | 0.2012 | 0.6692 | difference not detected (CI includes 0; NOT evidence of no effect) |

## Verifier semantics: what a label-preservation gate can decide (A5.2 / A5.3)

- probe: 512 rows, seed 777 (gate reads train rows[:64]; the probe excludes them)

### Measured label-symmetry groups (all n! permutations tested)

| family | target | label-symmetry order | hypothesis space |L|/|S_n| | contains declared group | = full symmetric |
|---|---|---|---|---|---|---|
| ring_n6 | alpha_0 | 12 | 720 | 0.0167 | True | False |
| ring_n6 | alpha_0.1 | 2 | 720 | 0.0028 | False | False |
| ring_n6 | alpha_0.25 | 2 | 720 | 0.0028 | False | False |
| ring_n6 | alpha_0.5 | 2 | 720 | 0.0028 | False | False |
| ring_n6 | alpha_1 | 2 | 720 | 0.0028 | False | False |
| ring_n6 | ALL_COLUMNS | 2 | 720 | 0.0028 | False | False |
| graphs_n6 | connected | 720 | 720 | 1.0000 | True | True |
| graphs_n6 | triangle | 720 | 720 | 1.0000 | True | True |
| graphs_n6 | ALL_COLUMNS | 720 | 720 | 1.0000 | True | True |

### Fixed-panel selectivity (identical inputs, target varied)

| family | target | gate variant | sensitivity | false-accept |
|---|---|---|---|---|
| ring_n6 | alpha_0 | implemented | 1/6 = 0.17 [0.030, 0.564] | 0/3 = 0.00 [0.000, 0.561] |
| ring_n6 | alpha_0 | target_specific | 1/6 = 0.17 [0.030, 0.564] | 0/3 = 0.00 [0.000, 0.561] |
| ring_n6 | alpha_0 | target_specific_tol | 6/6 = 1.00 [0.610, 1.000] | 0/3 = 0.00 [0.000, 0.561] |
| ring_n6 | alpha_0.1 | implemented | 1/2 = 0.50 [0.095, 0.905] | 0/7 = 0.00 [0.000, 0.354] |
| ring_n6 | alpha_0.1 | target_specific | 1/2 = 0.50 [0.095, 0.905] | 0/7 = 0.00 [0.000, 0.354] |
| ring_n6 | alpha_0.1 | target_specific_tol | 2/2 = 1.00 [0.342, 1.000] | 0/7 = 0.00 [0.000, 0.354] |
| ring_n6 | alpha_0.25 | implemented | 1/2 = 0.50 [0.095, 0.905] | 0/7 = 0.00 [0.000, 0.354] |
| ring_n6 | alpha_0.25 | target_specific | 1/2 = 0.50 [0.095, 0.905] | 0/7 = 0.00 [0.000, 0.354] |
| ring_n6 | alpha_0.25 | target_specific_tol | 2/2 = 1.00 [0.342, 1.000] | 0/7 = 0.00 [0.000, 0.354] |
| ring_n6 | alpha_0.5 | implemented | 1/2 = 0.50 [0.095, 0.905] | 0/7 = 0.00 [0.000, 0.354] |
| ring_n6 | alpha_0.5 | target_specific | 1/2 = 0.50 [0.095, 0.905] | 0/7 = 0.00 [0.000, 0.354] |
| ring_n6 | alpha_0.5 | target_specific_tol | 2/2 = 1.00 [0.342, 1.000] | 0/7 = 0.00 [0.000, 0.354] |
| ring_n6 | alpha_1 | implemented | 1/2 = 0.50 [0.095, 0.905] | 0/7 = 0.00 [0.000, 0.354] |
| ring_n6 | alpha_1 | target_specific | 1/2 = 0.50 [0.095, 0.905] | 0/7 = 0.00 [0.000, 0.354] |
| ring_n6 | alpha_1 | target_specific_tol | 2/2 = 1.00 [0.342, 1.000] | 0/7 = 0.00 [0.000, 0.354] |
| graphs_n6 | connected | implemented | 9/9 = 1.00 [0.701, 1.000] | 0/0 = n/a [n/a] |
| graphs_n6 | connected | target_specific | 9/9 = 1.00 [0.701, 1.000] | 0/0 = n/a [n/a] |
| graphs_n6 | connected | target_specific_tol | 9/9 = 1.00 [0.701, 1.000] | 0/0 = n/a [n/a] |
| graphs_n6 | triangle | implemented | 9/9 = 1.00 [0.701, 1.000] | 0/0 = n/a [n/a] |
| graphs_n6 | triangle | target_specific | 9/9 = 1.00 [0.701, 1.000] | 0/0 = n/a [n/a] |
| graphs_n6 | triangle | target_specific_tol | 9/9 = 1.00 [0.701, 1.000] | 0/0 = n/a [n/a] |

### Panel members: truth, gate decision under each variant, and margin

| family | target | member | closure order | sound on probe | accepted (implemented) | accepted (scored, tol 0) | accepted (scored, tol 1e-9) | gate margin (implemented) | worst violated fraction (probe) |
|---|---|---|---|---|---|---|---|---|---|
| graphs_n6 | connected | cyclic_rotation | 6 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | connected | dihedral_declared | 12 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | connected | full_symmetric | 720 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | connected | identity | 1 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | connected | random_permutations | 720 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | connected | reflection | 2 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | connected | rotation_subgroup_c2 | 2 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | connected | rotation_subgroup_c3 | 3 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | connected | single_transpositions | 720 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | triangle | cyclic_rotation | 6 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | triangle | dihedral_declared | 12 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | triangle | full_symmetric | 720 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | triangle | identity | 1 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | triangle | random_permutations | 720 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | triangle | reflection | 2 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | triangle | rotation_subgroup_c2 | 2 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | triangle | rotation_subgroup_c3 | 3 | True | True | True | True | 0.00000 | 0.00000 |
| graphs_n6 | triangle | single_transpositions | 720 | True | True | True | True | 0.00000 | 0.00000 |
| ring_n6 | alpha_0 | cyclic_rotation | 6 | True | False | False | True | 1.95018 | 0.00000 |
| ring_n6 | alpha_0 | dihedral_declared | 12 | True | False | False | True | 1.95018 | 0.00000 |
| ring_n6 | alpha_0 | full_symmetric | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_0 | identity | 1 | True | True | True | True | 0.00000 | 0.00000 |
| ring_n6 | alpha_0 | random_permutations | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_0 | reflection | 2 | True | False | False | True | 0.00000 | 0.00000 |
| ring_n6 | alpha_0 | rotation_subgroup_c2 | 2 | True | False | False | True | 1.93358 | 0.00000 |
| ring_n6 | alpha_0 | rotation_subgroup_c3 | 3 | True | False | False | True | 1.95018 | 0.00000 |
| ring_n6 | alpha_0 | single_transpositions | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_0.1 | cyclic_rotation | 6 | False | False | False | False | 1.95018 | 1.00000 |
| ring_n6 | alpha_0.1 | dihedral_declared | 12 | False | False | False | False | 1.95018 | 1.00000 |
| ring_n6 | alpha_0.1 | full_symmetric | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_0.1 | identity | 1 | True | True | True | True | 0.00000 | 0.00000 |
| ring_n6 | alpha_0.1 | random_permutations | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_0.1 | reflection | 2 | True | False | False | True | 0.00000 | 0.00000 |
| ring_n6 | alpha_0.1 | rotation_subgroup_c2 | 2 | False | False | False | False | 1.93358 | 1.00000 |
| ring_n6 | alpha_0.1 | rotation_subgroup_c3 | 3 | False | False | False | False | 1.95018 | 1.00000 |
| ring_n6 | alpha_0.1 | single_transpositions | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_0.25 | cyclic_rotation | 6 | False | False | False | False | 1.95018 | 1.00000 |
| ring_n6 | alpha_0.25 | dihedral_declared | 12 | False | False | False | False | 1.95018 | 1.00000 |
| ring_n6 | alpha_0.25 | full_symmetric | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_0.25 | identity | 1 | True | True | True | True | 0.00000 | 0.00000 |
| ring_n6 | alpha_0.25 | random_permutations | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_0.25 | reflection | 2 | True | False | False | True | 0.00000 | 0.00000 |
| ring_n6 | alpha_0.25 | rotation_subgroup_c2 | 2 | False | False | False | False | 1.93358 | 1.00000 |
| ring_n6 | alpha_0.25 | rotation_subgroup_c3 | 3 | False | False | False | False | 1.95018 | 1.00000 |
| ring_n6 | alpha_0.25 | single_transpositions | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_0.5 | cyclic_rotation | 6 | False | False | False | False | 1.95018 | 1.00000 |
| ring_n6 | alpha_0.5 | dihedral_declared | 12 | False | False | False | False | 1.95018 | 1.00000 |
| ring_n6 | alpha_0.5 | full_symmetric | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_0.5 | identity | 1 | True | True | True | True | 0.00000 | 0.00000 |
| ring_n6 | alpha_0.5 | random_permutations | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_0.5 | reflection | 2 | True | False | False | True | 0.00000 | 0.00000 |
| ring_n6 | alpha_0.5 | rotation_subgroup_c2 | 2 | False | False | False | False | 1.93358 | 1.00000 |
| ring_n6 | alpha_0.5 | rotation_subgroup_c3 | 3 | False | False | False | False | 1.95018 | 1.00000 |
| ring_n6 | alpha_0.5 | single_transpositions | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_1 | cyclic_rotation | 6 | False | False | False | False | 1.95018 | 1.00000 |
| ring_n6 | alpha_1 | dihedral_declared | 12 | False | False | False | False | 1.95018 | 1.00000 |
| ring_n6 | alpha_1 | full_symmetric | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_1 | identity | 1 | True | True | True | True | 0.00000 | 0.00000 |
| ring_n6 | alpha_1 | random_permutations | 720 | False | False | False | False | 2.66439 | 1.00000 |
| ring_n6 | alpha_1 | reflection | 2 | True | False | False | True | 0.00000 | 0.00000 |
| ring_n6 | alpha_1 | rotation_subgroup_c2 | 2 | False | False | False | False | 1.93358 | 1.00000 |
| ring_n6 | alpha_1 | rotation_subgroup_c3 | 3 | False | False | False | False | 1.95018 | 1.00000 |
| ring_n6 | alpha_1 | single_transpositions | 720 | False | False | False | False | 2.66439 | 1.00000 |

### Search-generated hypotheses: status and recorded gate decisions

| family | target | exact declared | valid proper subgroup | valid supergroup | sound non-comparable | invalid |
|---|---|---|---|---|---|---|
| graphs_n6 | connected | 10 | 289 | 0 | 0 | 0 |
| ring_n6 | alpha_0 | 0 | 120 | 0 | 0 | 72 |

| family | target | gate label-pass | of those invalid (false accepts) | gate label-fail | of those sound for the scored target |
|---|---|---|---|---|---|
| graphs_n6 | connected | 144 | 0 (0.00 [0.000, 0.026]) | 0 | 0 (n/a [n/a]) |
| ring_n6 | alpha_0 | 7 | 0 (0.00 [0.000, 0.354]) | 95 | 95 (1.00 [0.961, 1.000]) |

## Verification as a decision rule (A5.4)

### graphs_n6 — 60 candidates, MC-twirl share 1.00, verify 0.45s vs average 12.51s

Thresholds (development only): median 0.0854, q1 0.058, q3 0.128

| rule | fired | realised mean risk change | if always applied | precision | recall | harmed | missed beneficial (total gain) |
|---|---|---|---|---|---|---|---|
| R0_supplied_group | 60/60 | -0.08705 | -0.08705 | 60/60 [0.940, 1.000] | 60/60 [0.940, 1.000] | 0 | 0 (0.0000) |
| R1_label_gate | 60/60 | -0.08705 | -0.08705 | 60/60 [0.940, 1.000] | 60/60 [0.940, 1.000] | 0 | 0 (0.0000) |
| R2_deployed_gate | 60/60 | -0.08705 | -0.08705 | 60/60 [0.940, 1.000] | 60/60 [0.940, 1.000] | 0 | 0 (0.0000) |
| R2b_channel_below_tol | 0/60 | +0.00000 | -0.08705 | 0/0 [n/a] | 0/60 [0.000, 0.060] | 0 | 60 (5.2230) |
| R3_predictor_defect_median | 30/60 | -0.06024 | -0.08705 | 30/30 [0.886, 1.000] | 30/60 [0.377, 0.623] | 0 | 30 (1.6084) |
| R3_predictor_defect_q1 | 45/60 | -0.07544 | -0.08705 | 45/45 [0.921, 1.000] | 45/60 [0.628, 0.842] | 0 | 15 (0.6965) |
| R3_predictor_defect_q3 | 12/60 | -0.03434 | -0.08705 | 12/12 [0.758, 1.000] | 12/60 [0.118, 0.318] | 0 | 48 (3.1626) |

- **R4 mismatched-group control:** undefined on this family: no mismatched group exists: the scored target's label-symmetry group is the full symmetric group

| arm | n | mean delta (declared-group average) | mean predictor defect | channel above repair floor | repair fired in the run |
|---|---|---|---|---|---|
| llm-fitness | 12 | -0.07162 | 0.0759 | 12 | 0 |
| llm-verify | 12 | -0.08267 | 0.0916 | 12 | 0 |
| llm-verify-repair | 12 | -0.08181 | 0.0904 | 12 | 7 |
| mutation-ea | 12 | -0.09732 | 0.1018 | 12 | 0 |
| random | 12 | -0.10183 | 0.1129 | 12 | 0 |

### ring_n6 — 60 candidates, MC-twirl share 0.00, verify 0.01s vs average 0.18s

Thresholds (development only): median 0.00385, q1 0.00326, q3 0.0044

| rule | fired | realised mean risk change | if always applied | precision | recall | harmed | missed beneficial (total gain) |
|---|---|---|---|---|---|---|---|
| R0_supplied_group | 60/60 | -0.00345 | -0.00345 | 60/60 [0.940, 1.000] | 60/60 [0.940, 1.000] | 0 | 0 (0.0000) |
| R1_label_gate | 0/60 | +0.00000 | -0.00345 | 0/0 [n/a] | 0/60 [0.000, 0.060] | 0 | 60 (0.2068) |
| R2_deployed_gate | 0/60 | +0.00000 | -0.00345 | 0/0 [n/a] | 0/60 [0.000, 0.060] | 0 | 60 (0.2068) |
| R2b_channel_below_tol | 0/60 | +0.00000 | -0.00345 | 0/0 [n/a] | 0/60 [0.000, 0.060] | 0 | 60 (0.2068) |
| R3_predictor_defect_median | 30/60 | -0.00197 | -0.00345 | 30/30 [0.886, 1.000] | 30/60 [0.377, 0.623] | 0 | 30 (0.0884) |
| R3_predictor_defect_q1 | 45/60 | -0.00274 | -0.00345 | 45/45 [0.921, 1.000] | 45/60 [0.628, 0.842] | 0 | 15 (0.0421) |
| R3_predictor_defect_q3 | 14/60 | -0.00096 | -0.00345 | 14/14 [0.785, 1.000] | 14/60 [0.144, 0.354] | 0 | 46 (0.1490) |

- **R4 mismatched-group control:** mean risk change +0.00399 over 60 candidates

| arm | n | mean delta (declared-group average) | mean predictor defect | channel above repair floor | repair fired in the run |
|---|---|---|---|---|---|
| llm-fitness | 12 | -0.00307 | 0.0033 | 12 | 0 |
| llm-verify | 12 | -0.00326 | 0.0036 | 12 | 0 |
| llm-verify-repair | 12 | -0.00308 | 0.0035 | 12 | 0 |
| mutation-ea | 12 | -0.00390 | 0.0046 | 12 | 0 |
| random | 12 | -0.00393 | 0.0045 | 12 | 0 |

_(A5.5 deployed-endpoint evaluation not yet run)_
