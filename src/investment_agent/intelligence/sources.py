"""Data source documentation + connectors for the Intelligence Agent.

Every source here is documented with: what it provides, how to access (URL +
API key requirement), and rate limits. The fetch functions are stubs in this
prototype — they return None unless an API key / connector is wired in. Live
runs against Claude/Gemini can call these via the WebSearch + WebFetch tools
to populate the same IntelligenceSignal shape.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class DataSource:
    name: str
    url: str
    category: str          # "free_api" | "free_scrape" | "paid_api" | "paid_data"
    auth: str              # "none" | "env:VAR_NAME" | "paid"
    description: str


# ---- Catalogue of sources the Intelligence Agent can use ----
SOURCES: list[DataSource] = [
    DataSource(
        name="USAspending.gov",
        url="https://api.usaspending.gov/api/v2/search/spending_by_award/",
        category="free_api",
        auth="none",
        description=(
            "All US federal contract awards + grants since 2008. POST a JSON "
            "body with `recipient_name` filter to get awards per company. "
            "Maps directly to `federal_contract` signals."
        ),
    ),
    DataSource(
        name="DoD Contract Announcements",
        url="https://www.defense.gov/News/Contracts/",
        category="free_scrape",
        auth="none",
        description=(
            "Daily-posted Defense Department contracts >$7.5M. Plain HTML; "
            "scrape with WebFetch + parse for company names and values."
        ),
    ),
    DataSource(
        name="Senate EFD Search",
        url="https://efdsearch.senate.gov/search/",
        category="free_scrape",
        auth="none",
        description=(
            "Senate Periodic Transaction Reports (STOCK Act). POST form with "
            "filter_type=PT to search ALL Senate financial disclosures. "
            "45-day filing window after each trade. Captures `congressional_trade`."
        ),
    ),
    DataSource(
        name="House Clerk Disclosures",
        url="https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure",
        category="free_scrape",
        auth="none",
        description=(
            "House Periodic Transaction Reports. PDFs require parsing. "
            "Alternative: house-stock-watcher.com aggregates a clean JSON dump."
        ),
    ),
    DataSource(
        name="Quiver Quantitative",
        url="https://api.quiverquant.com/",
        category="free_api",
        auth="env:QUIVER_API_KEY",
        description=(
            "Aggregates Senate + House trades, government contracts, lobbying. "
            "Free tier: 10 requests/day. Set QUIVER_API_KEY env var to enable."
        ),
    ),
    DataSource(
        name="Capitol Trades",
        url="https://www.capitoltrades.com/",
        category="free_scrape",
        auth="none",
        description="Clean front-end for STOCK Act disclosures. Easy to scrape per ticker.",
    ),
    DataSource(
        name="SEC EDGAR Form 4",
        url="https://www.sec.gov/cgi-bin/browse-edgar",
        category="free_api",
        auth="none",
        description=(
            "Corporate insider transactions (CEOs, directors, officers). "
            "GET ?action=getcompany&CIK={cik}&type=4&dateb=&owner=include "
            "&count=40. Parse XML/HTML for transaction details."
        ),
    ),
    DataSource(
        name="OpenInsider",
        url="http://openinsider.com/screener",
        category="free_scrape",
        auth="none",
        description=(
            "Aggregates SEC Form 4 with cluster-buy flags. Best free source "
            "for identifying coordinated insider activity."
        ),
    ),
    DataSource(
        name="BIS Entity List",
        url="https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern/entity-list",
        category="free_scrape",
        auth="none",
        description=(
            "Federal Register publishes additions/removals. Companies on the "
            "list are barred from receiving US exports without a license. "
            "Captures `policy_headwind`."
        ),
    ),
    DataSource(
        name="DoC CHIPS Act announcements",
        url="https://www.commerce.gov/news/press-releases",
        category="free_scrape",
        auth="none",
        description=(
            "Press releases for each CHIPS Act preliminary memorandum of "
            "terms (PMT) and definitive award. Plain text; easy to extract "
            "company + amount."
        ),
    ),
    DataSource(
        name="Bloomberg Terminal",
        url="bloomberg://",
        category="paid_data",
        auth="paid",
        description=(
            "Most comprehensive for sovereign flows + Big Fund tracking. "
            "Required for institutional-grade China coverage."
        ),
    ),
    DataSource(
        name="FactSet Government Edge",
        url="https://www.factset.com/",
        category="paid_data",
        auth="paid",
        description=(
            "Government contract + lobbying + congressional trade dataset, "
            "structured and back-tested."
        ),
    ),
]


def available_sources() -> list[DataSource]:
    """Return sources that are usable in this environment (free or have keys set)."""
    out = []
    for s in SOURCES:
        if s.auth == "none":
            out.append(s); continue
        if s.auth.startswith("env:"):
            var = s.auth.split(":", 1)[1]
            if os.environ.get(var):
                out.append(s)
    return out


def source_status() -> list[dict]:
    """Status table for the UI: which sources are connected."""
    rows = []
    for s in SOURCES:
        connected = False
        reason = ""
        if s.auth == "none":
            connected = True
            reason = "Free public source"
        elif s.auth.startswith("env:"):
            var = s.auth.split(":", 1)[1]
            if os.environ.get(var):
                connected = True
                reason = f"{var} configured"
            else:
                reason = f"Set {var} to enable"
        else:
            reason = "Requires paid subscription"
        rows.append({
            "Source": s.name,
            "Category": s.category,
            "URL": s.url,
            "Status": ":white_check_mark: connected" if connected else ":lock: gated",
            "Note": reason,
        })
    return rows
