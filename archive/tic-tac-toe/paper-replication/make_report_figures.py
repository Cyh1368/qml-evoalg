"""Generate the three figures for the gate-insertion robustness report."""

from __future__ import annotations
import json, glob
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

HERE = Path(__file__).resolve().parent

# ── load data ────────────────────────────────────────────────────────────────
baseline = [json.loads(p.read_text())
            for p in sorted(HERE.glob("robustness_histories/seed_*.json"))]
ng5_all  = [json.loads(p.read_text())
            for p in sorted(HERE.glob("gate_insertion_results/ng05_cs042_ts*.json"))]

# Showcase seed: highest accuracy among the 10 ng=5 runs
showcase = max(ng5_all, key=lambda x: x["final_test_accuracy"])

# ── colour palette ────────────────────────────────────────────────────────────
C_BASE = "#2196F3"   # blue
C_AUG  = "#FF5722"  # orange-red
C_ZERO = "#9E9E9E"  # grey

# ─────────────────────────────────────────────────────────────────────────────
# Figure 1 – Before / After training curves (mean ± std bands)
# ─────────────────────────────────────────────────────────────────────────────
epochs = np.arange(1, 101)

base_mat = np.array([r["test_acc_history"] for r in baseline])   # (50, 100)
ng5_mat  = np.array([r["test_acc_history"] for r in ng5_all])    # (10, 100)

base_mean, base_std = base_mat.mean(0), base_mat.std(0)
ng5_mean,  ng5_std  = ng5_mat.mean(0),  ng5_mat.std(0)

fig1, ax = plt.subplots(figsize=(8, 4.5))

ax.fill_between(epochs, base_mean - base_std, base_mean + base_std,
                color=C_BASE, alpha=0.18)
ax.plot(epochs, base_mean, color=C_BASE, lw=2,
        label=f"Baseline — no extra gates  (n=50, final {base_mean[-1]:.3f}±{base_std[-1]:.3f})")

ax.fill_between(epochs, ng5_mean - ng5_std, ng5_mean + ng5_std,
                color=C_AUG, alpha=0.18)
ax.plot(epochs, ng5_mean, color=C_AUG, lw=2,
        label=f"+5 extra gates (n=10, final {ng5_mean[-1]:.3f}±{ng5_std[-1]:.3f})")

# Horizontal reference
ax.axhline(base_mean[-1], color=C_BASE, lw=0.8, ls="--", alpha=0.5)
ax.axhline(ng5_mean[-1],  color=C_AUG,  lw=0.8, ls="--", alpha=0.5)

ax.set_xlabel("Training epoch", fontsize=12)
ax.set_ylabel("Test accuracy", fontsize=12)
ax.set_title("Before vs. After: inserting 5 random rotation gates\n"
             "cemoid L=3, P=2 — shaded band = ±1 std", fontsize=12)
ax.legend(fontsize=10)
ax.set_ylim(0.3, 1.0)
ax.grid(True, alpha=0.25)
fig1.tight_layout()
out1 = HERE / "fig1_before_after.png"
fig1.savefig(out1, dpi=150)
print(f"Saved {out1}")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 2 – Showcase run: extra-gate angles + accuracy
# ─────────────────────────────────────────────────────────────────────────────
positions = showcase["positions"]          # list of [slot, wire, gate_type]
angles    = np.array(showcase["final_extra_angles"])
acc_final = showcase["final_test_accuracy"]
acc_hist  = np.array(showcase["test_acc_history"])
ts        = showcase["train_seed"]

gate_labels = [f"Gate {i+1}\n{gt} q{w}\nslot {sl}"
               for i, (sl, w, gt) in enumerate(positions)]
bar_colors  = [C_AUG if abs(a) > 0.05 else C_ZERO for a in angles]

fig2, (ax_bar, ax_curve) = plt.subplots(1, 2, figsize=(11, 4.5),
                                         gridspec_kw={"width_ratios": [1.1, 1]})

# ── left: angle bar chart ────────────────────────────────────────────────────
bars = ax_bar.bar(range(len(angles)), angles, color=bar_colors, edgecolor="white",
                  linewidth=0.8, width=0.55)
ax_bar.axhline(0, color="black", lw=0.8)
ax_bar.axhline( 0.05, color=C_ZERO, lw=0.8, ls=":", label="±0.05 rad threshold")
ax_bar.axhline(-0.05, color=C_ZERO, lw=0.8, ls=":")
ax_bar.set_xticks(range(len(angles)))
ax_bar.set_xticklabels(gate_labels, fontsize=8.5)
ax_bar.set_ylabel("Final rotation angle (rad)", fontsize=11)
ax_bar.set_title("Learned angles of 5 inserted gates\n"
                 f"(train seed {ts},  final acc = {acc_final:.3f})", fontsize=11)
ax_bar.legend(fontsize=9)

# Annotate each bar with its value
for i, (rect, val) in enumerate(zip(bars, angles)):
    ax_bar.text(i, val + (0.015 if val >= 0 else -0.025),
                f"{val:.3f}", ha="center", va="bottom" if val >= 0 else "top",
                fontsize=8.5, color="black")

sig_patch   = mpatches.Patch(color=C_AUG,  label="Significant (|θ|>0.05)")
zero_patch  = mpatches.Patch(color=C_ZERO, label="Near-zero  (|θ|≤0.05)")
ax_bar.legend(handles=[sig_patch, zero_patch], fontsize=9, loc="upper left")

# ── right: accuracy training curve ───────────────────────────────────────────
ax_curve.plot(np.arange(1, 101), acc_hist, color=C_AUG, lw=2)
ax_curve.axhline(acc_final, color=C_AUG, lw=1, ls="--",
                 label=f"Final accuracy = {acc_final:.3f}")
ax_curve.axhline(base_mean[-1], color=C_BASE, lw=1, ls="--",
                 label=f"Baseline mean = {base_mean[-1]:.3f}")
ax_curve.set_xlabel("Training epoch", fontsize=11)
ax_curve.set_ylabel("Test accuracy", fontsize=11)
ax_curve.set_title("Training curve — showcase run\n"
                   f"(+5 extra gates, train seed {ts})", fontsize=11)
ax_curve.legend(fontsize=9)
ax_curve.set_ylim(0.3, 1.0)
ax_curve.grid(True, alpha=0.25)

fig2.tight_layout()
out2 = HERE / "fig2_angles_and_curve.png"
fig2.savefig(out2, dpi=150)
print(f"Saved {out2}")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 3 – Full gate-insertion sweep (accuracy + mean |angle|)  [existing]
# ─────────────────────────────────────────────────────────────────────────────
# This was already generated by gate_insertion.py --plot-only; just confirm
existing = HERE / "gate_insertion_analysis.png"
if existing.exists():
    print(f"Existing sweep figure: {existing}")
else:
    print("WARNING: gate_insertion_analysis.png not found")
