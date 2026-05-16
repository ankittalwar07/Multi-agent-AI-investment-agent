"""Ollama provider — local open-source models via Ollama's OpenAI-compatible API.

Why Ollama for this dashboard:
  * Zero cloud cost, zero rate limits — runs entirely on your machine
  * Privacy — every token stays local
  * One-click install: https://ollama.com/download
  * OpenAI-compatible API at http://localhost:11434/v1
  * Strong open-source models: Qwen 2.5, Llama 3.1/3.3, Mistral Nemo, Gemma 2

Setup (one-time):
  1. Install Ollama from https://ollama.com/download
  2. Pull a model:
        ollama pull qwen2.5:7b           # ~4 GB, best JSON output
        ollama pull llama3.1:8b          # ~5 GB, strong all-around
        ollama pull mistral-nemo:12b     # ~7 GB, larger but slower
  3. Verify:
        ollama run qwen2.5:7b "Hello, return JSON {\"ok\": true}"
  4. Start the dashboard — Ollama API is auto-discovered at localhost:11434

Hardware guidance (approximate):
  * 7B-8B models:  ~6-8 GB RAM/VRAM   (most modern Macs / PCs)
  * 12B-14B:       ~10-12 GB           (Apple Silicon M-series, RTX 3060+)
  * 70B:           ~40 GB+             (RTX 4090, M3 Ultra, datacenter)

Speed expectations (single completion):
  * Apple M-series (M2/M3 Pro+) on 7B:  50-100 tok/sec  (fast)
  * NVIDIA RTX 4060/4070 on 7B:         80-150 tok/sec
  * CPU-only on 7B:                      5-20 tok/sec   (slow but functional)
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Literal

from .base import LLMMessage, LLMProvider, LLMResponse, ToolCall, ToolSpec, Usage


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "openai SDK not installed. `pip install openai`. (Used as the "
                "client for Ollama's OpenAI-compatible endpoint.)"
            ) from e

        # Qwen 2.5 7B = best balance of quality (especially JSON) and size
        self.model = model or "qwen2.5:7b"
        url = (
            base_url
            or os.environ.get("OLLAMA_BASE_URL")
            or "http://localhost:11434/v1"
        )
        # Ollama doesn't require auth but the OpenAI SDK insists on a non-empty key.
        self._client = OpenAI(
            api_key=api_key or os.environ.get("OLLAMA_API_KEY") or "ollama-local",
            base_url=url,
        )
        self._base_url = url

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
            # Ollama supports OpenAI-compatible JSON mode on most models
            kwargs["response_format"] = {"type": "json_object"}

        try:
            resp = self._client.chat.completions.create(**kwargs)
        except Exception as e:
            msg = str(e)
            if "Connection" in msg or "refused" in msg.lower() or "connect" in msg.lower():
                # Detect the "running on Streamlit Cloud but pointing at localhost" trap
                is_localhost = "localhost" in self._base_url or "127.0.0.1" in self._base_url
                hint = (
                    "\n  NOTE: If this is Streamlit Cloud, localhost refers to the "
                    "cloud container, not your laptop. Either:\n"
                    "    (a) run Streamlit locally on the same machine as Ollama, OR\n"
                    "    (b) expose your local Ollama via a tunnel (cloudflared/ngrok)\n"
                    "        and set OLLAMA_BASE_URL to the public tunnel URL."
                    if is_localhost else ""
                )
                raise RuntimeError(
                    f"Could not reach Ollama at {self._base_url}. "
                    "Is Ollama running? Start it with `ollama serve` or open the "
                    f"Ollama app. Verify with `curl {self._base_url.rstrip('/v1')}/api/tags`."
                    f"{hint}"
                ) from e
            if "model" in msg.lower() and ("not found" in msg.lower() or "pull" in msg.lower()):
                raise RuntimeError(
                    f"Ollama model '{self.model}' not found locally. "
                    f"Pull it first: `ollama pull {self.model}`. "
                    "See `ollama list` for what's installed."
                ) from e
            raise

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

        # Local inference is free — report $0 cost but keep the token count
        # for transparency.
        usage = Usage(
            input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            output_tokens=resp.usage.completion_tokens if resp.usage else 0,
            cost_usd=0.0,
        )
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=choice.finish_reason,
            raw={"id": resp.id, "model": resp.model},
        )
