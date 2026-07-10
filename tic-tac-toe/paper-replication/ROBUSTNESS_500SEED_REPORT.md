# 500-Seed Robustness Report — cemoid L=3, P=2 (Experiment 1)

**Question:** When the cemoid (L=3, P=2) tic-tac-toe classifier is trained **to
convergence** from many random parameter initialisations, is the resulting
distribution of test accuracy **unimodal (a single peak)**? This sharpens the
50-seed study to a high-resolution null-hypothesis test: *the count-vs-accuracy
histogram has exactly one peak.*

**Headline result:** Across **500 independent seeds**, converged test accuracy is
**0.698 ± 0.042** (mean ± sample std), median 0.700, range 0.555–0.795. All 500
runs converged via validation-loss early stopping. The distribution is
**unambiguously unimodal**: Hartigan's dip test does not reject unimodality
(**dip = 0.018, p = 0.34**), the shape is statistically indistinguishable from a
normal (**Shapiro–Wilk W = 0.995, p = 0.071**; skew −0.17, excess kurtosis −0.27),
and the single KDE peak is robust across bandwidths. **The single-peak null
hypothesis stands.**

---

## 1. Methodology

### 1.1 Data source

Generated programmatically from the rules of tic-tac-toe (`initial_program.py`):

- **Board enumeration.** `enumerate_valid_boards()` depth-first expands all legal
  play sequences (cross first), recording unique states; recursion stops at a win
  or a full board. → **5,478 unique legal boards**.
- **Labels (3 classes)** via `board_label()`: `cross` / `circle` / `draw`. Natural
  distribution — cross 626, circle 316, draw 4,536.
- **Encoding.** Length-9 vector, +1/−1/0 per cell; value *i* → qubit *i* via RX
  scaled by `FEATURE_SCALE = 2π/3`.
- **Label vectors.** ±1 one-hot: cross `[+1,−1,−1]`, circle `[−1,+1,−1]`, draw `[−1,−1,+1]`.

### 1.2 Train / validation / test splits

`build_data_splits(seed=2027)` draws three **class-balanced** splits via
`default_rng(2027)`:

| Split | Size | Per class | Purpose |
|---|---:|---:|---|
| Train | 450 | 150 | gradient updates |
| Validation | 300 | 100 | early-stopping signal + model selection |
| Test | 600 | 200 | held-out reporting only |

**Data seed fixed at 2027 for all 500 runs** — every seed trains on the *same*
data; only the model's initial parameters differ (this isolates initialisation
sensitivity). Because `circle` has only 316 unique boards, sampling is with
replacement to preserve balanced sizes.

### 1.3 Model

cemoid ansatz at **L = 3, P = 2**: 9 qubits; each layer = RX feature-map + 2 cemoid
blocks; each block carries 9 shared trainable params (corner/edge/center RX+RZ and
3 CRY couplings); total **3 × 2 × 9 = 54 trainable parameters**. Readout = 9 PauliZ
expectations → [cross, circle, draw], argmax = prediction. PennyLane `default.qubit`,
exact (`shots=None`), `diff_method="backprop"`.

**Initialisation (the only thing that varies):** for seed *s*, parameters are drawn
`default_rng(s).uniform(-0.05, 0.05, size=(6, 9))` — a small-angle near-identity
start. Seeds 0–499.

### 1.4 Training protocol & stopping criteria

- **Optimiser:** Adam, learning rate 0.03.
- **Epoch:** 30 minibatch steps, batch size 15 (train reshuffled each epoch).
- **Loss:** MSE between the 3-vector prediction and the ±1 target.
- **Validation-loss early stopping, restore-best-weights:** evaluate validation L2
  loss each epoch; improvement requires beating the best by ≥ `min_delta = 1e-4`;
  stop after `patience = 75` epochs without improvement; hard cap
  `max_epochs = 1000`; soft walltime cap ≈ 23.3 h; final model = parameters at the
  lowest-validation-loss epoch.
- **Reported metric:** `final_test_accuracy` = test accuracy at the restored
  best-validation epoch. The test set drives no training/stopping decision.

### 1.5 Compute

**500-task SLURM array** (one seed per task), Yale Bouchet HPC (`day` partition,
8 CPUs / 12 GB per task), conda env `qml-ea` (PennyLane 0.45), throttle `%200`.
**SLURM job `16420732`.**

---

## 2. Results

### 2.1 Summary statistics (n = 500)

| Metric | Value |
|---|---|
| Mean test accuracy | **0.698** |
| Std (sample) | 0.042 |
| Median | 0.700 |
| IQR (Q1–Q3) | 0.670 – 0.728 |
| Min / Max | 0.555 / 0.795 |
| Range | 0.240 |
| Best seed | seed 75 → 0.795 (best epoch 222) |
| Worst seed | seed 56 → 0.555 (best epoch 94) |
| Fraction ≥ 0.65 | 86.2% |
| Fraction ≥ 0.70 | 50.6% |
| Fraction ≥ 0.75 | 11.2% |
| Converged via early stopping | **500 / 500 (100%)** |

Random-guess accuracy for a balanced 3-class task is ≈ 0.333, so all 500 runs sit
far above chance. Trained to convergence, the model reliably reaches the **0.67–0.73**
band; the spread is tight (std 0.042) with thin symmetric tails.

### 2.2 Unimodality assessment (the null hypothesis test)

The null hypothesis is **one peak** in the count-vs-accuracy distribution. Three
independent lines of evidence all support it:

| Test | Statistic | p-value | Interpretation |
|---|---|---|---|
| **Hartigan dip test** | dip = 0.018 | **p = 0.34** | Fail to reject unimodality — no evidence of a second mode |
| **Shapiro–Wilk** (normal ⇒ unimodal) | W = 0.995 | p = 0.071 | Fail to reject normality at α = 0.05 — shape is essentially Gaussian |
| **Shape moments** | skew = −0.17, excess kurtosis = −0.27 | — | Near-symmetric, very slightly light-tailed; no second hump |
| **KDE mode count** | 1 dominant peak | — | Bandwidth-robust (see below) |

**On the KDE:** at the default Scott bandwidth the kernel density shows one large
peak plus a spurious micro-wiggle of **0.8% relative prominence** in the lower tail;
at Silverman's bandwidth and at 1.5×/2× Scott it collapses to **exactly one peak**.
A genuine second mode would persist (and grow more separated) under mild smoothing —
this one vanishes, so it is sampling noise, not structure.

**Conclusion:** the 500-seed distribution is **unimodal**. The earlier 50-seed
histogram already *looked* single-peaked; at 10× resolution the single peak is now
backed by a formal dip test (p = 0.34) and near-perfect normality.

### 2.3 Convergence behaviour (n = 500)

| Metric | Value |
|---|---|
| Best-validation epoch — mean / median | 177.4 / 154.5 |
| Best-validation epoch — min / max | 31 / 554 |
| Stopped epoch — mean / median | 252.4 / 229.5 |
| Stopped epoch — min / max | 106 / 629 |

Median convergence at epoch ~155 (max 554) again confirms the old fixed-100-epoch
cutoff truncated most runs before their best validation point.

### 2.4 Figure

![500-seed robustness — distribution, KDE robustness, Q–Q](robustness_500seed_distribution.png)

- **Left:** count-vs-accuracy histogram (n = 500) with KDE overlay. A single clean
  peak at ~0.70; dip p = 0.34 and Shapiro p = 0.07 annotated.
- **Middle:** KDE at three bandwidths (Scott, 1.5×, 2×) — the single dominant peak
  is bandwidth-robust; no second mode emerges under smoothing.
- **Right:** normal Q–Q plot — points track the diagonal closely across the bulk
  (skew −0.17, excess kurtosis −0.27), with only mild flattening in the extreme tails.

### 2.5 Relation to the 50-seed study

| Protocol | n | Mean | Std | Median | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| 50-seed (converged) | 50 | 0.704 | 0.042 | 0.706 | 0.600 | 0.787 |
| **500-seed (converged)** | 500 | **0.698** | **0.042** | 0.700 | 0.555 | 0.795 |

The 500-seed mean (0.698) sits within sampling error of the 50-seed mean (0.704),
with identical std (0.042). The larger sample mainly **fills in the tails** (new
min 0.555, new max 0.795) and converts the qualitative "looks single-peaked"
observation into a quantitative, test-backed conclusion.

---

## 3. Conclusions

1. **The single-peak null hypothesis holds.** With 500 seeds, Hartigan's dip test
   (p = 0.34) and Shapiro–Wilk (p = 0.071) both fail to reject unimodality/normality,
   and the lone KDE peak is bandwidth-robust. There is **one peak**, centred at
   ≈ 0.70 — no evidence of distinct "good-init" vs "bad-init" sub-populations.

2. **The cemoid L=3, P=2 classifier is robust to initialisation.** All 500/500
   seeds converge to 0.555–0.795 (mean 0.698 ± 0.042), far above the 0.333 chance
   level; 86% reach ≥ 0.65 and half reach ≥ 0.70. Outcome variance is driven by a
   smooth, near-Gaussian spread of luck, not by a bimodal success/failure split.

3. **Validation-driven early stopping remains the right protocol.** 500/500 runs
   converged without hitting the epoch cap; median best-epoch ~155 again shows the
   old fixed-100 protocol under-trained.

---

## 4. Reproducibility

| Item | Path / value |
|---|---|
| Per-seed converged results | `robustness_histories/seed_000.json … seed_499.json` (500 files) |
| Analysis + unimodality script | `unimodality.py` (uses `diptest`); `analyze_results.py` (`analyze_rob500`) |
| Unimodality statistics | `unimodality_stats.json` |
| Figure | `robustness_500seed_distribution.png` |
| Training/evaluation code | `sweep.py` (`train_model`) |
| Seed-sweep driver | `seed_robustness.py` |
| Dataset construction | `initial_program.py` (`enumerate_valid_boards`, `build_data_splits`) |
| Cluster job | SLURM array `16420732` (Bouchet, `qml-ea` env, `day` partition, `%200`) |
| Early stopping | monitor = validation L2 loss, patience = 75, min_delta = 1e-4, max_epochs = 1000, restore_best_weights = True |
| Data seed (fixed) | 2027 · splits train/val/test = 450 / 300 / 600 (class-balanced, with replacement) |
| Init per seed *s* | `default_rng(s).uniform(-0.05, 0.05, size=(6, 9))`, seeds 0–499 |
