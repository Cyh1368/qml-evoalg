#!/usr/bin/env python
"""Regenerate every figure in final-report/figures/.

Run with the render venv, which has matplotlib / numpy / scipy / pennylane:

    ../viz/.venv_render/bin/python make_figures.py

Inputs live in data/ next to this script, so the folder is self-contained:
    data/labels.json        per-program circuit structure labels
    data/note_labels.json   per-program patch-note labels
    data/dataset.npz        the task dataset (feature -> qubit pair table)
"""
from __future__ import annotations

import json
import os
from itertools import combinations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 160,
    "savefig.dpi": 160,
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.6,
})

C = {
    "weak": "#4C78A8",
    "mid": "#F58518",
    "frontier": "#54A24B",
    "frontier-no-gpt": "#B279A2",
}
GEN_CAP = 20          # from-scratch runs are truncated to this many generations
ARMS = ["weak", "mid", "frontier"]
NICE = {"weak": "weak", "mid": "mid", "frontier": "frontier",
        "frontier-no-gpt": "frontier\n(no GPT)"}


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def load():
    labels = json.load(open(os.path.join(HERE, "data/labels.json")))
    notes = json.load(open(os.path.join(HERE, "data/note_labels.json")))
    by_id = {r["program_id"]: r for r in notes}
    for r in labels:
        r["note"] = by_id.get(r["program_id"], {}).get("note")
    # Budget matching: from-scratch runs used either a 20- or a 50-generation
    # protocol, and best-so-far is monotone in generations, so pooling them
    # favours whichever arm has proportionally more long runs. Every scratch
    # run is therefore truncated to its first 20 generations. Continued runs
    # (generations 4-7) are unaffected.
    out = []
    for r in labels:
        if not (r.get("own") and r.get("parsed")):
            continue
        if r["setting"] == "scratch" and r["generation"] > GEN_CAP:
            continue
        out.append(r)
    return out


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def boot_ci(xs, n_boot=20000, seed=7):
    xs = np.asarray(xs, dtype=float)
    if len(xs) < 2:
        return (xs.mean() if len(xs) else np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    m = rng.choice(xs, size=(n_boot, len(xs)), replace=True).mean(axis=1)
    return xs.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5)


ROWS = load()


def group(setting, arm):
    return [r for r in ROWS if r["setting"] == setting and r["arm"] == arm]


def runs(setting, arm):
    out = {}
    for r in group(setting, arm):
        out.setdefault(r["run_id"], []).append(r)
    return out


# --------------------------------------------------------------------------
# fig 1: the task and its encoding
# --------------------------------------------------------------------------
def fig_encoding():
    data = np.load(os.path.join(HERE, "data/dataset.npz"))
    pairs = [tuple(int(w) for w in row) for row in data["feature_pairs"]]
    x = np.asarray(data["x_test"])
    y = np.asarray(data["y_test"])
    i_conn = int(np.flatnonzero(y > 0)[0])
    i_disc = int(np.flatnonzero(y < 0)[0])

    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6),
                             gridspec_kw={"width_ratios": [1, 1, 1.35]})
    for ax in axes:
        ax.set_axis_off()
        ax.grid(False)

    def draw_graph(ax, bits, title, colour):
        th = np.linspace(0, 2 * np.pi, 8, endpoint=False) + np.pi / 2
        pos = np.c_[np.cos(th), np.sin(th)]
        for k, (a, b) in enumerate(pairs):
            if bits[k]:
                ax.plot(*pos[[a, b]].T, color="#666", lw=1.1, zorder=1)
        ax.scatter(*pos.T, s=210, color=colour, zorder=3, edgecolor="white", lw=1.4)
        for q in range(8):
            ax.text(*pos[q], str(q), ha="center", va="center",
                    color="white", fontsize=8, fontweight="bold", zorder=4)
        ax.set_title(title, fontsize=9.5)
        ax.set_xlim(-1.35, 1.35)
        ax.set_ylim(-1.35, 1.35)
        ax.set_aspect("equal")

    draw_graph(axes[0], x[i_conn], "connected", "#54A24B")
    draw_graph(axes[1], x[i_disc], "disconnected", "#E45756")

    # the pre-processing circuit for the connected example
    ax = axes[2]
    bits = x[i_conn]
    ax.set_title("feature map", fontsize=9.5)
    n_show = 28
    for q in range(8):
        ax.plot([0, n_show + 1], [-q, -q], color="#bbb", lw=1.0, zorder=1)
        ax.text(-0.6, -q, f"$q_{q}$", ha="right", va="center", fontsize=7.5)
    for k in range(n_show):
        a, b = pairs[k]
        on = bool(bits[k])
        col = "#333" if on else "#dcdcdc"
        ax.plot([k + 1, k + 1], [-a, -b], color=col, lw=1.0, zorder=2)
        for w in (a, b):
            ax.plot([k + 1], [-w], marker="o", ms=3.2, color=col, zorder=3)
    ax.set_xlim(-2.0, n_show + 1.5)
    ax.set_ylim(-7.8, 1.4)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1-task-and-encoding.png"), bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig 2: the fixed pipeline
# --------------------------------------------------------------------------
def fig_pipeline():
    fig, ax = plt.subplots(figsize=(10.5, 2.4))
    ax.set_axis_off()
    ax.grid(False)

    def box(x, w, label, colour, h=0.9, y=0.6):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08",
                                    facecolor=colour, edgecolor="#555", lw=0.8))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=8)

    x = 0.2
    box(x, 0.7, "$|0\\rangle^{\\otimes 8}$", "#eee")
    x += 0.9
    for upload in range(3):
        box(x, 1.5, "feature map\n(28 IsingZZ)", "#DCE7F2")
        x += 1.7
        for rep in range(2):
            box(x, 1.35, "ansatz block\n(evolved)", "#FCE3C8")
            x += 1.55
        x += 0.15
    box(x, 1.9, "$\\langle Z\\rangle$ mean\n$\\rightarrow$ gain, bias", "#DFF0DA")
    ax.annotate("", xy=(x + 2.35, 1.05), xytext=(x + 1.95, 1.05),
                arrowprops=dict(arrowstyle="->", lw=1.0))
    ax.text(x + 2.4, 1.05, "$\\pm 1$", va="center", fontsize=9)

    ax.set_xlim(0, x + 3.2)
    ax.set_ylim(0.3, 2.2)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2-pipeline.png"), bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig 3: the seed circuit
# --------------------------------------------------------------------------
def fig_seed():
    """The seed ansatz block: RY, RZ, a CZ line chain, RZ. 24 free parameters."""
    fig, ax = plt.subplots(figsize=(7.6, 3.2))
    ax.set_axis_off()
    ax.grid(False)
    col = {"RY": "#F58518", "RZ": "#4C78A8"}

    layers = [("RY", "$ry_0 \\dots ry_7$", None),
              ("RZ", "$rz^{pre}_0 \\dots rz^{pre}_7$", None),
              ("CZ", "CZ line chain", [(i, i + 1) for i in range(7)]),
              ("RZ", "$rz^{post}_0 \\dots rz^{post}_7$", None)]

    slot = 0
    marks = []
    for kind, label, edges in layers:
        if edges is None:
            for q in range(8):
                ax.add_patch(FancyBboxPatch((slot + 0.15, -q - 0.28), 0.7, 0.56,
                                            boxstyle="round,pad=0.02,rounding_size=0.06",
                                            facecolor=col[kind], edgecolor="none"))
                ax.text(slot + 0.5, -q, kind, ha="center", va="center",
                        fontsize=6.5, color="white")
            marks.append((slot + 0.5, label))
            slot += 2.0
        else:
            for m, (a, b) in enumerate(edges):
                x = slot + m * 0.5
                ax.plot([x, x], [-a, -b], color="#333", lw=0.9, zorder=2)
                ax.plot([x, x], [-a, -b], marker="o", ms=3.0, color="#333",
                        ls="none", zorder=3)
            marks.append((slot + len(edges) * 0.5 / 2, label))
            slot += len(edges) * 0.5 + 1.5

    for q in range(8):
        ax.plot([-0.1, slot - 1.0], [-q, -q], color="#ccc", lw=0.9, zorder=1)
        ax.text(-0.35, -q, f"$q_{q}$", ha="right", va="center", fontsize=7.5)
    for x, name in marks:
        ax.text(x, 0.85, name, ha="center", fontsize=7.2, color="#444")
    ax.set_xlim(-1.2, slot - 0.7)
    ax.set_ylim(-7.9, 1.5)
    ax.set_title("The seed ansatz block", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3-seed-circuit.png"), bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig 4: scores
# --------------------------------------------------------------------------
def fig_scores():
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.6), sharey=True)
    settings = [("scratch", "from scratch"), ("continue", "continued")]
    arms_by_setting = {"scratch": ARMS, "continue": ARMS + ["frontier-no-gpt"]}

    for ax, (setting, title) in zip(axes, settings):
        arms = arms_by_setting[setting]
        for i, arm in enumerate(arms):
            bests = [max(r["score"] for r in rs) for rs in runs(setting, arm).values()]
            m, lo, hi = boot_ci(bests)
            jitter = np.random.default_rng(3).normal(0, 0.055, len(bests))
            ax.scatter(i + jitter, bests, s=26, color=C[arm], alpha=0.55,
                       edgecolor="none", zorder=2)
            ax.errorbar([i], [m], yerr=[[m - lo], [hi - m]], fmt="D", ms=6,
                        color=C[arm], capsize=4, lw=1.6, zorder=3,
                        markeredgecolor="white")
            ax.text(i, ax.get_ylim()[0], "", ha="center")
        if setting == "continue":
            ax.axhline(0.4477, color="#888", ls="--", lw=1.0, zorder=1)
            ax.text(len(arms) - 0.5, 0.4477 + 0.02, "handed-over parent (0.448)",
                    ha="right", fontsize=7.5, color="#666")
        ax.axhline(0.0, color="#bbb", lw=1.0, zorder=1)
        ax.set_xticks(range(len(arms)))
        ax.set_xticklabels([NICE[a] for a in arms])
        ax.set_title(title, fontsize=9.5)
        ax.set_xlim(-0.6, len(arms) - 0.4)
    axes[0].set_ylabel("best score reached in the run\n(0 = seed circuit, 1 = best known)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4-best-scores.png"), bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig 4: who builds the symmetry
# --------------------------------------------------------------------------
def fig_build_rates():
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4), sharey=True)
    specs = [("all-singular-tied", "tied 8-wire rotation layer"),
             ("all-double", "28-pair entangler")]
    settings = ["scratch", "continue"]
    width = 0.36

    for ax, (lab, title) in zip(axes, specs):
        for j, setting in enumerate(settings):
            xs, ps, los, his, cols = [], [], [], [], []
            for i, arm in enumerate(ARMS):
                rr = runs(setting, arm)
                k = sum(any(lab in r["circuit"]["labels"] for r in rs) for rs in rr.values())
                p, lo, hi = wilson(k, len(rr))
                xs.append(i + (j - 0.5) * width)
                ps.append(p); los.append(p - lo); his.append(hi - p); cols.append(C[arm])
            ax.bar(xs, ps, width=width * 0.92, color=cols,
                   alpha=1.0 if setting == "scratch" else 0.45,
                   edgecolor="#444", lw=0.6,
                   label="from scratch" if setting == "scratch" else "continued")
            ax.errorbar(xs, ps, yerr=[los, his], fmt="none", ecolor="#333",
                        capsize=3, lw=0.9)
        ax.set_xticks(range(len(ARMS)))
        ax.set_xticklabels([NICE[a] for a in ARMS])
        ax.set_ylim(0, 1.05)
        ax.set_title(title, fontsize=9.5)
    axes[0].set_ylabel("share of runs that built it at least once")
    h, l = axes[0].get_legend_handles_labels()
    axes[1].legend(h[:2], l[:2], fontsize=8, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5-build-rates.png"), bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig 5: say versus build
# --------------------------------------------------------------------------
def fig_say_build():
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4))

    # left: run-level identify / claim / build
    ax = axes[0]
    stages = [("identify", "mentions it"), ("claim", "claims to build it"),
              ("build", "actually builds it")]
    width = 0.26
    for si, (stage, name) in enumerate(stages):
        xs, ps, los, his = [], [], [], []
        for i, arm in enumerate(ARMS):
            rr = {}
            for setting in ("scratch", "continue"):
                rr.update(runs(setting, arm))
            k = 0
            for rs in rr.values():
                if stage == "identify":
                    hit = any(r["note"] and (set(r["note"]["flags"]) & {
                        "names_perm", "all_pairs", "task_pairs"}) for r in rs)
                elif stage == "claim":
                    hit = any(r["note"] and r["note"]["build_claim"] for r in rs)
                else:
                    hit = any("all-double" in r["circuit"]["labels"] for r in rs)
                k += bool(hit)
            p, lo, hi = wilson(k, len(rr))
            xs.append(i + (si - 1) * width)
            ps.append(p); los.append(p - lo); his.append(hi - p)
        ax.bar(xs, ps, width=width * 0.9, color=["#9ecae1", "#6baed6", "#2171b5"][si],
               edgecolor="#444", lw=0.5, label=name)
        ax.errorbar(xs, ps, yerr=[los, his], fmt="none", ecolor="#333", capsize=3, lw=0.9)
    ax.set_xticks(range(len(ARMS)))
    ax.set_xticklabels([NICE[a] for a in ARMS])
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("share of runs")
    ax.set_title("per run", fontsize=9.5)
    ax.legend(fontsize=7.5, frameon=False, ncol=1, loc="upper left")

    # right: agreement between note and circuit, per proposal
    ax = axes[1]
    cells = []
    for arm in ARMS:
        rs = [r for r in ROWS if r["arm"] == arm and r["note"]]
        say = np.array([bool(r["note"]["build_claim"]) for r in rs])
        build = np.array([("all-double" in r["circuit"]["labels"]) for r in rs])
        cells.append([np.sum(say & build), np.sum(say & ~build),
                      np.sum(~say & build), np.sum(~say & ~build)])
    cells = np.array(cells, dtype=float)
    frac = cells / cells.sum(axis=1, keepdims=True)
    names = ["said and built", "said, did not build",
             "built without saying", "neither"]
    cols = ["#2171b5", "#E45756", "#F2B701", "#dddddd"]
    bottom = np.zeros(len(ARMS))
    for j in range(4):
        ax.bar(range(len(ARMS)), frac[:, j], bottom=bottom, color=cols[j],
               edgecolor="white", lw=0.8, label=names[j])
        for i in range(len(ARMS)):
            if frac[i, j] > 0.045:
                ax.text(i, bottom[i] + frac[i, j] / 2, f"{int(cells[i, j])}",
                        ha="center", va="center", fontsize=7.5,
                        color="white" if j < 2 else "#333")
        bottom += frac[:, j]
    ax.set_xticks(range(len(ARMS)))
    ax.set_xticklabels([NICE[a] for a in ARMS])
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("share of proposals")
    ax.set_title("per proposal", fontsize=9.5)
    ax.legend(fontsize=7.5, frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5))
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig6-say-vs-build.png"), bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig 6: score against structure
# --------------------------------------------------------------------------
def fig_score_by_structure():
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    groups = [
        ("no shared structure", lambda r: not ({"all-singular-tied", "all-double"} &
                                               set(r["circuit"]["labels"]))),
        ("tied rotations only", lambda r: "all-singular-tied" in r["circuit"]["labels"]
                                          and "all-double" not in r["circuit"]["labels"]),
        ("all-28-pair entangler", lambda r: "all-double" in r["circuit"]["labels"]),
    ]
    for i, (name, f) in enumerate(groups):
        xs = [r["score"] for r in ROWS if f(r)]
        m, lo, hi = boot_ci(xs)
        jit = np.random.default_rng(11).normal(0, 0.07, len(xs))
        ax.scatter(np.full(len(xs), i) + jit, xs, s=8, alpha=0.18,
                   color="#4C78A8", edgecolor="none", zorder=2)
        ax.errorbar([i], [m], yerr=[[m - lo], [hi - m]], fmt="D", ms=7,
                    color="#E45756", capsize=5, lw=1.8, zorder=3,
                    markeredgecolor="white")
        ax.text(i, 1.85, f"n = {len(xs)}", ha="center", fontsize=8, color="#555")
    ax.set_xticks(range(3))
    ax.set_xticklabels([g[0] for g in groups], fontsize=8.5)
    ax.axhline(0, color="#bbb", lw=1.0)
    ax.set_ylim(-3.0, 2.0)
    ax.set_ylabel("score of the proposal")
    ax.set_title("Score by circuit structure", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig7-score-by-structure.png"), bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig 7: the winning circuit
# --------------------------------------------------------------------------
def fig_winner():
    layers = [
        ("RY", "collective_ry_encode", None),
        ("CZ", None, [(7, 0), (1, 6), (2, 5), (3, 4), (7, 1), (2, 0), (3, 6), (4, 5),
                      (7, 2), (3, 1), (4, 0), (5, 6), (7, 3), (4, 2), (5, 1), (6, 0),
                      (7, 4), (5, 3), (6, 2), (0, 1), (7, 5), (6, 4), (0, 3), (1, 2),
                      (7, 6), (0, 5), (1, 4), (2, 3)]),
        ("RZ", "collective_rz_phase", None),
        ("RY", "collective_ry_decode", None),
    ]
    fig, ax = plt.subplots(figsize=(10.0, 3.2))
    ax.set_axis_off()
    ax.grid(False)
    col = {"RY": "#F58518", "RZ": "#4C78A8"}

    slot = 0
    marks = []
    for kind, param, edges in layers:
        if edges is None:
            for q in range(8):
                ax.add_patch(FancyBboxPatch((slot + 0.15, -q - 0.28), 0.7, 0.56,
                                            boxstyle="round,pad=0.02,rounding_size=0.06",
                                            facecolor=col[kind], edgecolor="none"))
                ax.text(slot + 0.5, -q, kind, ha="center", va="center",
                        fontsize=6.5, color="white")
            marks.append((slot + 0.5, param))
            slot += 2.6
        else:
            for m, (a, b) in enumerate(edges):
                x = slot + m * 0.42
                ax.plot([x, x], [-a, -b], color="#333", lw=0.9, zorder=2)
                ax.plot([x, x], [-a, -b], marker="o", ms=3.0, color="#333",
                        ls="none", zorder=3)
            marks.append((slot + len(edges) * 0.42 / 2, "28 CZ = every pair of K8"))
            slot += len(edges) * 0.42 + 0.9

    for q in range(8):
        ax.plot([-0.1, slot], [-q, -q], color="#ccc", lw=0.9, zorder=1)
        ax.text(-0.35, -q, f"$q_{q}$", ha="right", va="center", fontsize=7.5)
    for x, name in marks:
        ax.text(x, 0.85 if "CZ" in name else 1.15, name.replace("_", " "), ha="center", fontsize=7.2, color="#444")
    ax.set_xlim(-1.4, slot + 0.3)
    ax.set_ylim(-7.9, 1.5)
    ax.set_title("permutation_twist", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig8-winning-circuit.png"), bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# fig 9: score against generation, one 50-generation run per ensemble
# --------------------------------------------------------------------------
def fig_trajectories():
    """Full 50-generation trajectories, untruncated, read straight from disk.

    One run per ensemble: the median run by final best score among that arm's
    50-generation from-scratch runs.
    """
    import sqlite3
    picks = [("weak", "weak_r2"), ("mid", "mid_r3"), ("frontier", "frontier_r1")]
    fig, ax = plt.subplots(figsize=(7.4, 3.6))

    for arm, run in picks:
        db = os.path.join(ROOT, "transfer-sn", f"results_or_{run}", "programs.sqlite")
        con = sqlite3.connect(db)
        pts = sorted((int(g), float(sc)) for g, sc in con.execute(
            "select generation, combined_score from programs "
            "where combined_score is not null"))
        con.close()
        gens = [g for g, _ in pts]
        best, run_best = [], -1e9
        for _, sc in pts:
            run_best = max(run_best, sc)
            best.append(run_best)
        ax.scatter(gens, [sc for _, sc in pts], s=9, color=C[arm], alpha=0.28,
                   edgecolor="none", zorder=2)
        ax.step(gens, best, where="post", color=C[arm], lw=1.7, zorder=3,
                label=f"{arm} ({run})")

    ax.axvline(GEN_CAP, color="#888", ls="--", lw=1.0, zorder=1)
    ax.text(GEN_CAP + 0.7, ax.get_ylim()[0] + 0.1, "truncation point",
            fontsize=7.5, color="#666", rotation=90, va="bottom")
    ax.axhline(0, color="#bbb", lw=1.0, zorder=1)
    ax.set_xlabel("generation")
    ax.set_ylabel("score")
    ax.set_xlim(-1, 51)
    ax.set_ylim(-3.0, 1.5)
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.set_title("Score against generation", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig9-trajectories.png"), bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_encoding()
    fig_pipeline()
    fig_seed()
    fig_scores()
    fig_build_rates()
    fig_say_build()
    fig_score_by_structure()
    fig_winner()
    fig_trajectories()
    fig_who_found_it()
    fig_record_counts()
    print("wrote figures to", FIG)


# --------------------------------------------------------------------------
# fig 10/11: which frontier model found each best-so-far record
# --------------------------------------------------------------------------
MODELS = ["gpt-5.6-sol", "claude-opus-4.6", "gemini-3.1-pro-preview"]
MC = {"gpt-5.6-sol": "#E45756",
      "claude-opus-4.6": "#4C78A8",
      "gemini-3.1-pro-preview": "#F58518"}


def _frontier_records():
    """Best-so-far trace per frontier run, and who set each record.

    Read from the raw label file rather than ROWS: the inherited generations of
    a continued run are not the ensemble's own proposals, but they do set the
    starting best-so-far, so they must stay in the trace. Only own proposals can
    be credited with a record. From-scratch runs are shown untruncated.
    """
    labels = json.load(open(os.path.join(HERE, "data/labels.json")))
    by_run = {}
    for r in labels:
        if not r["arm"].startswith("frontier") or not r["parsed"]:
            continue
        if r["score"] is None:
            continue
        by_run.setdefault(r["run_id"], []).append(r)

    out = []
    for run_id, rs in sorted(by_run.items()):
        rs.sort(key=lambda r: r["generation"])
        best, trace, recs = -1e9, [], []
        for r in rs:
            if r["score"] > best:
                best = r["score"]
                if r["own"]:
                    recs.append((r["generation"], r["score"],
                                 (r["model"] or "").split("/")[-1]))
            trace.append((r["generation"], best))
        out.append({"run_id": run_id, "arm": rs[0]["arm"],
                    "setting": rs[0]["setting"], "trace": trace,
                    "records": recs,
                    "own": [r for r in rs if r["own"]]})
    return out


def fig_who_found_it():
    data = _frontier_records()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), sharey=True,
                             gridspec_kw={"width_ratios": [1.55, 1]})

    for ax, (setting, title) in zip(axes, [("scratch", "from scratch"),
                                           ("continue", "continued")]):
        rows = [d for d in data if d["setting"] == setting]
        for d in rows:
            gens = [g for g, _ in d["trace"]]
            best = [b for _, b in d["trace"]]
            no_gpt = d["arm"] == "frontier-no-gpt"
            ax.step(gens, best, where="post", lw=1.3, zorder=2,
                    color=C["frontier-no-gpt"] if no_gpt else C["frontier"],
                    ls="--" if no_gpt else "-", alpha=0.75)
            for g, s, m in d["records"]:
                ax.scatter([g], [s], s=44, zorder=4, color=MC.get(m, "#999"),
                           edgecolor="white", lw=0.9)
        ax.axhline(0, color="#bbb", lw=1.0, zorder=1)
        ax.set_xlabel("generation")
        ax.set_title(title, fontsize=10)
    axes[0].set_ylabel("best score so far")
    axes[1].set_xlim(-0.3, 7.5)

    handles = [plt.Line2D([], [], color=C["frontier"], lw=1.3, label="frontier"),
               plt.Line2D([], [], color=C["frontier-no-gpt"], lw=1.3, ls="--",
                          label="frontier without GPT")]
    handles += [plt.Line2D([], [], ls="none", marker="o", ms=6.5,
                           markeredgecolor="white", color=MC[m], label=m)
                for m in MODELS]
    axes[1].legend(handles=handles, fontsize=7.5, frameon=False,
                   loc="lower right")
    fig.suptitle("Best-so-far score in the frontier runs, coloured by the model "
                 "that set each record", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig10-who-found-it.png"), bbox_inches="tight")
    plt.close(fig)


def fig_record_counts():
    """Records and proposals per model, over the runs that use all three models."""
    data = [d for d in _frontier_records() if d["arm"] == "frontier"]
    recs = {m: 0 for m in MODELS}
    props = {m: 0 for m in MODELS}
    for d in data:
        for _, _, m in d["records"]:
            recs[m] = recs.get(m, 0) + 1
        for r in d["own"]:
            m = (r["model"] or "").split("/")[-1]
            props[m] = props.get(m, 0) + 1

    n_rec, n_prop = sum(recs.values()), sum(props.values())
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    x = np.arange(len(MODELS))
    ax.bar(x, [recs[m] for m in MODELS], width=0.62,
           color=[MC[m] for m in MODELS])
    for i, m in enumerate(MODELS):
        ax.text(i, recs[m] + 0.25,
                f"{recs[m]}/{n_rec} records\n{props[m]}/{n_prop} proposals",
                ha="center", va="bottom", fontsize=7.5, color="#444")
    ax.set_xticks(x)
    ax.set_xticklabels(MODELS, fontsize=8)
    ax.set_ylabel("best-so-far records set")
    ax.set_ylim(0, max(recs.values()) * 1.45)
    ax.set_title("Who sets the records in the full frontier ensemble", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig11-record-counts.png"), bbox_inches="tight")
    plt.close(fig)
