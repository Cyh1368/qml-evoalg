"""A6.5 addendum: does the idealised uniform model reproduce the measured acceptance?

The manuscript contrasts two idealised proposal models with the measured acceptance rate:

* one uniform permutation: accept = |L_t| / |S_n|;
* k independent uniform generators: accept = (|L_t| / |S_n|)^k, since the closure is inside
  L_t iff every generator is.

Both are cheap predictions, so they should be *checked* rather than asserted. This module draws
independent uniform generator lists and probe-tests them, exactly as
``corrected_gate.accept_probability`` does, but with enough draws (4000) to resolve the
two-generator rate, which is ~2.8e-4 for the ring's scored target: 400 draws would see a tenth
of an event on average.

It also records the empirical LLM proposal rate next to them, because the gap between the two is
the point: the uniform models are correct about uniform proposals and silent about the ones this
paper actually studies.

Run: ``python3 -m research.search.uniform_model_check --out research/search/uniform_model_check.json``
"""
from __future__ import annotations

import argparse
import json
import math
import time

import numpy as np

from research.core import tasks as _T
from research.search import corrected_gate as CG
from research.search.verify_semantics import probe_indices

DRAWS = 4000
SEED = 20261112


def main(argv=None):
    ap = argparse.ArgumentParser(prog="research/search/uniform_model_check.py")
    ap.add_argument("--families", default="ring_n6,graphs_n6")
    ap.add_argument("--target", default="alpha_0")
    ap.add_argument("--draws", type=int, default=DRAWS)
    ap.add_argument("--out", default="research/search/uniform_model_check.json")
    a = ap.parse_args(argv)
    from research.core import paired as P
    out = {"protocol": "A6.5 addendum", "draws": int(a.draws), "seed": SEED,
           "probe_rows": CG.PROBE_ROWS, "probe_seed": CG.PROBE_SEED,
           "atol_abs": CG.ATOL_ABS, "atol_rel": CG.ATOL_REL, "families": {}}
    for fam in a.families.split(","):
        task = _T.load_family(fam.strip(), development=True, locked=False)
        n = int(task.n_qubits)
        probe = probe_indices(task, n_rows=CG.PROBE_ROWS, seed=CG.PROBE_SEED)
        tgt = a.target if a.target in task.targets else task.primary_target
        el = CG.exact_L(task, tgt, probe)
        ratio = el["ratio"]
        entry = {"n_qubits": n, "target": tgt, "exact_L_order": el["order"],
                 "factorial_n": math.factorial(n), "ratio": ratio, "cells": {}}
        for k in (1, 2, 3):
            hits = 0
            rng = np.random.default_rng(SEED)
            t0 = time.time()
            for _ in range(a.draws):
                gens = [tuple(rng.permutation(n)) for _ in range(k)]
                ok, _ = CG.sound_on_probe(task, gens, tgt, probe)
                hits += int(ok)
            w = P.wilson_ci(hits, a.draws)
            entry["cells"]["k=%d" % k] = {
                "k": k, "draws": int(a.draws), "accepted": int(hits),
                "measured": hits / a.draws, "ci95_low": w["ci95_low"],
                "ci95_high": w["ci95_high"], "model": (ratio ** k),
                "seconds": time.time() - t0}
        out["families"][fam.strip()] = entry
        print("%s: ratio %.6f  k=1 %.5f  k=2 %.5f (model %.6f)"
              % (fam, ratio, entry["cells"]["k=1"]["measured"],
                 entry["cells"]["k=2"]["measured"], entry["cells"]["k=2"]["model"]))
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
