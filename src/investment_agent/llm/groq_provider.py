"""Groq provider — open-source models via Groq's OpenAI-compatible API.

Default model is `llama-3.1-8b-instant` because it has 5× the daily token
quota of the 70B model on the free tier:

  llama-3.1-8b-instant:    30 RPM, 14,400 RPD, 6,000 TPM, 500,000 TPD
  llama-3.3-70b-versatile: 30 RPM,  1,000 RPD, 12,000 TPM, 100,000 TPD

A full pipeline run uses ~400-500k tokens, so the 8B model is the only
free-tier choice that fits. The 70B is great for one-off questions but
hits TPD quickly when running the full ~25-component pipeline.

When 429 hits we parse the "Please try again in Xs" hint and retry — TPM
errors usually recover within 10s, TPD errors won't recover until UTC
midnight.
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from typing import Literal

from .base import LLMMessage, LLMProvider, LLMResponse, ToolCall, ToolSpec, Usage

# 8B Instant pricing (paid tier — free tier is $0; we report notional cost
# so users can see token usage).
DEFAULT_INPUT_PRICE = 0.05 / 1_000_000
DEFAULT_OUTPUT_PRICE = 0.08 / 1_000_000

# Per-model published prices (used when the user picks something other than the default)
MODEL_PRICES: dict[str, tuple[float, float]] = {
    "llama-3.1-8b-instant": (0.05 / 1_000_000, 0.08 / 1_000_000),
    "llama-3.3-70b-versatile": (0.59 / 1_000_000, 0.79 / 1_000_000),
    "mixtral-8x7b-32768": (0.24 / 1_000_000, 0.24 / 1_000_000),
    "gemma2-9b-it": (0.20 / 1_000_000, 0.20 / 1_000_000),
}

_RETRY_AFTER_RE = re.compile(r"try again in ([\d.]+)s")


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, model: str | None = None, api_key: str | None = None,
                 max_retries: int = 3):
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "openai SDK not installed. `pip install openai`. (Used as the "
                "client for Groq's OpenAI-compatible endpoint.)"
            ) from e

        self.model = model or "llama-3.1-8b-instant"
        self.max_retries = max_retries
        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set. Get a free key at https://console.groq.com/keys")
        self._client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")

    def _is_tpd_error(self, exc: Exception) -> bool:
        """A TPD (tokens per day) 429 won't recover until UTC midnight — abort fast."""
        return "tokens per day" in str(exc).lower() or "(tpd)" in str(exc).lower()

    def _wait_seconds(self, exc: Exception) -> float:
        """Parse 'Please try again in Xs' from Groq's 429 message."""
        m = _RETRY_AFTER_RE.search(str(exc))
        if m:
            try:
                return float(m.group(1)) + 0.5  # small cushion
            except ValueError:
                pass
        return 5.0

    def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        response_format: Literal["text", "json"] = "text",
    ) -> LLMResponse:
        api_messages: list[dict] = []
        for m in messages:
            if m.role == "tool":
                api_messages.append({
                    "role": "tool",
                    "tool_call_id": m.tool_call_id or "",
                    "content": m.content,
                })
            else:
                api_messages.append({"role": m.role, "content": m.content})

        api_tools = None
        if tools:
            api_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.json_schema,
                    },
                }
                for t in tools
            ]

        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if api_tools:
            kwargs["tools"] = api_tools
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        # Retry on 429 (TPM) — abort on TPD (won't recover today).
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self._client.chat.completions.create(**kwargs)
                break
            except Exception as e:
                last_exc = e
                if "429" not in str(e) and "rate_limit" not in str(e).lower():
                    raise
                if self._is_tpd_error(e):
                    # Daily quota — useless to retry today. Fail fast with a
                    # clean message so the pipeline can mark this component
                    # as rate-limited and move on.
                    raise RuntimeError(
                        "Groq daily token quota exhausted. "
                        "Switch to llama-3.1-8b-instant (5x quota), Gemini, "
                        "or wait until UTC midnight for reset."
                    ) from e
                if attempt >= self.max_retries:
                    raise
                wait = self._wait_seconds(e)
                time.sleep(min(wait, 30.0))
        else:
            raise last_exc or RuntimeError("Groq retries exhausted")

        choice = resp.choices[0]
        content = choice.message.content or ""
        tool_calls: list[ToolCall] = []
        for tc in (choice.message.tool_calls or []):
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(
                ToolCall(
                    id=tc.id or f"call_{uuid.uuid4().hex[:8]}",
                    name=tc.function.name,
                    arguments=args,
                )
            )

        in_price, out_price = MODEL_PRICES.get(
            self.model, (DEFAULT_INPUT_PRICE, DEFAULT_OUTPUT_PRICE)
        )
        usage = Usage(
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
            cost_usd=(
                resp.usage.prompt_tokens * in_price
                + resp.usage.completion_tokens * out_price
            ),
        )
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=choice.finish_reason,
            raw={"id": resp.id, "model": resp.model},
        )

