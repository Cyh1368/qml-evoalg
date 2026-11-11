"""A5.2 / A5.3: what the label-preservation gate can and cannot decide.

The second-round referee identified two real defects in how we reported verifier
behaviour, both confirmed in the source before this module was written:

* ``dev_analysis.py`` scored a hypothesis correct only when its closure **equals** the
  declared task group, so a proper subgroup --- a genuine, sound symmetry that is simply
  weaker than declared --- was counted as a "wrong group". Soundness and maximal-group
  recovery are different objectives (A5.2).
* the graphs-versus-breaking-ring comparison changed inputs, target, proposal
  distribution and search trajectory at once, so it could not isolate the verifier (A5.3).

This module therefore measures two things, on **development rows only**:

1. **The label-symmetry group actually realised by each target.** For every one of the
   ``n!`` site permutations, labels are recomputed on an independent probe panel, giving
   ``L_t`` for each target ``t`` and ``L_all`` for the conjunction the implemented gate
   checks. ``|L_t|`` is what makes the graphs result interpretable: if ``L_t`` is the whole
   symmetric group, no permutation hypothesis can violate that target and the gate has no
   discriminating power there *by construction*.
2. **A fixed-panel selectivity test** on identical inputs, varying only the target:
   identity, the declared group's generators, its subgroups, the full symmetric group,
   random permutations and single transpositions, each with a known truth status. Reported
   as sensitivity and false-accept rate with explicit denominators and Wilson intervals.

Hypothesis statuses (A5.2), against declared group ``G`` and measured ``L_t``:

``exact_declared``          H = G
``valid_proper_subgroup``   H < G                    sound, incomplete
``valid_supergroup``        G < H <= L_t             sound, stronger than declared
``invalid``                 some h in H violates t   a genuine false accept

Usage::

    python3 -m research.search.verify_semantics --runs logs/runs_confirm \\
        --out research/search/verify_semantics.json
"""
import argparse
import glob
import itertools
import json
import os

import numpy as np

from research.core import paired as _P
from research.core import tasks as _tasks
from research.search import verifier_bridge as _vb

PROBE_ROWS = 512
PROBE_SEED = 777            # distinct from the gate, which reads train rows[:64]
GATE_ROWS = 64              # the implemented gate's budget (dev_analysis, harness)
N_RANDOM = 20
N_TRANSPOSITIONS = 15       # all C(6,2) single transpositions for n = 6
PANEL_SEED = 4242


# ------------------------------------------------------------------ group tools
def all_permutations(n):
    return [tuple(p) for p in itertools.permutations(range(n))]


def closure_of(gens, n):
    from verify import closure
    return [tuple(p) for p in closure([list(g) for g in gens], n)]


def action_columns(task, rows, perm):
    """Vectorised pullback action, identical to ``verifier_bridge.transform_rows``."""
    if str(getattr(task, "name", "")).startswith("graphs"):
        from verify import graph_edge_action
        return np.stack([graph_edge_action(r, perm) for r in rows])
    return np.asarray(rows)[:, list(perm)]


def probe_indices(task, n_rows=PROBE_ROWS, seed=PROBE_SEED):
    """Development rows the implemented gate never reads (it uses train rows[:64])."""
    splits = getattr(task, "splits", None) or {}
    train = np.asarray(splits.get("train"), bool)
    val = np.asarray(splits.get("validation"), bool)
    total = len(train)
    allowed = np.zeros(total, bool)
    tr = np.flatnonzero(train)
    allowed[tr[GATE_ROWS:]] = True
    allowed[val] = True
    pool = np.flatnonzero(allowed)
    rng = np.random.default_rng(int(seed))
    k = min(int(n_rows), pool.size)
    return np.sort(rng.choice(pool, size=k, replace=False))


def label_symmetry_group(task, target, probe):
    """Every permutation that preserves ``target`` on the probe rows, with margins."""
    rows = np.asarray(task.x)[probe]
    y0 = np.asarray(task.label_oracle(rows, target=target), float).reshape(-1)
    out = {}
    for perm in all_permutations(int(task.n_qubits)):
        yt = np.asarray(task.label_oracle(action_columns(task, rows, perm),
                                          target=target), float).reshape(-1)
        frac = float((np.abs(yt - y0) > 1e-9).mean())
        out[perm] = frac
    group = {p for p, f in out.items() if f == 0.0}
    return {"target": target, "probe_rows": int(len(rows)),
            "n_permutations_tested": len(out), "order": len(group),
            "group": group, "violated_fraction": out}


# --------------------------------------------------------------- classification
def classify(H, G, L):
    """A5.2 status of hypothesis closure ``H`` given declared ``G`` and measured ``L``.

    Five statuses. A sound hypothesis that is neither a subgroup nor a supergroup of the
    declared group (a different subgroup of the same order, e.g. a transposition group
    beside a declared rotation group) is ``sound_noncomparable``: it is still a genuine
    label symmetry, and counting it as a false accept would repeat the error A5.2 fixes.
    """
    H, G = set(H), set(G)
    if not H <= L:
        return "invalid"
    if H == G:
        return "exact_declared"
    if H < G:
        return "valid_proper_subgroup"
    if H > G:
        return "valid_supergroup"
    return "sound_noncomparable"


# ------------------------------------------------------------------ the panel
def panel(n, seed=PANEL_SEED):
    """Fixed transformation panel: name -> list of generators."""
    ident = tuple(range(n))
    rot = tuple((i + 1) % n for i in range(n))
    refl = tuple((-i) % n for i in range(n))
    adjacent = []
    for i in range(n - 1):
        p = list(range(n))
        p[i], p[i + 1] = p[i + 1], p[i]
        adjacent.append(tuple(p))
    rng = np.random.default_rng(int(seed))
    members = {
        "identity": [ident],
        "cyclic_rotation": [rot],
        "reflection": [refl],
        "dihedral_declared": [rot, refl],
        "rotation_subgroup_c3": [tuple((i + 2) % n for i in range(n))],
        "rotation_subgroup_c2": [tuple((i + 3) % n for i in range(n))],
        "full_symmetric": adjacent,
    }
    members["random_permutations"] = [tuple(rng.permutation(n)) for _ in range(N_RANDOM)]
    pairs = list(itertools.combinations(range(n), 2))
    chosen = rng.choice(len(pairs), size=min(N_TRANSPOSITIONS, len(pairs)),
                        replace=False)
    transpositions = []
    for k in chosen:
        i, j = pairs[int(k)]
        p = list(range(n))
        p[i], p[j] = p[j], p[i]
        transpositions.append(tuple(p))
    members["single_transpositions"] = transpositions
    return members


def panel_unit(task, gens, target, probe, gate_mode):
    """One panel member: truth status plus the gate's decision under a gate variant.

    Three variants, so the two design choices can be attributed separately:

    ``implemented``          every target column in the dataset, tolerance 0 (the harness)
    ``target_specific``      the scored target only, tolerance 0
    ``target_specific_tol``  the scored target only, tolerance 1e-9
    """
    n = int(task.n_qubits)
    H = closure_of(gens, n)
    rows = np.asarray(task.x)[probe]
    y0 = np.asarray(task.label_oracle(rows, target=target), float).reshape(-1)
    worst = 0.0
    for h in H:
        yt = np.asarray(task.label_oracle(action_columns(task, rows, h),
                                          target=target), float).reshape(-1)
        worst = max(worst, float((np.abs(yt - y0) > 1e-9).mean()))
    sound = (worst == 0.0)
    mask = np.asarray(task.splits["train"], bool)
    trows = np.asarray(task.x)[mask][:GATE_ROWS]
    if gate_mode == "implemented":
        lp = _vb.label_preservation(task, {"generators": [list(g) for g in gens]},
                                    GATE_ROWS)
        return {"sound_on_probe": sound, "accepted": bool(lp["violated_fraction"] == 0.0),
                "worst_violated_fraction": worst,
                "gate_margin": lp["max_discrepancy"], "closure_order": len(H)}
    tol = 0.0 if gate_mode == "target_specific" else 1e-9
    z0 = np.asarray(task.label_oracle(trows, target=target), float).reshape(-1)
    margin, acc = 0.0, True
    for h in H:
        zt = np.asarray(task.label_oracle(action_columns(task, trows, h),
                                          target=target), float).reshape(-1)
        v = float((np.abs(zt - z0) > tol).mean())
        if v > 0.0:
            acc = False
        margin = max(margin, v)
    return {"sound_on_probe": sound, "accepted": bool(acc),
            "worst_violated_fraction": worst, "gate_margin": margin,
            "closure_order": len(H)}


GATE_MODES = ("implemented", "target_specific", "target_specific_tol")


# ------------------------------------------------------------- run hypotheses
def hypothesis_statuses(run_dir, groups, sym):
    """Classify every hypothesis proposed by the frozen 120 development runs."""
    from research.search import refit as _refit
    rows = []
    for path in sorted(glob.glob(os.path.join(run_dir, "run_*.json"))):
        log = _refit.load_run(path)
        if log["arm"] not in ("llm-fitness", "llm-verify", "llm-verify-repair"):
            continue
        fam = log["family"]
        task = _tasks.load_family(fam, development=True, locked=False)
        G = groups[fam]
        for p in log.get("proposals") or []:
            cand = p.get("candidate") or {}
            hyp = cand.get("hypothesis") or {}
            gens = hyp.get("generators")
            if not gens or not p.get("valid"):
                continue
            try:
                H = closure_of(gens, int(task.n_qubits))
            except Exception:
                continue
            key = log.get("target") or task.primary_target
            v = p.get("verify") or {}
            entry = {"family": fam, "arm": log["arm"], "run": os.path.basename(path),
                     "closure_order": len(H), "target": key,
                     "recorded_label_pass": (v.get("label_violated_fraction") == 0.0)
                     if v else None,
                     "recorded_channel_pass": v.get("sampled_pass") if v else None}
            for tgt in (key, "alpha_0" if fam == "ring_n6" else "connected",
                        "ALL_COLUMNS"):
                if tgt not in sym[fam]:
                    continue
                L = sym[fam][tgt]["group"]
                entry["status_vs_%s" % tgt] = classify(H, G, L)
                entry["sound_for_%s" % tgt] = bool(set(H) <= L)
            entry["exact_declared_group"] = bool(set(H) == set(G))
            rows.append(entry)
    return rows


# ---------------------------------------------------------------------- driver
def main(argv=None):
    ap = argparse.ArgumentParser(prog="research/search/verify_semantics.py")
    ap.add_argument("--runs", default="logs/runs_confirm")
    ap.add_argument("--out", default="research/search/verify_semantics.json")
    ap.add_argument("--families", default="ring_n6,graphs_n6")
    a = ap.parse_args(argv)
    if "locked" in a.runs.lower() or "locked" in a.out.lower():
        raise SystemExit("verify_semantics is development-only")

    out = {"protocol": "REVISED_PROTOCOL Addendum A5.2-A5.3",
           "probe": {"rows": PROBE_ROWS, "seed": PROBE_SEED,
                     "note": "gate reads train rows[:%d]; the probe excludes them"
                             % GATE_ROWS},
           "families": {}, "panel": {}, "hypotheses": []}

    groups, sym = {}, {}
    for fam in [f.strip() for f in a.families.split(",") if f.strip()]:
        task = _tasks.load_family(fam, development=True, locked=False)
        n = int(task.n_qubits)
        G = closure_of(task.generators, n)
        groups[fam] = G
        probe = probe_indices(task)
        fam_sym = {}
        for tgt in list(task.target_keys) + ["ALL_COLUMNS"]:
            if tgt == "ALL_COLUMNS":
                continue
            res = label_symmetry_group(task, tgt, probe)
            fam_sym[tgt] = {"order": res["order"],
                            "n_permutations_tested": res["n_permutations_tested"],
                            "probe_rows": res["probe_rows"],
                            "contains_declared_group": bool(set(G) <= res["group"]),
                            "equals_full_symmetric": res["order"] ==
                            _factorial(n)}
            sym.setdefault(fam, {})[tgt] = {"group": res["group"]}
        # the conjunction the implemented gate actually checks
        inter = None
        for tgt in list(task.target_keys):
            g = label_symmetry_group(task, tgt, probe)["group"]
            inter = g if inter is None else (inter & g)
        fam_sym["ALL_COLUMNS"] = {"order": len(inter),
                                  "n_permutations_tested": _factorial(n),
                                  "probe_rows": int(len(probe)),
                                  "contains_declared_group": bool(set(G) <= inter),
                                  "equals_full_symmetric": len(inter) == _factorial(n)}
        sym[fam]["ALL_COLUMNS"] = {"group": inter}
        out["families"][fam] = {"declared_group_order": len(G),
                                "n_qubits": n,
                                "full_symmetric_order": _factorial(n),
                                "label_symmetry_groups": fam_sym}

        # fixed panel on identical inputs, one row per (member, target, gate)
        for tgt in list(task.target_keys):
            for gate_mode in GATE_MODES:
                sens_k = sens_n = fa_k = fa_n = 0
                members = {}
                for name, gens in panel(n).items():
                    r = panel_unit(task, gens, tgt, probe, gate_mode)
                    members[name] = r
                    if r["sound_on_probe"]:
                        sens_n += 1
                        sens_k += int(r["accepted"])
                    else:
                        fa_n += 1
                        fa_k += int(r["accepted"])
                out["panel"]["%s|%s|%s" % (fam, tgt, gate_mode)] = {
                    "target": tgt, "gate": gate_mode,
                    "sensitivity": _P.wilson_ci(sens_k, sens_n),
                    "false_accept": _P.wilson_ci(fa_k, fa_n),
                    "members": members}

    out["hypotheses"] = hypothesis_statuses(a.runs, groups, sym)
    tally, gate_tab = {}, {}
    for r in out["hypotheses"]:
        st = r.get("status_vs_%s" % r["target"], "unknown")
        t = tally.setdefault("%s|%s" % (r["family"], r["target"]), {})
        t[st] = t.get(st, 0) + 1
        t["exact_declared_group"] = t.get("exact_declared_group", 0) + \
            int(r["exact_declared_group"])
        # gate behaviour on search-generated hypotheses, analysed separately (A5.3)
        if r["recorded_label_pass"] is None:
            continue
        g = gate_tab.setdefault("%s|%s" % (r["family"], r["target"]),
                                {"label_pass": 0, "label_pass_invalid": 0,
                                 "label_fail": 0, "label_fail_sound": 0,
                                 "both_pass": 0, "both_pass_invalid": 0})
        sound = bool(r.get("sound_for_%s" % r["target"]))
        if r["recorded_label_pass"]:
            g["label_pass"] += 1
            g["label_pass_invalid"] += int(not sound)
        else:
            g["label_fail"] += 1
            g["label_fail_sound"] += int(sound)
        if r["recorded_label_pass"] and r["recorded_channel_pass"]:
            g["both_pass"] += 1
            g["both_pass_invalid"] += int(not sound)
    out["hypothesis_tally"] = tally
    out["gate_cross_tabulation"] = {
        k: {**v,
            "false_accept_of_accepted": _P.wilson_ci(v["label_pass_invalid"],
                                                     v["label_pass"]),
            "missed_sound_of_rejected": _P.wilson_ci(v["label_fail_sound"],
                                                     v["label_fail"])}
        for k, v in gate_tab.items()}
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    print(json.dumps({"label_symmetry_groups": {
        f: {t: v["order"] for t, v in d["label_symmetry_groups"].items()}
        for f, d in out["families"].items()},
        "declared_group_order": {f: d["declared_group_order"]
                                 for f, d in out["families"].items()},
        "hypothesis_tally": tally,
        "gate_cross_tabulation": out["gate_cross_tabulation"]}, indent=1))
    print("wrote", a.out)
    return 0


def _factorial(n):
    r = 1
    for i in range(2, n + 1):
        r *= i
    return r


if __name__ == "__main__":
    raise SystemExit(main())
