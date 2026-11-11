"""Generate every figure for the anonymized-motif paper."""
import json
import math
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle

SP = Path(__file__).resolve().parent
OUT = Path.home() / "QuantumAnsatz/qml-ea/tic-tac-toe/paper-anon-motif/figs"
OUT.mkdir(parents=True, exist_ok=True)

stats = json.loads((SP / "stats.json").read_text())
runs = json.loads((SP / "rundata.json").read_text())

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.labelsize": 9,
    "axes.titlesize": 9.5, "legend.fontsize": 8, "xtick.labelsize": 8,
    "ytick.labelsize": 8, "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight",
})

C_WIN, C_OFF, C_EDGE, C_NODE = "#1b7837", "#c2453a", "#b8b8b8", "#e8e8e8"

# Board layout for the ring+centre labelling used by the original task.
BOARD = {0: (0, 2), 1: (1, 2), 2: (2, 2),
         7: (0, 1), 8: (1, 1), 3: (2, 1),
         6: (0, 0), 5: (1, 0), 4: (2, 0)}
RING = {q: (math.cos(math.pi / 2 - 2 * math.pi * i / 8),
            math.sin(math.pi / 2 - 2 * math.pi * i / 8))
        for i, q in enumerate([0, 1, 2, 3, 4, 5, 6, 7])}
RING[8] = (0.0, 0.0)

LEAKY = stats["leaky"]
ANON_TAGS = [t for t in ("haiku", "sonnet", "gpt56sol") if t in stats]


def draw_nodes(ax, pos, labels=True, r=0.15):
    for q, (x, y) in pos.items():
        ax.add_patch(Circle((x, y), r, fc=C_NODE, ec="#555", lw=0.8, zorder=3))
        if labels:
            ax.text(x, y, str(q), ha="center", va="center", fontsize=7.5, zorder=4)


def draw_triple(ax, pos, t, color, alpha=0.30, lw=1.2):
    pts = [pos[q] for q in t]
    ax.add_patch(Polygon(pts, closed=True, fc=color, ec=color,
                         alpha=alpha, lw=lw, zorder=2))


def tidy(ax, lim=None):
    ax.set_aspect("equal")
    ax.axis("off")
    if lim:
        ax.set_xlim(lim[0])
        ax.set_ylim(lim[1])


# ---------------------------------------------------------------- figure 1
def fig_task():
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5))
    a, b, c = axes

    for x in range(3):
        for y in range(3):
            a.add_patch(plt.Rectangle((x - .5, y - .5), 1, 1, fc="white",
                                      ec="#666", lw=1.0))
    for q, (x, y) in BOARD.items():
        a.text(x, y, str(q), ha="center", va="center", fontsize=11)
    a.set_title("(a) board cell $\\rightarrow$ qubit index")
    tidy(a, [(-.6, 2.6), (-.6, 2.6)])

    for x in range(3):
        for y in range(3):
            b.add_patch(plt.Rectangle((x - .5, y - .5), 1, 1, fc="white",
                                      ec="#ddd", lw=0.8))
    for t in LEAKY["invisible"] + [tuple(w) for w in runs["leaky"]["win"]]:
        pass
    for w in runs["leaky"]["win"]:
        xs = [BOARD[q][0] for q in w]
        ys = [BOARD[q][1] for q in w]
        b.plot(xs, ys, "-", color=C_WIN, lw=2.2, alpha=.55, solid_capstyle="round")
    for q, (x, y) in BOARD.items():
        b.add_patch(Circle((x, y), .13, fc=C_NODE, ec="#555", lw=.7, zorder=3))
        b.text(x, y, str(q), ha="center", va="center", fontsize=7.5, zorder=4)
    b.set_title("(b) the 8 winning lines")
    tidy(b, [(-.6, 2.6), (-.6, 2.6)])

    for e in runs["leaky"]["edges"]:
        (x1, y1), (x2, y2) = RING[e[0]], RING[e[1]]
        c.plot([x1, x2], [y1, y2], "-", color=C_EDGE, lw=1.4, zorder=1)
    draw_nodes(c, RING)
    c.set_title("(c) hardware connectivity")
    tidy(c, [(-1.35, 1.35), (-1.35, 1.35)])

    fig.savefig(OUT / "fig_task.pdf"); fig.savefig(SP / "fig_task.png", dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------- figure 2
def fig_anonymize():
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 3.1))
    meta_edges = runs["haiku"]["edges"]
    inv = {tuple(t) for t in stats["haiku"]["invisible"]}

    ax = axes[0]
    for e in runs["leaky"]["edges"]:
        (x1, y1), (x2, y2) = BOARD[e[0]], BOARD[e[1]]
        ax.plot([x1, x2], [y1, y2], "-", color=C_EDGE, lw=1.2, zorder=1)
    # On the board the three cells of a line are collinear, so a filled
    # triangle would have zero area: draw them as strokes instead.
    for w in runs["leaky"]["win"]:
        ax.plot([BOARD[q][0] for q in w], [BOARD[q][1] for q in w], "-",
                color=C_WIN, lw=2.6, alpha=.55, solid_capstyle="round", zorder=2)
    draw_nodes(ax, BOARD, r=.13)
    ax.set_title("(a) original labelling:\nwinning lines are rows/cols/diagonals")
    tidy(ax, [(-.6, 2.6), (-.6, 2.6)])

    ax = axes[1]
    for e in meta_edges:
        (x1, y1), (x2, y2) = RING[e[0]], RING[e[1]]
        ax.plot([x1, x2], [y1, y2], "-", color=C_EDGE, lw=1.2, zorder=1)
    for w in runs["haiku"]["win"]:
        is_inv = tuple(sorted(w)) in inv
        draw_triple(ax, RING, w, "#7b3294" if is_inv else C_WIN,
                    alpha=.34 if is_inv else .18)
    draw_nodes(ax, RING)
    ax.set_title("(b) after the secret relabelling:\nno visible geometry")
    tidy(ax, [(-1.35, 1.35), (-1.35, 1.35)])

    fig.text(0.5, -0.03, "purple = the two lines with no hardware link "
             "(findable only from the score)", ha="center", fontsize=7.5,
             color="#7b3294")
    fig.savefig(OUT / "fig_anonymize.pdf"); fig.savefig(SP / "fig_anonymize.png", dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------- figure 3
def fig_strata():
    st = stats["haiku"]["strata"]
    degs = sorted(int(d) for d in st)
    tot = [st[str(d)]["n"] for d in degs]
    win = [st[str(d)]["n_win"] for d in degs]

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6))
    ax = axes[0]
    xs = range(len(degs))
    ax.bar(xs, tot, color="#d9d9d9", ec="#999", label="all triples", width=.62)
    ax.bar(xs, win, color=C_WIN, label="winning lines", width=.62)
    for i, (t, w) in enumerate(zip(tot, win)):
        ax.text(i, t + 1.2, f"{w}/{t}", ha="center", fontsize=8)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"{d}" for d in degs])
    ax.set_xlabel("hardware links inside the triple")
    ax.set_ylabel("number of triples")
    ax.set_ylim(0, max(tot) * 1.22)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("(a) where the winning lines sit")

    ax = axes[1]
    rates = [st[str(d)]["n_win"] / st[str(d)]["n"] for d in degs]
    ax.bar(xs, rates, color=["#9ecae1", "#9ecae1", "#3182bd"], width=.62)
    ax.axhline(stats["haiku"]["p_uni"], color=C_OFF, ls="--", lw=1.3,
               label=f"uniform chance = {stats['haiku']['p_uni']:.3f}")
    for i, r in enumerate(rates):
        ax.text(i, r + .012, f"{r:.3f}", ha="center", fontsize=8)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"{d}" for d in degs])
    ax.set_xlabel("hardware links inside the triple")
    ax.set_ylabel("P(triple is a winning line)")
    ax.set_ylim(0, .33)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("(b) the confound")
    fig.savefig(OUT / "fig_strata.pdf"); fig.savefig(SP / "fig_strata.png", dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------- figure 4
def fig_circuits():
    tags = ["leaky"] + ANON_TAGS
    fig, axes = plt.subplots(1, len(tags), figsize=(2.25 * len(tags), 2.85))
    if len(tags) == 1:
        axes = [axes]
    for ax, tag in zip(axes, tags):
        s = stats[tag]
        win = {frozenset(t) for t in runs[tag]["win"]}
        pos = BOARD if tag == "leaky" else RING
        for e in runs[tag]["edges"]:
            (x1, y1), (x2, y2) = pos[e[0]], pos[e[1]]
            ax.plot([x1, x2], [y1, y2], "-", color=C_EDGE, lw=1.1, zorder=1)
        seen = {}
        for t in s["best"]["triples"]:
            key = tuple(sorted(t))
            seen[key] = seen.get(key, 0) + 1
        for t, mult in seen.items():
            on = frozenset(t) in win
            draw_triple(ax, pos, t, C_WIN if on else C_OFF,
                        alpha=.18 + .10 * min(mult, 3))
        draw_nodes(ax, pos, r=.13 if tag == "leaky" else .15)
        b = s["best"]
        name = {"leaky": "Leaky run", "haiku": "Haiku-4.5",
                "sonnet": "Sonnet-5", "gpt56sol": "GPT-5.6-sol"}[tag]
        ax.set_title(f"{name}\n{b['n_win']}/{b['n_tr']} on lines, "
                     f"{b['covered']}/8 lines\nval acc {b['val']*100:.1f}%",
                     fontsize=8.5)
        lim = [(-.6, 2.6), (-.75, 2.6)] if tag == "leaky" else [(-1.35, 1.35), (-1.5, 1.35)]
        tidy(ax, lim)
    fig.text(0.5, -0.02, "green = three-qubit gate on a winning line, "
             "red = off a winning line", ha="center", fontsize=7.5)
    fig.savefig(OUT / "fig_circuits.pdf"); fig.savefig(SP / "fig_circuits.png", dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------- figure 5
def fig_trajectory():
    tags = ["leaky"] + ANON_TAGS
    colors = {"leaky": "#333333", "haiku": "#1f78b4",
              "sonnet": "#e08214", "gpt56sol": "#7b3294"}
    names = {"leaky": "Leaky (answer given)", "haiku": "Haiku-4.5 (hidden)",
             "sonnet": "Sonnet-5 (hidden)", "gpt56sol": "GPT-5.6-sol (hidden)"}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7))

    ax = axes[0]
    for tag in tags:
        tr = stats[tag]["trajectory"]
        g = [p["gen"] for p in tr] + [stats[tag]["max_gen"] - 1]
        v = [p["score"] for p in tr] + [tr[-1]["score"]]
        ax.step(g, v, where="post", color=colors[tag], lw=1.6, label=names[tag])
    ax.set_xlabel("generation")
    ax.set_ylabel("best-so-far score")
    ax.set_title("(a) search progress")
    ax.legend(frameon=False, fontsize=7.2)

    ax = axes[1]
    for tag in tags:
        tr = stats[tag]["trajectory"]
        g = [p["gen"] for p in tr] + [stats[tag]["max_gen"] - 1]
        f = [(p["n_win"] / p["n_tr"] if p["n_tr"] else 0.0) for p in tr]
        f = f + [f[-1]]
        ax.step(g, f, where="post", color=colors[tag], lw=1.6, label=names[tag])
    ax.axhline(stats["haiku"]["p_uni"], color=C_OFF, ls="--", lw=1.2)
    ax.axhline(stats["haiku"]["p_e2"], color="#3182bd", ls=":", lw=1.4)
    ax.text(1, stats["haiku"]["p_uni"] + .015, "uniform chance 0.095",
            fontsize=6.8, color=C_OFF)
    ax.text(1, stats["haiku"]["p_e2"] + .015, "fair chance 0.273",
            fontsize=6.8, color="#3182bd")
    ax.set_xlabel("generation")
    ax.set_ylabel("fraction of gates on winning lines")
    ax.set_ylim(-.03, 1.05)
    ax.set_title("(b) motif usage in the best circuit")
    fig.savefig(OUT / "fig_trajectory.pdf"); fig.savefig(SP / "fig_trajectory.png", dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------- figure 6
def fig_summary():
    tags = ["leaky"] + ANON_TAGS
    names = {"leaky": "Leaky\n(answer given)", "haiku": "Haiku-4.5",
             "sonnet": "Sonnet-5", "gpt56sol": "GPT-5.6-sol"}
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.4))
    xs = range(len(tags))
    cols = ["#333333"] + ["#1f78b4", "#e08214", "#7b3294"][:len(ANON_TAGS)]

    ax = axes[0]
    v = [stats[t]["population"]["frac"] for t in tags]
    ax.bar(xs, v, color=cols, width=.6)
    ax.axhline(stats["haiku"]["p_e2"], color="#3182bd", ls=":", lw=1.4)
    ax.axhline(stats["haiku"]["p_uni"], color=C_OFF, ls="--", lw=1.2)
    for i, x in enumerate(v):
        ax.text(i, x + .03, f"{x:.2f}", ha="center", fontsize=8)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("fraction on winning lines")
    ax.set_title("(a) all gates placed")

    ax = axes[1]
    v = [stats[t]["best"]["covered"] for t in tags]
    ax.bar(xs, v, color=cols, width=.6)
    for i, x in enumerate(v):
        ax.text(i, x + .18, str(x), ha="center", fontsize=8)
    ax.set_ylim(0, 9.2)
    ax.set_ylabel("distinct lines found (of 8)")
    ax.set_title("(b) coverage")

    ax = axes[2]
    v = [len(stats[t]["best"]["invisible_found"]) for t in tags]
    ax.bar(xs, v, color=cols, width=.6)
    for i, x in enumerate(v):
        ax.text(i, x + .05, str(x), ha="center", fontsize=8)
    ax.set_ylim(0, 2.5)
    ax.set_ylabel("hidden lines found (of 2)")
    ax.set_title("(c) the decisive test")

    for ax in axes:
        ax.set_xticks(list(xs))
        ax.set_xticklabels([names[t] for t in tags], fontsize=7.2)
    fig.savefig(OUT / "fig_summary.pdf"); fig.savefig(SP / "fig_summary.png", dpi=110)
    plt.close(fig)


for fn in (fig_task, fig_anonymize, fig_strata, fig_circuits,
           fig_trajectory, fig_summary):
    fn()
    print("wrote", fn.__name__)
print("figures in", OUT)
