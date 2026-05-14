from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

from ..llm.base import LLMMessage, LLMProvider
from ..scoring.moat_rubric import MoatScore, score_company
from .component_researcher import CompanyFinding
from .prompts import CONCENTRATION_ANALYZER


@dataclass
class ScoredCompany:
    finding: CompanyFinding
    component_name: str
    score: MoatScore


def _independent_citation_count(finding: CompanyFinding) -> int:
    seen: set[str] = set()
    for e in finding.evidence:
        key = e.source_url or e.source_name
        if key:
            seen.add(key)
    return len(seen)


class ConcentrationAnalyzer:
    def __init__(self, llm: LLMProvider, *, llm_rationale: bool = True):
        self.llm = llm
        self.llm_rationale = llm_rationale

    def score_all(
        self, results: Iterable[tuple[str, list[CompanyFinding]]]
    ) -> tuple[list[ScoredCompany], float]:
        total_cost = 0.0
        scored: list[ScoredCompany] = []
        for component_name, findings in results:
            for finding in findings:
                score = score_company(
                    single_source=finding.single_source,
                    independent_citations_for_sole_source=_independent_citation_count(finding),
                    market_share_bucket=finding.market_share_bucket,
                    moat_types=finding.moat_types,
                    switching_costs=finding.switching_costs,
                    demand_signal=finding.demand_signal,
                )
                if self.llm_rationale:
                    rationale, cost = self._llm_rationale(finding, component_name, score)
                    total_cost += cost
                    if rationale:
                        score.rationale = rationale
                scored.append(
                    ScoredCompany(finding=finding, component_name=component_name, score=score)
                )
        return scored, total_cost

    def _llm_rationale(
        self, finding: CompanyFinding, component_name: str, score: MoatScore
    ) -> tuple[str | None, float]:
        payload = {
            "component": component_name,
            "company": {
                "name": finding.name,
                "is_public": finding.is_public,
                "ticker": finding.ticker,
                "market_share_bucket": finding.market_share_bucket,
                "single_source": finding.single_source,
                "moat_types": finding.moat_types,
                "switching_costs": finding.switching_costs,
                "demand_signal": finding.demand_signal,
            },
            "score_breakdown": score.to_dict(),
            "evidence_summaries": [
                {"claim": e.claim, "source": e.source_url or e.source_name}
                for e in finding.evidence[:6]
            ],
        }
        messages = [
            LLMMessage(role="system", content=CONCENTRATION_ANALYZER),
            LLMMessage(role="user", content=json.dumps(payload, indent=2)),
        ]
        resp = self.llm.complete(messages=messages, response_format="json", max_tokens=300)
        try:
            return json.loads(resp.content).get("rationale"), resp.usage.cost_usd
        except (json.JSONDecodeError, AttributeError):
            return None, resp.usage.cost_usd
