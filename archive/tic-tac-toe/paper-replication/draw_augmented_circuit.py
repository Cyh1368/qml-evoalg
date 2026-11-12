"""Draw a schematic of the L=3, P=2 cemoid circuit with 5 highlighted extra gates.

Produces: fig3_augmented_circuit.png
"""

from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).resolve().parent

# ── circuit layout constants ──────────────────────────────────────────────────
L, P   = 3, 2
N_WIRE = 9

# ── qubit labels (tic-tac-toe grid positions) ─────────────────────────────────
#   0 -- 1 -- 2
#   |    |    |
#   7 -- 8 -- 3
#   |    |    |
#   6 -- 5 -- 4
WIRE_LABELS = [
    "q0 (corner)", "q1 (edge)",   "q2 (corner)",
    "q3 (edge)",   "q4 (corner)", "q5 (edge)",
    "q6 (corner)", "q7 (edge)",   "q8 (centre)",
]

# ── colours ────────────────────────────────────────────────────────────────────
C_FM    = "#90CAF9"   # light blue  — feature map
C_CB    = "#CE93D8"   # light purple — cemoid block
C_EXTRA = "#FF5722"   # orange-red  — extra gate (highlighted)
C_WIRE  = "#555555"
C_TEXT  = "white"
C_EXTRA_TEXT = "white"

# ── geometry ───────────────────────────────────────────────────────────────────
WIRE_H   = 0.6   # vertical spacing between wires
BLOCK_H  = 0.42  # height of gate boxes  (slightly smaller than spacing)
PAD      = 0.05  # gap between adjacent blocks

# Widths for each segment type
W_EXTRA  = 0.35
W_FM     = 1.0
W_CB     = 1.4
W_SLOT   = 0.45  # horizontal space reserved for each slot (even if empty)
W_END    = 0.3   # tail after last block

# Pre-compute x positions of every slot boundary.
# Slot ordering (L=3, P=2):  0  FM  1  CB  2  CB  3  FM  4  CB  5  CB  6  FM  7  CB  8  CB  9
# (slot k sits to the LEFT of its following block)
def build_layout():
    """Return list of (x_start, kind, layer, rep) for every segment."""
    segments = []
    x = 0.5   # left margin
    slot_x = {}   # slot_id -> x position where that slot starts
    slot_id = 0
    for layer in range(L):
        slot_x[slot_id] = x;  x += W_SLOT;  slot_id += 1   # before FM
        segments.append(("FM", layer, -1, x - W_SLOT + W_SLOT/2 - W_FM/2))  # placeholder, recompute
        # Actually let's just track x properly
    # redo cleanly
    segments = []
    x = 0.5
    slot_x = {}
    slot_id = 0
    for layer in range(L):
        slot_x[slot_id] = x;  x += W_SLOT;  slot_id += 1
        segments.append(("FM",  layer, -1, x));  x += W_FM + PAD
        for rep in range(P):
            slot_x[slot_id] = x;  x += W_SLOT;  slot_id += 1
            segments.append(("CB", layer, rep, x));  x += W_CB + PAD
    slot_x[slot_id] = x   # final slot
    return segments, slot_x, x + W_END

segments, slot_x, total_w = build_layout()

# ── extra gates from the showcase run ─────────────────────────────────────────
# [(slot, wire, gate_type, final_angle), ...]
EXTRA_GATES = [
    (0, 7, "RZ",  0.000),
    (4, 2, "RZ", +0.060),
    (4, 3, "RY", +0.117),
    (6, 4, "RY", -0.158),
    (7, 5, "RZ", -0.321),
]

# ── figure setup ───────────────────────────────────────────────────────────────
fig_w = total_w + 1.5
fig_h = N_WIRE * WIRE_H + 1.8
fig, ax = plt.subplots(figsize=(fig_w, fig_h))
ax.set_xlim(-0.3, total_w + 0.2)
ax.set_ylim(-0.8, N_WIRE * WIRE_H + 0.5)
ax.axis("off")

def wire_y(wire_id: int) -> float:
    """y coordinate for wire wire_id (wire 0 at top)."""
    return (N_WIRE - 1 - wire_id) * WIRE_H

# ── draw wire lines ────────────────────────────────────────────────────────────
for w in range(N_WIRE):
    y = wire_y(w)
    ax.plot([0, total_w], [y, y], color=C_WIRE, lw=1.0, zorder=1)
    ax.text(-0.12, y, WIRE_LABELS[w], ha="right", va="center",
            fontsize=7.5, color=C_WIRE)

# ── helper: draw a gate box on a single wire ──────────────────────────────────
def draw_gate(ax, x_centre, wire_id, label, color, text_color=C_TEXT,
              width=None, zorder=3, fontsize=7.5, border_color=None):
    w = width or W_CB
    y  = wire_y(wire_id)
    x0 = x_centre - w / 2
    box = FancyBboxPatch((x0, y - BLOCK_H/2), w, BLOCK_H,
                         boxstyle="round,pad=0.03",
                         facecolor=color, edgecolor=border_color or color,
                         linewidth=1.2, zorder=zorder)
    ax.add_patch(box)
    ax.text(x_centre, y, label, ha="center", va="center",
            fontsize=fontsize, color=text_color, zorder=zorder+1,
            fontweight="bold" if color == C_EXTRA else "normal")

# ── draw a block spanning ALL wires (FM or CB) ────────────────────────────────
def draw_block(ax, x_left, kind, label_top, label_bottom=None):
    w  = W_FM if kind == "FM" else W_CB
    color = C_FM if kind == "FM" else C_CB
    x_c  = x_left + w / 2
    y_top = wire_y(0) + BLOCK_H / 2 + 0.04
    y_bot = wire_y(N_WIRE - 1) - BLOCK_H / 2 - 0.04

    # Tall background rectangle spanning all wires
    bg = FancyBboxPatch((x_left - PAD/2, y_bot),
                        w + PAD, y_top - y_bot,
                        boxstyle="round,pad=0.04",
                        facecolor=color, edgecolor=color,
                        alpha=0.18, zorder=2)
    ax.add_patch(bg)

    # Individual wire-level boxes
    for w_id in range(N_WIRE):
        draw_gate(ax, x_c, w_id, "", color, zorder=2,
                  width=w - 0.04, border_color=color)

    # Block label at top
    ax.text(x_c, y_top + 0.06, label_top, ha="center", va="bottom",
            fontsize=8.5, color=color if kind == "FM" else "#6A1B9A",
            fontweight="bold", zorder=5)
    if label_bottom:
        ax.text(x_c, y_bot - 0.06, label_bottom, ha="center", va="top",
                fontsize=7, color="grey", zorder=5)

# ── draw all segments ─────────────────────────────────────────────────────────
for kind, layer, rep, x_left in segments:
    if kind == "FM":
        draw_block(ax, x_left, "FM",
                   f"FM\n(layer {layer+1})")
    else:
        draw_block(ax, x_left, "CB",
                   f"CB {layer*P+rep+1}\n(L{layer+1},P{rep+1})")

# ── draw extra gates (on top, highlighted) ────────────────────────────────────
for slot_id, wire_id, gtype, angle in EXTRA_GATES:
    x_slot = slot_x[slot_id]
    x_c    = x_slot + W_EXTRA / 2
    label  = f"{gtype}\nq{wire_id}\n{angle:+.3f}"
    draw_gate(ax, x_c, wire_id, label, C_EXTRA,
              text_color=C_EXTRA_TEXT, width=W_EXTRA,
              zorder=6, fontsize=6.5, border_color="#BF360C")
    # Dashed vertical marker line at slot
    y_top = wire_y(0) + BLOCK_H
    y_bot = wire_y(N_WIRE - 1) - BLOCK_H
    ax.plot([x_c, x_c], [y_bot, y_top], color=C_EXTRA, lw=0.8,
            ls="--", alpha=0.55, zorder=4)

# ── layer dividers ────────────────────────────────────────────────────────────
for layer in range(1, L):
    # x position just before layer's FM block
    idx = layer * (1 + P)   # index into segments list
    x_div = segments[idx][3] - W_SLOT * 0.7
    ax.axvline(x_div, color="#BDBDBD", lw=0.7, ls=":", zorder=1)
    ax.text(x_div, wire_y(0) + BLOCK_H * 1.4,
            f"Layer {layer}→{layer+1}", ha="center", va="bottom",
            fontsize=7, color="#9E9E9E")

# ── legend ────────────────────────────────────────────────────────────────────
legend_elements = [
    mpatches.Patch(facecolor=C_FM,    alpha=0.6, label="Feature map (FM) — RX data encoding"),
    mpatches.Patch(facecolor=C_CB,    alpha=0.6, label="Cemoid block (CB) — 9 shared params, 16 CRY + 18 RX/RZ"),
    mpatches.Patch(facecolor=C_EXTRA, label="Inserted extra gate (angle ≠ 0 → alternative solution)"),
]
ax.legend(handles=legend_elements, loc="lower center",
          bbox_to_anchor=(0.5, -0.10), ncol=1, fontsize=8,
          framealpha=0.9, edgecolor="#BDBDBD")

ax.set_title(
    "L=3, P=2 cemoid circuit with 5 inserted rotation gates (showcase run, train seed 1)\n"
    "Extra gates initialised to θ=0; final learned angles shown — none converged to zero",
    fontsize=10, pad=10
)

fig.tight_layout(rect=[0, 0.08, 1, 1])
out = HERE / "fig3_augmented_circuit.png"
fig.savefig(out, dpi=160, bbox_inches="tight")
print(f"Saved {out}")
