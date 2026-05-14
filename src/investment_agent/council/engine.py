"""Apply every council persona to a company and return their verdicts."""
from __future__ import annotations

from typing import Any

from .personas import COUNCIL, BY_KEY
from .rubrics import RUBRICS, apply_rubric
from .verdicts import InvestorVerdict


def company_to_view(
    finding: Any,
    score_obj: Any,
    component_name: str,
) -> dict:
    """Flatten a ScoredCompany into the dict shape rubrics expect."""
    e = finding.extras or {}
    return {
        "name": finding.name,
        "ticker": finding.ticker,
        "is_public": finding.is_public,
        "component": component_name,
        "market_share_pct": finding.market_share_pct,
        "market_share_bucket": finding.market_share_bucket,
        "single_source": finding.single_source,
        "demand_signal": finding.demand_signal,
        "valuation_usd": finding.valuation_usd,
        "composite": score_obj.composite if score_obj else 0,
        # Extras (financials, structure, recommendations)
        "structure": e.get("structure") if isinstance(e, dict) else getattr(e, "structure", None),
        "supply_status": e.get("supply_status") if isinstance(e, dict) else getattr(e, "supply_status", None),
        "stock_price": e.get("stock_price") if isinstance(e, dict) else getattr(e, "stock_price", None),
        "market_cap_usd": e.get("market_cap_usd") if isinstance(e, dict) else getattr(e, "market_cap_usd", None),
        "pe_trailing": e.get("pe_trailing") if isinstance(e, dict) else getattr(e, "pe_trailing", None),
        "pe_forward": e.get("pe_forward") if isinstance(e, dict) else getattr(e, "pe_forward", None),
        "peg": e.get("peg") if isinstance(e, dict) else getattr(e, "peg", None),
        "ev_ebitda": e.get("ev_ebitda") if isinstance(e, dict) else getattr(e, "ev_ebitda", None),
        "revenue_growth_ttm": e.get("revenue_growth_ttm") if isinstance(e, dict) else getattr(e, "revenue_growth_ttm", None),
        "revenue_growth_fwd": e.get("revenue_growth_fwd") if isinstance(e, dict) else getattr(e, "revenue_growth_fwd", None),
        "operating_margin": e.get("operating_margin") if isinstance(e, dict) else getattr(e, "operating_margin", None),
        "fcf_yield": e.get("fcf_yield") if isinstance(e, dict) else getattr(e, "fcf_yield", None),
        "dividend_yield": e.get("dividend_yield") if isinstance(e, dict) else getattr(e, "dividend_yield", None),
        "expected_return_12m": e.get("expected_return_12m") if isinstance(e, dict) else getattr(e, "expected_return_12m", None),
        # Earnings power (Pass 1) — needed by Buffett/Munger ROIC-anchored rubrics
        "roic": e.get("roic") if isinstance(e, dict) else getattr(e, "roic", None),
        "roic_5y_avg": e.get("roic_5y_avg") if isinstance(e, dict) else getattr(e, "roic_5y_avg", None),
        "roic_trend": e.get("roic_trend") if isinstance(e, dict) else getattr(e, "roic_trend", None),
        "wacc": e.get("wacc") if isinstance(e, dict) else getattr(e, "wacc", None),
        "net_debt_usd": e.get("net_debt_usd") if isinstance(e, dict) else getattr(e, "net_debt_usd", None),
        "debt_to_ebitda": e.get("debt_to_ebitda") if isinstance(e, dict) else getattr(e, "debt_to_ebitda", None),
        "interest_coverage": e.get("interest_coverage") if isinstance(e, dict) else getattr(e, "interest_coverage", None),
        "capex_to_sales": e.get("capex_to_sales") if isinstance(e, dict) else getattr(e, "capex_to_sales", None),
        "capex_guidance_trend": e.get("capex_guidance_trend") if isinstance(e, dict) else getattr(e, "capex_guidance_trend", None),
        "fcf_margin_after_capex": e.get("fcf_margin_after_capex") if isinstance(e, dict) else getattr(e, "fcf_margin_after_capex", None),
        "rd_to_sales": e.get("rd_to_sales") if isinstance(e, dict) else getattr(e, "rd_to_sales", None),
        "total_shareholder_yield": e.get("total_shareholder_yield") if isinstance(e, dict) else getattr(e, "total_shareholder_yield", None),
        # Risk & sentiment (Pass 2)
        "top_1_customer_pct": e.get("top_1_customer_pct") if isinstance(e, dict) else getattr(e, "top_1_customer_pct", None),
        "top_3_customer_pct": e.get("top_3_customer_pct") if isinstance(e, dict) else getattr(e, "top_3_customer_pct", None),
        "china_revenue_pct": e.get("china_revenue_pct") if isinstance(e, dict) else getattr(e, "china_revenue_pct", None),
        "hyperscaler_capex_beta": e.get("hyperscaler_capex_beta") if isinstance(e, dict) else getattr(e, "hyperscaler_capex_beta", None),
        "ai_revenue_pct": e.get("ai_revenue_pct") if isinstance(e, dict) else getattr(e, "ai_revenue_pct", None),
        "insider_net_buying_6m_usd": e.get("insider_net_buying_6m_usd") if isinstance(e, dict) else getattr(e, "insider_net_buying_6m_usd", None),
        "short_interest_pct": e.get("short_interest_pct") if isinstance(e, dict) else getattr(e, "short_interest_pct", None),
        "eps_revisions_3m_pct": e.get("eps_revisions_3m_pct") if isinstance(e, dict) else getattr(e, "eps_revisions_3m_pct", None),
        "analyst_revisions_up": e.get("analyst_revisions_up") if isinstance(e, dict) else getattr(e, "analyst_revisions_up", None),
        "analyst_revisions_down": e.get("analyst_revisions_down") if isinstance(e, dict) else getattr(e, "analyst_revisions_down", None),
        "intelligence_summary": e.get("intelligence_summary") if isinstance(e, dict) else getattr(e, "intelligence_summary", None),
    }


def run_council(company_view: dict) -> list[InvestorVerdict]:
    """Apply every council member's rubric to one company."""
    verdicts: list[InvestorVerdict] = []
    for persona in COUNCIL:
        v = apply_rubric(persona.key, company_view)
        v.investor_name = persona.name
        verdicts.append(v)
    return verdicts


def council_summary(verdicts: list[InvestorVerdict]) -> dict:
    """Aggregate stats for a company's council verdicts."""
    score_sum = sum(v.score for v in verdicts)
    buy_count = sum(1 for v in verdicts if v.verdict in ("STRONG_BUY", "BUY"))
    strong_buy_count = sum(1 for v in verdicts if v.verdict == "STRONG_BUY")
    avoid_count = sum(1 for v in verdicts if v.verdict in ("AVOID", "PASS"))
    high_conv_buy = sum(
        1 for v in verdicts
        if v.verdict in ("STRONG_BUY", "BUY") and v.conviction == "HIGH"
    )
    n = len(verdicts) or 1
    return {
        "n_members": len(verdicts),
        "score_sum": score_sum,           # -2n to +2n
        "score_pct": (score_sum / (2 * n)) * 100,  # -100 to +100
        "buy_count": buy_count,
        "strong_buy_count": strong_buy_count,
        "avoid_count": avoid_count,
        "high_conviction_buy_count": high_conv_buy,
        "unanimous_buy": buy_count == len(verdicts),
        "consensus": _consensus_label(verdicts),
    }


def _consensus_label(verdicts: list[InvestorVerdict]) -> str:
    n = len(verdicts) or 1
    buy_pct = sum(1 for v in verdicts if v.verdict in ("STRONG_BUY", "BUY")) / n
    sb_pct = sum(1 for v in verdicts if v.verdict == "STRONG_BUY") / n
    avoid_pct = sum(1 for v in verdicts if v.verdict in ("PASS", "AVOID")) / n
    if sb_pct >= 0.66:
        return "UNANIMOUS_STRONG_BUY"
    if buy_pct >= 0.83:
        return "UNANIMOUS_BUY"
    if buy_pct >= 0.5:
        return "MAJORITY_BUY"
    if avoid_pct >= 0.66:
        return "MAJORITY_AVOID"
    return "DIVIDED"


CONSENSUS_LABELS = {
    "UNANIMOUS_STRONG_BUY": "Unanimous STRONG BUY",
    "UNANIMOUS_BUY": "Unanimous BUY",
    "MAJORITY_BUY": "Majority BUY",
    "MAJORITY_AVOID": "Majority PASS / AVOID",
    "DIVIDED": "Divided council",
}

CONSENSUS_COLORS = {
    "UNANIMOUS_STRONG_BUY": "#16a34a",
    "UNANIMOUS_BUY": "#22c55e",
    "MAJORITY_BUY": "#84cc16",
    "MAJORITY_AVOID": "#dc2626",
    "DIVIDED": "#64748b",
}
