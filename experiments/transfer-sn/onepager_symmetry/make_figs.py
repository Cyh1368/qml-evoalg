#!/usr/bin/env python3
"""Figures for the symmetry one-pager.

Panel A  which symmetry each arm named (two vocabularies, kept separate)
Panel B  did the arm BUILD the symmetry it named (follow-through)
Panel C  when the orbit structure existed, and how it got there

Colors are categorical slots 1-3 of the validated default palette, assigned to
arms in fixed order and never reused for anything else. Aqua sits below 3:1 on
a light surface, so every bar carries a visible direct label (the relief rule).

Usage:  python3 make_figs.py     (run from transfer-sn/onepager_symmetry)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ARMS = ["weak", "mid", "frontier"]
LABEL = {"weak": "weak  (low effort)", "mid": "mid  (medium)", "frontier": "frontier  (xhigh)"}
C = {"weak": "#2a78d6", "mid": "#eb6834", "frontier": "#1baf7a"}

INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#8b8a85"
GRID = "#e4e3df"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8,
    "axes.edgecolor": GRID, "axes.linewidth": 0.8,
    "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})

prov = json.loads(Path("../symmetry_provenance.json").read_text())
mirror = json.loads(Path("mirror_stats.json").read_text())


def strip(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(length=0)
    ax.set_axisbelow(True)


# ----------------------------------------------------------------- panel A
fig, axes = plt.subplots(1, 3, figsize=(7.6, 1.72), sharey=True)
cats = ["any", "permutation", "mirror"]
for ax, arm in zip(axes, ARMS):
    rows = prov[arm]["rows"]
    n = len(rows)
    vals = [100 * sum(r["general"] for r in rows) / n,
            100 * sum(r["perm"] for r in rows) / n,
            100 * sum(r["mirror"] for r in rows) / n]
    bars = ax.bar(range(3), vals, color=C[arm], width=0.62, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 3, f"{v:.0f}%", ha="center",
                va="bottom", fontsize=8, color=INK, fontweight="bold")
    ax.set_xticks(range(3))
    ax.set_xticklabels(cats, fontsize=7.6)
    ax.set_ylim(0, 100)
    ax.set_title(LABEL[arm], fontsize=8.5, color=INK, pad=6, fontweight="bold")
    ax.yaxis.grid(True, color=GRID, lw=0.7, zorder=0)
    strip(ax)
axes[0].set_ylabel("% of proposals", fontsize=7.5)
fig.suptitle("A.  Which symmetry each arm named, in its own patch notes  (x: kind of symmetry named)",
             fontsize=9.5, fontweight="bold", x=0.008, ha="left", y=1.02, color=INK)
fig.tight_layout()
fig.savefig("figA_vocab.pdf", bbox_inches="tight")
plt.close(fig)

# ----------------------------------------------------------------- panel B
fig, ax = plt.subplots(figsize=(3.7, 1.80))
groups, said, built, cols = [], [], [], []
for arm in ARMS:
    rows = prov[arm]["rows"]
    n = len(rows)
    groups.append({"frontier":"front"}.get(arm, arm))
    said.append(100 * sum(r["perm"] for r in rows) / n)
    built.append(100 * sum(r["tied8"] for r in rows) / n)
    cols.append(C[arm])
for arm in ARMS:
    m = mirror[arm]
    groups.append({"frontier":"front"}.get(arm, arm))
    said.append(100 * m["says"] / m["n"])
    built.append(100 * m["built"] / m["n"])
    cols.append(C[arm])
x = range(len(groups))
w = 0.38
for i, (s, b, c) in enumerate(zip(said, built, cols)):
    ax.bar(i - w / 2, s, width=w, color=c, zorder=3)
    ax.bar(i + w / 2, b, width=w, facecolor="none", edgecolor=c, hatch="////",
           linewidth=1.0, zorder=3)
    for xx, v in ((i - w / 2, s), (i + w / 2, b)):
        if v > 2:
            ax.text(xx, v + 2.5, f"{v:.0f}", ha="center", va="bottom", fontsize=6.6, color=INK)
ax.set_xticks(list(x))
ax.set_xticklabels(groups, fontsize=7.2)
ax.set_ylim(0, 112)
ax.set_ylabel("% of proposals", fontsize=7.5)
ax.yaxis.grid(True, color=GRID, lw=0.7, zorder=0)
strip(ax)
ax.axvline(2.5, color=GRID, lw=0.9, zorder=1)
ax.text(1.0, 99, "permutation symmetry", ha="center", fontsize=7, color=INK2)
ax.text(4.0, 99, "mirror symmetry", ha="center", fontsize=7, color=INK2)
ax.legend(handles=[Patch(facecolor=MUTED, label="named it"),
                   Patch(facecolor="none", edgecolor=MUTED, hatch="////", label="built it")],
          fontsize=6.8, frameon=False, loc="upper left", ncol=2,
          bbox_to_anchor=(0.0, 1.20), handlelength=1.4)
ax.set_title("B.  Named vs actually built", fontsize=9.5, fontweight="bold",
             loc="left", pad=24, color=INK)
fig.tight_layout()
fig.savefig("figB_followthrough.pdf", bbox_inches="tight")
plt.close(fig)

# ----------------------------------------------------------------- panel C
fig, ax = plt.subplots(figsize=(3.8, 1.80))
for row, arm in enumerate(ARMS):
    y = len(ARMS) - 1 - row
    rows = sorted(prov[arm]["rows"], key=lambda r: r["gen"])
    ax.plot([0, 49], [y, y], color=GRID, lw=6, solid_capstyle="butt", zorder=1)
    for r in rows:
        if r["state"] in ("INHERITED", "INTRODUCTION"):
            ax.plot([r["gen"]], [y], marker="s", ms=3.4, color=C[arm], zorder=3)
    for e in prov[arm]["introductions"]:
        ax.plot([e["gen"]], [y], marker="v", ms=6.5, color=C[arm],
                markeredgecolor=SURFACE, markeredgewidth=0.8, zorder=4)
    ax.text(-2.0, y, LABEL[arm].split("  ")[0], ha="right", va="center",
            fontsize=7.6, color=INK, fontweight="bold")
    n_int = len(prov[arm]["introductions"])
    n_inh = sum(1 for r in rows if r["state"] == "INHERITED")
    ax.text(50.5, y, f"{n_int} found / {n_inh} kept", ha="left", va="center",
            fontsize=6.8, color=INK2)
ax.set_xlim(-13, 66)
ax.set_ylim(-0.7, 2.7)
ax.set_yticks([])
ax.set_xticks([0, 10, 20, 30, 40, 49])
ax.set_xlabel("generation", fontsize=7.5)
ax.xaxis.grid(True, color=GRID, lw=0.7, zorder=0)
strip(ax)
ax.legend(handles=[
    plt.Line2D([], [], marker="v", ls="", color=MUTED, ms=6, label="orbit introduced"),
    plt.Line2D([], [], marker="s", ls="", color=MUTED, ms=3.4, label="orbit present"),
], fontsize=6.8, frameon=False, loc="upper left", ncol=2, bbox_to_anchor=(0.0, 1.04),
    handlelength=1.2)
ax.set_title("C.  When an 8-wire tied orbit existed", fontsize=9.5,
             fontweight="bold", loc="left", pad=16, color=INK)
fig.tight_layout()
fig.savefig("figC_provenance.pdf", bbox_inches="tight")
plt.close(fig)

print("wrote figA_vocab.pdf, figB_followthrough.pdf, figC_provenance.pdf")
