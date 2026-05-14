"""Dashboard helpers: investor-grade tables, badges, and plotly charts."""
from __future__ import annotations

from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from investment_agent.storage.models import CompanyRow, RunView


# ---------------------- recommendation logic ----------------------

REC_ORDER = ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL", "N/A", "SEE_TSM"]
REC_COLORS = {
    "STRONG_BUY": "#16a34a",
    "BUY": "#22c55e",
    "HOLD": "#eab308",
    "SELL": "#f97316",
    "STRONG_SELL": "#dc2626",
    "N/A": "#64748b",
    "SEE_TSM": "#64748b",
}
REC_LABELS = {
    "STRONG_BUY": "STRONG BUY",
    "BUY": "BUY",
    "HOLD": "HOLD",
    "SELL": "SELL",
    "STRONG_SELL": "STRONG SELL",
    "N/A": "—",
    "SEE_TSM": "see parent",
}

STRUCTURE_COLORS = {
    "monopoly": "#dc2626",
    "duopoly": "#ea580c",
    "oligopoly": "#eab308",
    "fragmented": "#0ea5e9",
}


def rec_badge(rec: str | None) -> str:
    """Markdown-safe colored pill for a recommendation."""
    if not rec:
        return "—"
    color = REC_COLORS.get(rec, "#64748b")
    label = REC_LABELS.get(rec, rec)
    return f'<span style="background:{color};color:white;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;">{label}</span>'


def structure_badge(s: str | None) -> str:
    if not s:
        return "—"
    color = STRUCTURE_COLORS.get(s.lower(), "#475569")
    return f'<span style="background:{color};color:white;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;text-transform:uppercase;">{s}</span>'


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
    return fig


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
    return fig


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
    return fig


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
    return fig


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
    return fig


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
    return fig


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
    return fig


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
    return fig


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
    return fig
