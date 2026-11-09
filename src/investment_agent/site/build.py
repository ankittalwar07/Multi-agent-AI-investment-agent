"""Build the static dashboard data from a research file (pure Python, no LLM).

The research file is what the LLM side of the pipeline produces: components, and
per component the companies with their facts and cited evidence. It can come from
the weekly Claude routine (routines/weekly-market-map.md), where Claude itself plays
the Decomposer and Component Researcher agents, or from the offline demo run
(scripts/export_demo_data.py).

Everything after research is deterministic and lives in this repo:

* the moat rubric (scoring/moat_rubric.py) scores each company 0 to 100, and only
  credits sole-source status when at least two independent domains back it;
* the investor council (council/) runs nine rule-based investor rubrics per company;
* this module ranks the companies and writes docs/data/*.json for the UI.

So the numbers on the dashboard can be re-derived from the research file by anyone.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ..council.engine import council_summary
from ..council.personas import COUNCIL
from ..council.rubrics import apply_rubric
from ..scoring.moat_rubric import RUBRIC_VERSION, score_company

SCHEMA_VERSION = 1
HISTORY_KEEP = 26  # about six months of weekly runs

SHARE_BUCKETS = {"<10", "10-25", "25-50", "50-75", ">75", "sole"}

# Optional financial fields the council rubrics read. The routine may fill any of
# them, but only with values taken from a source it opened.
FINANCIAL_FIELDS = (
    "market_cap_usd", "pe_trailing", "pe_forward", "peg", "ev_ebitda",
    "revenue_growth_ttm", "revenue_growth_fwd", "operating_margin", "fcf_yield",
    "dividend_yield", "roic", "roic_5y_avg", "roic_trend", "wacc", "net_debt_usd",
    "debt_to_ebitda", "interest_coverage", "capex_to_sales", "capex_guidance_trend",
    "fcf_margin_after_capex", "rd_to_sales", "total_shareholder_yield",
    "top_1_customer_pct", "top_3_customer_pct", "china_revenue_pct",
    "ai_revenue_pct", "short_interest_pct", "eps_revisions_3m_pct",
    "stock_price", "expected_return_12m", "hyperscaler_capex_beta",
    "insider_net_buying_6m_usd", "analyst_revisions_up", "analyst_revisions_down",
)

_DASHES = re.compile(r"\s*[\u2012\u2013\u2014\u2015\u2212]\s*")
_SLUG = re.compile(r"[^a-z0-9]+")


def clean_text(value: Any) -> Any:
    """House style: no em or en dashes in published text. Recurses into lists/dicts."""
    if isinstance(value, str):
        out = _DASHES.sub(", ", value).strip()
        return out.replace(" ,", ",").replace(",,", ",")
    if isinstance(value, list):
        return [clean_text(v) for v in value]
    if isinstance(value, dict):
        return {k: clean_text(v) for k, v in value.items()}
    return value


def slugify(text: str) -> str:
    return _SLUG.sub("-", (text or "").lower()).strip("-") or "item"


def _domain(url: str | None) -> str | None:
    if not url or not url.startswith("https://"):
        return None
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host or None


def _evidence(raw: list[dict] | None) -> list[dict]:
    out = []
    for e in raw or []:
        url = e.get("source_url")
        if url and not str(url).startswith("https://"):
            url = None
        out.append({
            "claim": e.get("claim") or "",
            "source_url": url,
            "source_name": e.get("source_name") or (_domain(url) if url else "unsourced"),
        })
    return out


def _council_view(c: dict, component_name: str, composite: float) -> dict:
    fin = c.get("financials") or {}
    view = {
        "name": c.get("name"),
        "ticker": c.get("ticker"),
        "is_public": c.get("is_public"),
        "hq_country": c.get("hq_country"),
        "customer_concentration": c.get("customer_concentration"),
        "component": component_name,
        "market_share_pct": c.get("market_share_pct"),
        "market_share_bucket": c.get("market_share_bucket"),
        "single_source": c.get("single_source"),
        "demand_signal": c.get("demand_signal"),
        "valuation_usd": c.get("valuation_usd"),
        "composite": composite,
        "structure": c.get("structure"),
        "supply_status": c.get("supply_status"),
        "intelligence_summary": None,
    }
    for f in FINANCIAL_FIELDS:
        view[f] = fin.get(f)
    return view


def build_site_payload(research: dict, *, sample: bool = False,
                       generated_by: str = "claude-routine") -> dict:
    """Score, run the council, rank, and return the dashboard payload."""
    components = []
    comp_names: dict[str, str] = {}
    for comp in research.get("components", []):
        cid = comp.get("id") or slugify(comp.get("name", ""))
        comp_names[cid] = comp.get("name", cid)
        components.append({
            "id": cid,
            "name": comp.get("name", cid),
            "category": comp.get("category") or "other",
            "description": comp.get("description") or "",
        })

    companies = []
    for c in research.get("companies", []):
        cid = c.get("component_id")
        if cid not in comp_names:
            continue
        evidence = _evidence(c.get("evidence"))
        domains = {d for d in (_domain(e["source_url"]) for e in evidence) if d}
        bucket = c.get("market_share_bucket")
        if bucket not in SHARE_BUCKETS:
            bucket = None
        ms = score_company(
            single_source=bool(c.get("single_source")),
            independent_citations_for_sole_source=len(domains),
            market_share_bucket=bucket,
            moat_types=c.get("moat_types") or [],
            switching_costs=c.get("switching_costs"),
            demand_signal=c.get("demand_signal"),
        )
        view = _council_view(c, comp_names[cid], ms.composite)
        verdicts = []
        for persona in COUNCIL:
            v = apply_rubric(persona.key, view)
            v.investor_name = persona.name
            verdicts.append(v)
        summary = council_summary(verdicts)
        signals = []
        for s in c.get("signals") or []:
            url = s.get("source_url")
            signals.append({
                "category": s.get("category") or "other",
                "headline": s.get("headline") or "",
                "direction": s.get("direction") or "neutral",
                "note": s.get("note") or "",
                "source_url": url if url and str(url).startswith("https://") else None,
            })
        companies.append({
            "id": c.get("id") or f"{cid}--{slugify(c.get('name', ''))}",
            "name": c.get("name"),
            "ticker": c.get("ticker") or None,
            "is_public": c.get("is_public"),
            "hq_country": c.get("hq_country"),
            "component_id": cid,
            "market_share_bucket": bucket,
            "single_source_claimed": bool(c.get("single_source")),
            "single_source_credited": ms.sole_source_pts > 0,
            "independent_domains": len(domains),
            "moat_types": c.get("moat_types") or [],
            "switching_costs": c.get("switching_costs"),
            "demand_signal": c.get("demand_signal"),
            "structure": c.get("structure"),
            "supply_status": c.get("supply_status"),
            "thesis_summary": c.get("thesis_summary"),
            "risks": c.get("risks") or [],
            "catalysts": c.get("catalysts") or [],
            "score": {
                "composite": ms.composite,
                "breakdown": {
                    "sole_source": ms.sole_source_pts,
                    "share": ms.share_pts,
                    "ip": ms.ip_pts,
                    "regulatory": ms.regulatory_pts,
                    "switching": ms.switching_pts,
                    "demand": ms.demand_pts,
                },
                "rationale": ms.rationale,
            },
            "council": {
                "consensus": summary["consensus"],
                "score_pct": round(summary["score_pct"], 1),
                "buy_count": summary["buy_count"],
                "avoid_count": summary["avoid_count"],
                "n_members": summary["n_members"],
                "verdicts": [
                    {
                        "investor": v.investor_name,
                        "verdict": v.verdict,
                        "conviction": v.conviction,
                        "reason": (v.reasoning or [""])[0],
                        "top_concern": v.top_concern,
                    }
                    for v in verdicts
                ],
            },
            "signals": signals,
            "evidence": evidence,
        })

    companies.sort(key=lambda x: (-x["score"]["composite"], x["name"] or ""))
    for i, c in enumerate(companies, start=1):
        c["rank"] = i

    run_date = research.get("run_date") or date.today().isoformat()
    cited = {e["source_url"] for c in companies for e in c["evidence"] if e["source_url"]}
    payload = {
        "schema_version": SCHEMA_VERSION,
        "sample": sample,
        "generated_by": generated_by,
        "run_date": run_date,
        "rubric_version": RUBRIC_VERSION,
        "summary": research.get("summary") or "",
        "themes": research.get("themes") or [],
        "stats": {
            "components": len(components),
            "companies": len(companies),
            "sole_source_credited": sum(1 for c in companies if c["single_source_credited"]),
            "cited_sources": len(cited),
        },
        "components": components,
        "companies": companies,
    }
    return clean_text(payload)


def write_site_data(payload: dict, out_dir: Path) -> list[Path]:
    """Write latest.json plus a dated history entry and the history index."""
    out_dir = Path(out_dir)
    hist = out_dir / "history"
    hist.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    latest = out_dir / "latest.json"
    latest.write_text(text, encoding="utf-8")
    dated = hist / f"{payload['run_date']}.json"
    dated.write_text(text, encoding="utf-8")

    entries = []
    for p in sorted(hist.glob("????-??-??.json"), reverse=True):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        top = d.get("companies", [])[:3]
        entries.append({
            "run_date": d.get("run_date", p.stem),
            "file": f"history/{p.name}",
            "sample": bool(d.get("sample")),
            "companies": d.get("stats", {}).get("companies", 0),
            "top": [c.get("name") for c in top],
        })
    for old in entries[HISTORY_KEEP:]:
        (out_dir / old["file"]).unlink(missing_ok=True)
    entries = entries[:HISTORY_KEEP]
    index = out_dir / "history" / "index.json"
    index.write_text(json.dumps({"runs": entries}, indent=2, ensure_ascii=False) + "\n",
                     encoding="utf-8")
    return [latest, dated, index]
