#!/usr/bin/env python
"""Register the OpenRouter ensemble models in ShinkaEvolve's pricing.csv.

WHY THIS IS REQUIRED

`shinka/llm/kwargs.py` gates the entire reasoning branch on

    if is_reasoning_model(api_model_name):

and for an OpenRouter model the `api_model_name` is the vendor-prefixed form
that `resolve_model_backend` produces -- "openai/gpt-5.6-sol", NOT the bare
"gpt-5.6-sol" that pricing.csv already carries. Measured on the cluster:

    is_reasoning_model("openai/gpt-5.6-sol")  -> False
    is_reasoning_model("gpt-5.6-sol")         -> True

So without a row under the vendor-prefixed key, a requested reasoning effort is
SILENTLY DROPPED and the "frontier" arm runs its models at default effort. This
is the same failure add_openrouter_pricing's Azure sibling documents, reached by
a different route.

`has_fixed_temperature()` reads the same table, which matters because the
gpt-5.x family rejects non-default temperatures.

Cost tracking itself does NOT depend on these rows -- OpenRouter returns
cost_details on every response and `results_ens3_r2` recorded $3.54 across 77
programs with no rows present -- but the prices are filled in correctly anyway
so the max_api_costs fallback is right if that ever changes.

Prices are USD per 1M tokens, read from the OpenRouter /api/v1/models catalogue.

REASONING FLAGS ARE MEASURED, NOT ASSUMED (probe_reasoning_effort.py,
probe_anthropic_reasoning.py). Reasoning tokens returned at effort=xhigh:

    openai/gpt-5.6-sol                    124   -> reasoning
    google/gemini-3.1-pro-preview         905   -> reasoning
    openai/gpt-5.4-mini                  1034   -> reasoning
    google/gemini-3-flash-preview         361   -> reasoning
    anthropic/claude-haiku-4.5            375   -> reasoning
    openai/gpt-5.4-nano                   206   -> reasoning
    google/gemini-3.1-flash-lite-preview  833   -> reasoning
    anthropic/claude-opus-4.6              14   -> reasoning
    anthropic/claude-opus-4.7               0   -> NOT reasoning, at xhigh/high/
                                                 medium AND with a thinking
                                                 budget. Dropped from the
                                                 frontier arm for this reason.
    qwen/qwen3-coder                        0   -> not a reasoning model (fine,
                                                 it is in the weak arm)
"""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

import shinka.llm.providers.pricing as p

# model, in $/M, out $/M, is_reasoning, think_temp_fixed
ROWS = [
    # --- weak arm ---
    ("openai/gpt-5.4-nano", 0.20, 1.25, True, True),
    ("google/gemini-3.1-flash-lite-preview", 0.25, 1.50, True, False),
    ("qwen/qwen3-coder", 0.30, 1.00, False, False),
    # --- mid arm ---
    ("openai/gpt-5.4-mini", 0.75, 4.50, True, True),
    ("google/gemini-3-flash-preview", 0.50, 3.00, True, False),
    ("anthropic/claude-haiku-4.5", 1.00, 5.00, True, False),
    # --- frontier arm ---
    ("openai/gpt-5.6-sol", 5.00, 30.00, True, True),
    ("anthropic/claude-opus-4.6", 5.00, 25.00, True, False),
    ("google/gemini-3.1-pro-preview", 2.00, 12.00, True, False),
    # --- auxiliary (meta / novelty) ---
    # is_reasoning MUST stay False. o4-mini is the meta/novelty model and those
    # calls pass no reasoning_efforts, so a True here makes kwargs.py emit
    # reasoning={'effort': None} -> 'none', which o4-mini rejects with a 400
    # ("Supported values are: 'low', 'medium', and 'high'"). That produced 668
    # retries in 20 minutes on the first mid-arm launch. Guarded by
    # verify_aux_no_reasoning.py.
    ("openai/o4-mini", 1.10, 4.40, False, True),
]


def main() -> int:
    path = Path(p._pricing_csv_path)
    existing = {r["model_name"].strip() for r in csv.DictReader(path.open())}

    backup = path.with_suffix(".csv.bak-openrouter")
    if not backup.exists():
        shutil.copy(path, backup)

    added, skipped = [], []
    with path.open("a", newline="") as fh:
        for model, pin, pout, reasoning, fixed_temp in ROWS:
            if model in existing:
                skipped.append(model)
                continue
            # columns: model_name,provider,input_price,output_price,
            #          input_price_tier2,output_price_tier2,tier_threshold,
            #          is_reasoning,think_temp_fixed,requires_reasoning
            fh.write(
                f"{model},openrouter,{pin},{pout},,,,{reasoning},"
                f"{1 if fixed_temp else 0},0\n"
            )
            added.append((model, pin, pout, reasoning))

    print(f"pricing.csv: {path}")
    print(f"backup     : {backup}")
    if skipped:
        print(f"skipped (already present): {skipped}")
    print(f"\nadded {len(added)} rows:")
    for model, pin, pout, reasoning in added:
        print(f"  {model:<40} ${pin:>6.2f}/${pout:>6.2f} per M   reasoning={reasoning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
