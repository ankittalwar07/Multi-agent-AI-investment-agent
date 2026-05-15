"""Tier-1 Triage Researcher — one cheap LLM call per component.

Returns 3-5 incumbents with just enough structured data to populate the moat
rubric and show users what's interesting at a glance. No web tools, no ReAct
loop, no deep financials. Cost is ~5x cheaper than ComponentResearcher.

User then picks high-conviction names from the triage results and the Deep
Dive Researcher (existing ComponentResearcher logic) runs only on those.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..llm.base import LLMMessage, LLMProvider
from ..tools.seed_loader import SeedLoaderTool
from .component_researcher import CompanyFinding, EvidenceRecord, ResearchResult


TRIAGE_PROMPT = """<<AGENT:triage>>
You are an AI-infrastructure analyst doing a QUICK TRIAGE of one market layer.
Goal: surface 3-5 most important incumbents with just enough structured data
to populate a moat-strength scorecard. No web search needed — use your
training knowledge.

Component: __COMPONENT_NAME__
Category: __COMPONENT_CATEGORY__
Description: __COMPONENT_DESCRIPTION__
Known incumbents (from seed): __KNOWN_INCUMBENTS__

Output STRICT JSON:
{
  "companies": [
    {
      "name": str,
      "ticker": str | null,
      "is_public": bool,
      "hq_country": str | null,
      "market_share_pct": float | null,
      "market_share_bucket": "<10" | "10-25" | "25-50" | "50-75" | ">75" | "sole",
      "single_source": bool,
      "structure": "monopoly" | "duopoly" | "oligopoly" | "fragmented" | null,
      "supply_status": "constrained" | "balanced" | "oversupply" | null,
      "demand_signal": str,
      "moat_types": [str],
      "switching_costs": str | null,
      "thesis_one_liner": str,
      "valuation_usd": float | null
    }
  ]
}

Rules:
  - Include AT MOST 5 companies. Only the most relevant.
  - moat_types should be from: ip, tech, scale, regulatory, switching_costs, brand, network, process
  - Be honest about market_share_bucket — use 'sole' only when truly sole-source
  - Output JSON only, no prose around it.
"""


@dataclass
class TriageResult:
    component_name: str
    companies: list[CompanyFinding]
    cost_usd: float
    error: str | None = None


class TriageResearcher:
    """One LLM call per component. Returns sparse CompanyFinding objects."""

    def __init__(self, llm: LLMProvider, seed_tool: SeedLoaderTool):
        self.llm = llm
        self.seed_tool = seed_tool

    def run(self, component_name: str, component_category: str,
             component_description: str) -> TriageResult:
        # Look up the seeded incumbent list to give the LLM a starting prior
        seeded = []
        for c in self.seed_tool.all_components():
            if c.name == component_name:
                seeded = c.incumbents
                break
        seed_str = ", ".join(seeded) if seeded else "(none seeded)"

        system = (
            TRIAGE_PROMPT
            .replace("__COMPONENT_NAME__", component_name)
            .replace("__COMPONENT_CATEGORY__", component_category)
            .replace("__COMPONENT_DESCRIPTION__", component_description)
            .replace("__KNOWN_INCUMBENTS__", seed_str)
        )
        messages = [
            LLMMessage(role="system", content=system),
            LLMMessage(
                role="user",
                content=f"Triage the {component_name} market. Return JSON.",
            ),
        ]

        try:
            resp = self.llm.complete(
                messages=messages,
                response_format="json",
                max_tokens=1500,
                temperature=0.2,
            )
        except Exception as e:
            return TriageResult(
                component_name=component_name, companies=[],
                cost_usd=0.0, error=str(e),
            )

        companies = self._parse(resp.content, component_name, seeded)
        return TriageResult(
            component_name=component_name,
            companies=companies,
            cost_usd=resp.usage.cost_usd,
        )

    def _parse(self, content: str, component_name: str,
                seeded_incumbents: list[str]) -> list[CompanyFinding]:
        if not content:
            return []
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            stripped = content.strip().lstrip("`").rstrip("`")
            if stripped.lower().startswith("json"):
                stripped = stripped[4:]
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                return []

        companies: list[CompanyFinding] = []
        for raw in payload.get("companies", []) or []:
            # Triage findings get one synthetic evidence row pointing to seed
            evidence = [
                EvidenceRecord(
                    claim=raw.get("thesis_one_liner") or "Triage-tier finding",
                    source_url=None,
                    source_name="seed+llm-knowledge",
                    tool_name="triage",
                    snippet="Sparse triage data — run deep dive for cited research.",
                )
            ]
            extras = {
                "structure": raw.get("structure"),
                "supply_status": raw.get("supply_status"),
                "thesis_summary": raw.get("thesis_one_liner"),
                "analysis_depth": "triage",
            }
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
                    customer_concentration=None,
                    demand_signal=raw.get("demand_signal"),
                    valuation_usd=raw.get("valuation_usd"),
                    notes=None,
                    extras=extras,
                    evidence=evidence,
                )
            )
        return companies


def triage_to_research_result(t: TriageResult) -> ResearchResult:
    """Wrap a TriageResult so it slots into the existing pipeline plumbing."""
    return ResearchResult(
        component_name=t.component_name,
        companies=t.companies,
        cost_usd=t.cost_usd,
        search_count=0,
        fetch_count=0,
        error=t.error,
    )
