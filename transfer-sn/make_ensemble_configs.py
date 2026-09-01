#!/usr/bin/env python
"""Build the multi-provider ensemble configs for transfer-sn (T2, contextualized).

Derived from the existing single-model config so that EVERY field except the
LLM block is bit-identical to the arms already run -- same task_sys_msg, same
patch-type mix, same database/archive settings. The only variable is which
model(s) write the proposals.

Ensemble = one model per pretraining pipeline, all at the small/fast tier:
    anthropic/claude-haiku-4.5   Anthropic   $1.00/$5.00 per M   (tier anchor;
                                             already has a solo arm on this task)
    google/gemini-3.6-flash      Google      $1.50/$7.50 per M   (Flash is
                                             Google's small tier; Flash-Lite
                                             would be a tier BELOW Haiku)
    openai/gpt-5.6-luna          OpenAI      $0.10/$0.60 per M   (small tier of
                                             the family whose `sol` arm found
                                             permutation_equivariant_ansatz at
                                             generation 33)

Two design choices that are NOT inherited from the old configs:

  llm_dynamic_selection = "ucb1"
      With one model this was `null` and meaningless. With three it is the
      scheduler the PI referred to: it monitors each model's realised score
      gain and steers selection. AsymmetricUCB keeps an epsilon=0.2 exploration
      floor, so no model can be starved completely.

  cost_aware_coef = 0.0   (was 0.7)
      The three models span a 26x cost ratio per proposal (measured:
      luna $0.0017, haiku $0.0173, gemini-3.6-flash $0.0452). At 0.7 the bandit
      would chase the cheapest arm and quietly collapse the ensemble back to a
      near-solo run, which is exactly the thing being tested. Selection is
      therefore driven by score improvement alone.
"""
from __future__ import annotations

import json
from pathlib import Path

SRC = Path("shinka_config_haiku.json")

ENSEMBLE = [
    "openrouter/anthropic/claude-haiku-4.5",
    "openrouter/google/gemini-3.6-flash",
    "openrouter/openai/gpt-5.6-luna",
]

# (output filename, bandit seed) -- two independent replicates, because a single
# run cannot distinguish "the ensemble finds it" from "this run got lucky".
ARMS = [
    ("shinka_config_ens3_r1.json", 1),
    ("shinka_config_ens3_r2.json", 2),
]

MAX_API_COSTS = 8.0


def main() -> int:
    cfg = json.loads(SRC.read_text())
    evo = cfg["evo"]

    for fname, seed in ARMS:
        out = json.loads(json.dumps(cfg))  # deep copy
        e = out["evo"]

        e["llm_models"] = list(ENSEMBLE)
        # temperature 1.0 is mandatory: the gpt-5.x family rejects non-default
        # temperatures (108 'NoneType' proposal failures in the su2 v1 run).
        # Anthropic and Google both accept 1.0, so one value serves all three.
        e["llm_kwargs"] = {"temperatures": [1.0], "max_tokens": 16384}
        e["llm_dynamic_selection"] = "ucb1"
        e["llm_dynamic_selection_kwargs"] = {
            "exploration_coef": 1.0,
            "cost_aware_coef": 0.0,
            "seed": seed,
        }
        e["max_api_costs"] = MAX_API_COSTS

        Path(fname).write_text(json.dumps(out, indent=2))
        print(f"wrote {fname}")
        print(f"    models          : {e['llm_models']}")
        print(f"    selection       : {e['llm_dynamic_selection']} {e['llm_dynamic_selection_kwargs']}")
        print(f"    max_api_costs   : {e['max_api_costs']}")

    # Prove the ONLY differences from the reference arm are the LLM fields.
    ref = json.loads(SRC.read_text())
    new = json.loads(Path(ARMS[0][0]).read_text())
    changed = sorted(
        k for k in set(ref["evo"]) | set(new["evo"]) if ref["evo"].get(k) != new["evo"].get(k)
    )
    print(f"\nevo fields differing from {SRC.name}: {changed}")
    print(f"db block identical: {ref['db'] == new['db']}")
    print(f"task_sys_msg identical: {ref['evo']['task_sys_msg'] == new['evo']['task_sys_msg']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
