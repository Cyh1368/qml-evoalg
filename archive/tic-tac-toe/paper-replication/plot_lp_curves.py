"""7x7 grid of accuracy-vs-epoch curves for the L/P sweep (one subplot per config).

Each (L, P) trains to a different number of epochs (early stopping), so every
subplot carries its own epoch axis. Tick labels are kept small to avoid overlap.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

HERE = Path(__file__).resolve().parent
Ls = [1, 2, 3, 4, 5, 6, 7]
Ps = [1, 2, 3, 4, 5, 6, 7]

fig, axes = plt.subplots(len(Ls), len(Ps), figsize=(24, 22))

for i, L in enumerate(Ls):          # rows: L=1 (top) .. L=7 (bottom)
    for j, P in enumerate(Ps):      # cols: P=1 (left) .. P=7 (right)
        ax = axes[i][j]
        d = json.loads((HERE / "histories" / f"history_l{L}_p{P}.json").read_text())
        test = np.asarray(d["test_acc_history"], dtype=float)
        val = np.asarray(d["val_acc_history"], dtype=float)
        epochs = np.arange(1, len(test) + 1)

        ax.plot(epochs, test, color="tab:blue", lw=1.1, label="test")
        ax.plot(epochs, val, color="tab:orange", lw=0.8, alpha=0.6, label="val")
        # mark the restored best-validation epoch
        be = d["best_epoch"]
        ax.axvline(be, color="tab:green", ls="--", lw=0.8, alpha=0.8)
        ax.axhline(1 / 3, color="grey", ls=":", lw=0.6, alpha=0.6)  # chance

        ax.set_title(f"L={L}, P={P}  ({d['n_params']}p)  acc={d['final_test_accuracy']:.3f}@{be}",
                     fontsize=7)
        ax.set_ylim(0.25, 1.0)
        ax.set_xlim(1, len(test))
        # per-subplot epoch ticks (different range each), kept small
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=True, prune="both"))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.tick_params(axis="both", labelsize=5.5, length=2, pad=1)
        ax.grid(alpha=0.18, lw=0.4)
        # only label outer axes to reduce clutter
        if j == 0:
            ax.set_ylabel("accuracy", fontsize=6)
        if i == len(Ls) - 1:
            ax.set_xlabel("epoch", fontsize=6)

# single shared legend
handles, labels = axes[0][0].get_legend_handles_labels()
handles.append(plt.Line2D([0], [0], color="tab:green", ls="--", lw=0.8))
labels.append("best-val epoch (restored)")
fig.legend(handles, labels, loc="upper center", ncol=3, fontsize=10, frameon=False,
           bbox_to_anchor=(0.5, 0.997))
fig.suptitle("cemoid L/P sweep — test/validation accuracy vs. epoch (converged, early-stopped)",
             fontsize=14, y=0.985)
fig.tight_layout(rect=[0, 0, 1, 0.965])
out = HERE / "lp_sweep_accuracy_curves.png"
fig.savefig(out, dpi=130)
print(f"saved {out}")
