"""Generate the third fresh ring_n6 holdout (protocol Addendum A4).

Why a third one: the one-shot evaluator shipped in commit ``e910bf8f`` evaluated **every**
``eta`` against the ``alpha_0`` (invariant) label and, separately, the sealed ``.npz``
files' own ``alpha_*`` labels use a *different* breaking function
(``x[:,0] - mean(x)``, unnormalised) from WP-REPAIR-2's frozen-direction, train-normalised
``b``.  Both defects are recorded in ``research/PROVENANCE.md``; the v1 and v2 splits are
therefore reported as consumed by a defective evaluation and are not re-read.

This holdout ships **inputs only** (``x_test``): the target for each arm is rebuilt from the
same trusted ``TargetFn`` used to train it, so an untouched-input holdout is exactly what is
being tested.  The script never prints label values.
"""
import hashlib
import json
import os
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEED_V3 = 20261203
N_DRAW = 4000
OUT = HERE / "locked_holdout_v3"


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
    for name, key in (("development/ring_n6.npz", "x_train"),
                      ("development/ring_n6.npz", "x_validation"),
                      ("locked_holdout/ring_n6.npz", "x_test"),
                      ("locked_holdout_v2/ring_n6.npz", "x_test")):
        p = HERE / name
        if not p.exists():
            continue
        with np.load(p) as dd:
            seen |= set(map(tuple, ring_canonical(dd[key])))
    rng = np.random.default_rng(SEED_V3)
    x = rng.uniform(-1, 1, size=(N_DRAW, 6))
    fresh = np.array([tuple(c) not in seen for c in ring_canonical(x)], dtype=bool)
    x = x[fresh]
    path = OUT / "ring_n6_x.npz"
    np.savez_compressed(path, x_test=x, orbit_test=np.arange(len(x)))
    os.chmod(path, 0o444)
    manifest = {"seed": SEED_V3, "purpose": "E-R4' untouched-input holdout for "
                  "WP-REPAIR-2 (protocol Addendum A4)",
                "generated_after": "REVISED_PROTOCOL Addendum A3/A4 (2026-11-11)",
                "drawn": int(N_DRAW), "rows_kept": int(len(x)),
                "rows_dropped_overlap": int((~fresh).sum()),
                "overlap_definition": "exact dihedral canonical form shared with any "
                                      "development, v1-test or v2-test row",
                "contents": "inputs only; targets are rebuilt from the trusted "
                            "TargetFn at evaluation time",
                "sha256": {str(path.relative_to(HERE)): sha256(path)},
                "note": "labels never printed; only counts and digests are recorded"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
