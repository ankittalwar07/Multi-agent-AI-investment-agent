from pathlib import Path

from investment_agent.tools.seed_loader import SeedLoaderTool, SeedLookupArgs


def test_seed_loads_all_components(seed_path: Path):
    tool = SeedLoaderTool(seed_path=seed_path)
    comps = tool.all_components()
    names = [c.name for c in comps]
    assert "EUV Lithography" in names
    assert "High-Bandwidth Memory (HBM)" in names
    assert len(comps) >= 15


def test_seed_lookup_substring(seed_path: Path):
    tool = SeedLoaderTool(seed_path=seed_path)
    result = tool.run(SeedLookupArgs(component_name="EUV"))
    assert result.ok
    payload = result.content
    assert any("EUV" in c["name"] for c in payload)
