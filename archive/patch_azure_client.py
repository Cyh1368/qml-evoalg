#!/usr/bin/env python
"""Fix ShinkaEvolve's Azure client so it hits a URL that actually exists.

The bug: `_build_azure_endpoint()` returns "<endpoint>/openai/v1/", which is
then handed to `openai.AzureOpenAI(azure_endpoint=...)`. The SDK appends its own
"/openai/" to whatever it is given, so requests land on

    <endpoint>/openai/v1/openai/responses     -> 404 Resource not found

Measured against this resource from the Bouchet login node:

    <endpoint>/openai/v1/responses                    -> 200
    <endpoint>/openai/responses?api-version=preview   -> 404
    <endpoint>/openai/v1/openai/responses             -> 404

Only the v1 surface serves the Responses API, and it cannot be reached through
AzureOpenAI's endpoint mangling. The fix is to use the plain OpenAI client with
base_url set to the v1 surface directly, which is also what Microsoft documents
for the v1 API. Both `api-key:` and `Authorization: Bearer` were verified to
return 200 on this resource, so the SDK's Bearer header is fine.

The provider string stays "azure_openai", so query routing is unchanged; only
client construction differs. Idempotent, and keeps a .bak-azurefix backup.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import shinka.llm.client as m

SYNC_OLD = """        client = openai.AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_API_VERSION"),
            azure_endpoint=_build_azure_endpoint(),
            timeout=TIMEOUT,  # 20 minutes
        )"""

SYNC_NEW = """        # PATCHED: AzureOpenAI appends "/openai/" to azure_endpoint, producing
        # <ep>/openai/v1/openai/responses (404). Only <ep>/openai/v1/responses
        # exists, so talk to the v1 surface with the plain client.
        client = openai.OpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            base_url=_build_azure_endpoint(),
            timeout=TIMEOUT,  # 20 minutes
        )"""

ASYNC_OLD = """        client = openai.AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_API_VERSION"),
            azure_endpoint=_build_azure_endpoint(),
            timeout=TIMEOUT,
        )"""

ASYNC_NEW = """        # PATCHED: see the sync branch above.
        client = openai.AsyncOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            base_url=_build_azure_endpoint(),
            timeout=TIMEOUT,
        )"""


def main() -> int:
    path = Path(m.__file__)
    src = path.read_text()

    if "PATCHED: AzureOpenAI appends" in src:
        print(f"already patched: {path}")
        return 0

    for name, old in (("sync", SYNC_OLD), ("async", ASYNC_OLD)):
        if src.count(old) != 1:
            print(f"ABORT: {name} block matched {src.count(old)} times, expected 1")
            return 1

    backup = path.with_suffix(path.suffix + ".bak-azurefix")
    if not backup.exists():
        shutil.copy(path, backup)

    src = src.replace(SYNC_OLD, SYNC_NEW).replace(ASYNC_OLD, ASYNC_NEW)
    path.write_text(src)
    print(f"patched {path}\nbackup  {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
