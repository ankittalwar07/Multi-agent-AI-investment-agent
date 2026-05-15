"""Pipeline orchestration.

Fan-out is done with `ThreadPoolExecutor` — simpler than LangGraph for our
needs and avoids pulling LangGraph onto the smoke-test critical path. The
state object and per-component status updates are still compatible with a
LangGraph upgrade later: each agent invocation is a pure function over state.
"""
from __future__ import annotations

import json
import threading
import time
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
    resume_run_id: str | None = None  # if set, resume this run instead of creating new


_RESEARCHABLE_STATUSES = {"pending", "researching", "error", "rate_limited"}


def _status_needs_research(status: str | None) -> bool:
    return (status or "pending") in _RESEARCHABLE_STATUSES


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

        # ---- Resume vs fresh start ----
        resuming = bool(opts.resume_run_id)
        if resuming:
            rid = opts.resume_run_id
            repo_path = output_dir / f"{rid}.db"
            if not repo_path.exists():
                raise RuntimeError(f"Cannot resume run {rid}: {repo_path} not found")
            repo = RunRepository(repo_path)
            existing_run = repo.get_run(rid)
            if not existing_run:
                raise RuntimeError(f"Cannot resume run {rid}: row missing")
            self._emit(repo, rid, "info", "init", f"RESUME run; provider={opts.provider}")
        else:
            rid = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
            repo_path = output_dir / f"{rid}.db"
            repo = RunRepository(repo_path)
            repo.create_run(provider=opts.provider, model=opts.model, mock=opts.mock, run_id=rid)

        state = RunState(run_id=rid, provider=opts.provider, model=opts.model, mock=opts.mock)
        if not resuming:
            self._emit(repo, rid, "info", "init",
                       f"run started provider={opts.provider} mock={opts.mock}")
        # Carry forward existing cost
        if resuming:
            existing = repo.get_run(rid)
            if existing:
                state.cost_usd = existing.cost_usd or 0.0

        tools = _make_tools(self.settings.seed_file)
        seed_tool: SeedLoaderTool = tools["seed_lookup"]  # type: ignore[assignment]
        llm = self.llm_factory()

        # ---- Decomposer (skip on resume) ----
        component_ids: dict[str, str] = {}
        if resuming:
            view = repo.get_view(rid)
            from ..agents.decomposer import DecomposedComponent
            components = [
                DecomposedComponent(
                    name=c.name, category=c.category or "", description=c.description or "",
                    source=c.source or "seed",
                )
                for c in view.components
            ]
            for c in view.components:
                component_ids[c.name] = c.id
                state.per_component_status[c.name] = c.status
            state.components = components
            done_count = sum(1 for s in state.per_component_status.values() if s == "done")
            pending_count = len(components) - done_count
            self._emit(repo, rid, "info", "resume",
                       f"loaded {len(components)} components; "
                       f"{done_count} done, {pending_count} need research")
        else:
            try:
                decomposer = Decomposer(llm=llm, seed_tool=seed_tool, max_components=opts.max_components)
                components, cost = decomposer.run()
                self._add_cost(state, repo, cost)
                state.components = components
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

        # ---- Filter components to ones still needing research ----
        components_to_research = [
            c for c in components
            if _status_needs_research(state.per_component_status.get(c.name))
        ]
        if not components_to_research:
            self._emit(repo, rid, "info", "researcher",
                       "all components already done — refreshing scores/council")
        else:
            self._emit(repo, rid, "info", "researcher",
                       f"researching {len(components_to_research)}/{len(components)} components")

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
        # Throttle parallelism on rate-limited free tiers so we don't burst
        # past TPM caps (Groq free = 6k TPM on 8B, 12k on 70B).
        if opts.provider in ("groq", "multi"):
            max_workers = 1
        elif opts.provider == "gemini" and max_workers > 2:
            max_workers = 2
        results: list[ResearchResult] = []
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_research_one, c): c for c in components_to_research}
            for fut in as_completed(futures):
                comp = futures[fut]
                try:
                    res = fut.result()
                    self._add_cost(state, repo, res.cost_usd)
                    if state.cost_usd > self.settings.max_cost_usd:
                        self._emit(repo, rid, "error", "researcher",
                                   f"cost ceiling exceeded (${state.cost_usd:.2f}); aborting")
                        state.errors.append("cost ceiling exceeded")
                    results.append(res)
                    new_status = "error" if res.error else "done"
                    repo.set_component_status(component_ids[comp.name], new_status)
                    state.per_component_status[comp.name] = new_status
                    self._emit(
                        repo, rid, "info", "researcher",
                        f"{comp.name}: {len(res.companies)} companies (cost=${res.cost_usd:.4f})",
                    )
                except Exception as e:  # noqa: BLE001
                    err_str = str(e)
                    is_rate_limit = (
                        "429" in err_str or "rate" in err_str.lower()
                        or "quota" in err_str.lower()
                    )
                    new_status = "rate_limited" if is_rate_limit else "error"
                    self._emit(repo, rid, "error", "researcher",
                               f"{comp.name} failed ({new_status}): {err_str[:200]}")
                    repo.set_component_status(component_ids[comp.name], new_status)
                    state.per_component_status[comp.name] = new_status
                    if not is_rate_limit:
                        state.errors.append(f"{comp.name}: {err_str[:120]}")

        state.research_results = results

        # ---- Persist companies + evidence (only for newly-researched components) ----
        company_ids: dict[tuple[str, str], str] = {}
        for res in results:
            if res.error:
                continue  # don't persist anything for failed researchers
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

        # ---- Add company_ids for ALL companies (incl. previously-researched) ----
        # This way scoring/intel/council process the full set on every iteration.
        view = repo.get_view(rid)
        comp_name_by_id = {c.id: c.name for c in view.components}
        for c in view.companies:
            comp_name = comp_name_by_id.get(c.component_id, "?")
            company_ids.setdefault((comp_name, c.name), c.id)
        # Also rebuild state.research_results to include previously-completed
        # companies so scorer/intel/council see everyone, not just newly researched
        from ..agents.component_researcher import (
            CompanyFinding, EvidenceRecord, ResearchResult,
        )
        researched_components = {r.component_name for r in results if not r.error}
        for c in view.components:
            if c.name in researched_components:
                continue  # already in `results`
            existing_companies = [co for co in view.companies if co.component_id == c.id]
            if not existing_companies:
                continue
            findings = [
                CompanyFinding(
                    name=co.name, is_public=co.is_public, ticker=co.ticker,
                    hq_country=co.hq_country, market_share_pct=co.market_share_pct,
                    market_share_bucket=co.market_share_bucket,
                    single_source=bool(co.single_source), moat_types=co.moat_types,
                    switching_costs=co.switching_costs,
                    customer_concentration=co.customer_concentration,
                    demand_signal=co.demand_signal, valuation_usd=co.valuation_usd,
                    notes=co.notes,
                    extras=(co.extras.model_dump() if hasattr(co.extras, "model_dump") else dict(co.extras or {})),
                    evidence=[
                        EvidenceRecord(
                            claim=ev.claim or "", source_url=ev.source_url,
                            source_name=ev.source_name or "web",
                            tool_name=ev.tool_name or "", snippet=ev.snippet,
                        ) for ev in co.evidence
                    ],
                )
                for co in existing_companies
            ]
            results.append(ResearchResult(
                component_name=c.name, companies=findings,
                cost_usd=0.0, search_count=0, fetch_count=0,
            ))
        state.research_results = results

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

        # Compute final status:
        #   done    — every component has status=done
        #   partial — some components still need research (rate_limited / error)
        #             the user (or run_until_done) can resume to finish
        #   error   — non-recoverable errors (e.g., decomposer failed)
        all_done = all(
            s == "done" for s in state.per_component_status.values()
        )
        if state.errors:
            final_status = "error"
        elif all_done:
            final_status = "done"
        else:
            final_status = "partial"

        repo.finish_run(
            rid,
            status=final_status,
            error="; ".join(state.errors) if state.errors else None,
            cost_usd=state.cost_usd,
        )
        return self._finalize(state, repo, repo_path, output_dir)

    def run_until_done(
        self,
        opts: RunOptions,
        max_iterations: int = 30,
        sleep_between_s: float = 30.0,
        on_progress: callable | None = None,
    ) -> PipelineResult:
        """Loop run() until all components are 'done' or budget is exhausted.

        Used by the overnight CLI script and the Streamlit "Run with auto-resume"
        button. Each iteration:
          1. Calls run() with resume_run_id (after first iteration)
          2. Checks per-component status
          3. If all done, returns
          4. If some still need research, sleeps then loops
        """
        result = self.run(opts)
        for i in range(max_iterations - 1):
            statuses = result.state.per_component_status
            done = sum(1 for s in statuses.values() if s == "done")
            total = len(statuses)
            still_pending = total - done

            if on_progress:
                try:
                    on_progress(i + 1, done, total, still_pending, result.run_id)
                except Exception:
                    pass

            if still_pending == 0:
                break

            # Brief pause before retry — multi-provider LLM already handles
            # within-call rate-limit waits, so this just throttles outer loop.
            time.sleep(sleep_between_s)

            # Resume from the same run, only retrying the unfinished ones
            resume_opts = RunOptions(
                provider=opts.provider, model=opts.model, mock=opts.mock,
                max_components=opts.max_components, output_dir=opts.output_dir,
                resume_run_id=result.run_id,
            )
            result = self.run(resume_opts)

        return result

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
