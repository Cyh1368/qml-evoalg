"""Figure for the spin task: why it measures nothing, in both variants.

(a) test accuracy against generation, every arm, both variants: pinned at 100%.
(b) the reward redesign made the empty circuit optimal: score against gate count.
(c) nobody ever tied XX=YY=ZZ on a pair, which is the discovery threshold.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SP = Path(__file__).resolve().parent
OUT = SP / "figs"
S = json.loads((SP / "zcstats.json").read_text())

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.labelsize": 9,
    "axes.titlesize": 9.5, "legend.fontsize": 7.6, "xtick.labelsize": 8,
    "ytick.labelsize": 8, "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight",
})

PURPLE, BLUE, ORANGE = "#7b3294", "#1f78b4", "#e08214"
ORIG = [("hint_su2_gpt56sol_r2", "GPT-5.6-sol", PURPLE),
        ("hint_su2_haiku", "Haiku-4.5", BLUE),
        ("hint_su2_sonnet_r2", "Sonnet-5", ORANGE)]
ZERO = [("zc_su2_gpt56sol", "GPT-5.6-sol", PURPLE),
        ("zc_su2_haiku", "Haiku-4.5", BLUE),
        ("zc_su2_sonnet", "Sonnet-5", ORANGE)]

fig, axes = plt.subplots(1, 3, figsize=(9.6, 2.9))
fig.subplots_adjust(wspace=.34)

# (a) best-so-far test accuracy: saturates within a few generations everywhere
ax = axes[0]
for runs, style, lab in ((ORIG, "-", "original"), (ZERO, "--", "redesigned reward")):
    for tag, name, col in runs:
        if tag not in S:
            continue
        t = sorted(S[tag]["sym"]["trajectory"], key=lambda p: p["gen"])
        best, xs, ys = -1, [], []
        for p in t:
            if p["score"] > best:
                best = p["score"]
            xs.append(p["gen"])
            ys.append(100 * max(
                (q["test"] or 0) for q in t if q["gen"] <= p["gen"]))
        ax.plot(xs, ys, style, color=col, lw=1.3, alpha=.85)
ax.plot([], [], "-", color="#444", label="original")
ax.plot([], [], "--", color="#444", label="redesigned reward")
ax.set_xlabel("generation")
ax.set_ylabel("best test accuracy so far (%)")
ax.set_ylim(78, 103)
ax.axhline(100, color="#1b7837", ls=":", lw=1.2)
ax.text(42, 96.0, "100% reached by generation 2, 6, 9",
        fontsize=7, color="#1b7837", ha="center")
ax.legend(frameon=False, loc="lower right", fontsize=7)
ax.set_title("(a) the task is already solved")

# (b) score against gate count: fewer gates scores higher, zero scores best
ax = axes[1]
for tag, name, col in ZERO:
    t = S[tag]["sym"]["trajectory"]
    ax.scatter([p["n_gates"] for p in t], [p["score"] for p in t],
               s=16, color=col, alpha=.7, label=name, zorder=3)
empt = [p for tag, _, _ in ZERO for p in S[tag]["sym"]["trajectory"]
        if p["n_gates"] == 0]
if empt:
    ax.scatter([0] * len(empt), [p["score"] for p in empt], s=40,
               facecolors="none", edgecolors="#c2453a", lw=1.1, zorder=4)
    ax.annotate(f"{len(empt)} proposals with\nno gates at all",
                xy=(0, max(p["score"] for p in empt)), xytext=(52, .53),
                fontsize=7, color="#c2453a",
                arrowprops=dict(arrowstyle="->", color="#c2453a", lw=.8))
ax.set_xlabel("gates in the ansatz block")
ax.set_ylabel("score")
ax.legend(frameon=False, loc="lower right", fontsize=7)
ax.set_title("(b) the reward pays for deleting the circuit")

# (c) the discovery threshold, never crossed in either variant
ax = axes[2]
labels, vals, cols, xs = [], [], [], []
pos = 0.0
for runs in (ORIG, ZERO):
    for tag, name, col in runs:
        if tag not in S:
            continue
        labels.append(name.split("-")[0])
        vals.append(S[tag]["sym"]["n_with_tied"])
        cols.append(col)
        xs.append(pos)
        pos += 1
    pos += 0.7
ax.bar(xs, vals, color=cols, width=.62)
ax.set_xticks(xs)
ax.set_xticklabels(labels, fontsize=7)
ax.set_ylim(0, 1.15)
ax.set_yticks([0, 1])
ax.set_ylabel("circuits tying XX=YY=ZZ")
for x in xs:
    ax.text(x, .05, "0", ha="center", fontsize=8.5, color="#c2453a")
n_orig = sum(1 for t, _, _ in ORIG if t in S)
ax.text((n_orig - 1) / 2, 1.02, "original", ha="center", fontsize=7.5,
        color="#444")
ax.text(xs[n_orig] + (len(xs) - n_orig - 1) / 2, 1.02, "redesigned reward",
        ha="center", fontsize=7.5, color="#444")
ax.set_title("(c) nobody found the coupling")

fig.savefig(OUT / "fig_spin.pdf")
fig.savefig(SP / "fig_spin.png", dpi=110)
plt.close(fig)
print("wrote fig_spin")
