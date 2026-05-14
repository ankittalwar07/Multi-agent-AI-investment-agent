"""End-to-end smoke test: run the full pipeline against the mock provider
on a 3-component subset. No network, no LLM spend.
"""
from __future__ import annotations

from pathlib import Path

from investment_agent.config import Settings
from investment_agent.graph.build import Pipeline, RunOptions
from investment_agent.llm import get_provider
from investment_agent.storage.repository import RunRepository


def test_mock_pipeline_e2e(tmp_runs_dir: Path):
    settings = Settings(
        SEED_FILE=Path("data/seeds/ai_infra_components.yaml"),
        RUN_OUTPUT_DIR=tmp_runs_dir,
        LLM_PROVIDER="mock",
        MAX_PARALLEL_RESEARCHERS=2,
    )
    pipeline = Pipeline(
        settings=settings,
        llm_factory=lambda: get_provider("mock"),
    )
    result = pipeline.run(
        RunOptions(provider="mock", model=None, mock=True, max_components=3, output_dir=tmp_runs_dir)
    )

    # Artifacts on disk
    assert result.db_path.exists()
    assert result.json_path.exists()
    assert result.markdown_path.exists()

    # DB rows
    repo = RunRepository(result.db_path)
    view = repo.get_view(result.run_id)

    assert view.run.status == "done"
    assert view.run.cost_usd == 0.0  # mock provider has zero cost
    assert len(view.components) == 3
    assert all(c.status == "done" for c in view.components)

    assert len(view.companies) == 6  # mock returns 2 companies per component
    for company in view.companies:
        assert company.score is not None
        assert company.score.composite is not None
        assert len(company.evidence) >= 1

    # Markdown report mentions at least one company
    md = result.markdown_path.read_text()
    assert "Top Companies" in md
    assert any(c.name in md for c in view.companies)
