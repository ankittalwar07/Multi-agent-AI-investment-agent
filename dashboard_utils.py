"""Dashboard helpers: investor-grade tables, badges, and plotly charts."""
from __future__ import annotations

from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from design import plotly_layout_dark
from investment_agent.storage.models import CompanyRow, RunView


def _polish(fig: go.Figure, **overrides) -> go.Figure:
    """Apply the shared dark layout to any plotly figure for consistency."""
    layout = plotly_layout_dark()
    layout.update(overrides)
    fig.update_layout(**layout)
    return fig


# ---------------------- recommendation logic ----------------------

REC_ORDER = ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL", "PASS", "AVOID", "N/A", "SEE_TSM"]
REC_COLORS = {
    "STRONG_BUY": "#059669",   # emerald-600
    "BUY": "#10b981",          # emerald-500
    "HOLD": "#a16207",         # amber-700
    "SELL": "#c2410c",         # orange-700
    "STRONG_SELL": "#be123c",  # rose-800
    "PASS": "#475569",         # slate-600
    "AVOID": "#9f1239",        # rose-900
    "N/A": "#475569",
    "SEE_TSM": "#475569",
}
REC_LABELS = {
    "STRONG_BUY": "STRONG BUY",
    "BUY": "BUY",
    "HOLD": "HOLD",
    "SELL": "SELL",
    "STRONG_SELL": "STRONG SELL",
    "PASS": "PASS",
    "AVOID": "AVOID",
    "N/A": "—",
    "SEE_TSM": "see parent",
}

CONSENSUS_COLORS = {
    "UNANIMOUS_STRONG_BUY": "#059669",
    "UNANIMOUS_BUY": "#10b981",
    "MAJORITY_BUY": "#84cc16",
    "DIVIDED": "#94a3b8",
    "MAJORITY_AVOID": "#f43f5e",
}
CONSENSUS_LABELS = {
    "UNANIMOUS_STRONG_BUY": "Unanimous STRONG BUY",
    "UNANIMOUS_BUY": "Unanimous BUY",
    "MAJORITY_BUY": "Majority BUY",
    "DIVIDED": "Divided council",
    "MAJORITY_AVOID": "Majority PASS/AVOID",
}

STRUCTURE_COLORS = {
    "monopoly": "#f43f5e",
    "duopoly": "#fb923c",
    "oligopoly": "#fbbf24",
    "fragmented": "#38bdf8",
}


def rec_badge(rec: str | None) -> str:
    """Refined recommendation pill — squared, uppercase, dense typography."""
    if not rec:
        return '<span style="color:#64748b;">—</span>'
    color = REC_COLORS.get(rec, "#475569")
    label = REC_LABELS.get(rec, rec)
    return (
        f'<span style="display:inline-block;background:{color};color:#f8fafc;'
        f'padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;'
        f'letter-spacing:0.06em;text-transform:uppercase;">{label}</span>'
    )


def consensus_badge(label: str | None) -> str:
    """Refined consensus pill — squared, uppercase."""
    if not label:
        return '<span style="color:#64748b;">—</span>'
    color = CONSENSUS_COLORS.get(label, "#475569")
    text = CONSENSUS_LABELS.get(label, label)
    return (
        f'<span style="display:inline-block;background:rgba(255,255,255,0.02);'
        f'border:1px solid {color};color:{color};padding:3px 10px;border-radius:4px;'
        f'font-size:11px;font-weight:600;letter-spacing:0.06em;'
        f'text-transform:uppercase;">{text}</span>'
    )


def structure_badge(s: str | None) -> str:
    if not s:
        return '<span style="color:#64748b;">—</span>'
    color = STRUCTURE_COLORS.get(s.lower(), "#475569")
    return (
        f'<span style="display:inline-block;background:rgba(255,255,255,0.02);'
        f'border:1px solid {color};color:{color};padding:2px 8px;border-radius:3px;'
        f'font-size:10px;font-weight:600;letter-spacing:0.08em;'
        f'text-transform:uppercase;">{s}</span>'
    )


def fmt_pct(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{v * 100:+.1f}%" if abs(v) < 5 else f"{v:+.1f}%"


def fmt_money(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    if v >= 1e12:
        return f"${v/1e12:.2f}T"
    if v >= 1e9:
        return f"${v/1e9:.1f}B"
    if v >= 1e6:
        return f"${v/1e6:.0f}M"
    return f"${v:,.0f}"


def fmt_ratio(v, digits=1) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{v:.{digits}f}x" if v >= 0 else "—"


def fmt_price(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"${v:,.2f}"


# ---------------------- DataFrame builders ----------------------

# Column list kept explicit so an empty df still has the expected schema —
# this prevents KeyErrors when a run is in progress / produced no companies.
DF_COLUMNS = [
    "id", "name", "component", "is_public", "ticker", "hq_country",
    "market_share_pct", "market_share_bucket", "single_source", "moat_types",
    "switching_costs", "customer_concentration", "demand_signal", "valuation_usd",
    "composite", "evidence_count",
    "structure", "supply_status",
    "stock_price", "market_cap_usd", "pe_trailing", "pe_forward", "peg",
    "ev_ebitda", "ev_sales", "revenue_growth_ttm", "revenue_growth_fwd",
    "operating_margin", "fcf_yield", "dividend_yield", "beta",
    "week52_high", "week52_low",
    "analyst_buy", "analyst_hold", "analyst_sell",
    "price_target_low", "price_target_avg", "price_target_high",
    "recommendation", "conviction", "expected_return_12m",
    "bull_target", "base_target", "bear_target", "thesis_summary",
    "council_consensus", "council_score_pct", "council_buy_count",
    "council_strong_buy_count", "council_high_conv_buy",
    "roic", "roic_5y_avg", "roic_trend", "wacc",
    "net_debt_usd", "debt_to_ebitda", "interest_coverage", "current_ratio",
    "capex_to_sales", "capex_guidance_trend", "fcf_margin_after_capex",
    "rd_to_sales", "rd_trend", "buyback_yield", "total_shareholder_yield",
    "top_1_customer_pct", "top_3_customer_pct", "top_10_customer_pct",
    "china_revenue_pct", "hyperscaler_capex_beta", "ai_revenue_pct",
    "insider_net_buying_6m_usd", "short_interest_pct", "days_to_cover",
    "eps_revisions_3m_pct", "analyst_revisions_up", "analyst_revisions_down",
    "institutional_ownership_pct",
    "bull_probability", "base_probability", "bear_probability",
    "probability_weighted_return",
    "dcf_growth_y1_y5", "dcf_terminal_multiple", "dcf_wacc",
    "intelligence_score", "us_gov_total_usd", "federal_contract_total_usd",
    "politicians_buying_count", "politicians_net_value_usd",
    "intelligence_bull_count", "intelligence_bear_count",
]


def view_to_dataframe(view: RunView) -> pd.DataFrame:
    """Flatten the run into a tabular DataFrame for charts/tables.

    Pulls financials + recommendation out of CompanyExtras into top-level
    columns. Returns a column-stable DataFrame even when there are no
    companies (run still in progress).
    """
    comp_by_id = {c.id: c.name for c in view.components}
    rows = []
    for c in view.companies:
        e = c.extras
        rows.append(
            {
                "id": c.id, "name": c.name,
                "component": comp_by_id.get(c.component_id, "?"),
                "is_public": c.is_public, "ticker": c.ticker, "hq_country": c.hq_country,
                "market_share_pct": c.market_share_pct,
                "market_share_bucket": c.market_share_bucket,
                "single_source": bool(c.single_source),
                "moat_types": ", ".join(c.moat_types),
                "switching_costs": c.switching_costs,
                "customer_concentration": c.customer_concentration,
                "demand_signal": c.demand_signal,
                "valuation_usd": c.valuation_usd,
                "composite": c.score.composite if c.score and c.score.composite is not None else 0,
                "evidence_count": len(c.evidence),
                "structure": e.structure, "supply_status": e.supply_status,
                "stock_price": e.stock_price, "market_cap_usd": e.market_cap_usd,
                "pe_trailing": e.pe_trailing, "pe_forward": e.pe_forward, "peg": e.peg,
                "ev_ebitda": e.ev_ebitda, "ev_sales": e.ev_sales,
                "revenue_growth_ttm": e.revenue_growth_ttm,
                "revenue_growth_fwd": e.revenue_growth_fwd,
                "operating_margin": e.operating_margin, "fcf_yield": e.fcf_yield,
                "dividend_yield": e.dividend_yield, "beta": e.beta,
                "week52_high": e.week52_high, "week52_low": e.week52_low,
                "analyst_buy": e.analyst_buy, "analyst_hold": e.analyst_hold,
                "analyst_sell": e.analyst_sell,
                "price_target_low": e.price_target_low,
                "price_target_avg": e.price_target_avg,
                "price_target_high": e.price_target_high,
                "recommendation": e.recommendation, "conviction": e.conviction,
                "expected_return_12m": e.expected_return_12m,
                "bull_target": e.bull_target, "base_target": e.base_target,
                "bear_target": e.bear_target,
                "thesis_summary": e.thesis_summary,
                "council_consensus": (e.council_summary or {}).get("consensus"),
                "council_score_pct": (e.council_summary or {}).get("score_pct"),
                "council_buy_count": (e.council_summary or {}).get("buy_count"),
                "council_strong_buy_count": (e.council_summary or {}).get("strong_buy_count"),
                "council_high_conv_buy": (e.council_summary or {}).get("high_conviction_buy_count"),
                # Earnings power (Pass 1)
                "roic": e.roic, "roic_5y_avg": e.roic_5y_avg,
                "roic_trend": e.roic_trend, "wacc": e.wacc,
                "net_debt_usd": e.net_debt_usd, "debt_to_ebitda": e.debt_to_ebitda,
                "interest_coverage": e.interest_coverage, "current_ratio": e.current_ratio,
                "capex_to_sales": e.capex_to_sales,
                "capex_guidance_trend": e.capex_guidance_trend,
                "fcf_margin_after_capex": e.fcf_margin_after_capex,
                "rd_to_sales": e.rd_to_sales, "rd_trend": e.rd_trend,
                "buyback_yield": e.buyback_yield,
                "total_shareholder_yield": e.total_shareholder_yield,
                # Risk & sentiment (Pass 2)
                "top_1_customer_pct": e.top_1_customer_pct,
                "top_3_customer_pct": e.top_3_customer_pct,
                "top_10_customer_pct": e.top_10_customer_pct,
                "china_revenue_pct": e.china_revenue_pct,
                "hyperscaler_capex_beta": e.hyperscaler_capex_beta,
                "ai_revenue_pct": e.ai_revenue_pct,
                "insider_net_buying_6m_usd": e.insider_net_buying_6m_usd,
                "short_interest_pct": e.short_interest_pct,
                "days_to_cover": e.days_to_cover,
                "eps_revisions_3m_pct": e.eps_revisions_3m_pct,
                "analyst_revisions_up": e.analyst_revisions_up,
                "analyst_revisions_down": e.analyst_revisions_down,
                "institutional_ownership_pct": e.institutional_ownership_pct,
                # Scenario math (Pass 3)
                "bull_probability": e.bull_probability,
                "base_probability": e.base_probability,
                "bear_probability": e.bear_probability,
                "probability_weighted_return": e.probability_weighted_return,
                "dcf_growth_y1_y5": e.dcf_growth_y1_y5,
                "dcf_terminal_multiple": e.dcf_terminal_multiple,
                "dcf_wacc": e.dcf_wacc,
                # Intelligence Agent (Pass 4)
                "intelligence_score": (e.intelligence_summary or {}).get("intelligence_score"),
                "us_gov_total_usd": (e.intelligence_summary or {}).get("us_gov_total_usd"),
                "federal_contract_total_usd": (e.intelligence_summary or {}).get("federal_contract_total_usd"),
                "politicians_buying_count": (e.intelligence_summary or {}).get("politicians_buying_count"),
                "politicians_net_value_usd": (e.intelligence_summary or {}).get("politicians_net_value_usd"),
                "intelligence_bull_count": (e.intelligence_summary or {}).get("bullish_count"),
                "intelligence_bear_count": (e.intelligence_summary or {}).get("bearish_count"),
            }
        )
    if rows:
        return pd.DataFrame(rows)
    return pd.DataFrame(columns=DF_COLUMNS)


def get_top_picks(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Filter to actionable BUY/STRONG_BUY only, sort by expected return."""
    actionable = df[df["recommendation"].isin(["STRONG_BUY", "BUY"])].copy()
    if actionable.empty:
        return df.head(n)
    # Prioritize STRONG_BUY + HIGH conviction + expected return
    rec_priority = {"STRONG_BUY": 2, "BUY": 1}
    conv_priority = {"HIGH": 2, "MEDIUM": 1, "LOW": 0}
    actionable["_rec_p"] = actionable["recommendation"].map(rec_priority).fillna(0)
    actionable["_conv_p"] = actionable["conviction"].map(conv_priority).fillna(0)
    actionable["_score"] = (
        actionable["_rec_p"] * 2 + actionable["_conv_p"]
    ) * 10 + actionable["expected_return_12m"].fillna(0) * 100
    return actionable.sort_values("_score", ascending=False).head(n)


# ---------------------- Charts ----------------------

def _empty_fig(msg: str = "No data") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(color="#94a3b8", size=14))
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0), height=240,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    return _polish(fig)


def chart_recommendation_distribution(df: pd.DataFrame) -> go.Figure:
    if df.empty or "recommendation" not in df.columns:
        return _empty_fig("No recommendations yet")
    counts = df[df["recommendation"].isin(REC_ORDER)]["recommendation"].value_counts()
    ordered = [r for r in REC_ORDER if r in counts.index]
    values = [counts[r] for r in ordered]
    colors = [REC_COLORS.get(r, "#64748b") for r in ordered]
    labels = [REC_LABELS.get(r, r) for r in ordered]
    fig = go.Figure(
        go.Bar(
            x=labels, y=values, marker=dict(color=colors),
            text=values, textposition="outside",
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=260,
        xaxis_title="",
        yaxis_title="# companies",
        showlegend=False,
    )
    return _polish(fig)


def chart_analyst_consensus(buy: int | None, hold: int | None, sell: int | None) -> go.Figure:
    buy = buy or 0
    hold = hold or 0
    sell = sell or 0
    fig = go.Figure(
        go.Bar(
            x=["Buy", "Hold", "Sell"],
            y=[buy, hold, sell],
            marker=dict(color=["#16a34a", "#eab308", "#dc2626"]),
            text=[buy, hold, sell],
            textposition="outside",
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=240,
        xaxis_title="",
        yaxis_title="# analysts",
        showlegend=False,
    )
    return _polish(fig)


def chart_price_targets(price: float | None, bear: float | None, base: float | None, bull: float | None) -> go.Figure:
    """Horizontal range chart for bear/base/bull price targets."""
    if not all(v is not None and v > 0 for v in [price, bear, base, bull]):
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[bull - bear], y=["Targets"], base=[bear], orientation="h",
        marker=dict(color="rgba(34, 211, 238, 0.18)"), showlegend=False,
        hoverinfo="skip",
    ))
    for label, val, color in [
        ("Bear", bear, "#dc2626"),
        ("Base", base, "#22d3ee"),
        ("Bull", bull, "#16a34a"),
    ]:
        fig.add_trace(go.Scatter(
            x=[val], y=["Targets"], mode="markers+text",
            marker=dict(size=18, color=color, line=dict(color="white", width=1.5)),
            text=[f"{label}<br>${val:,.0f}"], textposition="top center",
            showlegend=False, hoverinfo="text",
            hovertext=f"{label}: ${val:,.2f}",
        ))
    fig.add_trace(go.Scatter(
        x=[price], y=["Targets"], mode="markers+text",
        marker=dict(size=22, color="#0b1220", symbol="line-ns",
                    line=dict(color="white", width=3)),
        text=[f"Now<br>${price:,.0f}"], textposition="bottom center",
        showlegend=False,
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=10),
        height=200,
        xaxis_title="$ per share",
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return _polish(fig)


def chart_market_structure(df: pd.DataFrame) -> go.Figure:
    """Pie chart of market structures across components (unique per component)."""
    if df.empty or "structure" not in df.columns:
        return _empty_fig("No structure data yet")
    by_comp = df.dropna(subset=["structure"]).drop_duplicates(subset=["component"])
    counts = by_comp["structure"].value_counts()
    if counts.empty:
        return go.Figure()
    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            marker=dict(colors=[STRUCTURE_COLORS.get(s.lower(), "#475569") for s in counts.index]),
            hole=0.55,
            textinfo="label+percent",
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=320,
        showlegend=False,
    )
    return _polish(fig)


def chart_top_picks_bar(df: pd.DataFrame, n: int = 10) -> go.Figure:
    if df.empty:
        return _empty_fig("No picks yet — run still in progress?")
    top = get_top_picks(df, n=n)
    if top.empty:
        return _empty_fig("No actionable BUY-rated names in this run")
    top = top.iloc[::-1]
    top["label"] = top["name"] + " · " + top["ticker"].fillna("—")
    top["ret_pct"] = top["expected_return_12m"].fillna(0) * 100
    fig = go.Figure(
        go.Bar(
            x=top["ret_pct"], y=top["label"], orientation="h",
            marker=dict(
                color=[REC_COLORS.get(r, "#64748b") for r in top["recommendation"]],
            ),
            text=[f"+{v:.0f}%" for v in top["ret_pct"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Expected return: %{x:.1f}%<br><extra></extra>",
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=20, t=10, b=0),
        height=max(360, 36 * len(top) + 60),
        xaxis_title="12-month expected return (%)",
        yaxis_title="",
    )
    return _polish(fig)


def chart_share_pie(df_component: pd.DataFrame, component_name: str) -> go.Figure:
    pie_df = df_component.copy()
    pie_df["share"] = pie_df["market_share_pct"].fillna(0)
    pie_df = pie_df[pie_df["share"] > 0]
    if pie_df.empty:
        return go.Figure()
    others_share = max(0, 100 - pie_df["share"].sum())
    if others_share > 1:
        pie_df = pd.concat([pie_df, pd.DataFrame([{"name": "Others / unallocated", "share": others_share}])], ignore_index=True)
    fig = px.pie(
        pie_df, names="name", values="share", hole=0.45,
        color_discrete_sequence=px.colors.sequential.Teal_r,
    )
    fig.update_traces(textposition="inside", textinfo="label+percent")
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=340,
        title=f"Share — {component_name}",
        showlegend=False,
    )
    return _polish(fig)


def chart_demand_supply(df_component: pd.DataFrame, component_name: str) -> go.Figure:
    """A schematic demand/supply chart (illustrative).

    Demand line trends up based on the strength of demand signals; supply line
    plateaus where supply_status indicates 'constrained'.
    """
    demands = df_component["demand_signal"].fillna("").str.lower()
    strong = demands.str.contains("exponential|accelerating|shortage|backlog|sold out").sum()
    growing = demands.str.contains(r"strong|growing|\+", regex=True).sum()
    base_growth = 0.10 + min(strong * 0.04 + growing * 0.02, 0.35)
    constrained = (df_component["supply_status"].fillna("") == "constrained").any()
    years = ["2024", "2025", "2026", "2027", "2028"]
    demand_idx = [100 * (1 + base_growth) ** i for i in range(len(years))]
    if constrained:
        supply_idx = [100, 100 * (1 + base_growth * 0.6), 100 * (1 + base_growth * 0.95), 100 * (1 + base_growth * 1.1), 100 * (1 + base_growth * 1.25)]
    else:
        supply_idx = [100 * (1 + base_growth * 0.95) ** i for i in range(len(years))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=demand_idx, name="Demand index",
                              line=dict(color="#22d3ee", width=3), mode="lines+markers"))
    fig.add_trace(go.Scatter(x=years, y=supply_idx, name="Supply index",
                              line=dict(color="#f97316", width=3, dash="dash"), mode="lines+markers"))
    if constrained:
        fig.add_annotation(
            x=years[-1], y=demand_idx[-1], text="DEMAND > SUPPLY",
            showarrow=True, arrowhead=2, ax=-60, ay=-30,
            font=dict(color="#dc2626", size=12, family="Arial Black"),
        )
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=300,
        title=f"Demand vs supply (illustrative) — {component_name}",
        yaxis_title="Index (2024 = 100)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return _polish(fig)


def chart_council_voting_matrix(df: pd.DataFrame, view, top_n: int = 25) -> go.Figure:
    """Heatmap: companies (rows) × investors (cols), colored by verdict score."""
    from investment_agent.council.personas import COUNCIL

    if df.empty:
        return _empty_fig("No companies yet")

    # Build a (company × investor) score matrix using the persisted verdicts
    verdict_by_co_inv: dict[tuple[str, str], dict] = {}
    for c in view.companies:
        for vd in c.extras.council_verdicts:
            verdict_by_co_inv[(c.id, vd["investor_key"])] = vd

    # Pick top-N most-loved by the council
    top_df = df.copy()
    top_df["_sort"] = top_df["council_score_pct"].fillna(-9999)
    top_df = top_df.sort_values("_sort", ascending=False).head(top_n).iloc[::-1]

    investor_keys = [p.key for p in COUNCIL]
    investor_names = [p.name.split()[-1] for p in COUNCIL]

    z = []
    text = []
    hover = []
    for _, row in top_df.iterrows():
        z_row = []
        t_row = []
        h_row = []
        for k in investor_keys:
            vd = verdict_by_co_inv.get((row["id"], k))
            if vd:
                z_row.append(vd["score"])
                t_row.append({"STRONG_BUY": "SB", "BUY": "B", "HOLD": "H",
                              "PASS": "P", "AVOID": "A"}.get(vd["verdict"], "·"))
                h_row.append(
                    f"<b>{row['name']}</b><br>"
                    f"{vd['investor_name']}: <b>{vd['verdict']}</b> "
                    f"({vd['conviction']})<br>"
                    f"{vd['reasoning'][0] if vd['reasoning'] else ''}"
                )
            else:
                z_row.append(0); t_row.append("—"); h_row.append("")
        z.append(z_row); text.append(t_row); hover.append(h_row)

    fig = go.Figure(go.Heatmap(
        z=z, x=investor_names, y=top_df["name"].tolist(),
        colorscale=[
            [0.0, "#7f1d1d"], [0.25, "#dc2626"], [0.5, "#475569"],
            [0.75, "#22c55e"], [1.0, "#15803d"],
        ],
        zmin=-2, zmax=2, showscale=False,
        text=text, texttemplate="%{text}", textfont=dict(size=11, color="white"),
        hovertext=hover, hoverinfo="text",
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=max(360, 24 * len(top_df) + 80),
        xaxis_title="", yaxis_title="",
        xaxis=dict(side="top"),
    )
    return _polish(fig)


def chart_council_score_distribution(df: pd.DataFrame) -> go.Figure:
    if df.empty or "council_score_pct" not in df.columns:
        return _empty_fig("No council data")
    fig = go.Figure(go.Histogram(
        x=df["council_score_pct"].dropna(),
        nbinsx=20,
        marker=dict(color="#22d3ee"),
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0), height=240,
        xaxis_title="Council score (%)", yaxis_title="# companies",
    )
    return _polish(fig)


# ---------------------- Scenario math (Pass 3) ----------------------

def probability_weighted_return(
    bull_p: float, base_p: float, bear_p: float,
    price: float, bull_target: float, base_target: float, bear_target: float,
) -> dict:
    """Return PW expected return given scenario weights + price targets.

    Returns dict with bull/base/bear/blended returns and individual contributions.
    Probabilities are normalized to sum to 1 (defensive against UI slider drift).
    """
    total_p = (bull_p or 0) + (base_p or 0) + (bear_p or 0)
    if total_p <= 0:
        return {"bull_ret": 0, "base_ret": 0, "bear_ret": 0,
                "pw_return": 0, "bull_contrib": 0, "base_contrib": 0, "bear_contrib": 0}
    bull_p, base_p, bear_p = bull_p / total_p, base_p / total_p, bear_p / total_p
    bull_ret = (bull_target / price - 1) if price else 0
    base_ret = (base_target / price - 1) if price else 0
    bear_ret = (bear_target / price - 1) if price else 0
    return {
        "bull_ret": bull_ret, "base_ret": base_ret, "bear_ret": bear_ret,
        "bull_contrib": bull_p * bull_ret,
        "base_contrib": base_p * base_ret,
        "bear_contrib": bear_p * bear_ret,
        "pw_return": bull_p * bull_ret + base_p * base_ret + bear_p * bear_ret,
        "bull_p": bull_p, "base_p": base_p, "bear_p": bear_p,
    }


def forward_dcf_fair_value(
    *,
    current_eps: float,
    growth_y1_y5: float,
    terminal_margin_uplift: float,   # multiplicative on EPS (1.0 = no change)
    terminal_pe: float,
    wacc: float,
) -> float:
    """Simple 5-year forward DCF on an EPS basis.

    Project EPS to year 5, apply a terminal P/E, discount back to today at WACC.
    `terminal_margin_uplift` lets us model margin expansion ("EPS grows faster
    than revenue" if op margin expands; <1.0 if margins compress).
    """
    eps_y5 = current_eps * ((1 + growth_y1_y5) ** 5) * terminal_margin_uplift
    fair_value_y5 = eps_y5 * terminal_pe
    return fair_value_y5 / ((1 + wacc) ** 5)


def chart_sensitivity_table(
    *,
    current_eps: float,
    current_price: float,
    growth_levels: list[float],   # e.g. [0.10, 0.15, 0.20, 0.25, 0.30]
    pe_levels: list[float],       # e.g. [15, 20, 25, 30, 35]
    wacc: float,
) -> go.Figure:
    """Sensitivity grid — growth (rows) × terminal P/E (cols), value = upside %."""
    if current_eps <= 0 or current_price <= 0:
        return _empty_fig("Not enough data for sensitivity")
    z = []
    text = []
    for g in growth_levels:
        z_row = []
        t_row = []
        for pe in pe_levels:
            fv = forward_dcf_fair_value(
                current_eps=current_eps, growth_y1_y5=g,
                terminal_margin_uplift=1.0, terminal_pe=pe, wacc=wacc,
            )
            upside = (fv / current_price - 1) * 100
            z_row.append(upside)
            t_row.append(f"{upside:+.0f}%")
        z.append(z_row); text.append(t_row)

    fig = go.Figure(go.Heatmap(
        z=z,
        x=[f"{pe:.0f}x" for pe in pe_levels],
        y=[f"{g*100:.0f}%" for g in growth_levels],
        colorscale=[
            [0.0, "#7f1d1d"], [0.25, "#dc2626"], [0.5, "#475569"],
            [0.75, "#22c55e"], [1.0, "#15803d"],
        ],
        zmid=0,
        text=text, texttemplate="%{text}",
        textfont=dict(size=12, color="white"),
        showscale=False,
        hovertemplate="Growth %{y}, Terminal P/E %{x}<br>Upside: %{z:.0f}%<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=320,
        xaxis_title="Terminal P/E",
        yaxis_title="5y revenue CAGR",
        xaxis=dict(side="top"),
    )
    return _polish(fig)


def chart_scenario_waterfall(
    bull_contrib: float, base_contrib: float, bear_contrib: float,
) -> go.Figure:
    """Show how each scenario contributes to the probability-weighted return."""
    fig = go.Figure(go.Waterfall(
        x=["Bull", "Base", "Bear", "PW return"],
        y=[bull_contrib * 100, base_contrib * 100, bear_contrib * 100, 0],
        measure=["relative", "relative", "relative", "total"],
        text=[f"{bull_contrib*100:+.1f}%", f"{base_contrib*100:+.1f}%",
              f"{bear_contrib*100:+.1f}%", ""],
        textposition="outside",
        increasing=dict(marker=dict(color="#16a34a")),
        decreasing=dict(marker=dict(color="#dc2626")),
        totals=dict(marker=dict(color="#22d3ee")),
        connector=dict(line=dict(color="rgba(148,163,184,0.3)")),
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=280,
        yaxis_title="Contribution to expected return (%)",
        showlegend=False,
    )
    return _polish(fig)


def chart_hyperscaler_capex_sensitivity(df: pd.DataFrame, top_n: int = 18) -> go.Figure:
    """Horizontal bar — which companies have the highest revenue beta to
    combined MSFT+GOOGL+AMZN+META capex. The portfolio's macro exposure map."""
    if df.empty or "hyperscaler_capex_beta" not in df.columns:
        return _empty_fig("No capex-sensitivity data yet")
    sub = df.dropna(subset=["hyperscaler_capex_beta"]).copy()
    if sub.empty:
        return _empty_fig("No capex-sensitivity data yet")
    sub = sub.sort_values("hyperscaler_capex_beta", ascending=False).head(top_n).iloc[::-1]
    sub["label"] = sub["name"] + " · " + sub["ticker"].fillna("—")
    # Color by recommendation
    sub["_color"] = sub["recommendation"].map(REC_COLORS).fillna("#64748b")
    fig = go.Figure(go.Bar(
        x=sub["hyperscaler_capex_beta"], y=sub["label"], orientation="h",
        marker=dict(color=sub["_color"]),
        text=[f"{b:.1f}x" for b in sub["hyperscaler_capex_beta"]],
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Hyperscaler capex beta: %{x:.1f}x<br>"
            "<extra></extra>"
        ),
    ))
    fig.update_layout(
        margin=dict(l=0, r=24, t=10, b=0),
        height=max(360, 28 * len(sub) + 60),
        xaxis_title="Revenue beta to MSFT+GOOGL+AMZN+META capex",
        yaxis_title="",
    )
    fig.add_vline(x=1.0, line=dict(color="#94a3b8", dash="dash"),
                   annotation_text="parity (1.0x)", annotation_position="top right")
    return _polish(fig)


def chart_treemap_by_recommendation(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_fig("No companies yet")
    plot_df = df.copy()
    plot_df["rec_label"] = plot_df["recommendation"].map(REC_LABELS).fillna("—")
    plot_df["mcap_b"] = (plot_df["market_cap_usd"].fillna(plot_df["valuation_usd"].fillna(1e8)) / 1e9).clip(lower=0.5, upper=4000)
    fig = px.treemap(
        plot_df, path=["rec_label", "component", "name"],
        values="mcap_b",
        color="expected_return_12m",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0.10,
        hover_data={"ticker": True, "composite": ":.0f"},
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=540)
    return _polish(fig)
