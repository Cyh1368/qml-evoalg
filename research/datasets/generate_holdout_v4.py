"""Fourth fresh inputs-only ring_n6 holdout (protocol Addendum A4, second attempt).

Why a fourth: the run that was supposed to use v3 (job ``32990036``) opened the v3 inputs
*before* its self-check gate ran, the gate then aborted the job, and the results were
discarded.  v3 contains **no labels** (inputs only), so no outcome information was exposed,
but the file is treated as consumed and this v4 file is the one the reported evaluation
reads, after the gate passes.  Seed 20261204; disjoint (exact dihedral canonical form) from
development, v1, v2 and v3.
"""
import hashlib
import json
import os
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEED_V4 = 20261204
N_DRAW = 4000
OUT = HERE / "locked_holdout_v4"
SOURCES = (("development/ring_n6.npz", "x_train"),
           ("development/ring_n6.npz", "x_validation"),
           ("locked_holdout/ring_n6.npz", "x_test"),
           ("locked_holdout_v2/ring_n6.npz", "x_test"),
           ("locked_holdout_v3/ring_n6_x.npz", "x_test"))


def ring_canonical(x):
    x = np.asarray(x, float)
    return np.array([min(tuple(np.roll(v, k))
                         for v in (row, row[::-1]) for k in range(len(row)))
                     for row in x])


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    seen = set()
    for name, key in SOURCES:
        p = HERE / name
        if p.exists():
            with np.load(p) as dd:
                seen |= set(map(tuple, ring_canonical(dd[key])))
    rng = np.random.default_rng(SEED_V4)
    x = rng.uniform(-1, 1, size=(N_DRAW, 6))
    fresh = np.array([tuple(c) not in seen for c in ring_canonical(x)], dtype=bool)
    x = x[fresh]
    path = OUT / "ring_n6_x.npz"
    np.savez_compressed(path, x_test=x, orbit_test=np.arange(len(x)))
    os.chmod(path, 0o444)
    manifest = {"seed": SEED_V4,
                "purpose": "E-R4' untouched-input holdout for WP-REPAIR-2 (Addendum A4)",
                "contents": "inputs only; targets rebuilt from the trusted TargetFn",
                "drawn": int(N_DRAW), "rows_kept": int(len(x)),
                "rows_dropped_overlap": int((~fresh).sum()),
                "disjoint_from": [s[0] for s in SOURCES],
                "sha256": {str(path.relative_to(HERE)): sha256(path)},
                "note": "labels never printed; only counts and digests are recorded"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
