#!/usr/bin/env python3
"""Guard against the o4-mini regression that killed the first mid-arm launch.

add_openrouter_pricing.py originally gave openai/o4-mini is_reasoning=True so its
cost would be tracked. That had a side effect: o4-mini is the meta/novelty model,
those calls pass NO reasoning_efforts, and kwargs.py then emits
`reasoning={'effort': None}` -> serialized as 'none'. o4-mini rejects it:

    Unsupported value: 'none' is not supported with the 'o4-mini-2025-04-16'
    model. Supported values are: 'low', 'medium', and 'high'.

668 retries in 20 minutes on the mid arm. Only mid hit it because the novelty
LLM judge fires only once embedding similarity crosses the threshold; weak and
frontier would have hit it as their archives filled.

Fix: is_reasoning=False for o4-mini, restoring the behaviour ens3_r2 ran with.

This asserts BOTH halves: aux models get no reasoning param, arm models keep
their per-arm effort.

Usage:  python3 verify_aux_no_reasoning.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from shinka.llm.kwargs import sample_model_kwargs
from shinka.llm.providers.pricing import is_reasoning_model

failures = []

# --- aux (meta / novelty): must receive NO reasoning param ---
cfg = json.loads(Path("shinka_config_or_mid_r1.json").read_text())["evo"]
aux = list(dict.fromkeys((cfg.get("meta_llm_models") or []) + (cfg.get("novelty_llm_models") or [])))
for model in aux:
    kw = sample_model_kwargs(
        model_names=[model], temperatures=[1.0], max_tokens=[4096], reasoning_efforts=[]
    )
    got = kw.get("reasoning")
    ok = got is None
    if not ok:
        failures.append(f"aux {model}: reasoning={got!r}, expected None")
    print(f"  {'PASS' if ok else 'FAIL'}  aux  {model:<34} reasoning={got!r}")

# --- arm models: must still carry their own effort ---
for arm in ["weak", "mid", "frontier"]:
    c = json.loads(Path(f"shinka_config_or_{arm}_r1.json").read_text())["evo"]
    effort = c["llm_kwargs"]["reasoning_efforts"][0]
    for model in c["llm_models"]:
        kw = sample_model_kwargs(
            model_names=[model],
            temperatures=[1.0],
            max_tokens=[c["llm_kwargs"]["max_tokens"]],
            reasoning_efforts=[effort],
        )
        got = (kw.get("reasoning") or {}).get("effort")
        api = model.replace("openrouter/", "")
        want = effort if is_reasoning_model(api) else None
        ok = got == want
        if not ok:
            failures.append(f"{arm} {model}: reasoning.effort={got!r}, expected {want!r}")
        print(f"  {'PASS' if ok else 'FAIL'}  {arm:<8} {model:<44} reasoning.effort={got!r}")

print()
if failures:
    print("BLOCKED:")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("VERIFIED: aux models get no reasoning param; arm models keep their effort.")
