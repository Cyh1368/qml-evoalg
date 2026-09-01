#!/usr/bin/env python
"""Build three OpenRouter-routed ensemble configs for transfer-sn (T2, with context).

Derived from shinka_config_ens3_r2.json -- the existing 3-model OpenRouter arm on
this task -- so every field except the LLM block is bit-identical to arms already
run, and scores stay directly comparable.

WHY THESE ROSTERS

Model choice follows the ensemble practice in the ShinkaEvolve paper
(arXiv:2509.19349, Tables 1-3) rather than a price band. Across all four of its
tasks the enabled pool is always CROSS-VENDOR:

  Circle Packing  claude-sonnet-4, o4-mini, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano
  AIME            gemini-2.5-pro, claude-sonnet-4, o4-mini
  ALE-Bench       gemini-2.5-pro, gemini-2.5-flash, claude-sonnet-4, o4-mini,
                  gpt-5, gpt-5-mini
  MoE LBL         gemini-2.5-pro, claude-sonnet-4, gpt-4.1

Two things follow that the az_* arms got wrong:

  1. Every paper arm draws from 2-3 DIFFERENT vendors. The az_mid_r1 and
     az_frontier_r1 arms shared 2 of their 3 members, so they were not
     independent draws and the tier contrast was confounded.
  2. The paper never builds "capability tiers" as separate arms; it mixes
     capability WITHIN an arm (gpt-5 alongside gpt-5-mini). Tiering across arms
     is our experimental question, so we keep it -- but each arm below is three
     distinct vendors, and NO model appears in two arms.

The paper's single-LLM ablation baseline is gpt-5-nano, which anchors what
"weak" means in this literature.

Empirical motivation from our own az_* runs (see the gallery in viz/circuits):
DeepSeek-V4-Pro scored 0.782 best in az_mid_r1 but 1.200 in az_frontier_r1 --
same model, same reasoning effort, different pool. The strongest member drove
the result and the others rode its archive entries. Disjoint rosters are the
only way to stop that from confounding the next comparison.
"""
from __future__ import annotations

import json
from pathlib import Path

SRC = Path("shinka_config_ens3_r2.json")

# 50 generations per arm. Caps stay at $10/$15/$30: measured xhigh cost is
# ~$0.30/generation for the frontier arm, so 50 generations lands near $15 and
# the cap no longer binds.
NUM_GENERATIONS = 50

ARMS = {
    # WEAK -- nano/lite tier, three vendors. gpt-5.4-nano is the direct
    # descendant of the paper's gpt-5-nano ablation baseline.
    "shinka_config_or_weak_r1.json": {
        "effort": "low",
        "models": [
            "openrouter/openai/gpt-5.4-nano",
            "openrouter/google/gemini-3.1-flash-lite-preview",
            "openrouter/qwen/qwen3-coder",
        ],
        "cap": 10.0,
        "seed": 1,
    },
    # MID -- modern fast/small tier, three vendors. Deliberately excludes
    # gpt-5-mini: in az_weak_r1 it produced 141 of 197 proposals and every
    # valid one, i.e. it was strong enough to turn a "weak" arm into a solo run.
    "shinka_config_or_mid_r1.json": {
        "effort": "medium",
        "models": [
            "openrouter/openai/gpt-5.4-mini",
            "openrouter/google/gemini-3-flash-preview",
            "openrouter/anthropic/claude-haiku-4.5",
        ],
        "cap": 15.0,
        "seed": 1,
    },
    # FRONTIER -- each vendor's top REASONING model. This is the arm Azure
    # could not build: only gpt-5.6-sol was both frontier-class and working.
    # opus-4.7 was the first pick and was dropped: it accepts reasoning.effort
    # at xhigh/high/medium and with an explicit thinking budget, and returns
    # reasoning_tokens=0 every time (probe_anthropic_reasoning.py). opus-4.6
    # actually reasons. A frontier model at default effort is not frontier.
    "shinka_config_or_frontier_r1.json": {
        "effort": "xhigh",
        "models": [
            "openrouter/openai/gpt-5.6-sol",
            "openrouter/anthropic/claude-opus-4.6",
            "openrouter/google/gemini-3.1-pro-preview",
        ],
        "cap": 30.0,
        "seed": 1,
    },
}


def main() -> int:
    cfg = json.loads(SRC.read_text())

    for fname, spec in ARMS.items():
        out = json.loads(json.dumps(cfg))
        e = out["evo"]

        e["llm_models"] = spec["models"]
        # temperatures [1.0] only, matching every prior arm on this task, so
        # scores stay comparable and the gpt-5.x fixed-temperature rule holds.
        # Reasoning effort is DELIBERATELY tiered with the arm: xhigh for
        # frontier, medium for mid, low for weak. Joe's call, and the reason is
        # that the comparison is meant to span capability AND reasoning budget
        # together, not model identity alone -- a top model at low effort is
        # not a frontier proposer. This does mean tier and effort move together
        # by design, so the arms differ in two respects rather than one.
        # reasoning_efforts is client-wide and applies only to models whose
        # pricing row says is_reasoning=True, so qwen3-coder is left alone.
        # REQUIRES add_openrouter_pricing.py to have been run, or the whole
        # reasoning branch is skipped and this setting is silently dropped.
        e["llm_kwargs"] = {
            "temperatures": [1.0],
            "max_tokens": 16384,
            "reasoning_efforts": [spec["effort"]],
        }
        e["llm_dynamic_selection"] = "ucb1"
        e["llm_dynamic_selection_kwargs"] = {
            # Paper value for the bandit that beat both single-LLM and fixed
            # uniform ensembling.
            "exploration_coef": 1.0,
            # Cost spread within each arm is large; a cost-aware bandit would
            # chase the cheapest member and collapse the ensemble into a solo
            # run, which is the thing under test.
            "cost_aware_coef": 0.0,
            "seed": spec["seed"],
        }
        e["max_api_costs"] = spec["cap"]
        # Half the 200-generation target the az_* arms were resumed to.
        e["num_generations"] = NUM_GENERATIONS

        Path(fname).write_text(json.dumps(out, indent=2))
        print(f"wrote {fname}")
        print(f"    models : {e['llm_models']}")
        print(f"    cap    : ${spec['cap']}   generations: {NUM_GENERATIONS}   effort: {spec['effort']}")

    ref = json.loads(SRC.read_text())
    new = json.loads(Path("shinka_config_or_weak_r1.json").read_text())
    changed = sorted(
        k for k in set(ref["evo"]) | set(new["evo"]) if ref["evo"].get(k) != new["evo"].get(k)
    )
    print(f"\nevo fields differing from {SRC.name}: {changed}")
    print(f"db block identical    : {ref['db'] == new['db']}")
    print(f"task_sys_msg identical: {ref['evo']['task_sys_msg'] == new['evo']['task_sys_msg']}")

    all_models = [m for s in ARMS.values() for m in s["models"]]
    print(f"roster overlap between arms: {len(all_models) - len(set(all_models))} (must be 0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
