#!/usr/bin/env python3
"""Check which reasoning-effort levels OpenRouter actually honours per model.

Motivation: shinka's kwargs.py gates the whole reasoning branch on
`is_reasoning_model(api_model_name)`, and for OpenRouter the api_model_name is
the vendor-prefixed form ("openai/gpt-5.6-sol"), which has no pricing.csv row.
The branch is therefore skipped and the requested effort is silently dropped --
the same failure mode add_azure_pricing.py documents for Azure.

Before adding pricing rows we need to know the effort levels are real. A model
that accepts the parameter but burns zero reasoning tokens is not reasoning.

Usage:  OPENROUTER_API_KEY=... python3 probe_reasoning_effort.py
"""
from __future__ import annotations

import json
import os
import urllib.request

MODELS = [
    ("openai/gpt-5.6-sol", "frontier"),
    ("anthropic/claude-opus-4.7", "frontier"),
    ("google/gemini-3.1-pro-preview", "frontier"),
    ("openai/gpt-5.4-mini", "mid"),
    ("google/gemini-3-flash-preview", "mid"),
    ("anthropic/claude-haiku-4.5", "mid"),
    ("openai/gpt-5.4-nano", "weak"),
    ("google/gemini-3.1-flash-lite-preview", "weak"),
    ("qwen/qwen3-coder", "weak"),
]
EFFORTS = ["xhigh", "high", "medium"]

PROMPT = "Prove there is no largest prime. Be rigorous but brief."


def call(key: str, model: str, effort: str | None) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 8000,
    }
    if effort:
        body["reasoning"] = {"effort": effort}
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.load(r)
    except Exception as e:
        return {"error": {"message": str(e)[:80], "code": "exc"}}


def main() -> int:
    key = os.environ["OPENROUTER_API_KEY"]
    print(f"{'model':<40}{'arm':<10}{'effort':<8}{'status':<8}{'reasoning_tok':<15}{'cost':<10}")
    print("-" * 91)
    out = {}
    for model, arm in MODELS:
        for effort in EFFORTS:
            d = call(key, model, effort)
            if "error" in d:
                msg = str(d["error"].get("message"))[:34]
                print(f"{model:<40}{arm:<10}{effort:<8}{'FAIL':<8}{msg}")
                out[f"{model}|{effort}"] = {"ok": False, "error": msg}
                continue
            u = d.get("usage") or {}
            rt = (u.get("completion_tokens_details") or {}).get("reasoning_tokens")
            cost = u.get("cost", 0.0)
            print(f"{model:<40}{arm:<10}{effort:<8}{'OK':<8}{str(rt):<15}${cost:<9.5f}")
            out[f"{model}|{effort}"] = {"ok": True, "reasoning_tokens": rt, "cost": cost}
            # First effort that genuinely reasons is enough for this model.
            if rt:
                break
    with open("probe_reasoning_effort.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nwrote probe_reasoning_effort.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
