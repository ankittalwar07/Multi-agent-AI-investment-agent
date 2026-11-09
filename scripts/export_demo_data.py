"""Seed docs/data with SAMPLE data from the offline demo (mock provider, no API calls).

Runs the real LangGraph pipeline with the deterministic MockProvider, converts the
run into the research-file format, and builds the dashboard data from it, marked
"sample": true so the UI shows a banner. The weekly Claude routine replaces it with
real, cited research.

Usage:
    python scripts/export_demo_data.py
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from investment_agent.config import get_settings  # noqa: E402
from investment_agent.graph.build import Pipeline, RunOptions  # noqa: E402
from investment_agent.llm import get_provider  # noqa: E402
from investment_agent.site import build_site_payload, write_site_data  # noqa: E402
from investment_agent.site.build import clean_text, slugify  # noqa: E402
from investment_agent.storage.repository import RunRepository  # noqa: E402

_ADVICE = re.compile(r"^(buy|sell|short|accumulate|trim|add)\b", re.IGNORECASE)


def _no_advice(text: str | None) -> str | None:
    """Drop advice-style sentences ("Buy on any pullback.") from demo text."""
    if not text:
        return text
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    kept = [p for p in parts if not _ADVICE.match(p)]
    return " ".join(kept) or None


def run_to_research(view, run_date: str) -> dict:
    comp_ids = {}
    components = []
    for c in view.components:
        cid = slugify(c.name)
        comp_ids[c.id] = cid
        components.append({"id": cid, "name": c.name, "category": c.category,
                           "description": c.description})
    companies = []
    for co in view.companies:
        # The mock fills a few components with placeholder leaders; skip those.
        if "(mock)" in (co.name or "") or (co.ticker or "").upper() == "TBD":
            continue
        ex = co.extras
        companies.append({
            "name": co.name,
            "ticker": co.ticker,
            "is_public": co.is_public,
            "hq_country": co.hq_country,
            "component_id": comp_ids.get(co.component_id),
            "market_share_pct": co.market_share_pct,
            "market_share_bucket": co.market_share_bucket,
            "single_source": co.single_source,
            "moat_types": co.moat_types,
            "switching_costs": co.switching_costs,
            "demand_signal": co.demand_signal,
            "structure": ex.structure,
            "supply_status": ex.supply_status,
            "thesis_summary": _no_advice(ex.thesis_summary),
            "risks": [r for r in ex.risks if not _ADVICE.match(r)],
            "catalysts": [c for c in ex.catalysts if not _ADVICE.match(c)],
            # Demo evidence has no URLs and some advice-style wording; publish none.
            "evidence": [],
            "signals": [
                {k: s.get(k) for k in ("category", "headline", "direction", "note")}
                for s in ex.intelligence_signals
            ],
        })
    return {
        "run_date": run_date,
        "summary": ("Sample output from the offline demo mode (deterministic mock agents, "
                    "no web research). The weekly Claude routine replaces it with cited research."),
        "themes": [],
        "components": components,
        "companies": companies,
    }


def main() -> int:
    settings = get_settings()
    with tempfile.TemporaryDirectory() as tmp:
        pipeline = Pipeline(settings=settings,
                            llm_factory=lambda: get_provider("mock", mock=True))
        result = pipeline.run(RunOptions(provider="mock", model=None, mock=True, output_dir=Path(tmp)))
        view = RunRepository(Path(result.db_path)).get_view(result.run_id)
    run_date = "2026-11-08"
    research = run_to_research(view, run_date)
    payload = build_site_payload(research, sample=True, generated_by="offline-demo")
    for p in write_site_data(payload, ROOT / "docs" / "data"):
        print(f"wrote {p.relative_to(ROOT)}")
    example = ROOT / "routines" / "example-research.json"
    example.write_text(json.dumps(clean_text(research), indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
    print(f"wrote {example.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
