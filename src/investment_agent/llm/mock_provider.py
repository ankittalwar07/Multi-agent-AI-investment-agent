"""Deterministic mock LLM for tests and `make smoke`.

Strategy: each agent prompt embeds an `<<AGENT:name>>` marker in its system
prompt. The mock inspects messages for that marker plus the call-count
(provider state) and returns a canned response shaped for that agent. This
lets us run the full pipeline end-to-end with no API spend and no network.
"""
from __future__ import annotations

import json
import re
import uuid
from collections import defaultdict
from typing import Literal

from .base import LLMMessage, LLMProvider, LLMResponse, ToolCall, ToolSpec, Usage

AGENT_MARKER_RE = re.compile(r"<<AGENT:(?P<agent>[a-z_]+)>>")


class MockProvider(LLMProvider):
    name = "mock"

    def __init__(self, model: str | None = None):
        self.model = model or "mock-v1"
        self._call_counts: dict[str, int] = defaultdict(int)

    def _detect_agent(self, messages: list[LLMMessage]) -> str:
        for m in messages:
            if m.role == "system":
                match = AGENT_MARKER_RE.search(m.content)
                if match:
                    return match.group("agent")
        return "unknown"

    def _detect_component(self, messages: list[LLMMessage]) -> str:
        # Researcher system prompt embeds "Component: <name>"
        for m in messages:
            if m.role == "system":
                match = re.search(r"Component:\s*([^\n]+)", m.content)
                if match:
                    return match.group(1).strip()
        return "Unknown Component"

    def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        response_format: Literal["text", "json"] = "text",
    ) -> LLMResponse:
        agent = self._detect_agent(messages)
        self._call_counts[agent] += 1
        call_n = self._call_counts[agent]

        if agent == "decomposer":
            return self._decomposer_response()
        if agent == "triage":
            return self._triage_response(messages)
        if agent == "component_researcher":
            return self._researcher_response(messages, call_n, tools or [])
        if agent == "concentration_analyzer":
            return self._analyzer_response(messages)
        if agent == "synthesizer":
            return self._synthesizer_response(messages)

        # Default: echo back as JSON
        return LLMResponse(
            content=json.dumps({"echo": True, "agent": agent}),
            usage=Usage(input_tokens=10, output_tokens=10, cost_usd=0.0),
            finish_reason="stop",
        )

    def _decomposer_response(self) -> LLMResponse:
        # Pretend we accepted the seed taxonomy verbatim plus added one new component.
        payload = {
            "components": [
                {
                    "name": "Seeded passthrough",
                    "category": "passthrough",
                    "description": "Mock decomposer passes through seed components.",
                    "source": "seed",
                }
            ],
            "added": [
                {
                    "name": "AI Energy Infrastructure",
                    "category": "facilities",
                    "description": "Dedicated power generation and grid for AI data centers.",
                    "justification": "Power constraints now dominate AI buildout.",
                }
            ],
        }
        return LLMResponse(
            content=json.dumps(payload),
            usage=Usage(input_tokens=200, output_tokens=120, cost_usd=0.0),
            finish_reason="stop",
        )

    def _researcher_response(
        self, messages: list[LLMMessage], call_n: int, tools: list[ToolSpec]
    ) -> LLMResponse:
        component = self._detect_component(messages)
        # Two-step ReAct: first call makes a search, second returns final JSON.
        if call_n == 1 and any(t.name == "web_search" for t in tools):
            return LLMResponse(
                content="",
                tool_calls=[
                    ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        name="web_search",
                        arguments={"query": f"{component} market leaders share"},
                    )
                ],
                usage=Usage(input_tokens=300, output_tokens=40, cost_usd=0.0),
                finish_reason="tool_use",
            )

        # Final: pull realistic mock data for this component.
        from .mock_data import findings_for_component

        companies = findings_for_component(component)
        findings = {"component": component, "companies": companies}
        return LLMResponse(
            content=json.dumps(findings),
            usage=Usage(input_tokens=400, output_tokens=400, cost_usd=0.0),
            finish_reason="stop",
        )

    def _triage_response(self, messages: list[LLMMessage]) -> LLMResponse:
        """Sparse companies pulled from the same MOCK_FINDINGS table but
        with only the triage-tier fields populated."""
        component = self._detect_component(messages)
        from .mock_data import findings_for_component

        full = findings_for_component(component)
        # Trim to triage shape: only the sparse fields
        triage_companies = []
        for c in full[:5]:
            triage_companies.append({
                "name": c.get("name"),
                "ticker": c.get("ticker"),
                "is_public": c.get("is_public"),
                "hq_country": c.get("hq_country"),
                "market_share_pct": c.get("market_share_pct"),
                "market_share_bucket": c.get("market_share_bucket"),
                "single_source": c.get("single_source", False),
                "structure": (c.get("extras") or {}).get("structure"),
                "supply_status": (c.get("extras") or {}).get("supply_status"),
                "demand_signal": c.get("demand_signal"),
                "moat_types": c.get("moat_types") or [],
                "switching_costs": c.get("switching_costs"),
                "thesis_one_liner": (c.get("extras") or {}).get("thesis_summary")
                                       or c.get("notes") or "Mock triage finding.",
                "valuation_usd": c.get("valuation_usd"),
            })
        return LLMResponse(
            content=json.dumps({"companies": triage_companies}),
            usage=Usage(input_tokens=200, output_tokens=300, cost_usd=0.0),
            finish_reason="stop",
        )

    def _analyzer_response(self, messages: list[LLMMessage]) -> LLMResponse:
        # The analyzer is mostly pure-python; the LLM just returns a rationale string.
        return LLMResponse(
            content=json.dumps(
                {"rationale": "Mock rationale: scored per moat rubric, see breakdown."}
            ),
            usage=Usage(input_tokens=150, output_tokens=40, cost_usd=0.0),
            finish_reason="stop",
        )

    def _synthesizer_response(self, messages: list[LLMMessage]) -> LLMResponse:
        report = {
            "summary": (
                "The strongest arbitrage opportunities cluster in capacity-constrained, "
                "single-source layers of the AI stack — EUV (ASML), CoWoS packaging (TSMC), "
                "and HBM3E (SK Hynix) — where backlog stretches into 2026+ and pricing power "
                "is durable. A second cluster is emerging in datacenter power & cooling, where "
                "grid constraints are the new binding factor; Vertiv and Schneider look "
                "underappreciated relative to capex commitments. Private-market mispricings "
                "appear in neoclouds (customer-concentration discount on CoreWeave, latent "
                "moat in Crusoe's stranded-power thesis) and frontier labs (Anthropic at "
                "~60B vs. OpenAI at ~300B implies non-linear share scenarios)."
            ),
            "top_companies": [],
            "themes": [
                "Single-source bottlenecks (ASML, TSMC CoWoS, SK Hynix HBM) keep pricing power into 2026.",
                "Power & cooling has graduated from cost line to binding constraint — re-rate ahead.",
                "Neoclouds: customer-concentration risk is mispriced; secondary-source neoclouds (Crusoe, Lambda) are the asymmetric bet.",
                "Frontier-model labs trading at wide implied-share dispersion — Anthropic vs OpenAI gap suggests upside on share gains.",
                "Tooling layer (vector DBs, agent frameworks) has weak switching costs; commodity risk is real.",
            ],
        }
        return LLMResponse(
            content=json.dumps(report),
            usage=Usage(input_tokens=500, output_tokens=400, cost_usd=0.0),
            finish_reason="stop",
        )
