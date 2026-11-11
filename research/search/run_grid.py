"""Run a grid of search configs inside ONE Slurm job (respects per-user job
limits by using a single slot and looping internally). Resumable: a config whose
run JSON already exists is skipped. Calls ``research.search.harness.run_search``
directly so the locked-holdout guard and provenance still apply.

Example (LLM arm, three model treatments, two development families, three paired
seeds)::

    python3 -m research.search.run_grid --arm llm-verify \
      --families ring_n6,graphs_n6 \
      --treatments ycrc-local:none,ycrc-local:medium,ycrc-local-think:medium \
      --seeds 20261110,20261111,20261112 --budget 12 --steps 120 \
      --max-train 256 --out logs/runs_pilot

Non-LLM arms ignore --treatments (model is None)."""
import argparse
import json
import os
import sys

from research.search import harness


def _tag(arm, family, model, effort, seed):
    return "run_%s_%s_%s-%s_seed%d.json" % (arm, family, model or "none",
                                             effort or "none", int(seed))


def main(argv=None):
    p = argparse.ArgumentParser(prog="research/search/run_grid.py")
    p.add_argument("--arm", required=True, choices=harness.ARMS)
    p.add_argument("--families", required=True)
    p.add_argument("--treatments", default="",
                   help="comma list model:effort for LLM arms; ignored otherwise")
    p.add_argument("--seeds", required=True)
    p.add_argument("--budget", type=int, required=True)
    p.add_argument("--steps", type=int, default=200)
    p.add_argument("--max-train", type=int, default=None)
    p.add_argument("--out", required=True)
    args = p.parse_args(argv)

    families = [f.strip() for f in args.families.split(",") if f.strip()]
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    if args.arm in harness.LLM_ARMS:
        treatments = []
        for t in args.treatments.split(","):
            t = t.strip()
            if not t:
                continue
            model, _, effort = t.partition(":")
            treatments.append((model, effort or "none"))
    else:
        treatments = [(None, None)]

    os.makedirs(args.out, exist_ok=True)
    total = len(families) * len(treatments) * len(seeds)
    done = ran = skipped = 0
    for family in families:
        for model, effort in treatments:
            for seed in seeds:
                path = os.path.join(args.out, _tag(args.arm, family, model,
                                                   effort, seed))
                if os.path.exists(path):
                    skipped += 1
                    done += 1
                    continue
                log = harness.run_search(
                    arm=args.arm, family=family, seed=seed, budget=args.budget,
                    out_dir=args.out, model=model or "ycrc-local",
                    reasoning_effort=effort or "none", steps=args.steps,
                    max_train=args.max_train)
                ran += 1
                done += 1
                print("[%d/%d] %s %s %s/%s seed%d -> dev_risk=%.5f "
                      "valid=%d invalid=%d tok=%d repaired=%s"
                      % (done, total, args.arm, family, model, effort, seed,
                         log["best"]["dev_risk"], log["evaluated_valid"],
                         log["invalid_total"], log["tokens"]["total_tokens"],
                         log["best"]["repair"].get("repaired", False)),
                      flush=True)
    print("GRID DONE arm=%s ran=%d skipped=%d total=%d"
          % (args.arm, ran, skipped, total), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
