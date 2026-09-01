#!/usr/bin/env python
"""Capability probe for the ensemble candidates.

Runs the REAL ShinkaEvolve LLM path (shinka.llm.query) against the REAL
transfer-sn task system message and seed program, asks for a SEARCH/REPLACE
diff, and validates the reply with ShinkaEvolve's own patch applier.

What we need to know before committing a model to an ensemble arm:
  1. does the call succeed at all through OpenRouter,
  2. does it emit a diff ShinkaEvolve can actually apply,
  3. what it costs and how long it takes per proposal.

Usage:  python probe_models.py <task_dir> <config_with_task_sys_msg.json>
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from shinka.llm import LLMClient
from shinka.prompts.prompts_diff import DIFF_SYS_FORMAT
from shinka.edit import apply_diff_patch

CANDIDATES = [
    # (model_id, provider pipeline, note)
    ("anthropic/claude-haiku-4.5", "Anthropic", "tier anchor; has solo baseline on this task"),
    ("google/gemini-3.6-flash", "Google", "newest Flash tier"),
    ("google/gemini-3.5-flash-lite", "Google", "cheaper Flash-lite alt"),
    ("openai/gpt-5.6-luna", "OpenAI", "small tier of the family whose sol arm solved it at gen33"),
    ("openai/gpt-5.4-mini", "OpenAI", "price-matched-to-Haiku alt"),
    ("x-ai/grok-4.3", "xAI", "4th-pipeline alt"),
    ("deepseek/deepseek-v4-flash", "DeepSeek", "4th-pipeline alt"),
]


def build_msg(seed_code: str) -> str:
    return (
        "Here is the current program:\n\n"
        f"```python\n{seed_code}\n```\n\n"
        "Propose ONE concrete improvement to the ANSATZ_SPEC inside the "
        "EVOLVE-BLOCK. Respond with the exact SEARCH/REPLACE diff format."
    )


def main() -> int:
    task_dir = Path(sys.argv[1]).resolve()
    cfg = json.loads(Path(sys.argv[2]).read_text())
    sys_msg = cfg["evo"]["task_sys_msg"] + "\n\n" + DIFF_SYS_FORMAT
    seed = (task_dir / "initial_program.py").read_text(encoding="utf-8")
    msg = build_msg(seed)

    print(f"seed chars={len(seed)}  sys chars={len(sys_msg)}\n")
    hdr = f"{'model':<34}{'pipeline':<11}{'ok':<5}{'applies':<9}{'$cost':<10}{'sec':<7}{'in/out tok':<16}note"
    print(hdr)
    print("-" * len(hdr))

    results = {}
    for model, pipeline, note in CANDIDATES:
        t0 = time.time()
        try:
            client = LLMClient(
                model_names=[f"openrouter/{model}"],
                temperatures=[1.0],
                max_tokens=[16384],
                verbose=False,
            )
            r = client.query(msg=msg, system_msg=sys_msg, msg_history=[])
            if r is None:
                raise RuntimeError("query returned None after retries")
        except Exception as e:
            dt = time.time() - t0
            print(f"{model:<34}{pipeline:<11}{'ERR':<5}{'-':<9}{'-':<10}{dt:<7.0f}{'-':<16}{type(e).__name__}: {str(e)[:60]}")
            results[model] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
            continue
        dt = time.time() - t0

        text = r.content if isinstance(r.content, str) else str(r.content)
        try:
            patched, n_applied, _out, err, _ptxt, _pp = apply_diff_patch(
                patch_str=text, original_str=seed, patch_dir=None, verbose=False
            )
            applied = bool(n_applied) and patched is not None and patched != seed
            applies = f"YES({n_applied})" if applied else (f"NO:{str(err)[:14]}" if err else "NO")
        except Exception as e:
            applies = f"ERR:{type(e).__name__}"
            applied = False
            err = str(e)

        tok = f"{r.input_tokens}/{r.output_tokens}"
        print(f"{model:<34}{pipeline:<11}{'OK':<5}{applies:<9}{r.cost:<10.5f}{dt:<7.0f}{tok:<16}{note}")
        results[model] = {
            "ok": True,
            "applies": applied,
            "cost": r.cost,
            "sec": dt,
            "in_tokens": r.input_tokens,
            "out_tokens": r.output_tokens,
            "reply_head": text[:400],
        }

    out = Path("probe_results.json")
    out.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
