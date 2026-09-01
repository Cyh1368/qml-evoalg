#!/usr/bin/env python3
"""Verify xhigh reasoning effort actually reaches the request through shinka.

Checking is_reasoning_model() alone is not enough: the point of failure is that
kwargs.py builds the request dict and silently omits `reasoning` when the model
lookup misses. This asserts on the built kwargs dict itself, per arm, exactly as
the runner would construct it.

Run AFTER add_openrouter_pricing.py.

Usage:  python3 verify_reasoning_wired.py
"""
from __future__ import annotations

import json
import sys

from shinka.llm.client import resolve_model_backend
from shinka.llm.providers.pricing import has_fixed_temperature, is_reasoning_model

from shinka.llm.kwargs import sample_model_kwargs

ARMS = ["weak", "mid", "frontier"]
NOT_REASONING = {"qwen/qwen3-coder"}

fail = []
for arm in ARMS:
    cfg = json.load(open(f"shinka_config_or_{arm}_r1.json"))["evo"]
    want_effort = cfg["llm_kwargs"]["reasoning_efforts"][0]
    print(f"\n=== {arm} (requested effort={want_effort}) ===")
    for model in cfg["llm_models"]:
        rm = resolve_model_backend(model)
        api = rm.api_model_name
        reasoning = is_reasoning_model(api)
        fixed_t = has_fixed_temperature(api)
        # sample_model_kwargs is what the runner calls; it returns the dict
        # that is handed to the provider, so asserting on it tests the real path.
        kw = sample_model_kwargs(
            model_names=[model],
            temperatures=cfg["llm_kwargs"]["temperatures"],
            max_tokens=[cfg["llm_kwargs"]["max_tokens"]],
            reasoning_efforts=cfg["llm_kwargs"]["reasoning_efforts"],
        )
        got = (kw.get("reasoning") or {}).get("effort")
        if got is None:  # some versions flatten it
            got = kw.get("reasoning_effort")
        expect_effort = None if api in NOT_REASONING else want_effort
        ok = got == expect_effort
        if not ok:
            fail.append(f"{arm}/{api}: reasoning.effort={got!r}, expected {expect_effort!r}")
        print(
            f"  {'PASS' if ok else 'FAIL'}  {api:<40} is_reasoning={str(reasoning):<5} "
            f"fixed_temp={str(fixed_t):<5} -> reasoning.effort={got!r}"
        )

print()
if fail:
    print("FAILURES:")
    for f in fail:
        print("  " + f)
    sys.exit(1)
print("ALL ARMS: xhigh is wired through to the request payload "
      "(and correctly absent for the non-reasoning model).")
