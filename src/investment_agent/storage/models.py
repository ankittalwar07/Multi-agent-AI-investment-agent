"""Pydantic view models — what the Streamlit layer consumes."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RunRow(BaseModel):
    id: str
    started_at: datetime
    finished_at: datetime | None = None
    provider: str
    model: str | None = None
    mock: bool = False
    cost_usd: float = 0.0
    status: str
    error: str | None = None


class ComponentRow(BaseModel):
    id: str
    run_id: str
    name: str
    category: str | None = None
    description: str | None = None
    source: str
    status: str


class EvidenceRow(BaseModel):
    id: int
    company_id: str
    claim: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    retrieved_at: datetime | None = None
    snippet: str | None = None
    snippet_hash: str | None = None
    tool_name: str | None = None


class ScoreRow(BaseModel):
    company_id: str
    sole_source_pts: float = 0
    share_pts: float = 0
    ip_pts: float = 0
    regulatory_pts: float = 0
    switching_pts: float = 0
    demand_pts: float = 0
    composite: float | None = None
    rubric_version: str | None = None
    rationale: str | None = None


class CompanyExtras(BaseModel):
    """Investor-grade financials, analyst consensus, and our recommendation.

    All fields optional — real LLM runs may not populate everything.
    """
    # Market structure
    structure: str | None = None  # monopoly | duopoly | oligopoly | fragmented
    supply_status: str | None = None  # constrained | balanced | oversupply

    # Stock / valuation (public companies only)
    stock_price: float | None = None
    currency: str = "USD"
    market_cap_usd: float | None = None
    pe_trailing: float | None = None
    pe_forward: float | None = None
    peg: float | None = None
    ev_ebitda: float | None = None
    ev_sales: float | None = None
    revenue_growth_ttm: float | None = None
    revenue_growth_fwd: float | None = None
    operating_margin: float | None = None
    fcf_yield: float | None = None
    dividend_yield: float | None = None
    beta: float | None = None
    week52_high: float | None = None
    week52_low: float | None = None

    # Analyst consensus
    analyst_buy: int | None = None
    analyst_hold: int | None = None
    analyst_sell: int | None = None
    price_target_low: float | None = None
    price_target_avg: float | None = None
    price_target_high: float | None = None

    # Our recommendation
    recommendation: str | None = None  # STRONG_BUY | BUY | HOLD | SELL | STRONG_SELL
    conviction: str | None = None  # HIGH | MEDIUM | LOW
    expected_return_12m: float | None = None  # e.g. 0.25 = +25%
    bull_target: float | None = None
    base_target: float | None = None
    bear_target: float | None = None

    # Narrative
    thesis_summary: str | None = None
    thesis_points: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    catalysts: list[str] = Field(default_factory=list)


class CompanyRow(BaseModel):
    id: str
    run_id: str
    component_id: str
    name: str
    is_public: bool | None = None
    ticker: str | None = None
    hq_country: str | None = None
    market_share_pct: float | None = None
    market_share_bucket: str | None = None
    single_source: bool | None = None
    moat_types: list[str] = Field(default_factory=list)
    switching_costs: str | None = None
    customer_concentration: str | None = None
    demand_signal: str | None = None
    valuation_usd: float | None = None
    notes: str | None = None
    extras: CompanyExtras = Field(default_factory=CompanyExtras)
    score: ScoreRow | None = None
    evidence: list[EvidenceRow] = Field(default_factory=list)


class RunEvent(BaseModel):
    id: int
    run_id: str
    ts: datetime
    level: str
    node: str | None = None
    message: str | None = None


class RunView(BaseModel):
    run: RunRow
    components: list[ComponentRow] = Field(default_factory=list)
    companies: list[CompanyRow] = Field(default_factory=list)
    events: list[RunEvent] = Field(default_factory=list)
