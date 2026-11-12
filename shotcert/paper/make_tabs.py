"""Emit the LaTeX table fragments the draft \\input{}s. No number in the paper is typed by hand."""
from __future__ import annotations
import argparse, json, os

def load(p):
    return json.load(open(p)) if os.path.exists(p) else None

def esc(x):
    """Underscores in task and policy names are LaTeX specials; escape them at the boundary."""
    return str(x).replace("_", "\\textunderscore{}")


def w(path, lines):
    with open(os.path.join(os.path.dirname(path), os.path.basename(path)), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", path, "(%d lines)" % len(lines))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default="shotcert/results")
    ap.add_argument("--out", default="shotcert/paper")
    a = ap.parse_args()
    ctl = load(os.path.join(a.res, "control.json"))
    phy = load(os.path.join(a.res, "physics.json"))
    var = load(os.path.join(a.res, "variance.json"))
    bnd = load(os.path.join(a.res, "bound.json"))

    if ctl:
        L = ["\\begin{table}[h]\\centering\\small",
             "\\begin{tabular}{llrrrrr}", "\\toprule",
             "Regime & Policy & $\\risk_{64}$ & bias$^2$ & $V_G$ & $\\Sigma$ & residual \\\\",
             "\\midrule"]
        for reg in ("help", "hurt", "interior"):
            for nm, r in ctl["q1_decomposition"][reg]["rows"].items():
                L.append("%s & %s & %.5f & %.5f & %.5f & %.5f & %.1e \\\\"
                         % (reg, nm, r["R"], r["bias2"], r["V_G"], r["Sigma"],
                            abs(r["identity_gap"])))
        L += ["\\bottomrule\\end{tabular}",
              "\\caption{Risk-at-budget decomposition, enumerated exactly on the 2-qubit control. "
              "Residual is the gap between the enumerated risk and Eq.~\\eqref{eq:decomp}.}",
              "\\end{table}"]
        w(os.path.join(a.out, "tabs_risk.tex"), L)

        L = ["\\begin{table}[h]\\centering\\small", "\\begin{tabular}{lrrrr}", "\\toprule",
             "$n$ (preps) & $S$ (shots) & violation & power & fallback \\\\", "\\midrule"]
        for r in ctl["q3_budget_frontier"]:
            if r["regime"] != "help":
                continue
            L.append("%d & %d & %.3f & %.3f & %.3f \\\\"
                     % (r["n"], r["S"], r["violation_rate"], r["power"], r["fallback_rate"]))
        L += ["\\bottomrule\\end{tabular}",
              "\\caption{Certificate power along the preparations/shots axis at fixed total budget "
              "$B=nS=6400$, averaging-helps regime, empirical-Bernstein bound, $\\epsilon=0$, "
              "$\\delta=0.05$.}", "\\label{tab:frontier}", "\\end{table}"]
        w(os.path.join(a.out, "tabs_frontier.tex"), L)

    if var:
        L = ["\\begin{table}[h]\\centering\\small", "\\begin{tabular}{lrrrrrr}", "\\toprule",
             "Regime & $S$ & $\\mathrm{Var}(D)$ & between & noise & EB var.\\ term & EB range term \\\\",
             "\\midrule"]
        for reg in ("help", "hurt", "interior"):
            e = var["regimes"][reg]["var_vs_S"]; eb = var["regimes"][reg]["eb_split"]
            for S in ("4", "16", "64", "256"):
                if S not in e or "strat" not in e[S]:
                    continue
                r = e[S]["strat"]
                key = None
                for k in eb:
                    if int(k.split("_")[1]) == int(S):
                        key = k; break
                vt = rt = float("nan")
                if key:
                    d = eb[key]; best = min(d, key=lambda k: d[k]["ub"])
                    vt, rt = d[best]["var_term"], d[best]["range_term"]
                L.append("%s & %s & %.5f & %.5f & %.5f & %.4f & %.3f \\\\"
                         % (reg, S, r["var_total"], r["var_between"], r["var_noise"], vt, rt))
        L += ["\\bottomrule\\end{tabular}",
              "\\caption{What the calibration contrast is made of, and what the bound adds. "
              "$\\mathrm{Var}(D)$ splits into a between-instance part (only preparations reduce it) "
              "and a deployed-noise part (shots reduce it). The last two columns split the "
              "empirical-Bernstein bound at the matching allocation.}",
              "\\label{tab:variance}", "\\end{table}"]
        w(os.path.join(a.out, "tabs_variance.tex"), L)

    if phy:
        L = ["\\begin{table}[h]\\centering\\small", "\\begin{tabular}{lrrrrr}", "\\toprule",
             "Task & $\\risk(a_0)$ & best policy & $\\risk$(best) & $\\Delta$ & max resid. \\\\",
             "\\midrule"]
        for tr in phy["tasks"]:
            raw = tr["risk_S64"]["a0"]["R"]
            best = min(((v["R"], k) for k, v in tr["risk_S64"].items()))
            L.append("%s & %.5f & %s & %.5f & $%+.5f$ & %.1e \\\\"
                     % (esc(tr["label"]), raw, esc(best[1]), best[0], best[0] - raw, tr["max_identity_gap"]))
        L += ["\\bottomrule\\end{tabular}",
              "\\caption{Physical tasks at $S=64$ total shots, enumerated risk. The sign of the "
              "benefit of orbit averaging flips with the odd content of the target.}",
              "\\label{tab:physics}", "\\end{table}"]
        w(os.path.join(a.out, "tabs_physics.tex"), L)

    led = None
    import glob as _g
    lrows = []
    for fp in _g.glob(os.path.join(a.res, "ledger*.json")):
        lrows += load(fp)["rows"]
    if lrows:
        L = ["\\begin{table}[h]\\centering\\small", "\\begin{tabular}{llrrrrr}", "\\toprule",
             "Task & Menu & $n$ & $S$ & total shots & power & violation \\", "\\midrule"]
        for task in sorted(set(r["task"] for r in lrows)):
            for mn in ("sym", "generic"):
                rs = [r for r in lrows if r["task"] == task and r["menu"] == mn]
                ok = [r for r in rs if r["power"] >= 0.9]
                pick = min(ok, key=lambda r: r["ledger"]["total_shots"]) if ok else \
                       max(rs, key=lambda r: r["power"])
                L.append("%s & %s & %d & %d & %d & $%.3f\,[{\scriptsize %.2f},{\scriptsize %.2f}]$ "
                         "& $%.3f$ \\"
                         % (esc(task), mn, pick["n_instances"], pick["S"],
                            pick["ledger"]["total_shots"], pick["power"],
                            pick["power_ci"][0], pick["power_ci"][1], pick["violation_rate"]))
        L += ["\\bottomrule\\end{tabular}",
              "\\caption{A2.6 matched-total-cost comparison. Both menus are certified by the same "
              "procedure at the same declared $\\epsilon$; `total shots' includes the factor of the "
              "menu size that calibration actually pays (A2.2). Rows show the cheapest allocation "
              "reaching power $\\ge 0.9$, or the best available.}", "\\label{tab:ledger}",
              "\\end{table}"]
        w(os.path.join(a.out, "tabs_ledger.tex"), L)

    swt = load(os.path.join(a.res, "switch.json"))
    if swt:
        runs = swt["runs"]
        agg = {}
        for key, v in runs.items():
            unit = key.split("_")[-1]
            for c, r in v.items():
                agg.setdefault(unit, [0, 0])
                agg[unit][0] += int(r["interior"]); agg[unit][1] += 1
        L = ["\\begin{table}[h]\\centering\\small", "\\begin{tabular}{lrrr}", "\\toprule",
             "Charged resource & cells & interior optimum in $k$ & max distinct circuits \\",
             "\\midrule"]
        for unit in ("circuit", "switch"):
            if unit in agg:
                mx = max(r["max_circuits"] for k, v in runs.items()
                         if k.endswith(unit) for r in v.values())
                L.append("%s & %d & %d (%.1f\\%%) & %d \\"
                         % ("per distinct circuit" if unit == "circuit" else "per switch",
                            agg[unit][1], agg[unit][0], 100.0 * agg[unit][0] / agg[unit][1], mx))
        L += ["\\bottomrule\\end{tabular}",
              "\\caption{A2.3, the retracted switching result. With circuits correctly bounded by "
              "$|G|=2$, a per-circuit price is flat for every $k\\ge2$ and never produces an interior "
              "optimum; the previously reported $k=2$ optimum came from charging eight circuits. An "
              "interior optimum appears only under a per-switch price on an interleaved schedule.}",
              "\\label{tab:switch}", "\\end{table}"]
        w(os.path.join(a.out, "tabs_switch.tex"), L)

    if phy:
        L = ["\\begin{table}[h]\\centering\\small", "\\begin{tabular}{lrrrrr}", "\\toprule",
             "Task & $\\risk(a_0)$ & full averaging & $\\Delta$ & best mixture & $\\Delta$ \\",
             "\\midrule"]
        for tr in phy["tasks"]:
            tab = tr["risk_S64"]
            raw = tab["a0"]["R"]
            st = tab.get("strat", tab["a0"])["R"]
            mixes = {k: v["R"] for k, v in tab.items() if k.startswith("mix")}
            bm = min(mixes, key=lambda k: mixes[k]) if mixes else "a0"
            L.append("%s & %.5f & %.5f & $%+.5f$ & %s: %.5f & $%+.5f$ \\"
                     % (esc(tr["label"]), raw, st, st - raw, esc(bm), mixes.get(bm, raw),
                        mixes.get(bm, raw) - raw))
        L += ["\\bottomrule\\end{tabular}",
              "\\caption{Raw, full averaging and the best partial mixture side by side (A2.5 and the "
              "reviewer's presentation point): the sign flip is visible only when all three are "
              "shown. Risks at $S=64$ total shots, enumerated exactly.}",
              "\\label{tab:physics2}", "\\end{table}"]
        w(os.path.join(a.out, "tabs_physics2.tex"), L)
        mir = [t.get("mirror_residual") for t in phy["tasks"] if t.get("mirror_residual")]
        if mir:
            m = mir[0]
            L = ["\\begin{table}[h]\\centering\\small", "\\begin{tabular}{lr}", "\\toprule",
                 "Quantity tested & residual \\", "\\midrule",
                 "$\\|M H(\\lambda) M - H(-\\lambda)\\|$ (Hamiltonian only) & %.2e \\"
                 % m["hamiltonian_residual"],
                 "$\\|M|\\psi_0\\> - |\\psi_0\\|\\|$ (N\\'eel preparation) & %.2e \\"
                 % m["state_not_invariant"],
                 "$\\|M Z_0 M - Z_0\\|$ (site-0 readout) & %.2e \\" % m["observable_not_invariant"],
                 "$|\\<Z_0\\>_t(\\lambda) - \\<Z_{n-1}\\>_t(-\\lambda)|$ (transformed experiment) "
                 "& %.2e \\" % m["transformed_relation_max_gap"],
                 "$|\\<Z_0\\>_t(\\lambda) - \\<Z_0\\>_t(-\\lambda)|$ (fixed readout, as claimed) "
                 "& %.2e \\" % m["naive_fixed_readout_max_gap"],
                 "\\bottomrule\\end{tabular}",
                 "\\caption{A2.5: the mirror relation holds for the Hamiltonian and for the "
                 "transformed experiment, and fails for the preparation and the readout actually "
                 "used. Flipping only $\\Delta$ is therefore a paired control transformation, not a "
                 "symmetry of the deployed prediction.}", "\\label{tab:mirror}", "\\end{table}"]
            w(os.path.join(a.out, "tabs_mirror.tex"), L)

    if bnd:
        L = ["\\begin{table}[h]\\centering\\small", "\\begin{tabular}{lrrrrrr}", "\\toprule",
             "Bound & $S$ & $n{=}25$ & $n{=}50$ & $n{=}100$ & $n{=}200$ & $n{=}400$ \\\\",
             "\\midrule"]
        for bound in ("eb", "normal"):
            for S in (8, 32, 128):
                cells = []
                for n in (25, 50, 100, 200, 400):
                    m = [r for r in bnd["rows"] if r["bound"] == bound and r["S"] == S
                         and r["n"] == n and r["regime"] == "help"]
                    cells.append("%.2f/%.2f" % (m[0]["power"], m[0]["violation_rate"]) if m else "--")
                L.append("%s & %d & %s \\\\" % (bound, S, " & ".join(cells)))
        L += ["\\bottomrule\\end{tabular}",
              "\\caption{Power/violation rate for the distribution-free empirical-Bernstein bound "
              "and the tighter Studentised bound, averaging-helps regime, $\\epsilon=0$, "
              "$\\delta=0.05$. A bound is admissible only where its measured violation rate stays at "
              "or below $\\delta$.}", "\\label{tab:bound}", "\\end{table}"]
        w(os.path.join(a.out, "tabs_bound.tex"), L)

if __name__ == "__main__":
    main()
