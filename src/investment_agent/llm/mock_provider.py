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

        # Otherwise, emit the final findings as JSON.
        findings = {
            "component": component,
            "companies": [
                {
                    "name": f"Mock Leader for {component}",
                    "is_public": True,
                    "ticker": "MOCK",
                    "hq_country": "US",
                    "market_share_pct": 72.0,
                    "market_share_bucket": "50-75",
                    "single_source": False,
                    "moat_types": ["scale", "ip"],
                    "switching_costs": "high - integrated toolchain",
                    "customer_concentration": "top 5 customers = 60% of revenue",
                    "demand_signal": "order book +40% YoY",
                    "valuation_usd": None,
                    "notes": "Mock-mode placeholder finding.",
                    "evidence": [
                        {
                            "claim": "Mock leader holds ~72% share.",
                            "source_url": "https://example.com/mock-report",
                            "source_name": "web",
                            "tool_name": "web_search",
                            "snippet": "Mock snippet describing market position.",
                        }
                    ],
                },
                {
                    "name": f"Mock Challenger for {component}",
                    "is_public": False,
                    "ticker": None,
                    "hq_country": "US",
                    "market_share_pct": 18.0,
                    "market_share_bucket": "10-25",
                    "single_source": False,
                    "moat_types": ["tech"],
                    "switching_costs": "medium",
                    "customer_concentration": "diversified",
                    "demand_signal": "growing customer pipeline",
                    "valuation_usd": 5_000_000_000.0,
                    "notes": "Mock-mode placeholder finding.",
                    "evidence": [
                        {
                            "claim": "Mock challenger raised at $5B.",
                            "source_url": "https://example.com/mock-funding",
                            "source_name": "web",
                            "tool_name": "web_search",
                            "snippet": "Series E raise reported by tech press.",
                        }
                    ],
                },
            ],
        }
        return LLMResponse(
            content=json.dumps(findings),
            usage=Usage(input_tokens=400, output_tokens=300, cost_usd=0.0),
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
                "Mock synthesis: top opportunities cluster in single-source layers "
                "(EUV, HBM, advanced packaging) where capacity is the binding constraint."
            ),
            "top_companies": [],
            "themes": [
                "Capacity-constrained suppliers capture disproportionate margin.",
                "Power and cooling have re-emerged as bottlenecks.",
            ],
        }
        return LLMResponse(
            content=json.dumps(report),
            usage=Usage(input_tokens=500, output_tokens=200, cost_usd=0.0),
            finish_reason="stop",
        )
