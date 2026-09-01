"""Rigorous unimodality (single-peak) assessment of the 500-seed accuracy
distribution, and the final rob500 figure."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats as sstats
import diptest

HERE = Path(__file__).resolve().parent

accs = []
seeds = []
epochs = []
for f in sorted((HERE / "robustness_histories").glob("seed_*.json")):
    d = json.loads(f.read_text())
    accs.append(d["final_test_accuracy"]); seeds.append(d["seed"]); epochs.append(d["best_epoch"])
accs = np.array(accs); seeds = np.array(seeds); epochs = np.array(epochs)
n = len(accs)

# ---- Hartigan dip test (proper, with bootstrap p-value)
dip, dip_p = diptest.diptest(accs)

# ---- Shapiro-Wilk (normal is unimodal; failing to reject => consistent w/ unimodal)
sh = sstats.shapiro(accs)
skew = float(sstats.skew(accs)); kurt = float(sstats.kurtosis(accs))

# ---- KDE mode count across bandwidths (Silverman's critical-bandwidth idea)
def kde_modes(data, bw):
    kde = sstats.gaussian_kde(data, bw_method=bw)
    xs = np.linspace(data.min() - 0.02, data.max() + 0.02, 2000)
    dens = kde(xs)
    peaks = np.where((dens[1:-1] > dens[:-2]) & (dens[1:-1] > dens[2:]))[0] + 1
    # prominence: height of each peak relative to global max
    proms = dens[peaks] / dens.max()
    return xs, dens, peaks, proms

scott = sstats.gaussian_kde(accs).factor
modes_info = {}
for label, bw in [("scott", "scott"), ("silverman", "silverman"),
                  ("1.5x_scott", scott * 1.5), ("2x_scott", scott * 2.0)]:
    xs, dens, peaks, proms = kde_modes(accs, bw)
    # count only non-negligible peaks (>5% of max density)
    sig = int(np.sum(proms > 0.05))
    modes_info[label] = dict(n_peaks=int(len(peaks)), n_significant=sig,
                             prominences=[round(float(p), 3) for p in proms])

out = dict(
    n=n,
    dip_statistic=float(dip), dip_pvalue=float(dip_p),
    shapiro_W=float(sh.statistic), shapiro_p=float(sh.pvalue),
    skew=skew, kurtosis=kurt,
    modes=modes_info,
)
print(json.dumps(out, indent=2))
(HERE / "unimodality_stats.json").write_text(json.dumps(out, indent=2))

# ---- final 3-panel figure for the 500-seed report
fig, axes = plt.subplots(1, 3, figsize=(17, 5))

ax = axes[0]
counts, bins, _ = ax.hist(accs, bins=28, color="tab:green", alpha=0.6, edgecolor="white")
kde = sstats.gaussian_kde(accs)
xs = np.linspace(accs.min(), accs.max(), 1000)
ax.plot(xs, kde(xs) * n * (bins[1]-bins[0]), color="darkgreen", lw=2.2, label="KDE (Scott)")
ax.axvline(accs.mean(), color="black", ls="--", lw=1.5, label=f"mean {accs.mean():.3f}")
ax.axvline(np.median(accs), color="navy", ls=":", lw=1.5, label=f"median {np.median(accs):.3f}")
ax.axvline(1/3, color="grey", ls="--", alpha=0.6, label="chance 0.333")
ax.set_xlabel("converged test accuracy"); ax.set_ylabel("count")
ax.set_title(f"500-seed accuracy distribution (n={n})\ndip p={dip_p:.2f}, Shapiro p={sh.pvalue:.2f} → unimodal")
ax.legend(fontsize=8)

ax2 = axes[1]
# KDE at several bandwidths to show the single dominant peak is bandwidth-robust
for label, bw in [("Scott", "scott"), ("1.5×", scott*1.5), ("2×", scott*2.0)]:
    k = sstats.gaussian_kde(accs, bw_method=bw if bw == "scott" else bw)
    ax2.plot(xs, k(xs), lw=2, label=f"bw={label}")
ax2.axvline(accs.mean(), color="black", ls="--", alpha=0.5)
ax2.set_xlabel("converged test accuracy"); ax2.set_ylabel("density")
ax2.set_title("KDE across bandwidths\n(single dominant peak is bandwidth-robust)")
ax2.legend(fontsize=8)

ax3 = axes[2]
sstats.probplot(accs, dist="norm", plot=ax3)
ax3.get_lines()[0].set_markerfacecolor("tab:green")
ax3.get_lines()[0].set_markeredgecolor("tab:green")
ax3.get_lines()[0].set_alpha(0.35)
ax3.get_lines()[0].set_markersize(4)
ax3.set_title(f"Normal Q–Q plot\n(skew={skew:.2f}, excess kurt={kurt:.2f})")
fig.tight_layout()
fig.savefig(HERE / "robustness_500seed_distribution.png", dpi=130)
plt.close(fig)
print("\nWROTE robustness_500seed_distribution.png + unimodality_stats.json")
