"""Two extra figures: how the proposers reason, and the recall test."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SP = Path(__file__).resolve().parent
OUT = Path.home() / "QuantumAnsatz/qml-ea/tic-tac-toe/paper-anon-motif/figs"

runs = json.loads((SP / "rundata.json").read_text())
reas = json.loads((SP / "reasoning.json").read_text())

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.labelsize": 9,
    "axes.titlesize": 9.5, "legend.fontsize": 7.6, "xtick.labelsize": 8,
    "ytick.labelsize": 8, "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight",
})

TAGS = ["leaky", "haiku", "sonnet", "gpt56sol"]
COL = {"leaky": "#333333", "haiku": "#1f78b4", "sonnet": "#e08214",
       "gpt56sol": "#7b3294"}
NAME = {"leaky": "Leaky (answer given)", "haiku": "Haiku-4.5 (hidden)",
        "sonnet": "Sonnet-5 (hidden)", "gpt56sol": "GPT-5.6-sol (hidden)"}

ROWMAJOR = {frozenset(t) for t in
            [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]}


def triples(spec):
    return [frozenset(int(w) for w in it["wires"])
            for it in (spec or [])
            if isinstance(it, dict)
            and str(it.get("gate", "")).upper() in ("ZZZ", "CCRZ")
            and isinstance(it.get("wires"), (list, tuple)) and len(it["wires"]) == 3]


# ------------------------------------------------- figure: game vocabulary
def fig_vocab():
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6))

    ax = axes[0]
    frac = []
    for t in TAGS:
        items = [i for i in reas[t] if i["desc"]]
        frac.append(sum(1 for i in items if i["leak_hits"]) / len(items))
    ax.bar(range(len(TAGS)), frac, color=[COL[t] for t in TAGS], width=.6)
    for i, f in enumerate(frac):
        ax.text(i, f + .02, f"{f*100:.0f}%", ha="center", fontsize=8)
    ax.set_xticks(range(len(TAGS)))
    ax.set_xticklabels(["Leaky", "Haiku", "Sonnet", "GPT-5.6-sol"], fontsize=7.4)
    ax.set_ylabel("proposals using game vocabulary")
    ax.set_ylim(0, 1.12)
    ax.set_title("(a) does the proposer talk about the game?")

    ax = axes[1]
    for t in TAGS:
        items = sorted([i for i in reas[t] if i["desc"]], key=lambda x: x["gen"])
        gens = [i["gen"] for i in items]
        cum, c = [], 0
        for i in items:
            c += 1 if i["leak_hits"] else 0
            cum.append(c)
        ax.plot(gens, cum, color=COL[t], lw=1.6, label=NAME[t])
    ax.set_xlabel("generation")
    ax.set_ylabel("cumulative proposals\nusing game vocabulary")
    ax.set_title("(b) when does it surface?")
    ax.legend(frameon=False)
    fig.savefig(OUT / "fig_vocab.pdf")
    fig.savefig(SP / "fig_vocab.png", dpi=110)
    plt.close(fig)


# ------------------------------------------------- figure: the recall test
def fig_recall():
    progs = {p["gen"]: p for p in runs["gpt56sol"]["programs"]}
    TRUE = {frozenset(t) for t in runs["gpt56sol"]["win"]}
    gens = [3, 7, 8, 9, 10]

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7))

    ax = axes[0]
    w = .38
    xs = range(len(gens))
    remembered = [sum(1 for t in triples(progs[g]["spec"]) if t in ROWMAJOR) for g in gens]
    true = [sum(1 for t in triples(progs[g]["spec"]) if t in TRUE) for g in gens]
    ax.bar([x - w/2 for x in xs], remembered, w, color="#c2453a",
           label="on remembered (unpermuted) lines")
    ax.bar([x + w/2 for x in xs], true, w, color="#1b7837",
           label="on true (permuted) lines")
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"gen {g}" for g in gens], fontsize=7.6)
    ax.set_ylabel("three-qubit gates (of 8)")
    ax.set_ylim(0, 9.6)
    ax.legend(frameon=False, loc="upper center")
    ax.set_title("(a) GPT-5.6-sol targets the lines it remembers")

    ax = axes[1]
    items = sorted(runs["gpt56sol"]["programs"], key=lambda p: p["gen"])
    g = [p["gen"] for p in items if p["score"] is not None]
    s = [p["score"] for p in items if p["score"] is not None]
    ax.plot(g, s, "-o", color="#7b3294", lw=1.2, ms=3)
    for gg in gens:
        ax.axvspan(gg - .45, gg + .45, color="#c2453a", alpha=.16, lw=0)
    ax.axhline(0.7341, color="#333", ls=":", lw=1.2)
    ax.text(21, .745, "best, no winning lines used", fontsize=7, ha="right")
    ax.text(7.0, .445, "recalled-motif\nattempts", fontsize=7,
            color="#c2453a", ha="center")
    ax.set_xlabel("generation")
    ax.set_ylabel("score")
    ax.set_ylim(.42, .79)
    ax.set_title("(b) the score rejects the recalled motif")
    fig.savefig(OUT / "fig_recall.pdf")
    fig.savefig(SP / "fig_recall.png", dpi=110)
    plt.close(fig)


fig_vocab()
fig_recall()
print("wrote fig_vocab, fig_recall")
