from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from ..llm.base import LLMMessage, LLMProvider
from ..tools.base import Tool, ToolResult
from .prompts import COMPONENT_RESEARCHER


@dataclass
class EvidenceRecord:
    claim: str
    source_url: str | None
    source_name: str
    tool_name: str
    snippet: str | None = None


@dataclass
class CompanyFinding:
    name: str
    is_public: bool | None = None
    ticker: str | None = None
    hq_country: str | None = None
    market_share_pct: float | None = None
    market_share_bucket: str | None = None
    single_source: bool = False
    moat_types: list[str] = field(default_factory=list)
    switching_costs: str | None = None
    customer_concentration: str | None = None
    demand_signal: str | None = None
    valuation_usd: float | None = None
    notes: str | None = None
    evidence: list[EvidenceRecord] = field(default_factory=list)


@dataclass
class ResearchResult:
    component_name: str
    companies: list[CompanyFinding]
    cost_usd: float
    search_count: int
    fetch_count: int
    error: str | None = None


class ComponentResearcher:
    """ReAct-style loop bounded by per-researcher tool-call caps."""

    def __init__(
        self,
        llm: LLMProvider,
        tools: dict[str, Tool],
        *,
        max_searches: int = 8,
        max_fetches: int = 15,
        max_steps: int = 12,
    ):
        self.llm = llm
        self.tools = tools
        self.max_searches = max_searches
        self.max_fetches = max_fetches
        self.max_steps = max_steps

    def run(self, component_name: str, component_category: str, component_description: str) -> ResearchResult:
        system = (
            COMPONENT_RESEARCHER
            .replace("__COMPONENT_NAME__", component_name)
            .replace("__COMPONENT_CATEGORY__", component_category)
            .replace("__COMPONENT_DESCRIPTION__", component_description)
            .replace("__MAX_SEARCHES__", str(self.max_searches))
            .replace("__MAX_FETCHES__", str(self.max_fetches))
        )
        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=system),
            LLMMessage(
                role="user",
                content=(
                    f"Research the component '{component_name}'. Begin by calling "
                    f"seed_lookup with this component name, then proceed."
                ),
            ),
        ]

        tool_specs = [t.to_spec() for t in self.tools.values()]
        total_cost = 0.0
        search_count = 0
        fetch_count = 0

        for _step in range(self.max_steps):
            resp = self.llm.complete(messages=messages, tools=tool_specs, max_tokens=2048)
            total_cost += resp.usage.cost_usd

            if not resp.tool_calls:
                # Final answer expected here.
                companies = self._parse_final(resp.content, component_name)
                return ResearchResult(
                    component_name=component_name,
                    companies=companies,
                    cost_usd=total_cost,
                    search_count=search_count,
                    fetch_count=fetch_count,
                )

            messages.append(LLMMessage(role="assistant", content=resp.content or ""))
            for call in resp.tool_calls:
                tool = self.tools.get(call.name)
                if not tool:
                    tool_result = ToolResult(ok=False, error=f"unknown tool: {call.name}")
                else:
                    if call.name == "web_search":
                        if search_count >= self.max_searches:
                            tool_result = ToolResult(ok=False, error="web_search budget exhausted")
                        else:
                            search_count += 1
                            tool_result = self._safe_run(tool, call.arguments)
                    elif call.name == "web_fetch":
                        if fetch_count >= self.max_fetches:
                            tool_result = ToolResult(ok=False, error="web_fetch budget exhausted")
                        else:
                            fetch_count += 1
                            tool_result = self._safe_run(tool, call.arguments)
                    else:
                        tool_result = self._safe_run(tool, call.arguments)

                messages.append(
                    LLMMessage(
                        role="tool",
                        content=tool_result.as_llm_text(),
                        tool_call_id=call.id,
                        name=call.name,
                    )
                )

        return ResearchResult(
            component_name=component_name,
            companies=[],
            cost_usd=total_cost,
            search_count=search_count,
            fetch_count=fetch_count,
            error="max_steps exceeded",
        )

    def _safe_run(self, tool: Tool, raw_args: dict[str, Any]) -> ToolResult:
        try:
            parsed = tool.args_schema.model_validate(raw_args)
        except ValidationError as e:
            return ToolResult(ok=False, error=f"invalid args: {e}")
        try:
            return tool.run(parsed)
        except Exception as e:  # tool-level errors are surfaced to the agent
            return ToolResult(ok=False, error=f"{type(e).__name__}: {e}")

    def _parse_final(self, content: str, component_name: str) -> list[CompanyFinding]:
        if not content:
            return []
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            # Some providers wrap JSON in markdown fences; try to recover.
            stripped = content.strip().lstrip("`").rstrip("`")
            if stripped.lower().startswith("json"):
                stripped = stripped[4:]
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                return []

        companies: list[CompanyFinding] = []
        for raw in payload.get("companies", []) or []:
            evidence = [
                EvidenceRecord(
                    claim=e.get("claim", ""),
                    source_url=e.get("source_url"),
                    source_name=e.get("source_name", "web"),
                    tool_name=e.get("tool_name", ""),
                    snippet=e.get("snippet"),
                )
                for e in raw.get("evidence", []) or []
            ]
            companies.append(
                CompanyFinding(
                    name=raw.get("name", "Unknown"),
                    is_public=raw.get("is_public"),
                    ticker=raw.get("ticker"),
                    hq_country=raw.get("hq_country"),
                    market_share_pct=raw.get("market_share_pct"),
                    market_share_bucket=raw.get("market_share_bucket"),
                    single_source=bool(raw.get("single_source", False)),
                    moat_types=raw.get("moat_types") or [],
                    switching_costs=raw.get("switching_costs"),
                    customer_concentration=raw.get("customer_concentration"),
                    demand_signal=raw.get("demand_signal"),
                    valuation_usd=raw.get("valuation_usd"),
                    notes=raw.get("notes"),
                    evidence=evidence,
                )
            )
        return companies
