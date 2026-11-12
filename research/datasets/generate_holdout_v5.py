"""Fifth fresh inputs-only holdout, for the deployed-endpoint search evaluation
(REVISED_PROTOCOL Addendum A5.5).

Why a fifth: the E-S7 evaluation in `research/HOLDOUT_RESULTS.json` scored the *candidate*
endpoint only (`holdout_oneshot._search_run` never applied the selected hypothesis's
averaging), and the original sealed split is consumed by that read. The referee's required
fix is a deployed-endpoint measurement, so it must run on **newly reserved** inputs rather
than a second look at inspected data; anything else would be labelled post hoc.

Contents: inputs only, both search families, seed 20261205.

* `ring_n6`: 4000 draws from the same Uniform([-1,1]^6) generator, exact dihedral-orbit
  disjoint from development and holdouts v1-v4.
* `graphs_n6`: 4000 labeled 6-vertex graphs whose exact isomorphism class (canonical form
  over all 720 vertex relabelings) appears in no development or holdout split.

Labels are never written: the evaluator rebuilds them from the trusted `label_oracle`.
"""
import hashlib
import itertools
import json
import os
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEED = 20261205
N_DRAW = 4000
OUT = HERE / "locked_holdout_v5"

RING_SOURCES = (("development/ring_n6.npz", "x_train"),
                ("development/ring_n6.npz", "x_validation"),
                ("locked_holdout/ring_n6.npz", "x_test"),
                ("locked_holdout_v2/ring_n6.npz", "x_test"),
                ("locked_holdout_v3/ring_n6_x.npz", "x_test"),
                ("locked_holdout_v4/ring_n6_x.npz", "x_test"))
GRAPH_SOURCES = (("development/graphs_n6.npz", "x_train"),
                 ("development/graphs_n6.npz", "x_validation"),
                 ("locked_holdout/graphs_n6.npz", "x_test"),
                 ("locked_holdout_v2/graphs_n6.npz", "x_test"))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ring_canonical(x):
    x = np.asarray(x, float)
    return np.array([min(tuple(np.roll(v, k))
                         for v in (row, row[::-1]) for k in range(len(row)))
                     for row in x])


def edge_relabel_maps(n=6):
    """Column map of the induced edge action for every vertex permutation."""
    pairs = list(itertools.combinations(range(n), 2))
    index = {p: i for i, p in enumerate(pairs)}
    maps = []
    for perm in itertools.permutations(range(n)):
        maps.append([index[tuple(sorted((perm[a], perm[b])))] for a, b in pairs])
    return np.array(maps, dtype=np.int64)


def graph_canonical(x, maps, chunk=2000):
    """Canonical isomorphism form: lexicographic minimum over all relabelings."""
    x = np.asarray(x, dtype=np.uint8)
    out = np.empty_like(x)
    weights = (np.int64(1) << np.arange(x.shape[1] - 1, -1, -1, dtype=np.int64))
    for start in range(0, len(x), chunk):
        block = x[start:start + chunk]
        rel = block[:, maps]                       # (rows, 720, 15)
        keys = rel.astype(np.int64) @ weights      # lexicographic == numeric here
        best = np.argmin(keys, axis=1)
        out[start:start + chunk] = rel[np.arange(len(block)), best]
    return out


def main():
    OUT.mkdir(exist_ok=True)
    # Provenance note: an earlier run of this generator crashed *after* writing the ring
    # file (a graphs-side bug), before any evaluator read it and while it held no labels.
    # It is overwritten here; the digest below is the one that matters, and no v5 input was
    # ever read by an evaluator before the recorded one-shot run.
    for stale in OUT.glob("*_x.npz"):
        os.chmod(stale, 0o644)
        stale.unlink()
    manifest = {"seed": SEED,
                "purpose": "deployed-endpoint search evaluation (Addendum A5.5)",
                "contents": "inputs only; labels rebuilt from the trusted label_oracle",
                "families": {}}

    # ---- ring_n6
    seen = set()
    for name, key in RING_SOURCES:
        p = HERE / name
        if p.exists():
            with np.load(p) as dd:
                seen |= set(map(tuple, ring_canonical(dd[key])))
    rng = np.random.default_rng(SEED)
    x = rng.uniform(-1, 1, size=(N_DRAW, 6))
    keep = np.array([tuple(c) not in seen for c in ring_canonical(x)], dtype=bool)
    x_ring = x[keep]
    path = OUT / "ring_n6_x.npz"
    np.savez_compressed(path, x_test=x_ring, orbit_test=np.arange(len(x_ring)))
    os.chmod(path, 0o444)
    manifest["families"]["ring_n6"] = {
        "file": str(path.relative_to(HERE)), "drawn": N_DRAW,
        "rows_kept": int(len(x_ring)), "rows_dropped_overlap": int((~keep).sum()),
        "disjoint_from": [s[0] for s in RING_SOURCES]}

    # ---- graphs_n6
    maps = edge_relabel_maps(6)
    seen_g = set()
    for name, key in GRAPH_SOURCES:
        p = HERE / name
        if p.exists():
            with np.load(p) as dd:
                canon = graph_canonical(dd[key], maps)
                seen_g |= {tuple(r) for r in canon}
    all_graphs = np.array(list(itertools.product([0, 1], repeat=15)), dtype=np.uint8)
    canon_all = graph_canonical(all_graphs, maps)
    fresh = np.array([tuple(r) not in seen_g for r in canon_all], dtype=bool)
    pool = all_graphs[fresh]
    rng2 = np.random.default_rng(SEED + 1)
    pick = rng2.choice(len(pool), size=min(N_DRAW, len(pool)), replace=False)
    x_graphs = pool[pick]
    gpath = OUT / "graphs_n6_x.npz"
    np.savez_compressed(gpath, x_test=x_graphs, orbit_test=np.arange(len(x_graphs)))
    os.chmod(gpath, 0o444)
    manifest["families"]["graphs_n6"] = {
        "file": str(gpath.relative_to(HERE)), "unseen_isomorphism_rows_available":
            int(fresh.sum()), "rows_kept": int(len(x_graphs)),
        "sampling": "uniform over labeled graphs whose isomorphism class is unseen",
        "disjoint_from": [s[0] for s in GRAPH_SOURCES]}

    manifest["sha256"] = {f["file"]: sha256(HERE / f["file"])
                          for f in manifest["families"].values()}
    manifest["rewrite_note"] = ("the ring file was rewritten once during generator "
                                "debugging before any read; it contains no labels, and "
                                "the digests below describe the files as evaluated")
    manifest["note"] = ("labels never printed; only counts and digests are recorded; "
                        "read once, after the evaluator's development self-check passes")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
