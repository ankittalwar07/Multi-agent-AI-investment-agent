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
