"""Shared dashboard helpers: arbitrage scoring + plotly chart builders.

The arbitrage angle: a savvy investor wants opportunities where the moat is
strong relative to how priced-in / accessible the company is. We surface:
  - composite moat score (already computed by the rubric)
  - "arbitrage tilt" — heuristic that boosts privates, capacity-constrained
    incumbents, and high-demand single-source positions, and penalizes
    weak-moat / overcrowded names
"""
from __future__ import annotations

from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from investment_agent.storage.models import CompanyRow, RunView


# ----- scoring -----

def arbitrage_tilt(c: CompanyRow) -> float:
    """Bounded 0–30 heuristic that rewards mispricing-prone positions.

    +10 if private (harder to access -> potential premium for those who can get in)
    +10 if demand signal mentions "shortage", "backlog", "exponential", "accelerating"
    +5  if customer concentration is high (acquisition-target dynamics)
    +5  if sole-source or top share-bucket
    """
    pts = 0.0
    if c.is_public is False:
        pts += 10
    demand = (c.demand_signal or "").lower()
    if any(w in demand for w in ("shortage", "backlog", "exponential", "accelerating", "sold out")):
        pts += 10
    cc = (c.customer_concentration or "").lower()
    if any(w in cc for w in (">", "concentration", "heavy", "majority")):
        pts += 5
    if c.single_source or c.market_share_bucket in (">75", "sole"):
        pts += 5
    return min(pts, 30)


def composite_with_tilt(c: CompanyRow) -> float:
    base = c.score.composite if (c.score and c.score.composite is not None) else 0
    return base + arbitrage_tilt(c)


def view_to_dataframe(view: RunView) -> pd.DataFrame:
    """Flatten a RunView into a pandas DataFrame for charting."""
    comp_by_id = {c.id: c.name for c in view.components}
    rows = []
    for c in view.companies:
        rows.append(
            {
                "name": c.name,
                "component": comp_by_id.get(c.component_id, "?"),
                "is_public": c.is_public,
                "ticker": c.ticker,
                "hq_country": c.hq_country,
                "market_share_pct": c.market_share_pct,
                "market_share_bucket": c.market_share_bucket,
                "single_source": bool(c.single_source),
                "moat_types": ", ".join(c.moat_types),
                "switching_costs": c.switching_costs,
                "customer_concentration": c.customer_concentration,
                "demand_signal": c.demand_signal,
                "valuation_usd": c.valuation_usd,
                "composite": c.score.composite if c.score and c.score.composite is not None else 0,
                "arb_tilt": arbitrage_tilt(c),
                "arb_score": composite_with_tilt(c),
                "evidence_count": len(c.evidence),
            }
        )
    return pd.DataFrame(rows)


# ----- charts -----

def chart_moat_heatmap(df: pd.DataFrame) -> go.Figure:
    """For each (component, share bucket) cell, show the # of companies."""
    bucket_order = ["<10", "10-25", "25-50", "50-75", ">75", "sole"]
    pivot = (
        df.assign(market_share_bucket=df["market_share_bucket"].fillna("<10"))
        .groupby(["component", "market_share_bucket"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=bucket_order, fill_value=0)
    )
    fig = px.imshow(
        pivot,
        labels=dict(x="Market share bucket", y="Component", color="Companies"),
        aspect="auto",
        color_continuous_scale="Blues",
        text_auto=True,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=520, coloraxis_showscale=False)
    return fig


def chart_demand_vs_share(df: pd.DataFrame) -> go.Figure:
    """Bubble: x=market_share_pct, y=composite, size=valuation, color=public/private."""
    plot_df = df.copy()
    plot_df["valuation_b"] = (plot_df["valuation_usd"].fillna(500_000_000) / 1e9).clip(lower=0.3, upper=3500)
    plot_df["status"] = plot_df["is_public"].map({True: "Public", False: "Private"}).fillna("Unknown")
    fig = px.scatter(
        plot_df,
        x="market_share_pct",
        y="composite",
        size="valuation_b",
        color="status",
        hover_name="name",
        hover_data={
            "component": True,
            "ticker": True,
            "single_source": True,
            "demand_signal": True,
            "valuation_b": ":.1f",
            "market_share_pct": ":.0f",
            "composite": ":.0f",
        },
        size_max=55,
        color_discrete_map={"Public": "#2563eb", "Private": "#dc2626", "Unknown": "#6b7280"},
        labels={"market_share_pct": "Market share (%)", "composite": "Moat composite (0-100)"},
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=520, legend_title="")
    return fig


def chart_top_arbitrage(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Horizontal bar of top arbitrage-tilted companies."""
    top = df.sort_values("arb_score", ascending=False).head(top_n).iloc[::-1]
    top["label"] = top["name"] + " (" + top["component"].str.slice(0, 22) + ")"
    fig = go.Figure(
        go.Bar(
            x=top["arb_score"],
            y=top["label"],
            orientation="h",
            marker=dict(
                color=top["arb_score"],
                colorscale="Viridis",
                showscale=False,
            ),
            text=top["arb_score"].round(0),
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "arb score=%{x:.0f}<br>"
                "<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=max(380, 28 * len(top) + 60),
        xaxis_title="Arbitrage score (moat + tilt, 0-130)",
        yaxis_title="",
    )
    return fig


def chart_component_concentration(df: pd.DataFrame) -> go.Figure:
    """For each component, a stacked bar of share by company."""
    plot_df = df.copy()
    plot_df["share"] = plot_df["market_share_pct"].fillna(0)
    fig = px.bar(
        plot_df,
        x="component",
        y="share",
        color="name",
        labels={"share": "Market share (%)"},
        hover_data={"composite": ":.0f", "single_source": True},
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=80),
        height=520,
        legend=dict(orientation="v", yanchor="top", y=1.0, xanchor="left", x=1.02),
        xaxis_tickangle=-30,
    )
    return fig


def chart_score_distribution(df: pd.DataFrame) -> go.Figure:
    """Histogram of composite scores."""
    fig = px.histogram(df, x="composite", nbins=20, color_discrete_sequence=["#2563eb"])
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=320,
        xaxis_title="Composite moat score",
        yaxis_title="# companies",
    )
    return fig


def chart_public_vs_private_treemap(df: pd.DataFrame) -> go.Figure:
    """Treemap: component -> company, colored by composite."""
    plot_df = df.copy()
    plot_df["status"] = plot_df["is_public"].map({True: "Public", False: "Private"}).fillna("Unknown")
    fig = px.treemap(
        plot_df,
        path=["status", "component", "name"],
        values=plot_df["composite"].clip(lower=1),
        color="composite",
        color_continuous_scale="Viridis",
        hover_data={"single_source": True, "ticker": True},
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=620)
    return fig
