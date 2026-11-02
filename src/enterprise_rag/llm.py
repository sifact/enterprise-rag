"""Small Groq chat client shared by drafting, judging and (later) answer generation.

Groq's free tier allows 8,000 tokens per minute, so every call goes through one client that
paces requests with a token bucket and retries on 429/5xx. The API key is read from the
environment (or the git-ignored .env) and never stored in anything that gets printed.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

from enterprise_rag.config import PROJECT_ROOT

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_RETRIES = 4  # retries after the first attempt
BACKOFF_START_S = 2.0
DEFAULT_MAX_TOKENS = 2048
REQUEST_TIMEOUT_S = 120

log = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """The call failed after every retry; callers skip the one item, not the whole run."""


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float


class _TokenBucket:
    """Spends estimated tokens per call and sleeps until the per-minute budget refills."""

    def __init__(self, tokens_per_minute: int):
        self.capacity = float(tokens_per_minute)
        self.rate = tokens_per_minute / 60.0
        self.tokens = self.capacity
        self.updated = time.monotonic()

    def take(self, n: float) -> None:
        n = min(n, self.capacity)  # an oversized request still goes through once the bucket is full
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
        self.updated = now
        if self.tokens < n:
            wait = (n - self.tokens) / self.rate
            time.sleep(wait)
            # Book the refill we just waited for instead of re-reading the clock in a loop.
            self.tokens = n
            self.updated = now + wait
        self.tokens -= n


class _Retryable(Exception):
    def __init__(self, reason: str, wait_s: float | None = None):
        super().__init__(reason)
        self.wait_s = wait_s


class GroqClient:
    def __init__(
        self,
        model: str,
        tokens_per_minute: int,
        api_key: str | None = None,
        session: requests.Session | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        extra_body: dict | None = None,
    ):
        if api_key is None and "GROQ_API_KEY" not in os.environ:
            load_dotenv(PROJECT_ROOT / ".env")
        self.model = model
        self.max_tokens = max_tokens
        self.extra_body = dict(extra_body or {})  # model-specific options, e.g. reasoning_format
        self._api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self._api_key:
            raise LLMError("GROQ_API_KEY is not set (environment or .env)")
        self._session = session or requests.Session()
        self._bucket = _TokenBucket(tokens_per_minute)

    def __repr__(self) -> str:
        return f"GroqClient(model={self.model!r})"

    def complete_json(self, system: str, user: str, temperature: float = 0.0,
                      max_tokens: int | None = None) -> tuple[dict, Usage]:
        def parse(content: str) -> dict:
            try:
                data = json.loads(content)
            except json.JSONDecodeError as exc:
                raise _Retryable(f"invalid JSON: {exc}") from exc
            if not isinstance(data, dict):
                raise _Retryable("JSON reply is not an object")
            return data

        return self._chat(system, user, temperature, json_mode=True, parse=parse,
                          max_tokens=max_tokens)

    def complete_text(self, system: str, user: str, temperature: float = 0.0,
                      max_tokens: int | None = None) -> tuple[str, Usage]:
        return self._chat(system, user, temperature, json_mode=False, parse=lambda c: c,
                          max_tokens=max_tokens)

    def _chat(self, system, user, temperature, json_mode, parse, max_tokens=None):
        max_tokens = max_tokens or self.max_tokens
        payload = {
            **self.extra_body,
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        estimate = (len(system) + len(user)) / 4 + max_tokens

        last_error = ""
        for attempt in range(MAX_RETRIES + 1):
            self._bucket.take(estimate)
            try:
                return self._attempt(payload, parse)
            except _Retryable as exc:
                last_error = str(exc)
                if attempt == MAX_RETRIES:
                    break
                wait = exc.wait_s if exc.wait_s is not None else BACKOFF_START_S * 2**attempt
                log.warning("Groq %s (attempt %d), retrying in %.1fs", exc, attempt + 1, wait)
                time.sleep(wait)
        raise LLMError(f"{self.model}: gave up after {MAX_RETRIES + 1} attempts: {last_error}")

    def _attempt(self, payload: dict, parse):
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        start = time.perf_counter()
        try:
            resp = self._session.post(GROQ_URL, headers=headers, json=payload,
                                      timeout=REQUEST_TIMEOUT_S)
        except requests.RequestException as exc:
            raise _Retryable(f"network error: {type(exc).__name__}") from exc
        latency_ms = (time.perf_counter() - start) * 1000

        if resp.status_code == 429 or resp.status_code >= 500:
            retry_after = resp.headers.get("retry-after")
            raise _Retryable(f"HTTP {resp.status_code}",
                             float(retry_after) if retry_after is not None else None)
        if resp.status_code == 400 and "json_validate_failed" in resp.text:
            raise _Retryable("model output failed JSON validation")
        if resp.status_code != 200:
            raise LLMError(f"HTTP {resp.status_code}: {resp.text[:300]}")

        body = resp.json()
        content = body["choices"][0]["message"]["content"] or ""
        usage = body.get("usage", {})
        return parse(content), Usage(
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            latency_ms=latency_ms,
        )
