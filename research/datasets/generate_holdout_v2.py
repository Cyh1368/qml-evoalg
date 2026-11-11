"""Generate a FRESH, never-inspected ring_n6 holdout (protocol section 5).

Why: the v1 sealed split was opened once for a metadata-only inspection
(``npz`` keys and row counts) on 2026-11-11, recorded in
``research/PROVENANCE.md``. Rather than argue that no decision depended on it, this
script produces a second holdout whose rows come from orbits that appear in **no**
development or v1-test artifact, generated after the revised protocol was frozen.

The script never prints label values: only row counts, orbit-overlap counts and
sha256 digests are written, so generating the file cannot leak its labels.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEED_V2 = 20261112
N_DRAW = 4000
OUT = HERE / "locked_holdout_v2"


def ring_canonical(x):
    x = np.asarray(x, float)
    return np.array([min(tuple(np.roll(v, k))
                         for v in (row, row[::-1]) for k in range(len(row)))
                     for row in x])


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    dev = np.load(HERE / "development" / "ring_n6.npz")
    v1 = np.load(HERE / "locked_holdout" / "ring_n6.npz")
    seen = set(map(tuple, ring_canonical(dev["x_train"])))
    seen |= set(map(tuple, ring_canonical(dev["x_validation"])))
    seen |= set(map(tuple, ring_canonical(v1["x_test"])))
    rng = np.random.default_rng(SEED_V2)
    x = rng.uniform(-1, 1, size=(N_DRAW, 6))
    canon = ring_canonical(x)
    fresh = np.array([tuple(c) not in seen for c in canon], dtype=bool)
    x = x[fresh]
    invariant = np.mean(x * np.roll(x, 1, axis=1), axis=1)
    breaking = x[:, 0] - x.mean(axis=1)
    payload = {"x_test": x, "orbit_test": np.arange(len(x))}
    for a in (0.0, 0.1, 0.25, 0.5, 1.0):
        payload["y_alpha_%g_test" % a] = invariant + a * breaking
    path = OUT / "ring_n6.npz"
    np.savez_compressed(path, **payload)
    manifest = {"seed": SEED_V2, "generated_after": "REVISED_PROTOCOL freeze commit "
                  "ecd1be7246f6ee74e8605b38ddaafa654dd7c6b7 (2026-11-11T16:20Z)",
                "drawn": int(N_DRAW), "rows_kept": int(len(x)),
                "rows_dropped_overlap": int((~fresh).sum()),
                "overlap_definition": "exact dihedral canonical form shared with any "
                                      "development or v1-test row",
                "sha256": {str(path.relative_to(HERE)): sha256(path)},
                "note": "labels never printed; only counts and digests are recorded"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
