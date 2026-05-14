from __future__ import annotations

import os
import uuid
from typing import Literal

from .base import LLMMessage, LLMProvider, LLMResponse, ToolCall, ToolSpec, Usage

# Token prices in USD per 1M tokens (Claude Sonnet 4.6 reference).
DEFAULT_INPUT_PRICE = 3.0 / 1_000_000
DEFAULT_OUTPUT_PRICE = 15.0 / 1_000_000


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover - import guard
            raise RuntimeError(
                "anthropic SDK not installed. `pip install anthropic`."
            ) from e

        self.model = model or "claude-sonnet-4-6"
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set.")
        self._client = anthropic.Anthropic(api_key=key)

    def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        response_format: Literal["text", "json"] = "text",
    ) -> LLMResponse:
        system_chunks = [m.content for m in messages if m.role == "system"]
        system = "\n\n".join(system_chunks) if system_chunks else None

        api_messages = []
        for m in messages:
            if m.role == "system":
                continue
            if m.role == "tool":
                api_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": m.tool_call_id or "",
                                "content": m.content,
                            }
                        ],
                    }
                )
            else:
                api_messages.append({"role": m.role, "content": m.content})

        api_tools = None
        if tools:
            api_tools = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.json_schema,
                }
                for t in tools
            ]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": api_messages,
        }
        if system:
            kwargs["system"] = system
        if api_tools:
            kwargs["tools"] = api_tools

        resp = self._client.messages.create(**kwargs)

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in resp.content:
            btype = getattr(block, "type", None)
            if btype == "text":
                text_parts.append(block.text)
            elif btype == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id or f"call_{uuid.uuid4().hex[:8]}",
                        name=block.name,
                        arguments=dict(block.input or {}),
                    )
                )

        usage = Usage(
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            cost_usd=(
                resp.usage.input_tokens * DEFAULT_INPUT_PRICE
                + resp.usage.output_tokens * DEFAULT_OUTPUT_PRICE
            ),
        )
        return LLMResponse(
            content="".join(text_parts),
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=getattr(resp, "stop_reason", None),
            raw={"id": resp.id},
        )
