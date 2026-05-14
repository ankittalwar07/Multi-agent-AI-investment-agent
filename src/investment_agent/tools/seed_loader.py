from __future__ import annotations

from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import ClassVar

import yaml
from pydantic import BaseModel, Field, field_validator

from .base import Citation, Tool, ToolResult


class SeedComponent(BaseModel):
    name: str
    category: str
    description: str = ""
    incumbents: list[str] = Field(default_factory=list)
    notes: str = ""


class SeedFile(BaseModel):
    version: int
    updated: str | None = None
    description: str = ""
    components: list[SeedComponent]

    @field_validator("updated", mode="before")
    @classmethod
    def _coerce_date(cls, v):
        if isinstance(v, (date, datetime)):
            return v.isoformat()
        return v


@lru_cache(maxsize=4)
def load_seed(path: Path) -> SeedFile:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return SeedFile.model_validate(raw)


class SeedLookupArgs(BaseModel):
    component_name: str | None = Field(
        default=None,
        description="If provided, return only the matching component (case-insensitive substring match).",
    )


class SeedLoaderTool(Tool):
    name: ClassVar[str] = "seed_lookup"
    description: ClassVar[str] = (
        "Look up the curated taxonomy of AI-infrastructure components and known "
        "incumbents. Use this BEFORE web search to get a starting prior."
    )
    args_schema: ClassVar[type[BaseModel]] = SeedLookupArgs

    def __init__(self, seed_path: Path):
        self._seed_path = Path(seed_path)

    def all_components(self) -> list[SeedComponent]:
        return load_seed(self._seed_path).components

    def run(self, args: SeedLookupArgs) -> ToolResult:
        seed = load_seed(self._seed_path)
        components = seed.components
        if args.component_name:
            needle = args.component_name.lower()
            components = [c for c in components if needle in c.name.lower()]
        payload = [c.model_dump() for c in components]
        citation = Citation(
            source_url=str(self._seed_path),
            source_name="seed",
            snippet=f"{len(payload)} seed components",
            tool_name=self.name,
        )
        return ToolResult(ok=True, content=payload, citations=[citation])
