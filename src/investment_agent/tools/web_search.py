from __future__ import annotations

import time
from typing import ClassVar

from pydantic import BaseModel, Field

from .base import Citation, Tool, ToolResult


class WebSearchArgs(BaseModel):
    query: str = Field(..., description="Search query string.")
    max_results: int = Field(default=8, ge=1, le=20)


class WebSearchTool(Tool):
    name: ClassVar[str] = "web_search"
    description: ClassVar[str] = (
        "Search the web for recent news, analyst notes, filings, and product pages. "
        "Returns a list of {title, url, snippet}. Use this to discover sources, then "
        "follow up with web_fetch for full text."
    )
    args_schema: ClassVar[type[BaseModel]] = WebSearchArgs

    _last_call: float = 0.0
    _min_interval_s: float = 1.0  # 1 req/sec token bucket

    def _throttle(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self._min_interval_s:
            time.sleep(self._min_interval_s - elapsed)
        self._last_call = time.monotonic()

    def run(self, args: WebSearchArgs) -> ToolResult:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return ToolResult(
                ok=False,
                error="duckduckgo-search not installed. `pip install duckduckgo-search`.",
            )

        self._throttle()
        try:
            with DDGS() as ddgs:
                hits = list(ddgs.text(args.query, max_results=args.max_results))
        except Exception as e:  # network/rate-limit failures bubble up as ToolResult
            return ToolResult(ok=False, error=f"web_search failed: {e}")

        results = [
            {"title": h.get("title"), "url": h.get("href"), "snippet": h.get("body")}
            for h in hits
        ]
        citations = [
            Citation(
                source_url=h.get("href"),
                source_name="web",
                snippet=h.get("body"),
                tool_name=self.name,
            )
            for h in hits
            if h.get("href")
        ]
        return ToolResult(ok=True, content=results, citations=citations)
