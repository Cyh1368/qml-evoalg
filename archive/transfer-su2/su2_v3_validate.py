#!/usr/bin/env python3
"""v3 pre-launch validation harness (LOCAL/TOOLS ONLY, never inside a task dir).

Implements the three pre-registered checks from
context/zc-su2-v3-redesign-plan-2026-08-03.md:

  P4  probe ladder      -- known circuits, incl. the ones evolution actually
                           found in v1/v2, scored by the exact cluster evaluator
  P3  stepping stones   -- is there a mutation-scale path out of the generic
                           basin, or only an endpoint separation?
  P2  adversarial sweep -- random + hill-climbed non-equivariant circuits, to
                           estimate the CEILING of the non-equivariant families
                           rather than one weak representative of them

Gates:
  G1  no circuit lacking the tied-isotropic structure scores within 0.10 of
      exchange_true, and the surviving gap is carried by the margin term
  G2  the gen-66 replica (a real tied ring plus leftover generic gates, the
      configuration v2's fitness threw away) outscores every non-equivariant
      circuit found anywhere in this sweep

Equivariance is judged two ways, because the structural test can be fooled:
  * structural: every entangled pair carries XX, YY and ZZ under ONE shared
    param name, with no single-qubit rotations and no CZ/CNOT/CR* left over
  * behavioural: ||[U, S_a]|| for the TRAINED block unitary against the three
    global spin components. This needs the answer key, so it stays in tools/.

Usage:
    su2_v3_validate.py --list                    enumerate task ids
    su2_v3_validate.py --task <id>               evaluate one item -> JSON
    su2_v3_validate.py --hillclimb <start>       greedy single-edit climb
    su2_v3_validate.py --report                  aggregate + evaluate gates
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
import types
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TASK_DIR = Path(os.environ.get("SU2_TASK_DIR", str(HERE.parent / "zc_su2_v3")))
OUT = Path(os.environ.get("SU2_VALIDATE_OUT", str(HERE / "v3_validation")))
OUT.mkdir(parents=True, exist_ok=True)

# Match the cluster evaluation protocol EXACTLY. The v2 postmortem found the
# probe ladder had run at N_EPOCHS=300 while the cluster used 1000; since the
# convergence term is 1 - log1p(step)/log1p(max_steps), the two score frames
# were not comparable and every published probe number was ~0.004 low.
os.environ.setdefault("TASK_DATA", str(TASK_DIR / "dataset.npz"))
os.environ.setdefault("TRAIN_SIZE", "16")
os.environ.setdefault("DATA_SEED", "2027")
os.environ.setdefault("BATCH_SIZE", "8")
os.environ.setdefault("N_EPOCHS", "1000")
os.environ.setdefault("STEPS_PER_EPOCH", "30")
os.environ.setdefault("LEARNING_RATE", "0.03")
os.environ.setdefault("EARLY_STOPPING", "1")
os.environ.setdefault("PATIENCE", "75")
os.environ.setdefault("USE_TEST_IN_SCORE", "0")
# Per-candidate training logs are OFF by default here. The backend names the
# log file after the training seed, and every validation task uses the same
# seed, so ~90 concurrent array tasks on shared NFS raced on one path and died
# with "Stale file handle" / FileNotFoundError. The logs are not used by any
# gate; set SU2_KEEP_TRAINING_LOGS=1 to get them in a per-process directory.
if os.environ.get("SU2_KEEP_TRAINING_LOGS") == "1":
    os.environ["TTT_LOG_DIR"] = str(OUT / "training_logs" / str(os.getpid()))
else:
    os.environ.pop("TTT_LOG_DIR", None)

sys.path.insert(0, str(TASK_DIR))

N = 8
KEY = json.loads((HERE / "answer_key.json").read_text())
RELABEL = KEY["qubit_relabel"]
BONDS_SITE = KEY["bonds_site_order"]
TRUE_EVEN_BONDS = [[RELABEL[a], RELABEL[b]] for i, (a, b) in enumerate(BONDS_SITE) if i % 2 == 0]
TRUE_ODD_BONDS = [[RELABEL[a], RELABEL[b]] for i, (a, b) in enumerate(BONDS_SITE) if i % 2 == 1]
ALL_BONDS = TRUE_EVEN_BONDS + TRUE_ODD_BONDS
WRONG_PAIRS = [[RELABEL[s], RELABEL[(s + 2) % N]] for s in (0, 1, 4, 5)]

sys.path.insert(0, str(HERE))
from probe_ladder_v2winners import V2_SONNET_WINNER, V2_GPT_WINNER  # noqa: E402

SINGLE = ["RX", "RY", "RZ"]
FIXED2 = ["CZ", "CNOT"]
CTRL2 = ["CRX", "CRY", "CRZ"]
ISING = ["XX", "YY", "ZZ"]


# ----------------------------------------------------------------- circuits


def tied_exchange(pairs, names=("w", "w", "w")):
    spec = []
    for a, b in pairs:
        for gate, name in zip(ISING, names):
            spec.append({"gate": gate, "wires": [int(a), int(b)], "param": name})
    return spec


def sonnet_trivial():
    spec = [{"gate": "RX", "wire": w, "param": "theta"} for w in range(N)]
    spec += [{"gate": "RY", "wire": w, "param": "theta"} for w in range(N)]
    for i in range(N):
        a, b = i, (i + 1) % N
        if i % 2 == 0:
            spec.append({"gate": "XX", "wires": [a, b], "param": "theta"})
        else:
            spec.append({"gate": "CZ", "wires": [a, b]})
    spec += [{"gate": "CZ", "wires": [i, (i + 2) % N]} for i in range(0, N, 2)]
    spec += [{"gate": "CZ", "wires": [i, i + N // 2]} for i in range(N // 2)]
    spec += [{"gate": "RZ", "wire": w, "param": "theta"} for w in range(N)]
    return spec


def seed_spec():
    import importlib
    return importlib.import_module("initial_program").ANSATZ_SPEC


def index_ring():
    """The nearest-neighbour ring in QUBIT INDEX order, i.e. the textbook
    topology rather than the one in the data. This is what sonnet reached for
    at gen 66 in v2 (2/8 overlap with the true bonds, chance is 2.29)."""
    return [[i, (i + 1) % N] for i in range(N)]


def gen66_replica():
    """Sonnet's v2 gen-66 circuit: a genuine tied XX=YY=ZZ ring under one name,
    carrying twelve leftover ZZ-only couplings under a second name. Under the
    v2 fitness this LOST to a generic one-name circuit on the economy term;
    G2 asks whether v3 keeps it."""
    spec = tied_exchange(index_ring(), names=("theta", "theta", "theta"))
    extra = [[a, b] for a, b in itertools.combinations(range(N), 2)
             if abs(a - b) not in (1, N - 1)][:12]
    spec += [{"gate": "ZZ", "wires": [a, b], "param": "phi"} for a, b in extra]
    return spec


STONES = {
    # Does raw exchange vocabulary bolted onto the generic seed move anything?
    "stone_seed_plus_untied": lambda: seed_spec() + [
        {"gate": g, "wires": [int(a), int(b)], "param": f"is_{g.lower()}_{k}"}
        for k, (a, b) in enumerate(TRUE_EVEN_BONDS) for g in ISING],
    # First step out of the generic basin: one tied triple added to the winner.
    "stone_gpt_plus_one_tied": lambda: list(V2_GPT_WINNER) + [
        {"gate": g, "wires": TRUE_EVEN_BONDS[0], "param": "tied"} for g in ISING],
    # Partial tying en route to full tying: XX=YY share a name, ZZ separate.
    "stone_partial_tie": lambda: tied_exchange(TRUE_EVEN_BONDS, names=("w", "w", "wz")),
    # A tied ring on the WRONG (index-order) topology, no leftovers.
    "stone_tied_index_ring": lambda: tied_exchange(index_ring()),
    "stone_gen66_replica": gen66_replica,
    # The fair version of the gen-66 test. v3 turns out to reward correct BOND
    # PLACEMENT as well as the tied structure (exchange_wrong scores 0.616 vs
    # exchange_true's 0.756), which the v3 plan had assumed would stay
    # fitness-invisible. Sonnet's gen-66 circuit was tied but sat on index-order
    # bonds at chance overlap with the true ones, so v3 ranks it low for a
    # substantive reason rather than a blind one. The question G2 was really
    # asking -- does the fitness keep a genuine tied structure that still
    # carries leftover generic gates? -- needs the leftovers on TRUE bonds.
    "stone_true_ring_plus_leftovers": lambda: (
        tied_exchange(ALL_BONDS, names=("theta", "theta", "theta"))
        + [{"gate": "ZZ", "wires": [a, b], "param": "phi"}
           for a, b in [p for p in itertools.combinations(range(N), 2)
                        if tuple(sorted(p)) not in {tuple(sorted(x)) for x in ALL_BONDS}][:12]]),
    # Same, but the leftovers are single-qubit rotations rather than couplings.
    "stone_true_ring_plus_rotations": lambda: (
        tied_exchange(ALL_BONDS, names=("theta", "theta", "theta"))
        + [{"gate": "RY", "wire": w, "param": "phi"} for w in range(N)]),
}

PROBES = {
    "seed": seed_spec,
    "trivial_1p": sonnet_trivial,
    "v2_sonnet_winner": lambda: list(V2_SONNET_WINNER),
    "v2_gpt_winner": lambda: list(V2_GPT_WINNER),
    "exchange_true": lambda: tied_exchange(TRUE_EVEN_BONDS),
    "exchange_odd": lambda: tied_exchange(TRUE_ODD_BONDS),
    "exchange_wrong": lambda: tied_exchange(WRONG_PAIRS),
    "exchange_untied": lambda: tied_exchange(TRUE_EVEN_BONDS, names=("wx", "wy", "wz")),
    "exchange_full_ring": lambda: tied_exchange(ALL_BONDS),
    "fixed_0p": lambda: (
        [{"gate": "CZ", "wires": [i, (i + 1) % N]} for i in range(N)]
        + [{"gate": "CZ", "wires": [i, (i + 2) % N]} for i in range(0, N, 2)]),
}


def random_spec(index: int) -> list[dict]:
    """Adversarial sampler. Deliberately NOT uniform over the vocabulary: it
    over-samples the shapes that actually won v1 and v2 (layered single-qubit
    rotations with fixed entanglers under very few names), because the quantity
    G1 needs is the CEILING of those families, not a uniform random baseline."""
    rng = np.random.default_rng(20260803 + index)
    mode = ["generic_layered", "generic_random", "mixed", "ising_untied"][index % 4]
    n_names = int(rng.integers(1, 7))
    names = [f"p{i}" for i in range(n_names)]
    pick = lambda: names[int(rng.integers(0, n_names))]
    spec: list[dict] = []

    if mode == "generic_layered":
        for _ in range(int(rng.integers(1, 4))):
            g = SINGLE[int(rng.integers(0, 3))]
            nm = pick()
            spec += [{"gate": g, "wire": w, "param": nm} for w in range(N)]
            ent = FIXED2[int(rng.integers(0, 2))]
            stride = int(rng.integers(1, 4))
            spec += [{"gate": ent, "wires": [i, (i + stride) % N]}
                     for i in range(N) if i != (i + stride) % N]
        return spec

    if mode == "ising_untied":
        pairs = [list(p) for p in itertools.combinations(range(N), 2)]
        rng.shuffle(pairs)
        for a, b in pairs[: int(rng.integers(2, 9))]:
            for g in ISING:
                if rng.random() < 0.8:
                    spec.append({"gate": g, "wires": [a, b], "param": pick()})
        return spec or [{"gate": "RY", "wire": 0, "param": "p0"}]

    pool = SINGLE + FIXED2 + CTRL2 + (ISING if mode == "mixed" else [])
    for _ in range(int(rng.integers(4, 25))):
        g = pool[int(rng.integers(0, len(pool)))]
        if g in SINGLE:
            spec.append({"gate": g, "wire": int(rng.integers(0, N)), "param": pick()})
        else:
            a, b = rng.choice(N, size=2, replace=False)
            item = {"gate": g, "wires": [int(a), int(b)]}
            if g not in FIXED2:
                item["param"] = pick()
            spec.append(item)
    return spec


N_RANDOM = int(os.environ.get("SU2_N_RANDOM", "320"))
HILLCLIMB_STARTS = ["v2_sonnet_winner", "v2_gpt_winner", "seed", "trivial_1p"]


def get_spec(task_id: str) -> list[dict]:
    kind, _, name = task_id.partition(":")
    if kind == "probe":
        return PROBES[name]()
    if kind == "stone":
        return STONES[name]()
    if kind == "rand":
        return random_spec(int(name))
    raise SystemExit(f"unknown task id {task_id!r}")


def all_task_ids() -> list[str]:
    return ([f"probe:{k}" for k in PROBES]
            + [f"stone:{k}" for k in STONES]
            + [f"rand:{i}" for i in range(N_RANDOM)])


# -------------------------------------------------- structure + behaviour


def structure(spec: list[dict]) -> dict:
    """Gate-level signature. `tied_isotropic` is the exact SU(2) signature the
    task is designed to select for: every entangled pair carries XX, YY and ZZ
    under one shared name, with nothing else in the circuit."""
    by_pair: dict[tuple, dict] = {}
    n_single = 0
    n_fixed2 = 0
    n_ctrl2 = 0
    for item in spec:
        g = str(item["gate"]).upper()
        if g in SINGLE:
            n_single += 1
        elif g in FIXED2:
            n_fixed2 += 1
        elif g in CTRL2:
            n_ctrl2 += 1
        elif g in ISING:
            key = tuple(sorted(int(w) for w in item["wires"]))
            by_pair.setdefault(key, {})[g] = item["param"]

    tied_pairs, untied_pairs = [], []
    for pair, gates in by_pair.items():
        if set(gates) == set(ISING) and len(set(gates.values())) == 1:
            tied_pairs.append(list(pair))
        else:
            untied_pairs.append(list(pair))

    true_bonds = {tuple(sorted(b)) for b in ALL_BONDS}
    even_bonds = {tuple(sorted(b)) for b in TRUE_EVEN_BONDS}
    return {
        "n_single_qubit_gates": n_single,
        "n_fixed_two_qubit_gates": n_fixed2,
        "n_controlled_rotations": n_ctrl2,
        "tied_pairs": tied_pairs,
        "untied_ising_pairs": untied_pairs,
        "has_tied_triple": bool(tied_pairs),
        # The full equivariance signature: nothing in the circuit breaks SU(2).
        "tied_isotropic": bool(tied_pairs) and not untied_pairs
                          and n_single == 0 and n_fixed2 == 0 and n_ctrl2 == 0,
        "tied_on_true_bonds": sum(tuple(p) in true_bonds for p in map(tuple, tied_pairs)),
        "tied_on_even_bonds": sum(tuple(p) in even_bonds for p in map(tuple, tied_pairs)),
        "n_tied_pairs": len(tied_pairs),
    }


def spin_operators() -> list[np.ndarray]:
    """Global spin components S_a = sum_i sigma_a^(i)/2 on N qubits."""
    paulis = [np.array([[0, 1], [1, 0]], dtype=complex),
              np.array([[0, -1j], [1j, 0]], dtype=complex),
              np.array([[1, 0], [0, -1]], dtype=complex)]
    ops = []
    for p in paulis:
        total = np.zeros((2 ** N, 2 ** N), dtype=complex)
        for site in range(N):
            mats = [np.eye(2, dtype=complex)] * N
            mats[site] = p
            acc = mats[0]
            for m in mats[1:]:
                acc = np.kron(acc, m)
            total += acc / 2.0
        ops.append(total)
    return ops


def equivariance_norms(spec, params) -> dict:
    """||[U, S_a]|| for the trained block unitary. Zero for an SU(2)-equivariant
    block regardless of how it is written, so this catches equivariance that the
    name-based structural test would miss (and vice versa)."""
    import pennylane as qml
    import _backend
    _backend.bind_spec(spec)
    circuit_params = np.asarray(params, dtype=float)[: _backend.N_CIRCUIT_PARAMS]

    dev = qml.device("default.qubit", wires=N)

    @qml.qnode(dev)
    def block():
        _backend.apply_ansatz_block(circuit_params, 0)
        return qml.state()

    matrix = qml.matrix(block, wire_order=list(range(N)))()
    norms = []
    for s_op in spin_operators():
        comm = matrix @ s_op - s_op @ matrix
        norms.append(float(np.linalg.norm(comm) / np.linalg.norm(s_op)))
    return {"commutator_norms": norms, "max_commutator_norm": float(max(norms))}


# ------------------------------------------------------------------ scoring


def load_scorer():
    shinka = types.ModuleType("shinka")
    core = types.ModuleType("shinka.core")
    core.run_shinka_eval = None
    shinka.core = core
    sys.modules.setdefault("shinka", shinka)
    sys.modules.setdefault("shinka.core", core)
    import importlib.util
    spec = importlib.util.spec_from_file_location("zc_evaluate", TASK_DIR / "evaluate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def evaluate_spec(spec: list[dict], seeds=(1000,)) -> dict:
    import _backend
    scorer = load_scorer()
    runs = []
    for seed in seeds:
        result = _backend.run_experiment(spec, seed=seed)
        scored = scorer.score_result(result)
        try:
            behaviour = equivariance_norms(spec, result.get("best_params", []))
        except Exception as exc:  # never let diagnostics kill an evaluation
            behaviour = {"commutator_norms": None, "max_commutator_norm": None,
                         "error": str(exc)}
        runs.append({
            "seed": seed,
            "combined_score": scored["combined_score"],
            "margin_score": scored.get("margin_score"),
            "economy_score": scored.get("economy_score"),
            "gap_score": scored.get("gap_score"),
            "loss_score": scored.get("loss_score"),
            "convergence_score": scored.get("convergence_score"),
            "worst_group_margin": scored.get("worst_group_margin"),
            "n_params": result["n_params"],
            "n_distinct": result["n_params_per_block"],
            "validation_accuracy": result["validation_accuracy"],
            "test_accuracy": result["test_accuracy"],
            "validation_margin": result["validation_margin"],
            "convergence_step": result["convergence_step"],
            "stop_reason": result["stop_reason"],
            **behaviour,
        })
    best = max(runs, key=lambda r: r["combined_score"])
    scores = [r["combined_score"] for r in runs]
    return {
        "runs": runs,
        "combined_mean": float(np.mean(scores)),
        "combined_std": float(np.std(scores)),
        "combined_best": float(np.max(scores)),
        **{k: v for k, v in best.items() if k != "seed"},
        "structure": structure(spec),
        "spec": spec,
    }


def run_task(task_id: str, seeds) -> None:
    out = {"task_id": task_id, **evaluate_spec(get_spec(task_id), seeds=seeds)}
    safe = task_id.replace(":", "_")
    (OUT / f"{safe}.json").write_text(json.dumps(out, indent=2))
    s = out["structure"]
    print(f"{task_id:<34} comb={out['combined_mean']:.4f} "
          f"names={out['n_distinct']:>2} vacc={out['validation_accuracy']:.3f} "
          f"tied_iso={s['tied_isotropic']} commut={out.get('max_commutator_norm')}")


# --------------------------------------------------------------- hillclimb


def mutate(spec: list[dict], rng) -> list[dict]:
    """One single-edit mutation: the cheap moves an LLM proposer would make."""
    spec = [dict(g) for g in spec]
    names = sorted({g["param"] for g in spec if "param" in g})
    move = rng.integers(0, 5)
    if move == 0 and len(spec) > 1:                       # delete a gate
        spec.pop(int(rng.integers(0, len(spec))))
    elif move == 1:                                        # add a gate
        pool = SINGLE + FIXED2 + CTRL2 + ISING
        g = pool[int(rng.integers(0, len(pool)))]
        nm = names[int(rng.integers(0, len(names)))] if names else "p0"
        if g in SINGLE:
            spec.insert(int(rng.integers(0, len(spec) + 1)),
                        {"gate": g, "wire": int(rng.integers(0, N)), "param": nm})
        else:
            a, b = rng.choice(N, size=2, replace=False)
            item = {"gate": g, "wires": [int(a), int(b)]}
            if g not in FIXED2:
                item["param"] = nm
            spec.insert(int(rng.integers(0, len(spec) + 1)), item)
    elif move == 2 and names:                              # merge two names
        if len(names) > 1:
            a, b = rng.choice(len(names), size=2, replace=False)
            for g in spec:
                if g.get("param") == names[b]:
                    g["param"] = names[a]
    elif move == 3 and spec:                               # retype a gate
        i = int(rng.integers(0, len(spec)))
        g = spec[i]
        if "wires" in g:
            new = (FIXED2 + CTRL2 + ISING)[int(rng.integers(0, 8))]
            g["gate"] = new
            if new in FIXED2:
                g.pop("param", None)
            else:
                g.setdefault("param", names[0] if names else "p0")
        else:
            g["gate"] = SINGLE[int(rng.integers(0, 3))]
    elif spec:                                             # move wires
        i = int(rng.integers(0, len(spec)))
        if "wires" in spec[i]:
            a, b = rng.choice(N, size=2, replace=False)
            spec[i]["wires"] = [int(a), int(b)]
        else:
            spec[i]["wire"] = int(rng.integers(0, N))
    return spec or [{"gate": "RY", "wire": 0, "param": "p0"}]


def hillclimb(start: str, steps: int, seeds) -> None:
    rng = np.random.default_rng(hash(start) % (2 ** 31))
    spec = PROBES[start]()
    best = evaluate_spec(spec, seeds=seeds)
    trail = [{"step": 0, "combined": best["combined_mean"],
              "names": best["n_distinct"], "accepted": True,
              "tied_isotropic": best["structure"]["tied_isotropic"]}]
    dest = OUT / f"hill_{start}.json"

    def checkpoint():
        """Written every step, not just at the end: these jobs run for hours and
        a silent process is indistinguishable from a hung one."""
        dest.write_text(json.dumps(
            {"task_id": f"hill:{start}", "start": start, "trail": trail, **best},
            indent=2))

    print(f"[{start}] step 0 combined={best['combined_mean']:.4f}", flush=True)
    checkpoint()
    for step in range(1, steps + 1):
        cand_spec = mutate(best["spec"], rng)
        try:
            cand = evaluate_spec(cand_spec, seeds=seeds)
        except Exception as exc:
            print(f"[{start}] step {step} invalid ({exc})", flush=True)
            continue
        accept = cand["combined_mean"] > best["combined_mean"]
        trail.append({"step": step, "combined": cand["combined_mean"],
                      "names": cand["n_distinct"], "accepted": bool(accept),
                      "tied_isotropic": cand["structure"]["tied_isotropic"]})
        if accept:
            best = cand
        print(f"[{start}] step {step} cand={cand['combined_mean']:.4f} "
              f"best={best['combined_mean']:.4f} {'ACCEPT' if accept else ''}",
              flush=True)
        checkpoint()


# ------------------------------------------------------------------ report


def report() -> None:
    rows = []
    for path in sorted(OUT.glob("*.json")):
        d = json.loads(path.read_text())
        if "combined_mean" not in d:
            continue
        rows.append(d)
    if not rows:
        raise SystemExit(f"no results in {OUT}")

    ref = next((r for r in rows if r["task_id"] == "probe:exchange_true"), None)
    if ref is None:
        raise SystemExit("reference probe:exchange_true missing -- cannot grade gates")
    ref_score = ref["combined_mean"]

    def equivariant(r):
        """Trust the behavioural test when it ran; fall back to structure."""
        norm = r.get("max_commutator_norm")
        if norm is not None:
            return norm < 1e-6
        return r["structure"]["tied_isotropic"]

    rows.sort(key=lambda r: -r["combined_mean"])
    print(f"\n{'task':<34} {'comb':>7} {'names':>5} {'vacc':>6} {'wgmarg':>7} "
          f"{'marg-s':>7} {'econ-s':>7} {'equiv':>6} {'commut':>9}")
    print("-" * 100)
    for r in rows[:45]:
        cn = r.get("max_commutator_norm")
        print(f"{r['task_id']:<34} {r['combined_mean']:>7.4f} {r['n_distinct']:>5} "
              f"{r['validation_accuracy']:>6.3f} {r.get('worst_group_margin') or 0:>7.4f} "
              f"{r.get('margin_score') or 0:>7.4f} {r.get('economy_score') or 0:>7.4f} "
              f"{str(equivariant(r)):>6} {('%.2e' % cn) if cn is not None else 'n/a':>9}")

    # G1 is graded over the P2 ADVERSARIAL pool only: random circuits, greedy
    # hill-climbs, and the circuits real evolution actually produced in v1/v2.
    # The P3 stepping stones (partial ties, untied exchange on the true bonds)
    # are deliberately-built partial answers whose whole purpose is to score
    # ABOVE the generic basin -- they are the gradient the redesign needs, not
    # adversaries. Scoring them as adversaries would make the design fail for
    # succeeding. The two pools are separate items in the plan for this reason.
    def adversarial(r):
        t = r["task_id"]
        return (t.startswith("rand:") or t.startswith("hill:")
                or t in {"probe:v2_sonnet_winner", "probe:v2_gpt_winner",
                         "probe:trivial_1p", "probe:seed", "probe:fixed_0p"})

    non_equi = [r for r in rows if not equivariant(r) and adversarial(r)]
    best_non = max(non_equi, key=lambda r: r["combined_mean"]) if non_equi else None
    designed = [r for r in rows if not adversarial(r)]
    print("\ndesigned reference points (NOT adversaries; the intended gradient):")
    for r in sorted(designed, key=lambda x: -x["combined_mean"]):
        print(f"  {r['task_id']:<38} {r['combined_mean']:.4f}  names={r['n_distinct']} "
              f"equiv={equivariant(r)}")

    print("\n" + "=" * 100)
    print(f"reference probe:exchange_true = {ref_score:.4f}")
    print(f"circuits evaluated: {len(rows)}  (non-equivariant: {len(non_equi)})")

    verdict = {}
    if best_non is None:
        print("G1: NO non-equivariant circuits evaluated -- gate cannot be graded")
        verdict["G1"] = "ungraded"
    else:
        gap = ref_score - best_non["combined_mean"]
        margin_gap = (ref.get("margin_score") or 0) - (best_non.get("margin_score") or 0)
        econ_gap = (ref.get("economy_score") or 0) - (best_non.get("economy_score") or 0)
        ok = gap >= 0.10
        carried = margin_gap > econ_gap
        print(f"G1: best non-equivariant = {best_non['task_id']} at "
              f"{best_non['combined_mean']:.4f}; gap = {gap:.4f} "
              f"({'PASS' if ok else 'FAIL'}, need >= 0.10)")
        print(f"    gap composition: margin {margin_gap:+.4f} vs economy {econ_gap:+.4f} "
              f"-> carried by {'MARGIN' if carried else 'ECONOMY/OTHER'} "
              f"({'PASS' if carried else 'FAIL'})")
        verdict["G1"] = "pass" if (ok and carried) else "fail"

    # G2 comes in two forms. The literal pre-registered one uses sonnet's actual
    # gen-66 circuit, which was tied but sat on INDEX-ORDER bonds -- 2/8 overlap
    # with the true ones, chance being 2.29. v3 turns out to price bond
    # placement (exchange_wrong 0.616 vs exchange_true 0.756), which the plan had
    # assumed would stay invisible, so a half-right circuit is ranked low for a
    # substantive reason. The corrected form asks what G2 was really for: does
    # the fitness keep a genuine tied structure that still carries leftover
    # generic gates? Both are reported; neither is quietly dropped.
    for label, key in [("G2 (literal, index-order bonds)", "stone:stone_gen66_replica"),
                       ("G2' (corrected, true bonds)", "stone:stone_true_ring_plus_leftovers"),
                       ("G2'' (corrected, +rotations)", "stone:stone_true_ring_plus_rotations")]:
        row = next((r for r in rows if r["task_id"] == key), None)
        if row is None or best_non is None:
            print(f"{label}: missing -- ungraded")
            continue
        ok = row["combined_mean"] > best_non["combined_mean"]
        print(f"{label}: {row['combined_mean']:.4f} vs best adversarial "
              f"{best_non['combined_mean']:.4f} -> {'PASS' if ok else 'FAIL'}")
        verdict[label] = "pass" if ok else "fail"

    seed_row = next((r for r in rows if r["task_id"] == "probe:seed"), None)
    if seed_row:
        head = ref_score - seed_row["combined_mean"]
        print(f"\nS1/S2 seed check: seed = {seed_row['combined_mean']:.4f} "
              f"(vacc {seed_row['validation_accuracy']:.3f}, "
              f"wg-margin {seed_row.get('worst_group_margin') or 0:.4f}); "
              f"headroom to reference = {head:.4f} "
              f"({'PASS' if head >= 0.35 else 'FAIL'}, need >= 0.35)")
        verdict["seed_headroom"] = float(head)

    print("\nstepping stones (ordered path out of the generic basin):")
    for name in ["probe:seed", "probe:v2_gpt_winner", "stone:stone_seed_plus_untied",
                 "stone:stone_gpt_plus_one_tied", "probe:exchange_untied",
                 "stone:stone_partial_tie", "stone:stone_gen66_replica",
                 "stone:stone_tied_index_ring", "probe:exchange_true"]:
        r = next((x for x in rows if x["task_id"] == name), None)
        if r:
            print(f"  {name:<36} {r['combined_mean']:.4f}  names={r['n_distinct']}")

    (OUT / "gate_verdict.json").write_text(json.dumps({
        "reference": ref_score,
        "best_non_equivariant": best_non["task_id"] if best_non else None,
        "best_non_equivariant_score": best_non["combined_mean"] if best_non else None,
        "n_evaluated": len(rows),
        "verdict": verdict,
    }, indent=2))
    print(f"\nwrote {OUT / 'gate_verdict.json'}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task")
    ap.add_argument("--hillclimb")
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--seeds", default="1000")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    seeds = tuple(int(s) for s in args.seeds.split(","))

    if args.list:
        print("\n".join(all_task_ids()))
    elif args.task:
        run_task(args.task, seeds)
    elif args.hillclimb:
        hillclimb(args.hillclimb, args.steps, seeds)
    elif args.report:
        report()
    else:
        raise SystemExit("nothing to do; see --help")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
