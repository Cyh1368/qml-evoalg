#!/usr/bin/env python
"""Rewrite the azure_openai rows so their capability flags actually parse.

`_load_pricing_dataframe` strips whitespace only for columns whose dtype is
"object":

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].str.strip()

Modern pandas reports string columns as dtype "str", not "object", so the strip
never runs. Every historical row writes its flags quoted-with-a-leading-space
(`" True"`, `" 1"`), and after the missing strip `" True" == "True"` is False.
Net effect in this environment: is_reasoning and think_temp_fixed are False for
EVERY model in the shipped table, so reasoning effort has never actually been
applied on this cluster, and `has_fixed_temperature` never fired either (which
is why the su2 configs had to pin temperatures to [1.0] by hand).

Rather than change the loader -- which would silently switch reasoning on for
every model in the table and alter unrelated runs -- write only OUR rows in the
form that parses correctly under the current pandas:

    is_reasoning      bare True/False, no quotes, no leading space  -> == "True"
    think_temp_fixed  bare 1/0        -> read as int, astype(str) == "1"

Idempotent. Verifies the parsed result before returning success.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import shinka.llm.providers.pricing as pricing

# deployment -> (is_reasoning, think_temp_fixed)
FLAGS = {
    "gpt-5-mini": (True, True),
    "grok-code-fast-1": (False, False),
    "Phi-4": (False, False),
    "gpt-oss-120b": (False, False),
    "Mistral-Large-3": (False, False),
    "gpt-5.6-sol": (True, True),
    "grok-4": (False, False),
    "DeepSeek-V4-Pro": (True, False),
    "Kimi-K2.6": (False, False),
}


def main() -> int:
    path = Path(pricing._pricing_csv_path)
    lines = path.read_text().splitlines()

    out, touched = [], []
    for line in lines:
        parts = line.split(",")
        name = parts[0].strip()
        if len(parts) >= 10 and parts[1].strip() == "azure_openai" and name in FLAGS:
            reasoning, fixed = FLAGS[name]
            parts[7] = "True" if reasoning else "False"
            parts[8] = "1" if fixed else "0"
            parts[9] = "0"
            line = ",".join(parts)
            touched.append(name)
        out.append(line)

    path.write_text("\n".join(out) + "\n")
    print(f"rewrote {len(touched)} azure rows: {touched}")

    importlib.reload(pricing)
    print(f"\n{'deployment':<18}{'reasoning':<11}{'fixed_temp'}")
    ok = True
    for dep, (reasoning, fixed) in FLAGS.items():
        got_r = pricing.is_reasoning_model(dep)
        got_f = pricing.has_fixed_temperature(dep)
        mark = "" if (got_r == reasoning and got_f == fixed) else "   <-- MISMATCH"
        ok &= not mark
        print(f"{dep:<18}{str(got_r):<11}{got_f}{mark}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
