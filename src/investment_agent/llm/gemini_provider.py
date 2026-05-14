from __future__ import annotations

import json
import os
import uuid
from typing import Literal

from .base import LLMMessage, LLMProvider, LLMResponse, ToolCall, ToolSpec, Usage

# Gemini 2.0 Flash reference pricing (very cheap; generous free tier).
# Flash is the recommended free-tier model. Pro is metered and stricter.
DEFAULT_INPUT_PRICE = 0.10 / 1_000_000
DEFAULT_OUTPUT_PRICE = 0.40 / 1_000_000


def _clean_schema(schema: dict | None) -> dict:
    """Gemini's function-declaration schema is OpenAPI-3-ish but rejects some
    JSON Schema constructs (e.g. `additionalProperties`, `$ref`, `anyOf`).
    Strip the ones that commonly cause 400s."""
    if not isinstance(schema, dict):
        return {"type": "object"}
    drop = {"additionalProperties", "$ref", "$defs", "definitions"}
    out: dict = {}
    for k, v in schema.items():
        if k in drop:
            continue
        if isinstance(v, dict):
            out[k] = _clean_schema(v)
        elif isinstance(v, list):
            out[k] = [_clean_schema(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        try:
            import google.generativeai as genai
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "google-generativeai not installed. `pip install google-generativeai`."
            ) from e

        # Default to Flash — generous free tier on Google AI Studio.
        self.model = model or "gemini-2.0-flash"
        key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("GOOGLE_API_KEY not set.")
        genai.configure(api_key=key)
        self._genai = genai

    def _build_history(self, messages: list[LLMMessage]) -> list[dict]:
        """Convert our messages into Gemini's history shape.

        Gemini expects alternating user/model turns. Tool results are sent as
        function_response parts. Adjacent user-role messages are merged so we
        don't violate the alternation rule.
        """
        history: list[dict] = []
        for m in messages:
            if m.role == "system":
                continue
            if m.role == "tool":
                # function_response part
                try:
                    payload = json.loads(m.content)
                except (json.JSONDecodeError, TypeError):
                    payload = {"result": m.content}
                part = {
                    "function_response": {
                        "name": m.name or "tool",
                        "response": payload if isinstance(payload, dict) else {"result": payload},
                    }
                }
                history.append({"role": "user", "parts": [part]})
                continue

            role = "user" if m.role == "user" else "model"
            # Merge if previous turn has same role (Gemini dislikes consecutive same-role turns)
            if history and history[-1]["role"] == role:
                history[-1]["parts"].append(m.content)
            else:
                history.append({"role": role, "parts": [m.content]})
        return history

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
                            "parameters": _clean_schema(t.json_schema),
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

        history = self._build_history(messages)
        if not history:
            resp = model.generate_content("")
        else:
            prior, last = history[:-1], history[-1]
            chat = model.start_chat(history=prior) if prior else model.start_chat()
            resp = chat.send_message(last["parts"])

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for candidate in getattr(resp, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                fc = getattr(part, "function_call", None)
                if fc and getattr(fc, "name", None):
                    args = dict(fc.args) if getattr(fc, "args", None) else {}
                    tool_calls.append(
                        ToolCall(
                            id=f"call_{uuid.uuid4().hex[:8]}",
                            name=fc.name,
                            arguments=args,
                        )
                    )
                else:
                    text = getattr(part, "text", None)
                    if text:
                        text_parts.append(text)

        usage_meta = getattr(resp, "usage_metadata", None)
        input_tokens = getattr(usage_meta, "prompt_token_count", 0) if usage_meta else 0
        output_tokens = getattr(usage_meta, "candidates_token_count", 0) if usage_meta else 0
        usage = Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=(input_tokens * DEFAULT_INPUT_PRICE + output_tokens * DEFAULT_OUTPUT_PRICE),
        )

        return LLMResponse(
            content="".join(text_parts),
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=None,
        )
