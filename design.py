"""Shared design tokens + global CSS for the dashboard.

Import `apply_design()` at the top of every page (after st.set_page_config)
to inject the typography, spacing, and badge styles.

Design system: refined dark.
- Background:   #0b1220 (deep slate)
- Surface 1:    #131c30 (cards)
- Surface 2:    #1b2440 (elevated)
- Border subtle: #1f2a44
- Border solid:  #334155
- Text primary:  #f1f5f9
- Text muted:    #94a3b8
- Text dim:      #64748b
- Accent:        #22d3ee (cyan)
- Positive:      #10b981 (emerald)
- Negative:      #f43f5e (rose)
- Warning:       #f59e0b (amber)
"""
from __future__ import annotations

import streamlit as st


# ------- design tokens (importable by other modules) -------
PALETTE = {
    "bg": "#0b1220",
    "surface": "#131c30",
    "surface_2": "#1b2440",
    "border": "#1f2a44",
    "border_strong": "#334155",
    "text": "#f1f5f9",
    "text_muted": "#94a3b8",
    "text_dim": "#64748b",
    "accent": "#22d3ee",
    "positive": "#10b981",
    "positive_dim": "#059669",
    "negative": "#f43f5e",
    "negative_dim": "#be123c",
    "warning": "#f59e0b",
    "neutral": "#64748b",
}

# Refined recommendation badge palette
REC_BADGE_COLORS = {
    "STRONG_BUY":  "#059669",   # emerald-600 (darker than 500 for legibility on white)
    "BUY":         "#10b981",
    "HOLD":        "#a16207",   # amber-700
    "SELL":        "#c2410c",   # orange-700
    "STRONG_SELL": "#be123c",
    "PASS":        "#475569",   # slate-600
    "AVOID":       "#9f1239",   # rose-800
    "N/A":         "#475569",
    "SEE_TSM":     "#475569",
}


_CSS = """
<style>
/* ============ Typography ============ */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
    letter-spacing: -0.005em;
}

/* Display title (st.title) */
h1 {
    font-weight: 700 !important;
    font-size: 34px !important;
    letter-spacing: -0.025em !important;
    margin-top: 4px !important;
    margin-bottom: 6px !important;
    color: #f1f5f9;
}

/* Section headers */
h2 {
    font-weight: 600 !important;
    font-size: 22px !important;
    letter-spacing: -0.015em !important;
    color: #f1f5f9;
    margin-top: 32px !important;
    margin-bottom: 8px !important;
}
h3 {
    font-weight: 600 !important;
    font-size: 17px !important;
    letter-spacing: -0.01em !important;
    color: #e2e8f0;
    margin-top: 26px !important;
    margin-bottom: 8px !important;
    text-transform: none;
}
h4 {
    font-weight: 600 !important;
    font-size: 14px !important;
    color: #94a3b8 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em !important;
    margin-top: 20px !important;
    margin-bottom: 4px !important;
}

/* Body caption (st.caption) */
[data-testid="stCaptionContainer"], .stCaption {
    color: #94a3b8 !important;
    font-size: 13px !important;
    line-height: 1.5 !important;
}

/* ============ Containers / cards ============ */

/* st.container(border=True) — give it a refined, subtle border */
[data-testid="stContainerBlockBorderWrapper"], [data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #1f2a44 !important;
    background: #131c30 !important;
    border-radius: 10px !important;
    padding: 18px 20px !important;
    box-shadow: 0 1px 0 rgba(255,255,255,0.02) inset;
}

/* ============ Metrics (st.metric) ============ */
[data-testid="stMetric"] {
    background: transparent;
}
[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em !important;
}
[data-testid="stMetricValue"] {
    font-weight: 700 !important;
    font-size: 22px !important;
    letter-spacing: -0.015em !important;
    color: #f1f5f9 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* ============ Tables ============ */
.stDataFrame {
    border: 1px solid #1f2a44 !important;
    border-radius: 8px !important;
    overflow: hidden;
}

/* ============ Buttons ============ */
.stButton > button {
    border-radius: 6px !important;
    font-weight: 500 !important;
    letter-spacing: -0.005em;
    border: 1px solid #334155 !important;
    background: #131c30 !important;
}
.stButton > button:hover {
    border-color: #22d3ee !important;
    background: #1b2440 !important;
}
.stButton > button[kind="primary"] {
    background: #22d3ee !important;
    color: #0b1220 !important;
    border: none !important;
}

/* ============ Tabs ============ */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid #1f2a44;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 6px 6px 0 0;
    padding: 10px 16px !important;
    color: #94a3b8 !important;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    color: #f1f5f9 !important;
    border-bottom: 2px solid #22d3ee !important;
}

/* ============ Sidebar ============ */
[data-testid="stSidebar"] {
    background: #0d1729 !important;
    border-right: 1px solid #1f2a44;
}
[data-testid="stSidebar"] h3 {
    color: #cbd5e1 !important;
    font-size: 12px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase;
    margin-top: 20px !important;
}

/* ============ Sliders ============ */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: #22d3ee !important;
    border: 2px solid #0b1220 !important;
}

/* ============ Selectbox ============ */
.stSelectbox [data-baseweb="select"] > div {
    background: #131c30 !important;
    border: 1px solid #334155 !important;
}

/* ============ Alert banners (success/info/warning/error) — softened ============ */
.stAlert {
    border-radius: 8px !important;
    border-left-width: 3px !important;
    padding: 14px 18px !important;
}

/* ============ Dividers — subtle ============ */
hr {
    border-color: #1f2a44 !important;
    margin-top: 28px !important;
    margin-bottom: 20px !important;
    opacity: 0.6;
}

/* ============ Plotly — match dark canvas ============ */
.js-plotly-plot {
    background: transparent !important;
}

/* ============ Spacing polish ============ */
.block-container {
    padding-top: 36px !important;
    padding-bottom: 60px !important;
    max-width: 1280px;
}
</style>
"""


def apply_design() -> None:
    """Inject the global CSS. Call once at the top of every page."""
    st.markdown(_CSS, unsafe_allow_html=True)


# -------- refined badge helpers --------

def rec_pill(rec: str | None) -> str:
    """Recommendation pill — refined typography, no emoji."""
    if not rec:
        return '<span style="color:#64748b;">—</span>'
    color = REC_BADGE_COLORS.get(rec, "#475569")
    label = {
        "STRONG_BUY": "STRONG BUY",
        "BUY": "BUY",
        "HOLD": "HOLD",
        "SELL": "SELL",
        "STRONG_SELL": "STRONG SELL",
        "PASS": "PASS",
        "AVOID": "AVOID",
        "N/A": "—",
        "SEE_TSM": "see parent",
    }.get(rec, rec)
    return (
        f'<span style="display:inline-block;background:{color};color:#f8fafc;'
        f'padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;'
        f'letter-spacing:0.06em;text-transform:uppercase;">{label}</span>'
    )


def chip(text: str, color: str = "#475569") -> str:
    """Subtle inline chip — replaces the colored emoji circles."""
    return (
        f'<span style="display:inline-block;background:rgba(255,255,255,0.04);'
        f'border:1px solid {color};color:{color};padding:2px 8px;border-radius:3px;'
        f'font-size:11px;font-weight:500;letter-spacing:0.04em;'
        f'text-transform:uppercase;">{text}</span>'
    )


def positive_flag(msg: str) -> str:
    return (
        f'<div style="display:flex;align-items:flex-start;gap:10px;padding:6px 0;">'
        f'<span style="display:inline-block;width:3px;height:18px;background:#10b981;'
        f'border-radius:2px;flex-shrink:0;margin-top:2px;"></span>'
        f'<span style="color:#cbd5e1;">{msg}</span></div>'
    )


def negative_flag(msg: str) -> str:
    return (
        f'<div style="display:flex;align-items:flex-start;gap:10px;padding:6px 0;">'
        f'<span style="display:inline-block;width:3px;height:18px;background:#f43f5e;'
        f'border-radius:2px;flex-shrink:0;margin-top:2px;"></span>'
        f'<span style="color:#cbd5e1;">{msg}</span></div>'
    )


def warning_flag(msg: str) -> str:
    return (
        f'<div style="display:flex;align-items:flex-start;gap:10px;padding:6px 0;">'
        f'<span style="display:inline-block;width:3px;height:18px;background:#f59e0b;'
        f'border-radius:2px;flex-shrink:0;margin-top:2px;"></span>'
        f'<span style="color:#cbd5e1;">{msg}</span></div>'
    )


# -------- refined plotly layout --------

def plotly_layout_dark() -> dict:
    """Return a layout dict to apply to all plotly figures for consistency."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system, Inter, sans-serif", color="#cbd5e1", size=12),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            zerolinecolor="rgba(255,255,255,0.08)",
            tickfont=dict(color="#94a3b8"),
            title=dict(font=dict(color="#94a3b8", size=12)),
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            zerolinecolor="rgba(255,255,255,0.08)",
            tickfont=dict(color="#94a3b8"),
            title=dict(font=dict(color="#94a3b8", size=12)),
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(font=dict(color="#cbd5e1"), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#131c30", bordercolor="#334155",
                        font=dict(color="#f1f5f9", family="-apple-system, Inter, sans-serif")),
    )
