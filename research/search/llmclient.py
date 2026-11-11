"""Stdlib-urllib chat-completions client for the YCRC-hosted model, plus a
deterministic offline mock mode. Interfaces frozen in research/core/INTERFACES.md.

Real mode: POSTs to ${OPENAI_BASE_URL}/chat/completions with ${OPENAI_API_KEY},
models ``ycrc-local`` / ``ycrc-local-think``, ``reasoning_effort`` in
{``none``, ``medium``}. Retries with exponential backoff on timeouts, connection
errors and 429/5xx. Every call is recorded (id, model, prompt tokens, completion
tokens, latency, attempts) so the harness can copy the log into the run JSON.

Mock mode (``mock=True``): no network. A seeded ``numpy.random.Generator`` is
handed to a caller-supplied callback that returns a candidate dict; the client
serializes it as the assistant message, so arm loops run fully offline and
deterministically.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request

import numpy as np

ALLOWED_MODELS = ("ycrc-local", "ycrc-local-think")
ALLOWED_EFFORTS = ("none", "medium")
DEFAULT_MODEL = "ycrc-local"
DEFAULT_EFFORT = "none"
DEFAULT_TIMEOUT = 180.0
DEFAULT_MAX_RETRIES = 8
DEFAULT_BASE_DELAY = 1.0
MAX_DELAY = 60.0


class LLMError(RuntimeError):
    """Raised when a chat call fails after retries or is misconfigured."""


def _estimate_tokens(text):
    return max(1, len(str(text)) // 4)


def default_mock_candidate(rng):
    """Fallback mock generator: schema-shaped random candidate JSON (no task)."""
    n = 6
    k = int(rng.integers(2, 7))
    block = []
    for i in range(k):
        if rng.random() < 0.5:
            block.append({"gate": "RY", "wire": int(rng.integers(0, n)), "param": "t0"})
        else:
            a, b = rng.choice(n, size=2, replace=False)
            block.append({"gate": "CZ", "wires": [int(a), int(b)]})
    return {"block": block, "param_names": ["t0"], "hypothesis": None,
            "notes": "mock proposal %d gates" % k}


def chat_completion(messages, model=DEFAULT_MODEL, reasoning_effort=DEFAULT_EFFORT,
                    timeout=DEFAULT_TIMEOUT, max_retries=DEFAULT_MAX_RETRIES,
                    base_delay=DEFAULT_BASE_DELAY, base_url=None, api_key=None,
                    temperature=None):
    """One logical chat completion with exponential-backoff retries.

    Returns dict(content, prompt_tokens, completion_tokens, total_tokens,
    latency, attempts, model). Raises LLMError on terminal failure.
    """
    if model not in ALLOWED_MODELS:
        raise LLMError('model must be one of %s, got %r' % (ALLOWED_MODELS, model))
    if reasoning_effort is not None and reasoning_effort not in ALLOWED_EFFORTS:
        raise LLMError('reasoning_effort must be one of %s' % (ALLOWED_EFFORTS,))
    base = (base_url or os.environ.get("OPENAI_BASE_URL") or "").rstrip("/")
    key = api_key or os.environ.get("OPENAI_API_KEY") or ""
    if not base or not key:
        raise LLMError("OPENAI_BASE_URL and OPENAI_API_KEY must be set "
                       "(module load ycrc-llm) or passed explicitly")
    body = {"model": model, "messages": list(messages)}
    if reasoning_effort is not None:
        body["reasoning_effort"] = reasoning_effort
    if temperature is not None:
        body["temperature"] = temperature
    payload = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + key}
    last_err = None
    started = time.time()
    for attempt in range(max_retries):
        req = urllib.request.Request(base + "/chat/completions", data=payload,
                                     headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            retryable = exc.code == 429 or 500 <= exc.code < 600
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")[:400]
            except Exception:
                pass
            last_err = "HTTP %s: %s" % (exc.code, detail)
            if not retryable:
                raise LLMError("non-retryable %s" % last_err) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = "transport error: %r" % (exc,)
        if attempt < max_retries - 1:
            time.sleep(min(MAX_DELAY, base_delay * (2 ** attempt)))
    else:
        raise LLMError("chat completion failed after %d attempts: %s"
                       % (max_retries, last_err))
    latency = time.time() - started
    try:
        content = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError("malformed completion payload: %r" % (data,)) from exc
    usage = data.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens",
                                  sum(_estimate_tokens(m.get("content", ""))
                                      for m in messages)))
    completion_tokens = int(usage.get("completion_tokens",
                                      _estimate_tokens(content)))
    return {"content": content, "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": int(usage.get("total_tokens",
                                          prompt_tokens + completion_tokens)),
            "latency": latency, "attempts": attempt + 1, "model": model,
            "reasoning_effort": reasoning_effort}


class LLMClient:
    """Stateful wrapper: validates configuration, keeps a per-call log."""

    def __init__(self, model=DEFAULT_MODEL, reasoning_effort=DEFAULT_EFFORT,
                 mock=False, seed=0, timeout=DEFAULT_TIMEOUT,
                 max_retries=DEFAULT_MAX_RETRIES, mock_candidate_fn=None):
        if not mock:
            if model not in ALLOWED_MODELS:
                raise LLMError('model must be one of %s' % (ALLOWED_MODELS,))
            if reasoning_effort not in ALLOWED_EFFORTS:
                raise LLMError('reasoning_effort must be one of %s'
                               % (ALLOWED_EFFORTS,))
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.mock = bool(mock)
        self.timeout = timeout
        self.max_retries = max_retries
        self.mock_candidate_fn = mock_candidate_fn or default_mock_candidate
        self._rng = np.random.default_rng(seed) if self.mock else None
        self.calls = []

    def chat(self, messages):
        if self.mock:
            started = time.time()
            content = json.dumps(self.mock_candidate_fn(self._rng))
            result = {"content": content,
                      "prompt_tokens": sum(_estimate_tokens(m.get("content", ""))
                                           for m in messages),
                      "completion_tokens": _estimate_tokens(content),
                      "total_tokens": 0, "latency": time.time() - started,
                      "attempts": 1, "model": "mock",
                      "reasoning_effort": self.reasoning_effort}
            result["total_tokens"] = result["prompt_tokens"] + result["completion_tokens"]
        else:
            result = chat_completion(messages, model=self.model,
                                     reasoning_effort=self.reasoning_effort,
                                     timeout=self.timeout,
                                     max_retries=self.max_retries)
        record = {"id": len(self.calls), "model": result["model"],
                  "reasoning_effort": result.get("reasoning_effort"),
                  "prompt_tokens": result["prompt_tokens"],
                  "completion_tokens": result["completion_tokens"],
                  "total_tokens": result["total_tokens"],
                  "latency": result["latency"], "attempts": result["attempts"],
                  "mock": self.mock}
        self.calls.append(record)
        return result

    @property
    def tokens_total(self):
        return {"prompt_tokens": sum(c["prompt_tokens"] for c in self.calls),
                "completion_tokens": sum(c["completion_tokens"] for c in self.calls),
                "total_tokens": sum(c["total_tokens"] for c in self.calls),
                "calls": len(self.calls)}
