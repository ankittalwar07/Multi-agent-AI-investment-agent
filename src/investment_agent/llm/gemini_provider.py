from __future__ import annotations

import os
import uuid
from typing import Literal

from .base import LLMMessage, LLMProvider, LLMResponse, ToolCall, ToolSpec, Usage

# Gemini 1.5 Pro reference pricing.
DEFAULT_INPUT_PRICE = 1.25 / 1_000_000
DEFAULT_OUTPUT_PRICE = 5.0 / 1_000_000


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        try:
            import google.generativeai as genai
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "google-generativeai not installed. `pip install google-generativeai`."
            ) from e

        self.model = model or "gemini-1.5-pro"
        key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("GOOGLE_API_KEY not set.")
        genai.configure(api_key=key)
        self._genai = genai

    def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        response_format: Literal["text", "json"] = "text",
    ) -> LLMResponse:
        system_chunks = [m.content for m in messages if m.role == "system"]
        system_instruction = "\n\n".join(system_chunks) if system_chunks else None

        history = []
        latest_user: str | None = None
        for m in messages:
            if m.role == "system":
                continue
            role = "user" if m.role in ("user", "tool") else "model"
            history.append({"role": role, "parts": [m.content]})
            if m.role == "user":
                latest_user = m.content

        gen_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if response_format == "json":
            gen_config["response_mime_type"] = "application/json"

        gemini_tools = None
        if tools:
            gemini_tools = [
                {
                    "function_declarations": [
                        {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.json_schema,
                        }
                        for t in tools
                    ]
                }
            ]

        model = self._genai.GenerativeModel(
            model_name=self.model,
            system_instruction=system_instruction,
            tools=gemini_tools,
            generation_config=gen_config,
        )

        if history:
            chat = model.start_chat(history=history[:-1])
            resp = chat.send_message(history[-1]["parts"][0])
        else:
            resp = model.generate_content(latest_user or "")

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for candidate in getattr(resp, "candidates", []) or []:
            for part in getattr(candidate.content, "parts", []) or []:
                fc = getattr(part, "function_call", None)
                if fc:
                    tool_calls.append(
                        ToolCall(
                            id=f"call_{uuid.uuid4().hex[:8]}",
                            name=fc.name,
                            arguments=dict(fc.args or {}),
                        )
                    )
                elif getattr(part, "text", None):
                    text_parts.append(part.text)

        usage_meta = getattr(resp, "usage_metadata", None)
        input_tokens = getattr(usage_meta, "prompt_token_count", 0) if usage_meta else 0
        output_tokens = getattr(usage_meta, "candidates_token_count", 0) if usage_meta else 0
        usage = Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=(
                input_tokens * DEFAULT_INPUT_PRICE + output_tokens * DEFAULT_OUTPUT_PRICE
            ),
        )

        return LLMResponse(
            content="".join(text_parts),
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=None,
        )
