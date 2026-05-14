from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from ..llm.base import ToolSpec


class Citation(BaseModel):
    source_url: str | None = None
    source_name: str = "web"
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    snippet: str | None = None
    snippet_hash: str | None = None
    tool_name: str = ""


class ToolResult(BaseModel):
    ok: bool = True
    content: Any = None
    citations: list[Citation] = Field(default_factory=list)
    error: str | None = None

    def as_llm_text(self) -> str:
        import json

        if not self.ok:
            return f"ERROR: {self.error}"
        try:
            return json.dumps(self.content, default=str, indent=2)[:8000]
        except (TypeError, ValueError):
            return str(self.content)[:8000]


class Tool(ABC):
    name: ClassVar[str]
    description: ClassVar[str]
    args_schema: ClassVar[type[BaseModel]]

    @abstractmethod
    def run(self, args: BaseModel) -> ToolResult: ...

    def to_spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            json_schema=self.args_schema.model_json_schema(),
        )
