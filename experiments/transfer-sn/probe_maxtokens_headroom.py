#!/usr/bin/env python3
"""Find a max_tokens that lets each model finish a real diff at xhigh reasoning.

gpt-5.4-mini failed the full-seed diff probe at max_tokens=16384 with
    status=incomplete, reason='max_output_tokens', output_types=['reasoning']
i.e. at xhigh it spends the ENTIRE budget thinking and never emits a message.
All three retries failed the same way, so this would stall the mid arm.

The short-prompt probe did not catch this: reasoning length scales with the
task, and the real prompt carries a 17KB seed.

Usage:  OPENROUTER_API_KEY=... python3 probe_maxtokens_headroom.py
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

# The models that spend the most on reasoning, plus the one that failed.
MODELS = ["openai/gpt-5.4-mini", "openai/gpt-5.4-nano", "openai/gpt-5.6-sol"]
BUDGETS = [16384, 32768, 65536]

SEED = Path("initial_program.py").read_text()
PROMPT = (
    "Here is the current program:\n\n"
    f"```python\n{SEED}\n```\n\n"
    "Propose ONE concrete improvement to the ANSATZ_SPEC inside the "
    "EVOLVE-BLOCK. Respond with the exact SEARCH/REPLACE diff format."
)


def call(key: str, model: str, max_tokens: int) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": max_tokens,
        "reasoning": {"effort": "xhigh"},
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=900) as fh:
            return json.load(fh)
    except Exception as exc:
        return {"error": {"message": str(exc)[:70]}}


def main() -> int:
    key = os.environ["OPENROUTER_API_KEY"]
    print(f"{'model':<24}{'budget':<9}{'sec':<6}{'reason_tok':<12}{'msg_chars':<11}{'finish':<12}cost")
    print("-" * 84)
    for model in MODELS:
        for budget in BUDGETS:
            t0 = time.time()
            d = call(key, model, budget)
            dt = time.time() - t0
            if "error" in d:
                print(f"{model:<24}{budget:<9}{dt:<6.0f}FAIL {d['error']['message'][:40]}")
                continue
            ch = (d.get("choices") or [{}])[0]
            content = (ch.get("message") or {}).get("content") or ""
            usage = d.get("usage") or {}
            rt = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens")
            fin = ch.get("native_finish_reason") or ch.get("finish_reason")
            print(
                f"{model:<24}{budget:<9}{dt:<6.0f}{str(rt):<12}{len(content):<11}{str(fin):<12}"
                f"${usage.get('cost', 0):.4f}"
            )
            if content.strip():
                break  # this budget suffices for this model
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
