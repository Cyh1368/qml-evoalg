#!/usr/bin/env python3
"""Final pre-launch gate: every model must emit an APPLICABLE diff at the exact
reasoning effort its own arm will run with.

This is the check that matters, and it is arm-specific because effort is tiered:
frontier=xhigh, mid=medium, weak=low. Two earlier probes were not sufficient:

  * the short-prompt effort probe missed that reasoning length scales with the
    task -- gpt-5.4-mini reasoned past the whole 16384 budget on the real 17KB
    seed at xhigh and returned no message at all, three retries running;
  * the no-reasoning diff probe passed every model, which told us nothing about
    behaviour once reasoning is on.

Reads the arm configs so it cannot drift from what actually gets launched.

Usage:  OPENROUTER_API_KEY=... python3 probe_arms_final.py
Exit 0 only if every model in every arm produces an applicable patch.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from shinka.edit import apply_diff_patch
from shinka.llm import LLMClient
from shinka.prompts.prompts_diff import DIFF_SYS_FORMAT

ARMS = ["weak", "mid", "frontier"]

seed = Path("initial_program.py").read_text(encoding="utf-8")
sys_msg = (
    json.loads(Path("shinka_config_ens3_r2.json").read_text())["evo"]["task_sys_msg"]
    + "\n\n"
    + DIFF_SYS_FORMAT
)
msg = (
    "Here is the current program:\n\n"
    f"```python\n{seed}\n```\n\n"
    "Propose ONE concrete improvement to the ANSATZ_SPEC inside the "
    "EVOLVE-BLOCK. Respond with the exact SEARCH/REPLACE diff format."
)

print(f"{'arm':<10}{'effort':<8}{'model':<40}{'applies':<12}{'sec':<6}{'$cost':<9}out_tok")
print("-" * 92)

failures = []
for arm in ARMS:
    cfg = json.loads(Path(f"shinka_config_or_{arm}_r1.json").read_text())["evo"]
    effort = cfg["llm_kwargs"]["reasoning_efforts"][0]
    for model in cfg["llm_models"]:
        t0 = time.time()
        try:
            client = LLMClient(
                model_names=[model],
                temperatures=cfg["llm_kwargs"]["temperatures"],
                max_tokens=[cfg["llm_kwargs"]["max_tokens"]],
                reasoning_efforts=[effort],
                verbose=False,
            )
            r = client.query(msg=msg, system_msg=sys_msg, msg_history=[])
            if r is None:
                raise RuntimeError("query returned None after retries")
        except Exception as exc:
            dt = time.time() - t0
            print(f"{arm:<10}{effort:<8}{model:<40}{'ERROR':<12}{dt:<6.0f}"
                  f"{'-':<9}{type(exc).__name__}: {str(exc)[:40]}")
            failures.append(f"{arm}/{model}: {type(exc).__name__}: {str(exc)[:60]}")
            continue
        dt = time.time() - t0
        text = r.content if isinstance(r.content, str) else str(r.content)
        try:
            patched, n_applied, _o, err, _p, _pp = apply_diff_patch(
                patch_str=text, original_str=seed, patch_dir=None, verbose=False
            )
            ok = bool(n_applied) and patched is not None and patched != seed
        except Exception as exc:
            ok, err = False, str(exc)
        label = f"YES({n_applied})" if ok else f"NO:{str(err)[:8]}"
        if not ok:
            failures.append(f"{arm}/{model}: diff did not apply ({str(err)[:60]})")
        print(f"{arm:<10}{effort:<8}{model:<40}{label:<12}{dt:<6.0f}"
              f"${r.cost:<8.4f}{r.output_tokens}")

print()
if failures:
    print("LAUNCH BLOCKED:")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("ALL ARMS PASS at their own effort level - safe to launch.")
