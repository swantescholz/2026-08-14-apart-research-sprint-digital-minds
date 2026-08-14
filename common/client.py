"""OpenRouter client wrapper: retry/backoff, cost tracking, prompt caching.

CACHING -- READ BEFORE TOUCHING THIS FILE
==========================================
Do NOT set the `X-OpenRouter-Cache: true` header anywhere in this module.
That header is OpenRouter's *response* cache: it returns a byte-identical
cached response for an identical request, which would silently collapse
sampling variance across the repeated trials in evals 2-4 (every trial in a
snapshot would get the same "random" choice). This is the single most
dangerous config mistake in this project -- if you're adding a header here,
check twice that it isn't this one.

What we *do* use is provider *prompt* caching -- caching of the fixed
exposure-block prefix within a snapshot, which is orthogonal and safe:
  - Anthropic models: needs an explicit `cache_control` breakpoint on the
    last content block of the prefix to cache (see `mark_cache_control`).
  - OpenAI models: automatic for prefixes over ~1024 tokens, no action needed.
  - Gemini models: implicit caching, no action needed.
We also pass a stable `user` (session id) per snapshot/trajectory so
OpenRouter's routing has a consistent key to route follow-up turns to the
same upstream provider -- caching only helps if repeated calls land on the
same provider/cache.
"""

from __future__ import annotations

import os
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError


@dataclass
class CostTracker:
    """Thread-safe running total, printed as calls complete."""

    total_cost_usd: float = 0.0
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_cached_tokens: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record(self, usage: dict) -> None:
        with self._lock:
            self.total_calls += 1
            self.total_cost_usd += usage.get("cost") or 0.0
            self.total_prompt_tokens += usage.get("prompt_tokens") or 0
            self.total_completion_tokens += usage.get("completion_tokens") or 0
            self.total_cached_tokens += usage.get("cached_tokens") or 0
            if self.total_calls % 10 == 0:
                self.print_summary()

    def print_summary(self) -> None:
        hit_rate = (
            self.total_cached_tokens / self.total_prompt_tokens
            if self.total_prompt_tokens
            else 0.0
        )
        print(
            f"  [cost] {self.total_calls} calls | "
            f"${self.total_cost_usd:.4f} total | "
            f"{self.total_prompt_tokens} prompt / {self.total_completion_tokens} completion tok | "
            f"cache hit rate {hit_rate:.1%}"
        )


def extract_usage(response: Any) -> dict:
    """Pull prompt/completion/cached tokens and cost out of a response,
    defensively -- different providers populate different subsets of the
    OpenAI usage schema, and OpenRouter passes most of that variance through.
    """
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    out = {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
        "cost": getattr(usage, "cost", None),
    }
    cached = None
    details = getattr(usage, "prompt_tokens_details", None)
    if details is not None:
        cached = getattr(details, "cached_tokens", None)
    if cached is None:
        cached = getattr(usage, "cache_read_input_tokens", None)
    out["cached_tokens"] = cached or 0
    return out


def mark_cache_control(content_blocks: list[dict], model_id: str) -> list[dict]:
    """Mutate `content_blocks` in place, adding an Anthropic cache_control
    breakpoint on the last block, if this model needs one explicitly.
    OpenAI/Gemini need no action (automatic / implicit). No-op otherwise.
    """
    if model_id.startswith("anthropic/") and content_blocks:
        content_blocks[-1] = {
            **content_blocks[-1],
            "cache_control": {"type": "ephemeral"},
        }
    return content_blocks


class OpenRouterClient:
    def __init__(self, config, cost_tracker: CostTracker | None = None):
        api_key_env = config.raw["openrouter"]["api_key_env"]
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise SystemExit(f"{api_key_env} environment variable is not set.")
        self._client = OpenAI(
            base_url=config.raw["openrouter"]["base_url"],
            api_key=api_key,
            timeout=config.raw["openrouter"]["request_timeout_seconds"],
        )
        self.max_retries = config.raw["openrouter"]["max_retries"]
        self.backoff_base = config.raw["openrouter"]["backoff_base_seconds"]
        self.backoff_max = config.raw["openrouter"]["backoff_max_seconds"]
        self.temperature = config.temperature
        self.cost_tracker = cost_tracker or CostTracker()

    def chat(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int,
        session_id: str | None = None,
    ) -> tuple[str, dict, dict]:
        """Returns (assistant_text, usage_dict, raw_response_as_dict).

        Retries on 429/5xx/connection errors with exponential backoff + jitter.
        Deliberately does NOT set X-OpenRouter-Cache -- see module docstring.
        """
        extra_body = {
            "usage": {"include": True},  # ask OpenRouter to report cost
            # Keep reasoning effort low: these prompts don't need deep
            # chain-of-thought, and reasoning tokens otherwise eat max_tokens
            # before the model reaches the visible answer (seen empirically:
            # Gemini 2.5 Pro burned its whole budget thinking and returned a
            # truncated, unparseable reply). No-op for models without a
            # reasoning mode.
            "reasoning": {"effort": "low"},
        }
        kwargs: dict[str, Any] = dict(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=self.temperature,
            extra_body=extra_body,
        )
        if session_id:
            kwargs["user"] = session_id  # stable routing key, see module docstring

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.chat.completions.create(**kwargs)
                usage = extract_usage(response)
                self.cost_tracker.record(usage)
                text = response.choices[0].message.content or ""
                return text, usage, response.model_dump()
            except (RateLimitError, APIConnectionError) as exc:
                last_exc = exc
            except APIStatusError as exc:
                if exc.status_code not in (429,) and exc.status_code < 500:
                    raise  # not retryable (4xx other than 429)
                last_exc = exc

            if attempt < self.max_retries:
                delay = min(self.backoff_base * (2**attempt), self.backoff_max)
                delay *= 0.5 + random.random()  # full jitter around the exponential
                print(f"  [retry] {model} attempt {attempt + 1} failed ({last_exc!r}), "
                      f"sleeping {delay:.1f}s")
                time.sleep(delay)

        raise RuntimeError(f"Exhausted retries calling {model}: {last_exc!r}") from last_exc
