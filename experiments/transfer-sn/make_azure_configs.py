#!/usr/bin/env python
"""Build the two Azure-routed ensemble configs for transfer-sn (T2, with context).

Derived from shinka_config_haiku.json so every field except the LLM block is
bit-identical to the arms already run: same task_sys_msg, same patch mix, same
database/archive settings.

Model choice is from a measured probe of all 12 chat deployments on this Azure
resource, through ShinkaEvolve's own LLMClient and apply_diff_patch, not from
the catalogue listing. What that probe ruled out:

  grok-4       every request 429s ("exceeded rate limit" in eastus2) through all
               20 retries -- effectively zero quota on this resource
  Kimi-K2.6    returned 200 but could not produce an applicable SEARCH/REPLACE
               diff; rambled to the 4096-token cap
  Llama-4-...  200 but degenerate, burned the full token cap answering "say OK"

WEAK arm -- three pipelines, tightest capability band available:
  gpt-5-mini        OpenAI      $0.25/$2.00 per M    $0.0087/proposal
  grok-code-fast-1  xAI         $0.20/$1.50          $0.0048/proposal
  Phi-4             Microsoft   $0.125/$0.50         $0.0014/proposal
  (Mistral-Large-3 was the alternative to Phi-4, but at $2/$6 it is 8-16x the
   input price of the other two and would reintroduce exactly the capability
   gap the PI warned against.)

FRONTIER arm -- three pipelines, each at its top working tier here:
  gpt-5.6-sol       OpenAI      $5/$30, reasoning effort "xhigh"
  DeepSeek-V4-Pro   DeepSeek    $1.925/$3.828
  Mistral-Large-3   Mistral     $2/$6

reasoning_efforts is a client-WIDE setting that kwargs.py applies to any model
whose pricing row says is_reasoning=True. Measured: only gpt-5.6-sol accepts
reasoning.effort on this resource; DeepSeek-V4-Pro and Mistral-Large-3 both
answer "Unsupported parameter: 'reasoning.effort'". Their pricing rows are
therefore is_reasoning=False, so "xhigh" reaches sol alone and the other two are
left on their defaults instead of 400-ing on every proposal.

Meta, novelty and embedding models are moved onto Azure too -- otherwise the run
keeps drawing on the nearly-exhausted OpenRouter credit that prompted the switch.
"""
from __future__ import annotations

import json
from pathlib import Path

# Caps raised to $50 per arm on 2026-08-06 to continue the runs past their first
# stopping points. max_api_costs is a TOTAL, and a resumed run reloads the cost
# already spent from its database, so $50 means $50 lifetime, not $50 more:
# mid resumes with ~$35 of headroom and frontier with ~$33.

SRC = Path("shinka_config_haiku.json")

ARMS = {
    "shinka_config_az_weak_r1.json": {
        "models": ["azure-gpt-5-mini", "azure-grok-code-fast-1", "azure-Phi-4"],
        "effort": "disabled",   # none of the three accepts reasoning.effort
        "cap": 50.0,
        "seed": 1,
    },
    "shinka_config_az_frontier_r1.json": {
        "models": ["azure-gpt-5.6-sol", "azure-DeepSeek-V4-Pro", "azure-Mistral-Large-3"],
        "effort": "xhigh",      # reaches gpt-5.6-sol only, by design
        "cap": 50.0,
        "seed": 1,
    },
    # MID ("Sonnet-class") arm. Sonnet-5 lists at $2/$10 per M; these three sit
    # in a $1.925-$2.50 input band, the tightest capability match Azure offers,
    # across three pipelines:
    #   gpt-5.4          OpenAI     $2.50/$15.00
    #   Mistral-Large-3  Mistral    $2.00/$6.00
    #   DeepSeek-V4-Pro  DeepSeek   $1.925/$3.828
    #
    # gpt-5.4 gets the SAME xhigh effort gpt-5.6-sol got in the frontier arm
    # (verified accepted: medium/high/xhigh all return 200). Holding effort
    # fixed means mid-vs-frontier isolates model tier instead of confounding
    # tier with reasoning effort.
    #
    # Known overlap, stated rather than hidden: Mistral-Large-3 and
    # DeepSeek-V4-Pro also appear in the frontier arm, so this is not an
    # independent draw. Read positively, that makes it a near-controlled
    # swap -- frontier with gpt-5.6-sol@xhigh replaced by gpt-5.4@xhigh -- which
    # isolates the strongest member's contribution. Azure has no other working
    # mid-tier model from a fourth pipeline: grok-4 is quota-blocked and
    # Kimi-K2.6 cannot emit an applicable diff.
    "shinka_config_az_mid_r1.json": {
        "models": ["azure-gpt-5.4", "azure-Mistral-Large-3", "azure-DeepSeek-V4-Pro"],
        "effort": "xhigh",      # reaches gpt-5.4 only; the other two reject it
        "cap": 50.0,
        "seed": 1,
    },
}


def main() -> int:
    cfg = json.loads(SRC.read_text())

    for fname, spec in ARMS.items():
        out = json.loads(json.dumps(cfg))
        e = out["evo"]

        e["llm_models"] = spec["models"]
        # temperature 1.0 for everything: gpt-5.x rejects non-default
        # temperatures, and the others are indifferent.
        e["llm_kwargs"] = {
            "temperatures": [1.0],
            "max_tokens": 16384,
            "reasoning_efforts": [spec["effort"]],
        }
        e["llm_dynamic_selection"] = "ucb1"
        e["llm_dynamic_selection_kwargs"] = {
            "exploration_coef": 1.0,
            # Cost spread inside each arm is large (weak 6x, frontier 4x). A
            # cost-aware bandit would chase the cheapest member and collapse the
            # ensemble into a near-solo run, which is the thing under test.
            "cost_aware_coef": 0.0,
            "seed": spec["seed"],
        }
        e["max_api_costs"] = spec["cap"]

        # Keep every auxiliary call on Azure as well.
        e["meta_llm_models"] = ["azure-gpt-5-mini"]
        e["meta_llm_kwargs"] = {"temperatures": [1.0], "max_tokens": 8192}
        e["novelty_llm_models"] = ["azure-gpt-5-mini"]
        e["novelty_llm_kwargs"] = {"temperatures": [1.0]}
        e["embedding_model"] = "azure-text-embedding-3-large"

        Path(fname).write_text(json.dumps(out, indent=2))
        print(f"wrote {fname}")
        print(f"    models     : {e['llm_models']}")
        print(f"    effort     : {spec['effort']}   cap: ${spec['cap']}")

    ref = json.loads(SRC.read_text())
    new = json.loads(Path("shinka_config_az_weak_r1.json").read_text())
    changed = sorted(
        k for k in set(ref["evo"]) | set(new["evo"]) if ref["evo"].get(k) != new["evo"].get(k)
    )
    print(f"\nevo fields differing from {SRC.name}: {changed}")
    print(f"db block identical    : {ref['db'] == new['db']}")
    print(f"task_sys_msg identical: {ref['evo']['task_sys_msg'] == new['evo']['task_sys_msg']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
