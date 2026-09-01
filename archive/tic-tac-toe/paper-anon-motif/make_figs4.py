"""Figures for the zero-context experiment.

fig_zerocontext: the graph task with and without the sentence naming the
                 feature/qubit correspondence.
fig_zc_motif:    where the zero-context tic-tac-toe arms actually put their
                 three-qubit gates, over 80 generations.
"""
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SP = Path(__file__).resolve().parent
OUT = SP / "figs"
D = json.loads((SP / "zcdata.json").read_text())
S = json.loads((SP / "zcstats.json").read_text())

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.labelsize": 9,
    "axes.titlesize": 9.5, "legend.fontsize": 7.6, "xtick.labelsize": 8,
    "ytick.labelsize": 8, "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight",
})

PURPLE, BLUE, ORANGE, GREY = "#7b3294", "#1f78b4", "#e08214", "#888888"

# ---------------------------------------------------------------- figure one
HINT = [("hint_sn_gpt56sol_r2", "GPT-5.6-sol", PURPLE),
        ("hint_sn_haiku_r2", "Haiku-4.5", BLUE),
        ("hint_sn_sonnet_r2", "Sonnet-5", ORANGE)]
ZERO = [("zc_sn_gpt56sol", "GPT-5.6-sol", PURPLE),
        ("zc_sn_haiku", "Haiku-4.5", BLUE),
        ("zc_sn_sonnet", "Sonnet-5", ORANGE)]

fig, axes = plt.subplots(1, 3, figsize=(9.6, 2.85))
fig.subplots_adjust(wspace=.34)

for ax, runs, title in (
        (axes[0], HINT, "(a) told the features are qubit pairs"),
        (axes[1], ZERO, "(b) not told")):
    for tag, name, col in runs:
        if tag not in S:
            continue
        t = S[tag]["sym"]["trajectory"]
        ax.plot([p["gen"] for p in t], [p["partial"] for p in t], "-o",
                color=col, lw=1.1, ms=2.4, label=name)
    ax.axhline(1.0, color="#444", ls=":", lw=1.0)
    ax.set_xlabel("generation")
    ax.set_ylabel("how permutation-symmetric\nthe circuit is")
    ax.set_ylim(-.04, 1.06)
    ax.set_xlim(-2, 82)
    ax.set_title(title)
axes[0].legend(frameon=False, loc="lower right", fontsize=7)
axes[0].annotate("exactly equivariant\nfrom gen 33", xy=(40, 1.0),
                 xytext=(46, .80), fontsize=7, color="#444",
                 arrowprops=dict(arrowstyle="->", color="#444", lw=.8,
                                 connectionstyle="arc3,rad=.25"))
axes[1].text(.5, .9, "no arm ever reaches it", fontsize=7.5, color="#c2453a",
             ha="center", transform=axes[1].transAxes)

# (c) what it cost: best test accuracy against parameters, both conditions
ax = axes[2]
for tag, name, col in HINT:
    if tag not in S:
        continue
    b = S[tag]["sym"]["best"]
    ax.scatter(b["n_params"], (b["test"] or 0) * 100, s=62, color=col,
               marker="o", zorder=3)
for tag, name, col in ZERO:
    b = S[tag]["sym"]["best"]
    ax.scatter(b["n_params"], (b["test"] or 0) * 100, s=62, color=col,
               marker="X", zorder=3)
ax.scatter([146], [86.67], s=62, color=GREY, marker="s", zorder=3)
ax.annotate("seed", (146, 86.67), textcoords="offset points", xytext=(0, 9),
            ha="center", fontsize=7, color=GREY)
ax.scatter([], [], s=62, color="#444", marker="o", label="told")
ax.scatter([], [], s=62, color="#444", marker="X", label="not told")
ax.set_xlabel("trainable parameters")
ax.set_ylabel("test accuracy (%)")
ax.set_xlim(0, 165)
ax.set_ylim(84, 98.5)
ax.legend(frameon=False, loc="lower left")
ax.set_title("(c) the hint is worth six points")

fig.savefig(OUT / "fig_zerocontext.pdf"); fig.savefig(SP / "fig_zerocontext.png", dpi=110)
plt.close(fig)
print("wrote fig_zerocontext")

# ---------------------------------------------------------------- figure two
WIN = {frozenset(t) for t in D["keys"]["ttt"]["win"]}
EDGES = {frozenset(e) for e in D["keys"]["ttt"]["edges"]}
RM = {frozenset(t) for t in [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
                             (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]}
HIDDEN = {t for t in WIN
          if not any(frozenset(p) in EDGES for p in combinations(sorted(t), 2))}


def triples(spec):
    return [frozenset(int(w) for w in it["wires"])
            for it in (spec or [])
            if isinstance(it, dict)
            and str(it.get("gate", "")).upper() in ("ZZZ", "CCRZ")
            and isinstance(it.get("wires"), (list, tuple)) and len(it["wires"]) == 3]


ARMS = [("zc_ttt_haiku", "Haiku-4.5", BLUE),
        ("zc_ttt_sonnet", "Sonnet-5", ORANGE),
        ("zc_ttt_gpt56sol", "GPT-5.6-sol", PURPLE)]

fig, axes = plt.subplots(1, 3, figsize=(9.6, 2.9))
fig.subplots_adjust(wspace=.36)

# (a) placements split by what kind of triple they are
ax = axes[0]
labels = ["true line\n(coincidence)", "true line\n(other)",
          "unpermuted-board\nline only", "neither"]
colors = ["#1b7837", "#a6dba0", "#c2453a", "#cccccc"]
bottoms = [0.0, 0.0, 0.0]
for i, (lab, col) in enumerate(zip(labels, colors)):
    vals = []
    for tag, _, _ in ARMS:
        run = D["runs"][tag]
        pl = [t for p in run["programs"] if p["correct"] and p["score"] is not None
              for t in triples(p["spec"])]
        n = len(pl) or 1
        if i == 0:
            k = sum(1 for t in pl if t in WIN and t in RM)
        elif i == 1:
            k = sum(1 for t in pl if t in WIN and t not in RM)
        elif i == 2:
            k = sum(1 for t in pl if t not in WIN and t in RM)
        else:
            k = sum(1 for t in pl if t not in WIN and t not in RM)
        vals.append(100 * k / n)
    ax.bar(range(3), vals, bottom=bottoms, color=col, label=lab, width=.62,
           edgecolor="white", lw=.6)
    bottoms = [b + v for b, v in zip(bottoms, vals)]
ax.set_xticks(range(3))
ax.set_xticklabels([n for _, n, _ in ARMS], fontsize=7.5)
ax.set_ylabel("share of placed gates (%)")
ax.set_ylim(0, 100)
ax.legend(frameon=False, fontsize=6.4, loc="upper center", ncol=2,
          bbox_to_anchor=(.5, -.22))
ax.set_title("(a) where the gates go")

# (b) on-line rate, raw and de-duplicated, against both nulls
ax = axes[1]
x = range(3)
raw, dedup = [], []
for tag, _, _ in ARMS:
    m = S[tag]["motif"]
    raw.append(100 * (m["population"]["frac"] or 0))
    run = D["runs"][tag]
    pl = {t for p in run["programs"] if p["correct"] and p["score"] is not None
          for t in triples(p["spec"])}
    dedup.append(100 * sum(1 for t in pl if t in WIN) / len(pl) if pl else 0)
ax.bar([i - .18 for i in x], raw, width=.34, color="#6a51a3", label="every placement")
ax.bar([i + .18 for i in x], dedup, width=.34, color="#bcbddc",
       label="distinct triples")
ax.axhline(9.52, color="#c2453a", ls="--", lw=1.1)
ax.text(-.42, 11.0, "uniform null", fontsize=6.6, color="#c2453a", ha="left")
ax.axhline(27.27, color="#1f78b4", ls=":", lw=1.2)
ax.text(-.42, 28.8, "connectivity-matched null", fontsize=6.6, color="#1f78b4",
        ha="left")
ax.set_xticks(list(x))
ax.set_xticklabels([n for _, n, _ in ARMS], fontsize=7.5)
ax.set_ylabel("gates on a true line (%)")
ax.set_ylim(0, 74)
ax.legend(frameon=False, loc="upper left", fontsize=7)
ax.set_title("(b) the one positive signal, deflated")

# (c) hidden lines: the decisive test, across every run reported
ax = axes[2]
names = ["answer\ngiven", "anonymised\n30 gens", "zero-context\n80 gens"]
vals = [2, 0, max(S[t]["motif"]["hidden_found_anywhere"] for t, _, _ in ARMS)]
cols = ["#1b7837", "#c2453a", "#c2453a"]
ax.bar(range(3), vals, color=cols, width=.6)
ax.set_xticks(range(3))
ax.set_xticklabels(names, fontsize=7.5)
ax.set_yticks([0, 1, 2])
ax.set_ylim(0, 2.4)
ax.set_ylabel("hidden lines found (of 2)")
for i, v in enumerate(vals):
    ax.text(i, v + .08, str(v), ha="center", fontsize=8)
ax.set_title("(c) the decisive test, unchanged")

fig.savefig(OUT / "fig_zc_motif.pdf"); fig.savefig(SP / "fig_zc_motif.png", dpi=110)
plt.close(fig)
print("wrote fig_zc_motif")
