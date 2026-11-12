"""Figure for the symmetry experiment: the search finds S_8 equivariance."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SP = Path(__file__).resolve().parent
OUT = Path.home() / "QuantumAnsatz/qml-ea/tic-tac-toe/paper-anon-motif/figs"

eq = json.loads((SP / "equivariance.json").read_text())

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.labelsize": 9,
    "axes.titlesize": 9.5, "legend.fontsize": 7.6, "xtick.labelsize": 8,
    "ytick.labelsize": 8, "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight",
})

RUNS = [("results_gpt56sol_r2", "GPT-5.6-sol", "#7b3294"),
        ("results_haiku_r2", "Haiku-4.5", "#1f78b4"),
        ("results_sonnet_r2", "Sonnet-5", "#e08214")]
PIVOT = 33

fig, axes = plt.subplots(1, 3, figsize=(9.6, 2.85))
fig.subplots_adjust(wspace=.34)

# (a) equivariance of each proposal against generation
ax = axes[0]
for run, name, col in RUNS:
    if run not in eq:
        continue
    t = sorted(eq[run]["trajectory"], key=lambda p: p["gen"])
    ax.plot([p["gen"] for p in t], [p["partial"] for p in t], "-o",
            color=col, lw=1.2, ms=2.6, label=name)
ax.axvline(PIVOT, color="#444", ls=":", lw=1.2)
ax.text(PIVOT + 1.5, .015, "gen 33", fontsize=7, color="#444", va="bottom")
ax.set_xlabel("generation")
ax.set_ylabel("how permutation-symmetric\nthe circuit is")
ax.set_ylim(-.04, 1.06)
ax.legend(frameon=False, loc="upper left")
ax.set_title("(a) the search finds the symmetry")

# (b) score before/after the pivot, GPT arm
ax = axes[1]
t = sorted(eq["results_gpt56sol_r2"]["trajectory"], key=lambda p: p["gen"])
g = [p["gen"] for p in t]
s = [p["score"] for p in t]
ax.plot(g, s, "-o", color="#7b3294", lw=1.2, ms=3)
ax.axvspan(min(g), PIVOT, color="#c2453a", alpha=.10, lw=0)
ax.axvspan(PIVOT, max(g), color="#1b7837", alpha=.10, lw=0)
# place annotations in axes coordinates so they cannot escape the panel
ax.text(.22, .06, "before\nmean 0.821", fontsize=7, color="#c2453a",
        ha="center", va="bottom", transform=ax.transAxes)
ax.text(.76, .06, "after\nmean 0.932", fontsize=7, color="#1b7837",
        ha="center", va="bottom", transform=ax.transAxes)
ax.axvline(PIVOT, color="#444", ls=":", lw=1.2)
ax.set_xlabel("generation")
ax.set_ylabel("score")
ax.set_title("(b) and the score rewards it")

# (c) accuracy vs parameters, coloured by equivariance
ax = axes[2]
for run, name, col in RUNS:
    if run not in eq:
        continue
    b = eq[run]["best"]
    ax.scatter(b["np"], (b["test"] or 0) * 100, s=64, color=col,
               zorder=3, label=f"{name}  ({b['partial']:.2f})")
    ax.annotate(f"{b['partial']:.2f}", (b["np"], (b["test"] or 0) * 100),
                textcoords="offset points", xytext=(0, 9), ha="center", fontsize=7)
ax.scatter([146], [86.67], s=64, color="#888", marker="s", zorder=3, label="seed  (0.15)")
ax.annotate("0.15", (146, 86.67), textcoords="offset points", xytext=(0, 9),
            ha="center", fontsize=7)
ax.set_xlabel("trainable parameters")
ax.set_ylabel("test accuracy (%)")
ax.set_xlim(0, 165)
ax.set_ylim(84, 98.5)
ax.legend(frameon=False, loc="lower left", title="symmetry score", title_fontsize=7)
ax.set_title("(c) more symmetric, fewer knobs, better")

fig.savefig(OUT / "fig_symmetry.pdf")
fig.savefig(SP / "fig_symmetry.png", dpi=150)
plt.close(fig)
print("wrote fig_symmetry")
