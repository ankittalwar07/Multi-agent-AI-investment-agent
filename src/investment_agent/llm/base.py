from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant", "tool"]


class LLMMessage(BaseModel):
    role: Role
    content: str
    tool_call_id: str | None = None
    name: str | None = None


class ToolSpec(BaseModel):
    name: str
    description: str
    json_schema: dict[str, Any]


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class LLMResponse(BaseModel):
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    raw: dict[str, Any] = Field(default_factory=dict)
    finish_reason: str | None = None


class LLMProvider(ABC):
    """Provider-agnostic chat interface.

    All concrete providers normalize their native tool-call payloads into
    `ToolCall` so agents stay provider-agnostic.
    """

    name: str = "base"
    model: str = ""

    @abstractmethod
    def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        response_format: Literal["text", "json"] = "text",
    ) -> LLMResponse: ...

    def estimate_cost(self, usage: Usage) -> float:
        return usage.cost_usd
