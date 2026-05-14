from __future__ import annotations

import json
from dataclasses import dataclass

from ..llm.base import LLMMessage, LLMProvider
from .concentration_analyzer import ScoredCompany
from .prompts import SYNTHESIZER


@dataclass
class SynthesisReport:
    summary: str
    top_companies: list[dict]
    themes: list[str]
    cost_usd: float

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "top_companies": self.top_companies,
            "themes": self.themes,
        }

    def to_markdown(self) -> str:
        lines = [
            "# AI Infrastructure — Investment Opportunity Report",
            "",
            "## Summary",
            self.summary or "_no summary_",
            "",
            "## Top Companies",
        ]
        if not self.top_companies:
            lines.append("_none scored above threshold_")
        for i, c in enumerate(self.top_companies, start=1):
            name = c.get("name", "?")
            comp = c.get("component", "?")
            score = c.get("composite", "?")
            thesis = c.get("one_line_thesis", "")
            ticker = c.get("ticker")
            ticker_str = f" ({ticker})" if ticker else ""
            lines.append(f"{i}. **{name}**{ticker_str} — {comp} — score {score}")
            if thesis:
                lines.append(f"   - {thesis}")
        lines.append("")
        lines.append("## Themes")
        for t in self.themes or []:
            lines.append(f"- {t}")
        return "\n".join(lines)


class Synthesizer:
    def __init__(self, llm: LLMProvider, top_n: int = 20):
        self.llm = llm
        self.top_n = top_n

    def run(self, scored: list[ScoredCompany]) -> SynthesisReport:
        scored_sorted = sorted(
            scored, key=lambda s: (s.score.composite, s.finding.name), reverse=True
        )
        top = scored_sorted[: self.top_n]

        payload = {
            "scored_companies": [
                {
                    "name": s.finding.name,
                    "component": s.component_name,
                    "ticker": s.finding.ticker,
                    "is_public": s.finding.is_public,
                    "composite": s.score.composite,
                    "single_source": s.finding.single_source,
                    "market_share_bucket": s.finding.market_share_bucket,
                    "moat_types": s.finding.moat_types,
                    "demand_signal": s.finding.demand_signal,
                    "evidence_count": len(s.finding.evidence),
                }
                for s in top
            ],
            "total_companies_considered": len(scored),
        }
        messages = [
            LLMMessage(role="system", content=SYNTHESIZER),
            LLMMessage(role="user", content=json.dumps(payload, indent=2)),
        ]
        resp = self.llm.complete(messages=messages, response_format="json", max_tokens=1500)

        # Robust default: even if LLM JSON parsing fails, we still produce a useful report.
        summary = ""
        themes: list[str] = []
        top_companies: list[dict] = []
        try:
            data = json.loads(resp.content) if resp.content else {}
            summary = data.get("summary", "")
            themes = data.get("themes", []) or []
            top_companies = data.get("top_companies", []) or []
        except json.JSONDecodeError:
            pass

        # If the LLM didn't populate top_companies (e.g. mock returns empty), synthesize from scored data.
        if not top_companies:
            top_companies = [
                {
                    "name": s.finding.name,
                    "component": s.component_name,
                    "ticker": s.finding.ticker,
                    "composite": s.score.composite,
                    "one_line_thesis": (s.score.rationale or "")[:160],
                }
                for s in top
            ]
        if not summary:
            summary = (
                f"Evaluated {len(scored)} companies across the AI-infrastructure stack. "
                f"Top {len(top_companies)} ranked by composite moat-strength score."
            )

        return SynthesisReport(
            summary=summary,
            top_companies=top_companies,
            themes=themes,
            cost_usd=resp.usage.cost_usd,
        )
