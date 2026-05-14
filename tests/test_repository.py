from pathlib import Path

from investment_agent.storage.repository import RunRepository


def test_repository_round_trip(tmp_runs_dir: Path):
    repo = RunRepository(tmp_runs_dir / "test.db")
    rid = repo.create_run(provider="mock", model="mock-v1", mock=True)
    comp_id = repo.upsert_component(
        run_id=rid,
        name="EUV Lithography",
        category="semiconductor_capex",
        description="EUV scanners",
        source="seed",
        status="pending",
    )
    co_id = repo.add_company(
        run_id=rid,
        component_id=comp_id,
        name="ASML",
        is_public=True,
        ticker="ASML",
        market_share_bucket="sole",
        single_source=True,
        moat_types=["ip", "regulatory"],
    )
    repo.add_evidence(
        company_id=co_id,
        claim="ASML is sole EUV supplier.",
        source_url="https://example.com/asml-euv",
        source_name="web",
        snippet="ASML is the only producer of EUV scanners.",
        tool_name="web_search",
    )
    repo.add_evidence(
        company_id=co_id,
        claim="Confirmed by 10-K.",
        source_url="https://example.com/asml-10k",
        source_name="web",
        tool_name="web_fetch",
    )
    repo.set_score(
        company_id=co_id,
        sole_source_pts=30,
        share_pts=25,
        ip_pts=15,
        regulatory_pts=10,
        switching_pts=10,
        demand_pts=10,
        composite=100,
        rubric_version="moat-v1",
        rationale="sole-source confirmed",
    )
    repo.finish_run(rid, status="done", cost_usd=0.0)

    view = repo.get_view(rid)
    assert view.run.id == rid
    assert len(view.components) == 1
    assert len(view.companies) == 1
    company = view.companies[0]
    assert company.ticker == "ASML"
    assert company.score is not None and company.score.composite == 100
    assert len(company.evidence) == 2
    assert company.moat_types == ["ip", "regulatory"]
