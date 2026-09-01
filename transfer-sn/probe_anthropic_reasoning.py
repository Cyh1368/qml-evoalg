#!/usr/bin/env python3
"""Find a reasoning configuration that actually works for Anthropic on OpenRouter.

claude-opus-4.7 accepted reasoning.effort at xhigh/high/medium and returned
reasoning_tokens=0 every time -- it takes the parameter and ignores it, which
would put a non-reasoning model in the frontier arm. Anthropic's native control
is a thinking-token budget rather than an effort label, so this tries the
budget form and the 4.6 fallback.

Usage:  OPENROUTER_API_KEY=... python3 probe_anthropic_reasoning.py
"""
from __future__ import annotations

import json
import os
import urllib.request

TESTS = [
    ("anthropic/claude-opus-4.7", {"max_tokens": 4000}),
    ("anthropic/claude-opus-4.7", {"enabled": True}),
    ("anthropic/claude-opus-4.6", {"effort": "xhigh"}),
    ("anthropic/claude-opus-4.6", {"max_tokens": 4000}),
    ("anthropic/claude-sonnet-4.6", {"effort": "xhigh"}),
]


def call(key: str, model: str, reasoning: dict | None) -> dict:
    body = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Prove there is no largest prime. Be rigorous but brief."}
        ],
        "max_tokens": 8000,
    }
    if reasoning:
        body["reasoning"] = reasoning
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as fh:
            return json.load(fh)
    except Exception as exc:
        return {"error": {"message": str(exc)[:70]}}


def main() -> int:
    key = os.environ["OPENROUTER_API_KEY"]
    for model, reasoning in TESTS:
        d = call(key, model, reasoning)
        label = f"  {model:<30}{str(reasoning):<26}"
        if "error" in d:
            print(label + "FAIL " + str(d["error"]["message"])[:40])
            continue
        usage = d.get("usage") or {}
        rt = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens")
        cost = usage.get("cost", 0.0)
        print(label + f"OK  reasoning_tokens={rt}  cost=${cost:.5f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
