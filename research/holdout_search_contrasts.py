"""Full paired arm-versus-random contrast matrix for the E-S7 sealed-test evaluation.

Why this exists: the manuscript's E-S7 table showed every arm against ``random`` on the
sealed split, but `holdout_oneshot.py` recorded only four contrasts per family, of which
exactly one involved ``random``. The other rows were therefore quoted from nothing. This
module regenerates the whole matrix from the per-run ``search_rows`` already stored in
``research/HOLDOUT_RESULTS.json``.

**No sealed array is read here.** The inputs are the per-run risks written by the one-shot
run that consumed the sealed split; recomputing contrasts from that record is arithmetic on
an already-read file, and this module asserts as much by refusing any locked path.

Units: runs (12 per arm per family), paired by seed. Endpoint: **candidate** sealed-test
risk (the deployed endpoint is measured by `research/holdout_deployed.py`, Addendum A5.5).
"""
import argparse
import json
import sys

import numpy as np

from research.core import paired as _P

BASELINE = "random"


def contrasts(rows, families=None):
    out = []
    fams = families or sorted({r["family"] for r in rows})
    for fam in fams:
        rs = [r for r in rows if r["family"] == fam]
        by = {}
        for r in rs:
            by.setdefault(r["arm"], {})[int(r["seed"])] = float(r["test_risk"])
        base = by.get(BASELINE)
        if not base:
            sys.exit("no %s arm in %s" % (BASELINE, fam))
        for arm in sorted(by):
            if arm == BASELINE:
                continue
            seeds = sorted(set(by[arm]) & set(base))
            d = [by[arm][s] - base[s] for s in seeds]
            if len(d) < 2:
                continue
            boot = _P.bootstrap_ci(d)
            out.append({"family": fam, "a": arm, "b": BASELINE, "n_pairs": len(seeds),
                        "mean_a": float(np.mean([by[arm][s] for s in seeds])),
                        "mean_b": float(np.mean([base[s] for s in seeds])),
                        "mean_diff_a_minus_b": float(np.mean(d)),
                        "bootstrap": boot,
                        "p_shifted_bootstrap": _P.shifted_bootstrap_p(d),
                        "p_signflip": _P.signflip_p(d),
                        "verdict": _P.verdict(boot["ci95_low"], boot["ci95_high"])})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="research/HOLDOUT_RESULTS.json")
    ap.add_argument("--out", default="research/HOLDOUT_SEARCH_CONTRASTS.json")
    a = ap.parse_args(argv)
    if "locked" in a.inp.lower():
        raise SystemExit("this module reads the result record, never a sealed array")
    d = json.load(open(a.inp))
    rows = d["search_rows"]
    out = {"source": a.inp, "endpoint": "candidate sealed-test risk (A5.5 supersedes for "
            "the deployed predictor)", "sealed_read_here": False,
           "baseline": BASELINE, "contrasts": contrasts(rows)}
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    for c in out["contrasts"]:
        print("%-11s %-18s vs %-6s n=%2d  %+.5f  CI [%+.5f, %+.5f]  %s"
              % (c["family"], c["a"], c["b"], c["n_pairs"], c["mean_diff_a_minus_b"],
                 c["bootstrap"]["ci95_low"], c["bootstrap"]["ci95_high"], c["verdict"]))
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
