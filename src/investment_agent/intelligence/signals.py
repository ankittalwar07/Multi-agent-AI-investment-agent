"""Intelligence signal types."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SignalCategory = Literal[
    "us_gov_investment",      # CHIPS Act, DPA, DoE LPO, etc.
    "federal_contract",       # DoD, DARPA, NSF, NTIA awards
    "congressional_trade",    # STOCK Act disclosures
    "foreign_gov_activity",   # China Big Fund, Saudi PIF, EU Chips Act, etc.
    "policy_headwind",        # BIS Entity List, CFIUS, export controls
    "form4_insider",          # SEC Form 4 cluster buys
]


class IntelligenceSignal(BaseModel):
    """One signal: a single CHIPS Act award, congressional trade, contract, etc."""
    category: SignalCategory
    headline: str                          # short human-readable summary
    counterparty: str | None = None        # e.g. "US Dept of Commerce", "Nancy Pelosi", "China Big Fund III"
    amount_usd: float | None = None        # dollar value
    direction: Literal["bullish", "bearish", "neutral"] = "neutral"
    weight: float = 1.0                    # 0-5 importance weight (CHIPS Act = 5, single Pelosi trade = 1)
    date: datetime | None = None
    source_url: str | None = None
    source_name: str | None = None         # e.g. "USAspending.gov", "Senate EFD"
    note: str | None = None


class IntelligenceSummary(BaseModel):
    """Aggregated view across all signals for one company."""
    total_signals: int = 0
    bullish_count: int = 0
    bearish_count: int = 0
    intelligence_score: float = 0.0        # -100 to +100
    # Per-category roll-ups for the UI:
    us_gov_total_usd: float = 0.0
    federal_contract_total_usd: float = 0.0
    foreign_gov_total_usd: float = 0.0
    politicians_buying_count: int = 0
    politicians_selling_count: int = 0
    politicians_net_value_usd: float = 0.0
    notable_politicians: list[str] = Field(default_factory=list)
    policy_tailwinds: list[str] = Field(default_factory=list)
    policy_headwinds: list[str] = Field(default_factory=list)
