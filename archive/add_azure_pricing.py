#!/usr/bin/env python
"""Register the Azure deployments in ShinkaEvolve's pricing.csv.

Without a row here, three things silently break for Azure-routed models:

  1. COST. `get_openai_costs` falls back to pricing.csv when the response has no
     OpenRouter-style `cost_details`. Azure has none, so every query is recorded
     at $0.00 and `max_api_costs` NEVER fires -- observed directly in the probe
     log: "Model 'gpt-5.6-sol' has no pricing entry and response cost metadata
     is absent. Defaulting query cost to 0."
  2. REASONING EFFORT. `is_reasoning_model()` reads this table, so without a row
     the reasoning branch in kwargs.py is skipped entirely and a request for
     high reasoning effort is silently dropped.
  3. TEMPERATURE. `has_fixed_temperature()` reads this table; the gpt-5.x family
     rejects non-default temperatures.

Rows are keyed on the DEPLOYMENT name, because resolve_model_backend() strips
the "azure-" prefix before these lookups.

Prices are USD per 1M tokens. Provenance for each is recorded below: "retail"
means read from the Azure Retail Prices API this session; "list" means the
published per-token list price for the same model, used where the retail API
exposes no meter under a searchable name. List-sourced numbers are a cost-cap
input only -- they do not affect scoring -- and a wrong one makes the cap
slightly loose or tight, not the run invalid.
"""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

import shinka.llm.providers.pricing as p

# deployment, in $/M, out $/M, is_reasoning, think_temp_fixed, provenance
ROWS = [
    # --- small tier ---
    ("gpt-5-mini",        0.25,  2.00,  True,  True,  "list (OpenAI gpt-5-mini)"),
    ("grok-code-fast-1",  0.20,  1.50,  False, False, "list (xAI fast-tier)"),
    ("Phi-4",             0.125, 0.50,  False, False, "retail: Phi-4-Input 0.000125/1K"),
    ("gpt-oss-120b",      0.15,  0.60,  False, False, "retail: gpt-oss-120B glbl"),
    ("Mistral-Large-3",   2.00,  6.00,  False, False, "list (Mistral Large tier)"),
    # --- frontier tier ---
    ("gpt-5.6-sol",       5.00, 30.00,  True,  True,  "list (matches OpenRouter gpt-5.6-sol)"),
    ("gpt-5.4",           2.50, 15.00,  True,  True,  "list (matches OpenRouter gpt-5.4)"),
    ("grok-4",            3.00, 15.00,  False, False, "retail: Grok-4 glbl 0.003/0.015 per 1K"),
    ("DeepSeek-V4-Pro",   1.925, 3.828, True,  False, "retail: FW DeepSeek-V4-Pro DZ"),
    ("Kimi-K2.6",         1.045, 4.40,  False, False, "retail: FW Kimi K2.6 DZ"),
]


def main() -> int:
    path = Path(p._pricing_csv_path)
    existing = {r["model_name"].strip() for r in csv.DictReader(path.open())}

    backup = path.with_suffix(".csv.bak-azure")
    if not backup.exists():
        shutil.copy(path, backup)

    added, skipped = [], []
    with path.open("a", newline="") as fh:
        for dep, pin, pout, reasoning, fixed_temp, prov in ROWS:
            if dep in existing:
                skipped.append(dep)
                continue
            # columns: model_name,provider,input_price,output_price,
            #          input_price_tier2,output_price_tier2,tier_threshold,
            #          is_reasoning,think_temp_fixed,requires_reasoning
            fh.write(
                f"{dep},azure_openai,{pin},{pout},,,, {reasoning}, "
                f"{1 if fixed_temp else 0}, 0\n"
            )
            added.append((dep, pin, pout, prov))

    print(f"pricing.csv: {path}")
    print(f"backup     : {backup}")
    if skipped:
        print(f"skipped (already present): {skipped}")
    print(f"\nadded {len(added)} rows:")
    for dep, pin, pout, prov in added:
        print(f"  {dep:<20} ${pin:>7.3f}/${pout:>7.3f} per M   [{prov}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
