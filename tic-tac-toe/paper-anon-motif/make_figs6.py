"""Figure: why the zero-context 67% is not a discovery.

(a) the denominator is a choice the model makes, and it collapses tenfold
(b) motif usage spans two orders of magnitude while accuracy does not move
(c) the claim shrinks monotonically as the measure is tightened
"""
import json
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

PURPLE, BLUE, ORANGE = "#7b3294", "#1f78b4", "#e08214"
ARMS = [("zc_ttt_haiku", "Haiku-4.5", BLUE),
        ("zc_ttt_sonnet", "Sonnet-5", ORANGE),
        ("zc_ttt_gpt56sol", "GPT-5.6-sol", PURPLE)]

WIN = {frozenset(t) for t in D["keys"]["ttt"]["win"]}
EDGES = {frozenset(e) for e in D["keys"]["ttt"]["edges"]}
HIDDEN = {t for t in WIN
          if not any(frozenset(p) in EDGES for p in combinations(sorted(t), 2))}


def triples(spec):
    return [frozenset(int(w) for w in it["wires"])
            for it in (spec or [])
            if isinstance(it, dict)
            and str(it.get("gate", "")).upper() in ("ZZZ", "CCRZ")
            and isinstance(it.get("wires"), (list, tuple)) and len(it["wires"]) == 3]


rows = []
for tag, name, col in ARMS:
    run = D["runs"][tag]
    ok = [p for p in run["programs"] if p["correct"] and p["score"] is not None]
    pl = [t for p in ok for t in triples(p["spec"])]
    distinct = set(pl)
    rows.append({
        "name": name, "col": col,
        "n_progs": len(ok),
        "n_using": sum(1 for p in ok if triples(p["spec"])),
        "n_pl": len(pl),
        "n_win": sum(1 for t in pl if t in WIN),
        "n_dist": len(distinct),
        "n_dist_win": sum(1 for t in distinct if t in WIN),
        "n_lines": len(distinct & WIN),
        "n_hidden": len(distinct & HIDDEN),
        "test": 100 * (S[tag]["motif"]["best"]["test"] or 0),
    })

fig, axes = plt.subplots(1, 3, figsize=(9.9, 3.0))
fig.subplots_adjust(wspace=.40)

# (a) the denominator collapses -----------------------------------------------
ax = axes[0]
x = range(3)
ax.bar(x, [r["n_pl"] for r in rows], color=[r["col"] for r in rows],
       width=.6, alpha=.35, label="gates placed")
ax.bar(x, [r["n_win"] for r in rows], color=[r["col"] for r in rows],
       width=.6, label="on a true line")
for i, r in enumerate(rows):
    ax.text(i, r["n_pl"] + 5, f'{r["n_win"]}/{r["n_pl"]}', ha="center", fontsize=8)
    pct = 100 * r["n_win"] / r["n_pl"]
    ax.text(i, r["n_pl"] + 24, f'= {pct:.1f}%' if pct < 10 else f'= {pct:.0f}%',
            ha="center", fontsize=8, color=r["col"], fontweight="bold")
ax.set_xticks(list(x))
ax.set_xticklabels([r["name"] for r in rows], fontsize=7.5)
ax.set_ylabel("three-qubit gates placed")
ax.set_ylim(0, 215)
ax.legend(frameon=False, loc="upper right", fontsize=7)
ax.set_title("(a) the denominator is a choice")

# (b) usage spans 100x, accuracy does not -------------------------------------
ax = axes[1]
usage = [100 * r["n_win"] / r["n_pl"] for r in rows]
ax.bar(x, usage, color=[r["col"] for r in rows], width=.6, alpha=.55)
ax.set_xticks(list(x))
ax.set_xticklabels([r["name"] for r in rows], fontsize=7.5)
ax.set_ylabel("gates on a true line (%)")
ax.set_ylim(0, 78)
ax.set_title("(b) usage moves, accuracy does not")
ax2 = ax.twinx()
ax2.spines["top"].set_visible(False)
ax2.plot(list(x), [r["test"] for r in rows], "-o", color="#12140f", lw=1.4, ms=6,
         zorder=5)
for i, r in enumerate(rows):
    ax2.annotate(f'{r["test"]:.1f}%', (i, r["test"]), textcoords="offset points",
                 xytext=(0, 9), ha="center", fontsize=7.6)
ax2.set_ylabel("best test accuracy (%)")
ax2.set_ylim(58, 70)
ax2.text(.03, .93, "accuracy is flat, and runs the wrong way",
         transform=ax.transAxes, ha="left", fontsize=7.2, color="#c2453a")

# (c) the claim shrinks as the measure tightens -------------------------------
ax = axes[2]
metrics = [
    ("all\nplacements", lambda r: 100 * r["n_win"] / r["n_pl"]),
    ("distinct\ntriples", lambda r: 100 * r["n_dist_win"] / r["n_dist"]),
    ("lines\nfound", lambda r: 100 * r["n_lines"] / 8),
    ("hidden\nlines", lambda r: 100 * r["n_hidden"] / 2),
]
w = .26
for j, r in enumerate(rows):
    ax.bar([i + (j - 1) * w for i in range(len(metrics))],
           [f(r) for _, f in metrics], width=w, color=r["col"], label=r["name"])
ax.set_xticks(range(len(metrics)))
ax.set_xticklabels([m for m, _ in metrics], fontsize=7)
ax.set_ylabel("percent")
ax.set_ylim(0, 78)
ax.legend(frameon=False, loc="upper right", fontsize=7)
# track GPT-5.6-sol's own claim across the four measures
gpt = rows[2]
ax.plot([i + w for i in range(len(metrics))], [f(gpt) for _, f in metrics],
        "o--", color="#c2453a", lw=1.2, ms=4, zorder=6)
ax.text(1.62, 51, "GPT-5.6-sol:  67 → 43 → 38 → 0",
        fontsize=7.2, color="#c2453a", ha="center")
for i, (_, f) in enumerate(metrics):
    for j, r in enumerate(rows):
        if f(r) == 0:
            ax.text(i + (j - 1) * w, 1.4, "0", ha="center", fontsize=6.6,
                    color=r["col"])
ax.set_title("(c) tighten the measure, lose the claim")

fig.savefig(OUT / "fig_deflate.pdf")
fig.savefig(SP / "fig_deflate.png", dpi=110)
plt.close(fig)
print("wrote fig_deflate")
for r in rows:
    print(f'  {r["name"]:<12} progs {r["n_progs"]:>3} using {r["n_using"]:>3} '
          f'placements {r["n_pl"]:>3} on-line {r["n_win"]:>2} '
          f'distinct {r["n_dist"]:>2} ({r["n_dist_win"]} lines) '
          f'hidden {r["n_hidden"]} test {r["test"]:.1f}%')
