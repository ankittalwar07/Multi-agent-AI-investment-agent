"""Groq provider — open-source models (Llama, Mixtral, Gemma) via Groq's
OpenAI-compatible API.

Why Groq for this dashboard:
  * Free tier, no credit card. Get a key at https://console.groq.com/keys
  * Open-source models (Llama 3.3 70B, Llama 3.1 8B, Mixtral, Gemma)
  * Independent rate limits from Gemini/OpenAI/Anthropic
  * 200+ tokens/sec inference — a full pipeline run finishes in ~30-60 seconds
  * OpenAI-compatible REST API
  * Native tool / function calling on Llama 3.1+

Free-tier rate limits (per Groq's docs, may change):
  * Llama 3.3 70B Versatile: 30 req/min, ~14,400 req/day
  * Llama 3.1 8B Instant:     30 req/min, ~30,000 req/day
  * Mixtral 8x7B:             30 req/min, ~14,400 req/day
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Literal

from .base import LLMMessage, LLMProvider, LLMResponse, ToolCall, ToolSpec, Usage

# Per-token cost in USD for reporting purposes (Groq's paid-tier published prices
# for Llama 3.3 70B Versatile — free tier is $0 but we report a notional cost
# so users can see token usage).
DEFAULT_INPUT_PRICE = 0.59 / 1_000_000
DEFAULT_OUTPUT_PRICE = 0.79 / 1_000_000


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "openai SDK not installed. `pip install openai`. (Used as the "
                "client for Groq's OpenAI-compatible endpoint.)"
            ) from e

        self.model = model or "llama-3.3-70b-versatile"
        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set. Get a free key at https://console.groq.com/keys")
        self._client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")

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

        resp = self._client.chat.completions.create(**kwargs)
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

        usage = Usage(
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
            cost_usd=(
                resp.usage.prompt_tokens * DEFAULT_INPUT_PRICE
                + resp.usage.completion_tokens * DEFAULT_OUTPUT_PRICE
            ),
        )
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=choice.finish_reason,
            raw={"id": resp.id, "model": resp.model},
        )
