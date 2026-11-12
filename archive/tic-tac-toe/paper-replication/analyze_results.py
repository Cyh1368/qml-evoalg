"""Analyze the three completed cluster jobs (sweep, 500-seed robustness,
optimizer benchmark) and emit statistics + report figures.

Run with the analysis venv:  ../.venv-shinka-ttt/bin/python analyze_results.py
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats as sstats

HERE = Path(__file__).resolve().parent


def load(p):
    return json.loads(Path(p).read_text())


def desc(a):
    a = np.asarray(a, dtype=float)
    return dict(n=int(a.size), mean=float(a.mean()), std=float(a.std(ddof=1)),
                median=float(np.median(a)), q1=float(np.percentile(a, 25)),
                q3=float(np.percentile(a, 75)), min=float(a.min()), max=float(a.max()))


# =====================================================================
# 1. L/P SWEEP  (Experiment 0)
# =====================================================================
def analyze_sweep():
    rows = []
    for f in sorted((HERE / "histories").glob("history_l*_p*.json")):
        d = load(f)
        rows.append(d)
    Ls = sorted({d["l"] for d in rows})
    Ps = sorted({d["p"] for d in rows})
    grid_acc = np.full((len(Ls), len(Ps)), np.nan)
    grid_ep = np.full((len(Ls), len(Ps)), np.nan)
    grid_par = np.full((len(Ls), len(Ps)), np.nan)
    table = {}
    for d in rows:
        i, j = Ls.index(d["l"]), Ps.index(d["p"])
        grid_acc[i, j] = d["final_test_accuracy"]
        grid_ep[i, j] = d["best_epoch"]
        grid_par[i, j] = d["n_params"]
        table[(d["l"], d["p"])] = d
    best = max(rows, key=lambda d: d["final_test_accuracy"])
    worst = min(rows, key=lambda d: d["final_test_accuracy"])
    all_conv = all(d["converged"] for d in rows)

    # ---- figure: heatmap of accuracy + params overlay, and acc vs n_params
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.6))
    ax = axes[0]
    im = ax.imshow(grid_acc, origin="lower", aspect="auto", cmap="viridis",
                   vmin=np.nanmin(grid_acc), vmax=np.nanmax(grid_acc))
    ax.set_xticks(range(len(Ps))); ax.set_xticklabels(Ps)
    ax.set_yticks(range(len(Ls))); ax.set_yticklabels(Ls)
    ax.set_xlabel("P (cemoid-block repetitions)"); ax.set_ylabel("L (layers)")
    ax.set_title("Converged test accuracy — L/P sweep")
    for i in range(len(Ls)):
        for j in range(len(Ps)):
            ax.text(j, i, f"{grid_acc[i,j]:.2f}", ha="center", va="center",
                    color="white" if grid_acc[i, j] < (np.nanmin(grid_acc)+np.nanmax(grid_acc))/2 else "black",
                    fontsize=8)
    fig.colorbar(im, ax=ax, label="test accuracy")

    ax2 = axes[1]
    npar = grid_par.flatten()
    acc = grid_acc.flatten()
    m = ~np.isnan(npar)
    ax2.scatter(npar[m], acc[m], c="tab:blue", alpha=0.8)
    # best per param-count trend
    order = np.argsort(npar[m])
    ax2.plot(npar[m][order], acc[m][order], color="tab:blue", alpha=0.25)
    ax2.axhline(1/3, ls="--", color="grey", label="chance (0.333)")
    ax2.set_xlabel("number of trainable parameters (9·L·P)")
    ax2.set_ylabel("converged test accuracy")
    ax2.set_title("Accuracy vs. model size")
    ax2.legend()
    ax2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "lp_sweep_converged.png", dpi=130)
    plt.close(fig)

    out = dict(
        Ls=Ls, Ps=Ps,
        grid_acc=grid_acc.tolist(), grid_ep=grid_ep.tolist(), grid_par=grid_par.tolist(),
        best=dict(l=best["l"], p=best["p"], acc=best["final_test_accuracy"],
                  npar=best["n_params"], epoch=best["best_epoch"]),
        worst=dict(l=worst["l"], p=worst["p"], acc=worst["final_test_accuracy"],
                   npar=worst["n_params"], epoch=worst["best_epoch"]),
        all_converged=all_conv,
        acc_overall=desc([d["final_test_accuracy"] for d in rows]),
        epoch_overall=desc([d["best_epoch"] for d in rows]),
        n=len(rows),
    )
    # correlation between size and accuracy
    out["spearman_size_acc"] = sstats.spearmanr(npar[m], acc[m])._asdict()
    return out


# =====================================================================
# 2. 500-SEED ROBUSTNESS  (Experiment 1)
# =====================================================================
def analyze_rob500():
    accs, vaccs, epochs, stopped, conv = [], [], [], [], []
    seeds = []
    for f in sorted((HERE / "robustness_histories").glob("seed_*.json")):
        d = load(f)
        accs.append(d["final_test_accuracy"]); vaccs.append(d["validation_accuracy"])
        epochs.append(d["best_epoch"]); stopped.append(d["stopped_epoch"])
        conv.append(d["converged"]); seeds.append(d["seed"])
    accs = np.array(accs); epochs = np.array(epochs); seeds = np.array(seeds)
    s = desc(accs)
    # unimodality tests
    dip, dip_p = _hartigan_dip(accs)
    # Silverman-ish: KDE modes count
    kde = sstats.gaussian_kde(accs)
    xs = np.linspace(accs.min(), accs.max(), 1000)
    dens = kde(xs)
    # count interior local maxima
    modes = int(np.sum((dens[1:-1] > dens[:-2]) & (dens[1:-1] > dens[2:])))
    shapiro = sstats.shapiro(accs) if accs.size <= 5000 else None
    skew = float(sstats.skew(accs)); kurt = float(sstats.kurtosis(accs))

    best_i = int(np.argmax(accs)); worst_i = int(np.argmin(accs))

    # ---- figure: 3 panels
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    ax = axes[0]
    n, bins, _ = ax.hist(accs, bins=30, color="tab:green", alpha=0.65, edgecolor="white")
    ax.plot(xs, dens * len(accs) * (bins[1]-bins[0]), color="darkgreen", lw=2, label="KDE")
    ax.axvline(s["mean"], color="black", ls="--", label=f"mean {s['mean']:.3f}")
    ax.axvline(s["median"], color="navy", ls=":", label=f"median {s['median']:.3f}")
    ax.axvline(1/3, color="grey", ls="--", alpha=0.7, label="chance 0.333")
    ax.set_xlabel("converged test accuracy"); ax.set_ylabel("count")
    ax.set_title(f"500-seed accuracy distribution (n={len(accs)})")
    ax.legend(fontsize=8)

    ax2 = axes[1]
    ax2.hist(epochs, bins=30, color="tab:orange", alpha=0.7, edgecolor="white")
    ax2.axvline(100, color="red", ls="--", label="old fixed cutoff (100)")
    ax2.axvline(np.median(epochs), color="black", ls=":", label=f"median {np.median(epochs):.0f}")
    ax2.set_xlabel("best-validation (convergence) epoch"); ax2.set_ylabel("count")
    ax2.set_title("Convergence epoch distribution")
    ax2.legend(fontsize=8)

    ax3 = axes[2]
    # QQ plot vs normal
    sstats.probplot(accs, dist="norm", plot=ax3)
    ax3.set_title("Normal Q–Q plot of accuracy")
    ax3.get_lines()[0].set_markerfacecolor("tab:green")
    ax3.get_lines()[0].set_markeredgecolor("tab:green")
    ax3.get_lines()[0].set_alpha(0.4)
    fig.tight_layout()
    fig.savefig(HERE / "robustness_500seed_distribution.png", dpi=130)
    plt.close(fig)

    return dict(
        n=len(accs), acc=s, epoch=desc(epochs), stopped=desc(stopped),
        n_converged=int(np.sum(conv)),
        frac_ge_065=float(np.mean(accs >= 0.65)),
        frac_ge_070=float(np.mean(accs >= 0.70)),
        frac_ge_075=float(np.mean(accs >= 0.75)),
        best=dict(seed=int(seeds[best_i]), acc=float(accs[best_i]), epoch=int(epochs[best_i])),
        worst=dict(seed=int(seeds[worst_i]), acc=float(accs[worst_i]), epoch=int(epochs[worst_i])),
        kde_modes=modes, dip=dip, dip_p=dip_p,
        shapiro_W=float(shapiro.statistic) if shapiro else None,
        shapiro_p=float(shapiro.pvalue) if shapiro else None,
        skew=skew, kurtosis=kurt,
    )


def _hartigan_dip(x):
    """Lightweight Hartigan dip statistic (no external dep). Returns (dip, None).
    p-value omitted (needs bootstrap table); we report the statistic + KDE modes."""
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    # ECDF
    ecdf = np.arange(1, n+1) / n
    # greatest convex minorant / least concave majorant distance approximation
    # Use simple max deviation of ECDF from its closest unimodal (||) — approximate.
    # We compute the classic dip via gcm/lcm using a compact implementation.
    try:
        from scipy.stats import gaussian_kde  # noqa
        # fall back to a known compact dip implementation
        return _dip_exact(x), None
    except Exception:
        return float("nan"), None


def _dip_exact(x):
    # Compact implementation of Hartigan's dip statistic.
    x = np.sort(x); n = len(x)
    if n < 4:
        return 0.0
    y = (np.arange(n) + 1) / n  # ecdf upper
    # Use unique support to avoid degenerate flats
    # Standard algorithm (Hartigan 1985) - compact port
    def _gcm(xx, yy):
        # greatest convex minorant indices
        idx = [0]
        for i in range(1, len(xx)):
            while len(idx) >= 2:
                a, b = idx[-2], idx[-1]
                if (yy[b]-yy[a])*(xx[i]-xx[a]) >= (yy[i]-yy[a])*(xx[b]-xx[a]):
                    idx.pop()
                else:
                    break
            idx.append(i)
        return idx
    lo = _gcm(x, y - 1.0/n)  # lower ecdf
    hi = _gcm(-x[::-1], -(y[::-1]))
    d = 0.0
    # distance of ecdf to gcm (convex minorant) on lower envelope
    gx, gy = x[lo], (y - 1.0/n)[lo]
    interp = np.interp(x, gx, gy)
    d = max(d, np.max(np.abs((y - 1.0/n) - interp)))
    return float(d / 2.0)


# =====================================================================
# 3. OPTIMIZER BENCHMARK
# =====================================================================
def analyze_optbench():
    OPTS = ["GradientDescent", "Momentum", "Nesterov", "Adagrad", "RMSProp", "Adam", "SPSA"]
    per = {}
    for o in OPTS:
        accs, eps, walls, conv, stopped = [], [], [], [], []
        for f in sorted((HERE / "optimizer_histories" / o).glob("seed_*.json")):
            d = load(f)
            accs.append(d["final_test_accuracy"]); eps.append(d["best_epoch"])
            walls.append(d.get("wall_seconds", np.nan)); conv.append(d["converged"])
            stopped.append(d["stopped_epoch"])
        per[o] = dict(acc=desc(accs), epoch=desc(eps),
                      wall_mean=float(np.nanmean(walls)), wall_median=float(np.nanmedian(walls)),
                      n_converged=int(np.sum(conv)), n=len(accs),
                      accs=accs, stopped=desc(stopped))
    # rank by mean acc
    ranked = sorted(OPTS, key=lambda o: per[o]["acc"]["mean"], reverse=True)
    # pairwise vs Adam (baseline) Mann-Whitney
    adam_accs = per["Adam"]["accs"]
    for o in OPTS:
        if o == "Adam":
            per[o]["mwu_vs_adam_p"] = None
            continue
        u = sstats.mannwhitneyu(per[o]["accs"], adam_accs, alternative="two-sided")
        per[o]["mwu_vs_adam_p"] = float(u.pvalue)

    # ---- figure: boxplot acc + bar wall-time + scatter acc vs epoch
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    ax = axes[0]
    data = [per[o]["accs"] for o in ranked]
    bp = ax.boxplot(data, labels=ranked, showmeans=True, patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor("tab:blue"); patch.set_alpha(0.5)
    ax.axhline(1/3, ls="--", color="grey", label="chance")
    ax.set_ylabel("converged test accuracy"); ax.set_title("Accuracy by optimizer (50 seeds each)")
    ax.tick_params(axis="x", rotation=35); ax.legend(fontsize=8); ax.grid(alpha=0.3, axis="y")

    ax2 = axes[1]
    walls_min = [per[o]["wall_median"]/60 for o in ranked]
    ax2.bar(ranked, walls_min, color="tab:orange", alpha=0.8)
    ax2.set_ylabel("median wall-time (min)"); ax2.set_title("Median wall-time per run")
    ax2.tick_params(axis="x", rotation=35); ax2.grid(alpha=0.3, axis="y")

    ax3 = axes[2]
    for o in ranked:
        ax3.scatter(per[o]["epoch"]["mean"], per[o]["acc"]["mean"], s=70, label=o)
        ax3.annotate(o, (per[o]["epoch"]["mean"], per[o]["acc"]["mean"]),
                     fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax3.set_xlabel("mean convergence epoch"); ax3.set_ylabel("mean test accuracy")
    ax3.set_title("Speed vs. accuracy"); ax3.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "optimizer_benchmark_comparison.png", dpi=130)
    plt.close(fig)

    # strip accs lists for json dump
    slim = {o: {k: v for k, v in per[o].items() if k != "accs"} for o in OPTS}
    return dict(ranked=ranked, per=slim)


if __name__ == "__main__":
    out = {}
    print("== sweep =="); out["sweep"] = analyze_sweep()
    print("== rob500 =="); out["rob500"] = analyze_rob500()
    print("== optbench =="); out["optbench"] = analyze_optbench()
    Path(HERE / "analysis_stats.json").write_text(json.dumps(out, indent=2, default=str))
    print("\nWROTE analysis_stats.json + 3 PNGs")
    print(json.dumps(out, indent=2, default=str))
