from __future__ import annotations

from dataclasses import dataclass, field

from ..agents.component_researcher import CompanyFinding, ResearchResult
from ..agents.concentration_analyzer import ScoredCompany
from ..agents.decomposer import DecomposedComponent
from ..agents.synthesizer import SynthesisReport


@dataclass
class RunState:
    run_id: str
    provider: str
    model: str | None
    mock: bool
    components: list[DecomposedComponent] = field(default_factory=list)
    research_results: list[ResearchResult] = field(default_factory=list)
    scored: list[ScoredCompany] = field(default_factory=list)
    report: SynthesisReport | None = None
    cost_usd: float = 0.0
    errors: list[str] = field(default_factory=list)
    per_component_status: dict[str, str] = field(default_factory=dict)

    def all_findings(self) -> list[tuple[str, list[CompanyFinding]]]:
        return [(r.component_name, r.companies) for r in self.research_results]
