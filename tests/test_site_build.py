"""Static-site export: scoring, council, and the validator (no LLM, no network)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from investment_agent.site import build_site_payload, clean_text, write_site_data

ROOT = Path(__file__).resolve().parents[1]


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_site_data", ROOT / "scripts" / "validate_site_data.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _research(**company_overrides) -> dict:
    company = {
        "name": "Example Litho",
        "ticker": "EXL",
        "is_public": True,
        "hq_country": "Netherlands",
        "component_id": "euv-lithography",
        "market_share_bucket": "sole",
        "single_source": True,
        "moat_types": ["ip", "export_control"],
        "switching_costs": "very high lock-in",
        "demand_signal": "multi-year backlog",
        "thesis_summary": "Only qualified EUV supplier.",
        "evidence": [
            {"claim": "Sole EUV supplier", "source_url": "https://www.asml.com/en/investors",
             "source_name": "Company IR"},
            {"claim": "No second source", "source_url": "https://www.reuters.com/technology/",
             "source_name": "Reuters"},
        ],
    }
    company.update(company_overrides)
    return {
        "run_date": "2026-11-09",
        "summary": "Lithography stays the tightest bottleneck.",
        "themes": ["Single-source tools keep pricing power."],
        "components": [{"id": "euv-lithography", "name": "EUV Lithography",
                        "category": "semiconductor_capex", "description": "EUV scanners."}],
        "companies": [company],
    }


def test_sole_source_needs_two_domains():
    two = build_site_payload(_research())["companies"][0]
    assert two["single_source_credited"] is True
    assert two["score"]["breakdown"]["sole_source"] == 30
    assert two["score"]["composite"] == 30 + 25 + 15 + 10 + 10 + 10

    one = build_site_payload(_research(evidence=[
        {"claim": "x", "source_url": "https://www.asml.com/a", "source_name": "IR"},
        {"claim": "y", "source_url": "https://asml.com/b", "source_name": "IR"},
    ]))["companies"][0]
    assert one["single_source_credited"] is False
    assert one["score"]["breakdown"]["sole_source"] == 0


def test_council_has_nine_votes_and_breakdown_adds_up():
    c = build_site_payload(_research())["companies"][0]
    assert len(c["council"]["verdicts"]) == 9
    assert sum(c["score"]["breakdown"].values()) == c["score"]["composite"]


def test_dashes_are_cleaned_and_http_urls_dropped():
    assert clean_text("moat \u2014 strong") == "moat, strong"
    c = build_site_payload(_research(
        thesis_summary="Tight supply \u2013 rising prices",
        evidence=[{"claim": "x", "source_url": "http://insecure.test/x", "source_name": "x"}],
    ))["companies"][0]
    assert "\u2013" not in c["thesis_summary"]
    assert c["evidence"][0]["source_url"] is None


def test_written_data_passes_validator(tmp_path):
    payload = build_site_payload(_research())
    write_site_data(payload, tmp_path)
    v = _load_validator()
    assert v.validate_dir(tmp_path) == []
    index = json.loads((tmp_path / "history" / "index.json").read_text())
    assert index["runs"][0]["run_date"] == "2026-11-09"


def test_validator_rejects_unsourced_real_runs(tmp_path):
    payload = build_site_payload(_research(evidence=[]))
    write_site_data(payload, tmp_path)
    problems = _load_validator().validate_dir(tmp_path)
    assert any("cited https source" in p for p in problems)


def test_committed_site_data_is_valid():
    assert _load_validator().validate_dir(ROOT / "docs" / "data") == []
