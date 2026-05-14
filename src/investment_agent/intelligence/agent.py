"""Intelligence Agent — fetches signals + aggregates an intelligence score.

Algorithm (deterministic — runs the same way in Demo + live):
  1. For each company, fetch IntelligenceSignal records from sources.
     In Demo mode we read from the INTELLIGENCE patch in mock_data.py.
     In live runs the LLM provider plus web_search/web_fetch tools populates them.
  2. Aggregate into an IntelligenceSummary:
       - bullish_count / bearish_count
       - composite intelligence_score in [-100, +100]
       - per-category roll-ups (gov investment $, politicians net buying $, ...)
  3. Returned object is JSON-serializable and persisted alongside other extras.

Scoring weights (per signal):
  us_gov_investment, foreign_gov_activity: weighted by amount + direction
  federal_contract: small weight (background revenue confirmation)
  congressional_trade: small weight (sentiment signal, not predictive on its own)
  policy_headwind: heavily bearish (Entity List = -30)
  form4_insider: medium (CEO cluster buy = +5 to +10)
"""
from __future__ import annotations

from dataclasses import dataclass

from .signals import IntelligenceSignal, IntelligenceSummary


CATEGORY_BASE_WEIGHT = {
    "us_gov_investment": 1.5,
    "federal_contract": 0.6,
    "congressional_trade": 0.4,
    "foreign_gov_activity": 1.0,
    "policy_headwind": 2.0,         # punishes hard
    "form4_insider": 0.8,
}


def _amount_weight(amount_usd: float | None) -> float:
    """Money-amount weight: $0 -> 0, $1M -> ~0.3, $1B -> ~1.5, $10B -> ~3."""
    if not amount_usd or amount_usd <= 0:
        return 0
    import math
    return min(3.0, max(0.0, math.log10(amount_usd / 1_000_000) * 0.5))


def score_signal(s: IntelligenceSignal) -> float:
    """Per-signal contribution to the composite score, in [-30, +30]."""
    sign = {"bullish": 1, "bearish": -1, "neutral": 0}[s.direction]
    base = CATEGORY_BASE_WEIGHT.get(s.category, 0.5)
    # Amount-weighted on the relevant categories
    amt = _amount_weight(s.amount_usd) if s.category in (
        "us_gov_investment", "federal_contract", "foreign_gov_activity"
    ) else 1.0
    return sign * (s.weight * 4.0) * base * amt


def summarize(signals: list[IntelligenceSignal]) -> IntelligenceSummary:
    """Aggregate signals into a summary record."""
    if not signals:
        return IntelligenceSummary()

    raw_score = sum(score_signal(s) for s in signals)
    # Squash to [-100, +100]
    composite = max(-100.0, min(100.0, raw_score))

    summary = IntelligenceSummary(
        total_signals=len(signals),
        bullish_count=sum(1 for s in signals if s.direction == "bullish"),
        bearish_count=sum(1 for s in signals if s.direction == "bearish"),
        intelligence_score=composite,
    )

    pols_buy = pols_sell = 0
    pols_net = 0.0
    notable: list[str] = []

    for s in signals:
        amt = s.amount_usd or 0
        if s.category == "us_gov_investment":
            summary.us_gov_total_usd += amt
            summary.policy_tailwinds.append(s.headline)
        elif s.category == "federal_contract":
            summary.federal_contract_total_usd += amt
        elif s.category == "foreign_gov_activity":
            summary.foreign_gov_total_usd += amt
            if s.direction == "bullish":
                summary.policy_tailwinds.append(s.headline)
        elif s.category == "policy_headwind":
            summary.policy_headwinds.append(s.headline)
        elif s.category == "congressional_trade":
            if s.direction == "bullish":
                pols_buy += 1
                pols_net += amt
            elif s.direction == "bearish":
                pols_sell += 1
                pols_net -= amt
            if s.counterparty and s.counterparty not in notable:
                notable.append(s.counterparty)

    summary.politicians_buying_count = pols_buy
    summary.politicians_selling_count = pols_sell
    summary.politicians_net_value_usd = pols_net
    summary.notable_politicians = notable[:6]
    return summary


# ---------------- agent entry point ----------------

@dataclass
class IntelligenceAgent:
    """Fetches signals per company. In Demo mode, reads from a pre-supplied dict.

    For live runs, you'd inject a `sources` connector that calls USAspending,
    Senate EFD, etc. Kept thin so the same agent class works in both paths.
    """

    demo_signals_by_company: dict[str, list[dict]] | None = None

    def fetch(self, company_name: str, ticker: str | None = None) -> list[IntelligenceSignal]:
        if self.demo_signals_by_company and company_name in self.demo_signals_by_company:
            raw = self.demo_signals_by_company[company_name]
            return [IntelligenceSignal.model_validate(r) for r in raw]
        # In a real run we'd dispatch to live connectors here.
        return []


def run_intelligence(
    company_name: str,
    ticker: str | None = None,
    *,
    demo_data: dict[str, list[dict]] | None = None,
) -> tuple[list[IntelligenceSignal], IntelligenceSummary]:
    agent = IntelligenceAgent(demo_signals_by_company=demo_data)
    signals = agent.fetch(company_name, ticker)
    summary = summarize(signals)
    return signals, summary
