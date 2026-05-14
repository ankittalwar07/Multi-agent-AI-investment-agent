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
    consensus_badge,
    fmt_money, fmt_pct, fmt_price, fmt_ratio, rec_badge, structure_badge,
    view_to_dataframe,
)
from investment_agent.council.personas import BY_KEY as INVESTOR_BY_KEY  # noqa: E402
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

# ---------------- EARNINGS POWER & BALANCE SHEET (Pass 1) ----------------
st.markdown("### :anatomical_heart: Earnings power & balance sheet")
st.caption(
    "The economic engine — what every Buffett/Munger underwriting actually anchors on. "
    "ROIC vs WACC is the real moat in basis points; the rest tells you whether "
    "this is a wonderful business or one that's eating its capital."
)

# Row 1 — Return on capital
ep1, ep2, ep3, ep4, ep5 = st.columns(5)
roic = extras.roic
wacc = extras.wacc
if roic is not None:
    spread = roic - (wacc or 0)
    spread_str = f"{spread*100:+.0f}pp vs WACC"
    ep1.metric("ROIC", f"{roic*100:.0f}%", delta=spread_str if wacc else None)
else:
    ep1.metric("ROIC", "—")
ep2.metric("ROIC 5y avg", fmt_pct(extras.roic_5y_avg))
trend = extras.roic_trend
trend_icon = ":arrow_up_small:" if trend == "improving" else (":arrow_down_small:" if trend == "declining" else ":left_right_arrow:")
ep3.metric("ROIC trend", (trend.title() if trend else "—"), help="Direction of ROIC over the last 5 years")
ep4.metric("WACC", fmt_pct(extras.wacc))
shy = extras.total_shareholder_yield
ep5.metric("Total SH yield", fmt_pct(shy), help="Dividend yield + buyback yield combined")

# Row 2 — Balance sheet
bs1, bs2, bs3, bs4 = st.columns(4)
nd = extras.net_debt_usd
if nd is not None:
    nd_str = fmt_money(abs(nd))
    if nd < 0:
        bs1.metric("Net cash", nd_str, delta="Fortress")
    else:
        bs1.metric("Net debt", nd_str)
else:
    bs1.metric("Net debt", "—")
bs2.metric("Debt / EBITDA", fmt_ratio(extras.debt_to_ebitda, 1) if extras.debt_to_ebitda is not None else "—")
bs3.metric("Interest coverage", fmt_ratio(extras.interest_coverage, 0) if extras.interest_coverage else "—")
bs4.metric("Current ratio", fmt_ratio(extras.current_ratio, 1) if extras.current_ratio else "—")

# Row 3 — Capital intensity
ci1, ci2, ci3, ci4 = st.columns(4)
ci1.metric("Capex / Sales", fmt_pct(extras.capex_to_sales))
ci2.metric("Capex trend", (extras.capex_guidance_trend.title() if extras.capex_guidance_trend else "—"),
            help="Management's guidance trajectory")
ci3.metric("FCF after capex", fmt_pct(extras.fcf_margin_after_capex),
            help="The real cash margin: ops cash flow minus capex, divided by revenue")
ci4.metric("R&D / Sales", fmt_pct(extras.rd_to_sales),
            help="How much of sales goes into widening the moat")


# Mini call-outs — a quick reader's-guide to the numbers
flags = []
if roic is not None and wacc is not None:
    if roic >= 0.30:
        flags.append((":green_circle:", f"**Exceptional ROIC ({roic*100:.0f}%)** — every reinvested dollar earns extraordinary returns. Buffett/Munger anchor."))
    elif roic >= 0.20:
        flags.append((":green_circle:", f"**Strong ROIC ({roic*100:.0f}%)** — clear economic moat, {(roic-wacc)*100:+.0f}pp over cost of capital."))
    elif roic < 0:
        flags.append((":red_circle:", f"**ROIC negative ({roic*100:.0f}%)** — burning capital. Munger's hard-pass criterion."))
    elif roic < wacc:
        flags.append((":red_circle:", f"**ROIC below WACC** ({roic*100:.0f}% vs {wacc*100:.0f}%) — destroying value with every dollar reinvested."))

if nd is not None and nd < -5_000_000_000:
    flags.append((":green_circle:", "**Net cash position** — fortress balance sheet, optionality on downturns."))
elif extras.debt_to_ebitda is not None and extras.debt_to_ebitda > 3.5:
    flags.append((":warning:", f"**Leverage elevated** ({extras.debt_to_ebitda:.1f}x EBITDA) — refinancing / cycle risk."))

if extras.capex_to_sales is not None and extras.capex_to_sales > 0.30:
    flags.append((":warning:", f"**Capex-heavy** ({extras.capex_to_sales*100:.0f}% of sales) — incremental ROIC matters more than headline FCF."))

if extras.fcf_margin_after_capex is not None and extras.fcf_margin_after_capex < 0:
    flags.append((":red_circle:", f"**Negative FCF after capex** ({extras.fcf_margin_after_capex*100:.0f}%) — funded by debt or equity, not internal cash."))
elif extras.fcf_margin_after_capex is not None and extras.fcf_margin_after_capex >= 0.20:
    flags.append((":green_circle:", f"**Strong FCF after capex** ({extras.fcf_margin_after_capex*100:.0f}%) — real cash generation, not accounting earnings."))

if extras.rd_to_sales is not None and extras.rd_to_sales >= 0.15:
    flags.append((":bulb:", f"**Heavy R&D ({extras.rd_to_sales*100:.0f}% of sales)** — moat-building investment."))

if flags:
    for icon, msg in flags:
        st.markdown(f"{icon} {msg}")

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

# ---------------- COUNCIL OF LEGENDS ----------------
verdicts = extras.council_verdicts or []
summary = extras.council_summary or {}

st.markdown("### :classical_building: Council of Legendary Investors")
st.caption(
    "Each council member applies their distinct philosophy to this name. Use the spread "
    "to gauge conviction: a unanimous BUY is high-confidence; a divided council often "
    "means alpha (the market hasn't decided yet)."
)

if verdicts:
    cc1, cc2, cc3, cc4 = st.columns([2, 1, 1, 1])
    cc1.markdown(
        f"**Consensus:** {consensus_badge(summary.get('consensus'))}",
        unsafe_allow_html=True,
    )
    cc2.metric("Council score", f"{summary.get('score_pct', 0):+.0f}%")
    cc3.metric("BUY votes", f"{summary.get('buy_count', 0)}/{len(verdicts)}")
    cc4.metric("HIGH-conv BUYs", summary.get("high_conviction_buy_count", 0))

    st.write("")
    # Render each investor's verdict as a card row
    for vd in verdicts:
        persona = INVESTOR_BY_KEY.get(vd["investor_key"])
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([3, 1, 6])
            with col_a:
                avatar = persona.avatar if persona else ":bust_in_silhouette:"
                style_str = f" · _{persona.style}_" if persona else ""
                st.markdown(
                    f"{avatar} **{vd['investor_name']}**{style_str}",
                    unsafe_allow_html=True,
                )
                if persona:
                    st.caption(persona.philosophy)
            with col_b:
                st.markdown(
                    rec_badge(vd["verdict"]) + f"<br/><small>{vd['conviction']} conv</small>",
                    unsafe_allow_html=True,
                )
            with col_c:
                for r in vd.get("reasoning", [])[:3]:
                    st.markdown(f"- {r}")
                if vd.get("top_positive") or vd.get("top_concern"):
                    pos = vd.get("top_positive") or ""
                    concern = vd.get("top_concern") or ""
                    st.caption(
                        f"&nbsp;&nbsp;:white_check_mark: {pos}"
                        + (f" &nbsp;|&nbsp; :warning: {concern}" if concern else "")
                    )
else:
    st.caption("Council has not reviewed this run.")

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
