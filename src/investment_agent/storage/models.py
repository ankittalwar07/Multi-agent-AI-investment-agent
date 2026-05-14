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

    # Earnings power & balance sheet (Pass 1)
    roic: float | None = None                   # e.g. 0.45 = 45%
    roic_5y_avg: float | None = None
    roic_trend: str | None = None               # "improving" | "stable" | "declining"
    wacc: float | None = None
    net_debt_usd: float | None = None           # negative = net cash
    debt_to_ebitda: float | None = None
    interest_coverage: float | None = None
    current_ratio: float | None = None
    capex_to_sales: float | None = None
    capex_guidance_trend: str | None = None     # "raising" | "stable" | "cutting"
    fcf_margin_after_capex: float | None = None
    rd_to_sales: float | None = None
    rd_trend: str | None = None
    buyback_yield: float | None = None
    total_shareholder_yield: float | None = None

    # Risk & sentiment (Pass 2)
    top_1_customer_pct: float | None = None      # 0.40 = top customer = 40% of revenue
    top_3_customer_pct: float | None = None
    top_10_customer_pct: float | None = None
    china_revenue_pct: float | None = None
    geographic_mix: dict | None = None           # {"US": 0.6, "China": 0.15, ...}
    hyperscaler_capex_beta: float | None = None  # rev beta to MSFT+GOOGL+AMZN+META capex
    ai_revenue_pct: float | None = None          # % of revenue tied to AI/datacenter
    insider_net_buying_6m_usd: float | None = None   # positive = net insider buying
    short_interest_pct: float | None = None      # 0.05 = 5% of float
    days_to_cover: float | None = None
    eps_revisions_3m_pct: float | None = None    # 0.05 = +5% revisions over 90 days
    analyst_revisions_up: int | None = None
    analyst_revisions_down: int | None = None
    institutional_ownership_pct: float | None = None

    # Scenario math (Pass 3)
    bull_probability: float | None = None       # e.g. 0.25
    base_probability: float | None = None       # e.g. 0.50
    bear_probability: float | None = None       # e.g. 0.25
    probability_weighted_return: float | None = None
    short_term_catalysts: list[str] = Field(default_factory=list)
    medium_term_thesis: list[str] = Field(default_factory=list)
    long_term_thesis: list[str] = Field(default_factory=list)
    exit_triggers: list[str] = Field(default_factory=list)
    # DCF assumption defaults — let the UI seed the sliders
    dcf_growth_y1_y5: float | None = None       # CAGR through Y5
    dcf_terminal_margin: float | None = None    # year-5 op margin
    dcf_terminal_multiple: float | None = None  # terminal P/E
    dcf_wacc: float | None = None
    dcf_fair_value: float | None = None         # baseline fair value computed at our inputs

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

    # Investor council (filled by the post-scoring council pass)
    council_verdicts: list[dict] = Field(default_factory=list)
    council_summary: dict = Field(default_factory=dict)


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
