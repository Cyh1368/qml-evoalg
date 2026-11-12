#!/usr/bin/env python
"""Capability probe for Azure-routed ensemble candidates.

Same harness as probe_models.py, but through provider=azure_openai, which is a
DIFFERENT code path: it uses the Responses API against {AZURE_API_ENDPOINT}/
openai/v1/ rather than OpenRouter. A model answering "OK" to a curl is not
evidence it can emit an applicable SEARCH/REPLACE diff on a 17KB seed, so every
candidate is checked on the real task before it is allowed into an arm.

Needs AZURE_OPENAI_API_KEY, AZURE_API_ENDPOINT, AZURE_API_VERSION in env.

Usage:  python probe_azure_models.py <task_dir> <config_with_task_sys_msg.json>
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from shinka.llm import LLMClient
from shinka.prompts.prompts_diff import DIFF_SYS_FORMAT
from shinka.edit import apply_diff_patch

# (azure deployment, pipeline, intended tier)
CANDIDATES = [
    # --- small / "haiku-level" tier ---
    ("gpt-5-mini", "OpenAI", "small"),
    ("grok-code-fast-1", "xAI", "small"),
    ("Phi-4", "Microsoft", "small"),
    ("gpt-oss-120b", "OpenAI-open", "small"),
    ("Mistral-Large-3", "Mistral", "small/mid"),
    # --- frontier tier ---
    ("gpt-5.6-sol", "OpenAI", "frontier"),
    # grok-4 dropped: this resource has effectively no quota for it -- every
    # request returned 429 "exceeded rate limit" through all 20 retries.
    ("DeepSeek-V4-Pro", "DeepSeek", "frontier"),
    ("Kimi-K2.6", "Moonshot", "frontier"),
    ("gpt-5.4", "OpenAI", "frontier-alt"),
]


def main() -> int:
    task_dir = Path(sys.argv[1]).resolve()
    cfg = json.loads(Path(sys.argv[2]).read_text())
    sys_msg = cfg["evo"]["task_sys_msg"] + "\n\n" + DIFF_SYS_FORMAT
    seed = (task_dir / "initial_program.py").read_text(encoding="utf-8")
    msg = (
        "Here is the current program:\n\n"
        f"```python\n{seed}\n```\n\n"
        "Propose ONE concrete improvement to the ANSATZ_SPEC inside the "
        "EVOLVE-BLOCK. Respond with the exact SEARCH/REPLACE diff format."
    )

    hdr = f"{'azure deployment':<32}{'pipeline':<13}{'tier':<13}{'ok':<5}{'applies':<11}{'sec':<7}{'in/out tok':<14}"
    print(hdr)
    print("-" * len(hdr))

    out = {}
    for dep, pipeline, tier in CANDIDATES:
        t0 = time.time()
        try:
            client = LLMClient(
                model_names=[f"azure-{dep}"],
                temperatures=[1.0],
                max_tokens=[16384],
                verbose=False,
            )
            r = client.query(msg=msg, system_msg=sys_msg, msg_history=[])
            if r is None:
                raise RuntimeError("query returned None after retries")
        except Exception as e:
            dt = time.time() - t0
            print(f"{dep:<32}{pipeline:<13}{tier:<13}{'ERR':<5}{'-':<11}{dt:<7.0f}{'-':<14}{type(e).__name__}: {str(e)[:55]}")
            out[dep] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
            continue
        dt = time.time() - t0

        text = r.content if isinstance(r.content, str) else str(r.content)
        try:
            patched, n_applied, _o, err, _p, _pp = apply_diff_patch(
                patch_str=text, original_str=seed, patch_dir=None, verbose=False
            )
            ok = bool(n_applied) and patched is not None and patched != seed
            applies = f"YES({n_applied})" if ok else (f"NO:{str(err)[:6]}" if err else "NO")
        except Exception as e:
            applies = f"ERR:{type(e).__name__}"
            ok = False

        print(f"{dep:<32}{pipeline:<13}{tier:<13}{'OK':<5}{applies:<11}{dt:<7.0f}{f'{r.input_tokens}/{r.output_tokens}':<14}")
        out[dep] = {
            "ok": True, "applies": ok, "sec": dt, "pipeline": pipeline, "tier": tier,
            "in_tokens": r.input_tokens, "out_tokens": r.output_tokens,
            "cost_reported": r.cost, "reply_head": text[:300],
        }

    Path("probe_azure_results.json").write_text(json.dumps(out, indent=2))
    print("\nNOTE: cost_reported is expected to be 0.0 until pricing.csv rows exist.")
    print(json.dumps({k: v.get("cost_reported") for k, v in out.items() if v.get("ok")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
