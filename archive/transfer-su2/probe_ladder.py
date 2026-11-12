"""Pre-flight probe ladder for the zc-su2 fitness (LOCAL ONLY, never shipped).

Runs known reference circuits through the exact backend + scoring and checks
the ordering the redesign requires:

    exchange_true, exchange_odd  >  every non-equivariant probe   (by a real gap)

v3 changes to the ladder itself, both fixing defects the v2 postmortem found
(context/zc-su2-v2-results-2026-07-29.md):
  * N_EPOCHS matches the cluster (1000, not 300). The convergence term is
    1 - log1p(step)/log1p(max_steps), so a 300-epoch ladder is not score
    comparable with a 1000-epoch run; v2's published probe numbers were all
    ~0.004 low.
  * the trivial family is represented by the circuits evolution ACTUALLY found
    (v2_sonnet_winner, v2_gpt_winner) as well as by the hand-built trivial_1p.
    v2's ladder passed only because its single trivial representative was a
    weak member of its family; evolution then found better ones and closed the
    gap. A family is only beaten if its best known member is beaten.

Probes:
  seed            generic 24-name seed (the shipped initial program)
  trivial_1p      sonnet's v1 winning 1-name circuit (the adversarial baseline)
  exchange_true   tied XX=YY=ZZ, one shared name, on the true even-sublattice
                  bonds (answer key), i.e. the SU(2)+dimer reference
  exchange_wrong  the same tied exchange on four non-bond (skip-2) pairs
  exchange_untied XX/YY/ZZ with three separate names on the true even bonds

Usage: probe_ladder.py <probe-name>   (run each probe as its own process)
       probe_ladder.py --report       (collect + rank saved results)
"""
from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ZC = HERE.parent / "zc-su2"
OUT = HERE / "probe_results"
OUT.mkdir(exist_ok=True)

os.environ.setdefault("TASK_DATA", str(ZC / "dataset.npz"))
os.environ.setdefault("TRAIN_SIZE", "16")
os.environ.setdefault("DATA_SEED", "2027")
os.environ.setdefault("BATCH_SIZE", "8")
os.environ.setdefault("N_EPOCHS", "1000")  # match the cluster; see docstring
os.environ.setdefault("TTT_LOG_DIR", str(OUT / "training_logs"))

sys.path.insert(0, str(ZC))

KEY = json.loads((HERE / "answer_key.json").read_text())
RELABEL = KEY["qubit_relabel"]
BONDS_SITE = KEY["bonds_site_order"]
# Even-index bonds carry coupling 1.0 (the strong sublattice when j < 1).
TRUE_EVEN_BONDS = [
    [RELABEL[a], RELABEL[b]] for i, (a, b) in enumerate(BONDS_SITE) if i % 2 == 0
]
TRUE_ODD_BONDS = [
    [RELABEL[a], RELABEL[b]] for i, (a, b) in enumerate(BONDS_SITE) if i % 2 == 1
]
WRONG_PAIRS = [[RELABEL[s], RELABEL[(s + 2) % 8]] for s in (0, 1, 4, 5)]  # skip-2, never ring bonds

from probe_ladder_v2winners import V2_SONNET_WINNER, V2_GPT_WINNER


def tied_exchange(pairs, names=("w", "w", "w")):
    spec = []
    for a, b in pairs:
        for gate, name in zip(("XX", "YY", "ZZ"), names):
            spec.append({"gate": gate, "wires": [int(a), int(b)], "param": name})
    return spec


def sonnet_trivial():
    """Sonnet's v1 winner, verbatim construction (one shared name)."""
    n = 8
    spec = []
    for wire in range(n):
        spec.append({"gate": "RX", "wire": wire, "param": "theta"})
    for wire in range(n):
        spec.append({"gate": "RY", "wire": wire, "param": "theta"})
    for i in range(n):
        a, b = i, (i + 1) % n
        if i % 2 == 0:
            spec.append({"gate": "XX", "wires": [a, b], "param": "theta"})
        else:
            spec.append({"gate": "CZ", "wires": [a, b]})
    for i in range(0, n, 2):
        spec.append({"gate": "CZ", "wires": [i, (i + 2) % n]})
    for i in range(n // 2):
        spec.append({"gate": "CZ", "wires": [i, i + n // 2]})
    for wire in range(n):
        spec.append({"gate": "RZ", "wire": wire, "param": "theta"})
    return spec


def seed_spec():
    import importlib
    mod = importlib.import_module("initial_program")
    return mod.ANSATZ_SPEC


PROBES = {
    "seed": seed_spec,
    "trivial_1p": sonnet_trivial,
    # The circuits evolution actually converged to in the v2 run: the strongest
    # known members of the non-equivariant one-name family, and therefore the
    # baselines the reference has to clear.
    "v2_sonnet_winner": lambda: V2_SONNET_WINNER,
    "v2_gpt_winner": lambda: V2_GPT_WINNER,
    "exchange_true": lambda: tied_exchange(TRUE_EVEN_BONDS),
    # The other sublattice: also SU(2) equivariant and also dimer-aligned, so it
    # is expected to tie with exchange_true (the two classes are related by a
    # one-site translation). Included to check that expectation, not to break it.
    "exchange_odd": lambda: tied_exchange(TRUE_ODD_BONDS),
    "exchange_wrong": lambda: tied_exchange(WRONG_PAIRS),
    "exchange_untied": lambda: tied_exchange(TRUE_EVEN_BONDS, names=("wx", "wy", "wz")),
    # Zero-name basin: fixed entanglers, only gain/bias train. Gets the maximum
    # economy score by construction (v1 sonnet exploited empty circuits), so it
    # must NOT outrank the reference.
    "fixed_0p": lambda: (
        [{"gate": "CZ", "wires": [i, (i + 1) % 8]} for i in range(8)]
        + [{"gate": "CZ", "wires": [i, (i + 2) % 8]} for i in range(0, 8, 2)]
    ),
}


def load_scorer():
    """Import the real evaluate.score_result with shinka stubbed out."""
    shinka = types.ModuleType("shinka")
    core = types.ModuleType("shinka.core")
    core.run_shinka_eval = None
    shinka.core = core
    sys.modules.setdefault("shinka", shinka)
    sys.modules.setdefault("shinka.core", core)
    import importlib.util
    spec = importlib.util.spec_from_file_location("zc_evaluate", ZC / "evaluate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_probe(name: str) -> None:
    import _backend
    scorer = load_scorer()
    spec = PROBES[name]()
    result = _backend.run_experiment(spec, seed=1000)
    scored = scorer.score_result(result)
    out = {
        "probe": name,
        "score": scored,
        "n_params": result["n_params"],
        "n_distinct": result["n_params_per_block"],
        "validation_accuracy": result["validation_accuracy"],
        "test_accuracy": result["test_accuracy"],
        "validation_margin": result["validation_margin"],
        "convergence_step": result["convergence_step"],
        "stop_reason": result["stop_reason"],
    }
    (OUT / f"{name}.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "score"}, indent=2))
    print("combined:", scored["combined_score"])


def report() -> None:
    rows = []
    for path in sorted(OUT.glob("*.json")):
        d = json.loads(path.read_text())
        s = d["score"]
        rows.append((s["combined_score"], d["probe"], d["n_distinct"],
                     d["validation_accuracy"], s["worst_group_margin"],
                     s["margin_score"], s["economy_score"]))
    rows.sort(reverse=True)
    print(f"{'probe':<16} {'comb':>6} {'names':>5} {'v-acc':>6} {'wg-marg':>8} "
          f"{'marg-s':>7} {'econ-s':>7}")
    for comb, probe, names, acc, wgm, ms, es in rows:
        print(f"{probe:<16} {comb:>6.4f} {names:>5} {acc:>6.3f} {wgm:>8.4f} "
              f"{ms:>7.4f} {es:>7.4f}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--report"
    if arg == "--report":
        report()
    else:
        run_probe(arg)
