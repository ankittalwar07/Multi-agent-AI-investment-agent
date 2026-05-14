from __future__ import annotations

import json
import os
import uuid
from typing import Literal

from .base import LLMMessage, LLMProvider, LLMResponse, ToolCall, ToolSpec, Usage

DEFAULT_INPUT_PRICE = 2.5 / 1_000_000
DEFAULT_OUTPUT_PRICE = 10.0 / 1_000_000


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("openai SDK not installed. `pip install openai`.") from e

        self.model = model or "gpt-4o"
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set.")
        self._client = OpenAI(api_key=key)

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
                api_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": m.tool_call_id or "",
                        "content": m.content,
                    }
                )
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
        for tc in choice.message.tool_calls or []:
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
            raw={"id": resp.id},
        )
