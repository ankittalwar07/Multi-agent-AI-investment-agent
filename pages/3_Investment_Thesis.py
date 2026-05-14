"""Investment Thesis — per-company drill-in.

Everything an analyst wants on a single page:
  - Stock price, market cap, 52w range
  - Valuation: P/E TTM, P/E fwd, PEG, EV/EBITDA, EV/Sales
  - Quality: revenue growth, op margin, FCF yield, beta
  - Analyst consensus (buy/hold/sell + price targets)
  - Our recommendation + bull/base/bear targets
  - Thesis bullets, risks, catalysts
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard_utils import (  # noqa: E402
    chart_analyst_consensus, chart_price_targets,
    fmt_money, fmt_pct, fmt_price, fmt_ratio, rec_badge, structure_badge,
    view_to_dataframe,
)
from investment_agent.storage.repository import RunRepository  # noqa: E402

st.title("Investment Thesis")

cfg = st.session_state.get("cfg")
if cfg is None or not cfg.get("chosen_run"):
    st.warning("Pick a run on the home page first.")
    st.stop()

repo = RunRepository(Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.db")
view = repo.get_view(cfg["chosen_run"])
df = view_to_dataframe(view)

# Company selector — default to highest-conviction BUY
ranked = df.copy()
ranked["_rec_p"] = ranked["recommendation"].map({"STRONG_BUY": 2, "BUY": 1}).fillna(0)
ranked["_score"] = ranked["_rec_p"] * 100 + ranked["expected_return_12m"].fillna(0) * 100
ranked = ranked.sort_values("_score", ascending=False)
options = [
    f"{row['name']}" + (f" ({row['ticker']})" if row.get("ticker") else "")
    for _, row in ranked.iterrows()
]
chosen = st.selectbox("Company", options)
chosen_name = chosen.split(" (")[0]

# Find the record
match = df[df["name"] == chosen_name].iloc[0]
co_obj = next(c for c in view.companies if c.name == chosen_name)
extras = co_obj.extras
comp_obj = next(c for c in view.components if c.id == co_obj.component_id)

# ---------------- HEADER ----------------
c1, c2 = st.columns([3, 1])
with c1:
    ticker_str = f" <span style='color:#94a3b8;font-size:22px;'>· {match['ticker']}</span>" if match.get("ticker") else ""
    st.markdown(
        f"<h2 style='margin-bottom:0;'>{chosen_name}{ticker_str}</h2>"
        f"<p style='color:#94a3b8;margin-top:4px;'>"
        f"<strong>{comp_obj.name}</strong> · {match.get('hq_country') or '—'} · "
        f"{'Public' if match.get('is_public') else 'Private'}</p>",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"<div style='text-align:right;'>{rec_badge(extras.recommendation)}<br/>"
        f"<span style='color:#94a3b8;font-size:12px;'>Conviction: <strong>{extras.conviction or '—'}</strong></span></div>",
        unsafe_allow_html=True,
    )

if extras.thesis_summary:
    st.info(f"**Headline thesis:** {extras.thesis_summary}")

st.markdown("---")

# ---------------- PRICE / VALUATION ROW ----------------
st.markdown("### :moneybag: Stock & valuation")

if extras.stock_price:
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("Price", fmt_price(extras.stock_price))
    p2.metric("Market cap", fmt_money(extras.market_cap_usd))
    if extras.week52_high and extras.week52_low and extras.stock_price:
        pct = (extras.stock_price - extras.week52_low) / (extras.week52_high - extras.week52_low) * 100
        p3.metric("52w range", f"${extras.week52_low:.0f} — ${extras.week52_high:.0f}",
                  delta=f"{pct:.0f}% of range")
    else:
        p3.metric("52w range", "—")
    p4.metric("Beta", f"{extras.beta:.2f}" if extras.beta else "—")
    p5.metric("Div yield", fmt_pct(extras.dividend_yield) if extras.dividend_yield else "—")
else:
    st.info(f":lock: Private company &middot; last valuation: {fmt_money(co_obj.valuation_usd)}")

st.markdown("#### Valuation multiples")
v1, v2, v3, v4, v5 = st.columns(5)
v1.metric("P/E (TTM)", fmt_ratio(extras.pe_trailing))
v2.metric("P/E (fwd)", fmt_ratio(extras.pe_forward))
v3.metric("PEG", fmt_ratio(extras.peg, 2))
v4.metric("EV/EBITDA", fmt_ratio(extras.ev_ebitda))
v5.metric("EV/Sales", fmt_ratio(extras.ev_sales))

st.markdown("#### Quality & growth")
q1, q2, q3, q4, q5 = st.columns(5)
q1.metric("Rev growth (TTM)", fmt_pct(extras.revenue_growth_ttm))
q2.metric("Rev growth (fwd)", fmt_pct(extras.revenue_growth_fwd))
q3.metric("Op margin", fmt_pct(extras.operating_margin))
q4.metric("FCF yield", fmt_pct(extras.fcf_yield))
q5.metric("Composite moat", f"{co_obj.score.composite:.0f}/100" if co_obj.score else "—")

st.markdown("---")

# ---------------- ANALYST CONSENSUS + PRICE TARGETS ----------------
left, right = st.columns([1, 2])
with left:
    st.markdown("### :pencil: Street consensus")
    if extras.analyst_buy or extras.analyst_hold or extras.analyst_sell:
        st.plotly_chart(
            chart_analyst_consensus(extras.analyst_buy, extras.analyst_hold, extras.analyst_sell),
            use_container_width=True,
        )
        if extras.price_target_avg:
            implied = None
            if extras.stock_price:
                implied = (extras.price_target_avg / extras.stock_price - 1) * 100
            st.caption(
                f"Street PT (avg): **${extras.price_target_avg:,.0f}**"
                + (f" — implied **+{implied:.0f}%**" if implied is not None else "")
                + f" &nbsp;[low ${extras.price_target_low:,.0f} / high ${extras.price_target_high:,.0f}]"
                if extras.price_target_low and extras.price_target_high else ""
            )
    else:
        st.caption("No analyst data available.")

with right:
    st.markdown("### :dart: Our price-target range (12m)")
    if extras.stock_price and extras.bull_target and extras.base_target and extras.bear_target:
        st.plotly_chart(
            chart_price_targets(extras.stock_price, extras.bear_target, extras.base_target, extras.bull_target),
            use_container_width=True,
        )
        b1, b2, b3 = st.columns(3)
        b1.metric("Bear", fmt_price(extras.bear_target),
                  f"{(extras.bear_target / extras.stock_price - 1) * 100:+.0f}%")
        b2.metric("Base", fmt_price(extras.base_target),
                  f"{(extras.base_target / extras.stock_price - 1) * 100:+.0f}%")
        b3.metric("Bull", fmt_price(extras.bull_target),
                  f"{(extras.bull_target / extras.stock_price - 1) * 100:+.0f}%")
        if extras.expected_return_12m is not None:
            st.success(
                f"**Expected 12-month return:** +{extras.expected_return_12m * 100:.0f}% "
                f"to ${extras.base_target:,.0f}"
            )
    else:
        st.caption("Insufficient data for price-target range.")

st.markdown("---")

# ---------------- THESIS / RISKS / CATALYSTS ----------------
t1, t2, t3 = st.columns(3)
with t1:
    st.markdown("### :white_check_mark: Why we like it")
    if extras.thesis_points:
        for p in extras.thesis_points:
            st.markdown(f"- {p}")
    else:
        st.caption("No thesis bullets available.")
with t2:
    st.markdown("### :warning: Key risks")
    if extras.risks:
        for r in extras.risks:
            st.markdown(f"- {r}")
    else:
        st.caption("No risk bullets available.")
with t3:
    st.markdown("### :rocket: Catalysts")
    if extras.catalysts:
        for c in extras.catalysts:
            st.markdown(f"- {c}")
    else:
        st.caption("No catalysts on the radar.")

st.markdown("---")

# ---------------- MARKET POSITION ----------------
st.markdown("### Market position")
mp1, mp2, mp3, mp4 = st.columns(4)
mp1.metric("Share", co_obj.market_share_bucket or "—",
           f"{co_obj.market_share_pct:.0f}%" if co_obj.market_share_pct else None)
mp2.metric("Sole-source?", "Yes" if co_obj.single_source else "No")
mp3.metric("Structure", extras.structure or "—")
mp4.metric("Supply status", extras.supply_status or "—")

if co_obj.moat_types:
    st.caption(f"**Moat types:** {', '.join(co_obj.moat_types)}")
if co_obj.switching_costs:
    st.caption(f"**Switching costs:** {co_obj.switching_costs}")
if co_obj.demand_signal:
    st.caption(f"**Demand signal:** {co_obj.demand_signal}")
if co_obj.customer_concentration:
    st.caption(f"**Customer concentration:** {co_obj.customer_concentration}")

st.markdown("---")

# ---------------- EVIDENCE ----------------
if co_obj.evidence:
    with st.expander(f"Evidence trail ({len(co_obj.evidence)} sources)"):
        for ev in co_obj.evidence:
            with st.container(border=True):
                st.markdown(f"**Claim:** {ev.claim or '_(unspecified)_'}")
                meta = f"_{ev.source_name or 'web'}_ via `{ev.tool_name or '-'}` &middot; {ev.retrieved_at or ''}"
                st.caption(meta)
                if ev.source_url:
                    st.markdown(f"[source]({ev.source_url})")
                if ev.snippet:
                    st.write(ev.snippet)
