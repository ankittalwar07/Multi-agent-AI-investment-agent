"""Pipeline orchestration.

Fan-out is done with `ThreadPoolExecutor` — simpler than LangGraph for our
needs and avoids pulling LangGraph onto the smoke-test critical path. The
state object and per-component status updates are still compatible with a
LangGraph upgrade later: each agent invocation is a pure function over state.
"""
from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..agents.component_researcher import ComponentResearcher, ResearchResult
from ..agents.concentration_analyzer import ConcentrationAnalyzer
from ..agents.decomposer import Decomposer
from ..agents.synthesizer import Synthesizer
from ..config import Settings
from ..council.engine import company_to_view, council_summary, run_council
from ..intelligence import run_intelligence
from ..llm import LLMProvider
from ..llm.mock_data import INTELLIGENCE as DEMO_INTELLIGENCE
from ..scoring.moat_rubric import RUBRIC_VERSION
from ..storage.repository import RunRepository
from ..tools.base import Tool
from ..tools.paid_market_data import PaidMarketDataTool
from ..tools.seed_loader import SeedLoaderTool
from ..tools.web_fetch import WebFetchTool
from ..tools.web_search import WebSearchTool
from .state import RunState


@dataclass
class RunOptions:
    provider: str
    model: str | None
    mock: bool
    max_components: int | None = None
    output_dir: Path | None = None


@dataclass
class PipelineResult:
    run_id: str
    state: RunState
    db_path: Path
    json_path: Path
    markdown_path: Path


def _make_tools(seed_path: Path) -> dict[str, Tool]:
    return {
        "seed_lookup": SeedLoaderTool(seed_path=seed_path),
        "web_search": WebSearchTool(),
        "web_fetch": WebFetchTool(),
        "paid_market_data": PaidMarketDataTool(),
    }


class Pipeline:
    def __init__(
        self,
        settings: Settings,
        llm_factory: Callable[[], LLMProvider],
        *,
        progress_cb: Callable[[str, str], None] | None = None,
    ):
        self.settings = settings
        self.llm_factory = llm_factory
        self.progress_cb = progress_cb or (lambda node, msg: None)
        self._cost_lock = threading.Lock()

    def _emit(self, repo: RunRepository, run_id: str, level: str, node: str, message: str) -> None:
        repo.log_event(run_id=run_id, level=level, node=node, message=message)
        try:
            self.progress_cb(node, message)
        except Exception:
            pass

    def _add_cost(self, state: RunState, repo: RunRepository, delta: float) -> None:
        if delta <= 0:
            return
        with self._cost_lock:
            state.cost_usd += delta
            repo.add_cost(state.run_id, delta)

    def run(self, opts: RunOptions) -> PipelineResult:
        import uuid
        from datetime import datetime, timezone

        output_dir = Path(opts.output_dir or self.settings.run_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        rid = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
        repo_path = output_dir / f"{rid}.db"
        repo = RunRepository(repo_path)
        repo.create_run(provider=opts.provider, model=opts.model, mock=opts.mock, run_id=rid)

        state = RunState(run_id=rid, provider=opts.provider, model=opts.model, mock=opts.mock)
        self._emit(repo, rid, "info", "init", f"run started provider={opts.provider} mock={opts.mock}")

        tools = _make_tools(self.settings.seed_file)
        seed_tool: SeedLoaderTool = tools["seed_lookup"]  # type: ignore[assignment]
        llm = self.llm_factory()

        # ----- Decomposer -----
        try:
            decomposer = Decomposer(llm=llm, seed_tool=seed_tool, max_components=opts.max_components)
            components, cost = decomposer.run()
            self._add_cost(state, repo, cost)
            state.components = components
            component_ids: dict[str, str] = {}
            for c in components:
                cid = repo.upsert_component(
                    run_id=rid,
                    name=c.name,
                    category=c.category,
                    description=c.description,
                    source=c.source,
                    status="pending",
                )
                component_ids[c.name] = cid
                state.per_component_status[c.name] = "pending"
            self._emit(repo, rid, "info", "decomposer", f"resolved {len(components)} components")
        except Exception as e:
            self._emit(repo, rid, "error", "decomposer", f"failed: {e}")
            state.errors.append(f"decomposer: {e}")
            repo.finish_run(rid, status="error", error=str(e), cost_usd=state.cost_usd)
            return self._finalize(state, repo, repo_path, output_dir)

        # ----- Component Researchers (fan-out) -----
        researcher = ComponentResearcher(
            llm=llm,
            tools=tools,
            max_searches=self.settings.max_searches_per_researcher,
            max_fetches=self.settings.max_fetches_per_researcher,
        )

        def _research_one(component) -> ResearchResult:
            repo.set_component_status(component_ids[component.name], "researching")
            self._emit(repo, rid, "info", "researcher", f"researching: {component.name}")
            return researcher.run(
                component_name=component.name,
                component_category=component.category,
                component_description=component.description,
            )

        max_workers = max(1, self.settings.max_parallel_researchers)
        results: list[ResearchResult] = []
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_research_one, c): c for c in components}
            for fut in as_completed(futures):
                comp = futures[fut]
                try:
                    res = fut.result()
                    self._add_cost(state, repo, res.cost_usd)
                    # Cost ceiling
                    if state.cost_usd > self.settings.max_cost_usd:
                        self._emit(repo, rid, "error", "researcher",
                                   f"cost ceiling exceeded (${state.cost_usd:.2f}); aborting")
                        state.errors.append("cost ceiling exceeded")
                    results.append(res)
                    repo.set_component_status(
                        component_ids[comp.name],
                        "error" if res.error else "done",
                    )
                    state.per_component_status[comp.name] = "error" if res.error else "done"
                    self._emit(
                        repo, rid, "info", "researcher",
                        f"{comp.name}: {len(res.companies)} companies (cost=${res.cost_usd:.4f})",
                    )
                except Exception as e:  # noqa: BLE001
                    self._emit(repo, rid, "error", "researcher", f"{comp.name} failed: {e}")
                    repo.set_component_status(component_ids[comp.name], "error")
                    state.per_component_status[comp.name] = "error"
                    state.errors.append(f"{comp.name}: {e}")

        state.research_results = results

        # Persist companies + evidence
        company_ids: dict[tuple[str, str], str] = {}
        for res in results:
            for finding in res.companies:
                cid = repo.add_company(
                    run_id=rid,
                    component_id=component_ids[res.component_name],
                    name=finding.name,
                    is_public=finding.is_public,
                    ticker=finding.ticker,
                    hq_country=finding.hq_country,
                    market_share_pct=finding.market_share_pct,
                    market_share_bucket=finding.market_share_bucket,
                    single_source=finding.single_source,
                    moat_types=finding.moat_types,
                    switching_costs=finding.switching_costs,
                    customer_concentration=finding.customer_concentration,
                    demand_signal=finding.demand_signal,
                    valuation_usd=finding.valuation_usd,
                    notes=finding.notes,
                    extras=finding.extras,
                )
                company_ids[(res.component_name, finding.name)] = cid
                for ev in finding.evidence:
                    repo.add_evidence(
                        company_id=cid,
                        claim=ev.claim,
                        source_url=ev.source_url,
                        source_name=ev.source_name,
                        snippet=ev.snippet,
                        tool_name=ev.tool_name,
                    )

        # ----- Concentration Analyzer -----
        analyzer = ConcentrationAnalyzer(llm=llm, llm_rationale=not opts.mock)  # save cost in tests
        scored, cost = analyzer.score_all(state.all_findings())
        self._add_cost(state, repo, cost)
        state.scored = scored
        for s in scored:
            cid = company_ids.get((s.component_name, s.finding.name))
            if not cid:
                continue
            repo.set_score(
                company_id=cid,
                sole_source_pts=s.score.sole_source_pts,
                share_pts=s.score.share_pts,
                ip_pts=s.score.ip_pts,
                regulatory_pts=s.score.regulatory_pts,
                switching_pts=s.score.switching_pts,
                demand_pts=s.score.demand_pts,
                composite=s.score.composite,
                rubric_version=RUBRIC_VERSION,
                rationale=s.score.rationale,
            )
        self._emit(repo, rid, "info", "analyzer", f"scored {len(scored)} companies")

        # ----- Intelligence Agent -----
        # Fetches gov investments, congressional trades, policy flags etc.
        # In Demo mode, reads from the INTELLIGENCE patch; in live runs the
        # LLM provider could call USAspending / Senate EFD / SEC EDGAR via
        # web tools to populate the same shape.
        for s in scored:
            cid = company_ids.get((s.component_name, s.finding.name))
            if not cid:
                continue
            signals, summary = run_intelligence(
                s.finding.name, s.finding.ticker,
                demo_data=DEMO_INTELLIGENCE if opts.mock else None,
            )
            if signals or summary.total_signals:
                repo.update_company_extras(
                    cid,
                    {
                        "intelligence_signals": [sig.model_dump(mode="json") for sig in signals],
                        "intelligence_summary": summary.model_dump(),
                    },
                )
                # Also patch the finding's extras dict so the council (next step)
                # can use intelligence signals in its rubrics.
                if isinstance(s.finding.extras, dict):
                    s.finding.extras["intelligence_summary"] = summary.model_dump()
        self._emit(repo, rid, "info", "intelligence",
                   f"intelligence agent reviewed {len(scored)} companies")

        # ----- Investor Council -----
        for s in scored:
            cid = company_ids.get((s.component_name, s.finding.name))
            if not cid:
                continue
            view = company_to_view(s.finding, s.score, s.component_name)
            verdicts = run_council(view)
            summary = council_summary(verdicts)
            repo.update_company_extras(
                cid,
                {
                    "council_verdicts": [v.model_dump() for v in verdicts],
                    "council_summary": summary,
                },
            )
        self._emit(repo, rid, "info", "council",
                   f"council reviewed {len(scored)} companies")

        # ----- Synthesizer -----
        synthesizer = Synthesizer(llm=llm)
        report = synthesizer.run(scored)
        self._add_cost(state, repo, report.cost_usd)
        state.report = report
        self._emit(repo, rid, "info", "synthesizer", "report generated")

        repo.finish_run(
            rid,
            status="error" if state.errors else "done",
            error="; ".join(state.errors) if state.errors else None,
            cost_usd=state.cost_usd,
        )
        return self._finalize(state, repo, repo_path, output_dir)

    def _finalize(
        self, state: RunState, repo: RunRepository, db_path: Path, output_dir: Path
    ) -> PipelineResult:
        json_path = output_dir / f"{state.run_id}.json"
        md_path = output_dir / f"{state.run_id}.md"

        json_payload = {
            "run_id": state.run_id,
            "provider": state.provider,
            "model": state.model,
            "mock": state.mock,
            "cost_usd": state.cost_usd,
            "components": [
                {"name": c.name, "category": c.category, "source": c.source}
                for c in state.components
            ],
            "companies": [
                {
                    "component": s.component_name,
                    "name": s.finding.name,
                    "ticker": s.finding.ticker,
                    "is_public": s.finding.is_public,
                    "market_share_bucket": s.finding.market_share_bucket,
                    "single_source": s.finding.single_source,
                    "moat_types": s.finding.moat_types,
                    "composite": s.score.composite,
                    "rationale": s.score.rationale,
                    "evidence_count": len(s.finding.evidence),
                }
                for s in state.scored
            ],
            "report": state.report.to_dict() if state.report else None,
            "errors": state.errors,
        }
        json_path.write_text(json.dumps(json_payload, indent=2, default=str))
        md_path.write_text((state.report.to_markdown() if state.report else "# (no report)\n"))

        return PipelineResult(
            run_id=state.run_id,
            state=state,
            db_path=db_path,
            json_path=json_path,
            markdown_path=md_path,
        )
