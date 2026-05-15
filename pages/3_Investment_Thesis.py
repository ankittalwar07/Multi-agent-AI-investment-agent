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

from design import apply_design  # noqa: E402
apply_design()

from dashboard_utils import (  # noqa: E402
    chart_analyst_consensus, chart_price_targets,
    chart_scenario_waterfall, chart_sensitivity_table,
    consensus_badge,
    fmt_money, fmt_pct, fmt_price, fmt_ratio,
    forward_dcf_fair_value, probability_weighted_return,
    rec_badge, structure_badge,
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
st.markdown("### Stock & valuation")

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
st.markdown("### Earnings power & balance sheet")
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
trend_icon = ":arrow_up_small:" if trend == "improving" else (":arrow_down_small:" if trend == "declining" else "")
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
    flags.append(("", f"**Leverage elevated** ({extras.debt_to_ebitda:.1f}x EBITDA) — refinancing / cycle risk."))

if extras.capex_to_sales is not None and extras.capex_to_sales > 0.30:
    flags.append(("", f"**Capex-heavy** ({extras.capex_to_sales*100:.0f}% of sales) — incremental ROIC matters more than headline FCF."))

if extras.fcf_margin_after_capex is not None and extras.fcf_margin_after_capex < 0:
    flags.append((":red_circle:", f"**Negative FCF after capex** ({extras.fcf_margin_after_capex*100:.0f}%) — funded by debt or equity, not internal cash."))
elif extras.fcf_margin_after_capex is not None and extras.fcf_margin_after_capex >= 0.20:
    flags.append((":green_circle:", f"**Strong FCF after capex** ({extras.fcf_margin_after_capex*100:.0f}%) — real cash generation, not accounting earnings."))

if extras.rd_to_sales is not None and extras.rd_to_sales >= 0.15:
    flags.append(("", f"**Heavy R&D ({extras.rd_to_sales*100:.0f}% of sales)** — moat-building investment."))

if flags:
    for icon, msg in flags:
        st.markdown(f"{icon} {msg}")

st.markdown("---")


# ---------------- RISK & SENTIMENT (Pass 2) ----------------
st.markdown("### Risk & sentiment")
st.caption(
    "Concentration, capex sensitivity, and positioning signals. Where the dollars "
    "come from, who's betting on it, and whether the consensus has already played out."
)

# Row 1 — Customer concentration
rs1, rs2, rs3, rs4 = st.columns(4)
top1 = extras.top_1_customer_pct
top3 = extras.top_3_customer_pct
top10 = extras.top_10_customer_pct
china = extras.china_revenue_pct
rs1.metric("Top customer", fmt_pct(top1) if top1 is not None else "—")
rs2.metric("Top 3 customers", fmt_pct(top3) if top3 is not None else "—")
rs3.metric("Top 10 customers", fmt_pct(top10) if top10 is not None else "—")
rs4.metric("China revenue", fmt_pct(china) if china is not None else "—",
           help="Direct revenue from China (geopolitical / export-control exposure)")

# Row 2 — AI exposure
ae1, ae2, ae3, ae4 = st.columns(4)
hs_beta = extras.hyperscaler_capex_beta
ai_pct = extras.ai_revenue_pct
ae1.metric(
    "Hyperscaler capex beta", f"{hs_beta:.1f}x" if hs_beta is not None else "—",
    help="Revenue beta to combined MSFT+GOOGL+AMZN+META capex. >1.0 = real leverage to the AI cycle.",
)
ae2.metric("AI / datacenter revenue", fmt_pct(ai_pct) if ai_pct is not None else "—")
inst = extras.institutional_ownership_pct
ae3.metric("Institutional ownership", fmt_pct(inst) if inst is not None else "—")
ae4.metric("Beta (5y)", f"{extras.beta:.2f}" if extras.beta else "—")

# Row 3 — Positioning signals
ps1, ps2, ps3, ps4 = st.columns(4)
insider = extras.insider_net_buying_6m_usd
if insider is not None:
    if abs(insider) >= 1e6:
        insider_str = f"${insider/1e6:+.0f}M"
    else:
        insider_str = f"${insider:+,.0f}"
    insider_label = "Buying" if insider > 1_000_000 else (":red_circle: Selling" if insider < -1_000_000 else "Flat")
else:
    insider_str = "—"
    insider_label = None
ps1.metric("Insider 6m", insider_str, delta=insider_label)

short = extras.short_interest_pct
ps2.metric(
    "Short interest", fmt_pct(short) if short is not None else "—",
    help="% of float sold short. >10% can flag controversy or squeeze setup.",
)
dtc = extras.days_to_cover
ps3.metric("Days to cover", f"{dtc:.1f}" if dtc is not None else "—")

eps_rev = extras.eps_revisions_3m_pct
ps4.metric(
    "EPS revisions (90d)", fmt_pct(eps_rev) if eps_rev is not None else "—",
    help="% change in consensus next-12m EPS over the last 90 days. The best leading earnings indicator.",
)


# Reader's-guide flags
flags2 = []
if top1 is not None and top1 >= 0.40:
    flags2.append((":red_circle:", f"**Top-customer risk** — single customer is {top1*100:.0f}% of revenue. One contract loss = thesis break."))
elif top1 is not None and top1 >= 0.25:
    flags2.append(("", f"**Concentrated customer base** — top customer is {top1*100:.0f}% of revenue."))

if china is not None and china >= 0.25:
    flags2.append((":red_circle:", f"**Heavy China exposure ({china*100:.0f}%)** — export-control / tariff tail risk is material."))
elif china is not None and china >= 0.15:
    flags2.append(("", f"**Meaningful China exposure ({china*100:.0f}%)** — monitor policy."))

if hs_beta is not None and hs_beta >= 1.5:
    flags2.append((":green_circle:", f"**High hyperscaler leverage ({hs_beta:.1f}x beta)** — direct play on AI capex cycle. Loves it on the way up; gets hit hardest on digestion."))
elif hs_beta is not None and hs_beta < 0.3:
    flags2.append(("", f"**Limited AI leverage ({hs_beta:.1f}x beta)** — narrative may overstate this name's AI exposure."))

if insider is not None and insider > 5_000_000:
    flags2.append((":green_circle:", f"**Insiders net-buying ({fmt_money(insider)})** — they're putting their own money behind the thesis."))
elif insider is not None and insider < -50_000_000:
    flags2.append((":red_circle:", f"**Heavy insider selling ({fmt_money(-insider)} in 6m)** — they may be trimming at the top."))

if short is not None and short >= 0.10:
    flags2.append(("", f"**High short interest ({short*100:.0f}%)** — controversy. Could be a squeeze setup OR a structural short thesis."))
elif short is not None and short <= 0.012:
    flags2.append(("", f"**Almost no shorts ({short*100:.1f}%)** — no marginal skeptics left; positioning is one-sided."))

if eps_rev is not None and eps_rev >= 0.10:
    flags2.append((":green_circle:", f"**EPS revisions {eps_rev*100:+.0f}%** in 90 days — street is raising estimates; momentum signal."))
elif eps_rev is not None and eps_rev <= -0.05:
    flags2.append((":red_circle:", f"**EPS revisions {eps_rev*100:+.0f}%** — consensus is cutting; thesis is breaking."))

if flags2:
    for icon, msg in flags2:
        st.markdown(f"{icon} {msg}")

st.markdown("---")


# ---------------- INTELLIGENCE SIGNALS (Pass 4) ----------------
intel_summary = extras.intelligence_summary or {}
intel_signals = extras.intelligence_signals or []

if intel_summary.get("total_signals", 0) > 0 or intel_signals:
    st.markdown("### Intelligence signals")
    st.caption(
        "Non-financial signals that the market often misprices — US government "
        "investments, federal contracts, congressional STOCK Act disclosures, "
        "foreign sovereign activity, and policy headwinds."
    )

    is1, is2, is3, is4, is5 = st.columns(5)
    score = intel_summary.get("intelligence_score", 0) or 0
    is1.metric(
        "Intelligence score", f"{score:+.0f}",
        help="Composite of all intelligence signals, -100 to +100. Positive = policy/political tailwinds; negative = Entity List / antitrust / sovereign headwinds.",
    )
    is2.metric(
        "US gov $", fmt_money(intel_summary.get("us_gov_total_usd", 0)),
        help="Total US gov direct investment (CHIPS Act, DPA, DoE LPO).",
    )
    is3.metric(
        "Federal contracts $", fmt_money(intel_summary.get("federal_contract_total_usd", 0)),
        help="Recent federal contract awards (DoD, DoE, IC, GSA).",
    )
    pb = intel_summary.get("politicians_buying_count", 0)
    ps = intel_summary.get("politicians_selling_count", 0)
    is4.metric("Politicians buy / sell", f"{pb} / {ps}",
                help="Count of distinct congressional STOCK Act disclosures (Senate EFD + House Clerk).")
    is5.metric(
        "Bull / Bear signals",
        f"{intel_summary.get('bullish_count', 0)} / {intel_summary.get('bearish_count', 0)}",
    )

    # Highlight policy tailwinds and headwinds
    if intel_summary.get("policy_tailwinds"):
        st.success(
            "**Policy tailwinds:** " +
            " · ".join(intel_summary["policy_tailwinds"][:3])
        )
    if intel_summary.get("policy_headwinds"):
        st.error(
            "**Policy headwinds:** " +
            " · ".join(intel_summary["policy_headwinds"][:3])
        )
    if intel_summary.get("notable_politicians"):
        st.info(
            "**Notable congressional activity:** " +
            ", ".join(intel_summary["notable_politicians"][:4])
        )

    with st.expander(f"Full intelligence signal list ({len(intel_signals)} records)"):
        if not intel_signals:
            st.caption("No raw signals persisted.")
        for sig in intel_signals:
            cat = sig.get("category", "")
            cat_emoji = {
                "us_gov_investment": "",
                "federal_contract": "",
                "congressional_trade": "",
                "foreign_gov_activity": "",
                "policy_headwind": "",
                "form4_insider": "",
            }.get(cat, ":pushpin:")
            direction_color = {"bullish": "#16a34a", "bearish": "#dc2626", "neutral": "#64748b"}.get(
                sig.get("direction", "neutral"), "#64748b",
            )
            amt = sig.get("amount_usd")
            amt_str = f" · **{fmt_money(amt)}**" if amt else ""
            with st.container(border=True):
                st.markdown(
                    f"{cat_emoji} **{sig.get('headline')}**"
                    f" <span style='background:{direction_color};color:white;"
                    f"padding:2px 8px;border-radius:10px;font-size:11px;"
                    f"margin-left:8px;'>{sig.get('direction','').upper()}</span>",
                    unsafe_allow_html=True,
                )
                meta_parts = []
                if sig.get("counterparty"):
                    meta_parts.append(f"_{sig['counterparty']}_")
                if amt:
                    meta_parts.append(fmt_money(amt))
                if sig.get("source_name"):
                    meta_parts.append(f"source: {sig['source_name']}")
                if meta_parts:
                    st.caption(" · ".join(meta_parts))
                if sig.get("note"):
                    st.write(sig["note"])
                if sig.get("source_url"):
                    st.markdown(f"[source]({sig['source_url']})")

    st.markdown("---")


# ---------------- SCENARIO & VALUATION (Pass 3) ----------------
st.markdown("### Scenario math & valuation")
st.caption(
    "The headline '12-month expected return' is just one number. This section "
    "decomposes it into probability-weighted scenarios and lets you stress-test "
    "the base case with an editable 5-year DCF."
)

# ----- 1) Probability-weighted return -----
if extras.stock_price and extras.bull_target and extras.base_target and extras.bear_target:
    st.markdown("#### Probability-weighted expected return")
    st.caption(
        "Set the probability you assign to each scenario. The blended return "
        "is the real expected value, not the headline base-case number."
    )

    default_bull = float(extras.bull_probability or 0.30)
    default_base = float(extras.base_probability or 0.50)
    default_bear = float(extras.bear_probability or 0.20)

    pw_cols = st.columns(3)
    bull_p = pw_cols[0].slider(
        ":green_circle: Bull case probability",
        0.0, 1.0, value=default_bull, step=0.05,
        key=f"bull_p_{co_obj.id}",
    )
    base_p = pw_cols[1].slider(
        ":blue_circle: Base case probability",
        0.0, 1.0, value=default_base, step=0.05,
        key=f"base_p_{co_obj.id}",
    )
    bear_p = pw_cols[2].slider(
        ":red_circle: Bear case probability",
        0.0, 1.0, value=default_bear, step=0.05,
        key=f"bear_p_{co_obj.id}",
    )

    pw = probability_weighted_return(
        bull_p, base_p, bear_p,
        extras.stock_price, extras.bull_target, extras.base_target, extras.bear_target,
    )

    sum_p = bull_p + base_p + bear_p
    if abs(sum_p - 1.0) > 0.01:
        st.caption(
            f":information_source: Probabilities sum to {sum_p:.0%} — normalized to 100% in the math."
        )

    res_cols = st.columns(4)
    res_cols[0].metric("Bull return", f"{pw['bull_ret']*100:+.0f}%",
                        f"to ${extras.bull_target:,.0f}")
    res_cols[1].metric("Base return", f"{pw['base_ret']*100:+.0f}%",
                        f"to ${extras.base_target:,.0f}")
    res_cols[2].metric("Bear return", f"{pw['bear_ret']*100:+.0f}%",
                        f"to ${extras.bear_target:,.0f}")
    pw_ret = pw["pw_return"]
    res_cols[3].metric("Prob-weighted return", f"{pw_ret*100:+.1f}%",
                        delta=("Better than headline" if pw_ret > (extras.expected_return_12m or 0)
                               else ("Below headline" if pw_ret < (extras.expected_return_12m or 0) - 0.01 else None)))

    if extras.expected_return_12m is not None and abs(pw_ret - extras.expected_return_12m) > 0.03:
        if pw_ret < extras.expected_return_12m:
            st.warning(
                f"**Probability-weighted return ({pw_ret*100:+.0f}%) is meaningfully "
                f"below the headline expected return ({extras.expected_return_12m*100:+.0f}%)** — "
                "the tail risks are mathematically reducing the case. Consider sizing down."
            )
        else:
            st.success(
                f"**Probability-weighted return ({pw_ret*100:+.0f}%) exceeds the "
                f"headline ({extras.expected_return_12m*100:+.0f}%)** — bull case is asymmetric."
            )

    st.plotly_chart(
        chart_scenario_waterfall(pw["bull_contrib"], pw["base_contrib"], pw["bear_contrib"]),
        use_container_width=True,
    )

    st.markdown("---")

# ----- 2) Editable DCF -----
if extras.stock_price and extras.pe_trailing and extras.pe_trailing > 0:
    st.markdown("#### Editable 5-year DCF")
    st.caption(
        "Slider-driven forward DCF on an EPS basis. Defaults seeded from our "
        "base case; move the sliders to pressure-test where the price stops working."
    )

    current_eps = extras.stock_price / extras.pe_trailing
    default_growth = float(extras.dcf_growth_y1_y5 or extras.revenue_growth_fwd or 0.15)
    default_pe = float(extras.dcf_terminal_multiple or extras.pe_forward or 20)
    default_wacc = float(extras.dcf_wacc or extras.wacc or 0.09)

    dcf_cols = st.columns(4)
    growth = dcf_cols[0].slider(
        "5y EPS CAGR",
        min_value=-0.05, max_value=0.60, value=default_growth, step=0.01,
        format="%.0f%%", key=f"dcf_g_{co_obj.id}",
    )
    margin_uplift = dcf_cols[1].slider(
        "Margin uplift over 5y",
        min_value=0.7, max_value=1.6, value=1.0, step=0.05,
        format="%.2fx", key=f"dcf_m_{co_obj.id}",
        help="EPS multiplier on top of revenue growth (1.0 = flat margins, 1.2 = ~20% margin expansion)",
    )
    term_pe = dcf_cols[2].slider(
        "Terminal P/E",
        min_value=8.0, max_value=50.0, value=default_pe, step=1.0,
        format="%.0fx", key=f"dcf_pe_{co_obj.id}",
    )
    wacc_input = dcf_cols[3].slider(
        "WACC / discount rate",
        min_value=0.05, max_value=0.16, value=default_wacc, step=0.005,
        format="%.1f%%", key=f"dcf_w_{co_obj.id}",
    )

    fv = forward_dcf_fair_value(
        current_eps=current_eps, growth_y1_y5=growth,
        terminal_margin_uplift=margin_uplift, terminal_pe=term_pe, wacc=wacc_input,
    )
    dcf_upside = (fv / extras.stock_price - 1) * 100

    dr_cols = st.columns(4)
    dr_cols[0].metric("Current EPS", f"${current_eps:.2f}",
                      help="Inferred from stock_price / trailing P/E")
    dr_cols[1].metric("Year-5 EPS",
                      f"${current_eps * ((1+growth)**5) * margin_uplift:.2f}")
    dr_cols[2].metric("DCF fair value", f"${fv:.2f}")
    dr_cols[3].metric("Upside / downside", f"{dcf_upside:+.0f}%",
                      delta=f"vs current ${extras.stock_price:,.2f}")

    # ----- 3) Sensitivity grid -----
    st.markdown("#### Sensitivity: growth × terminal P/E")
    st.caption(
        "Each cell = implied upside at that combo. Centerline ≈ 0% (fair-valued); "
        "green = upside, red = downside."
    )
    growth_levels = [max(0.0, growth - 0.10), max(0.0, growth - 0.05), growth,
                      growth + 0.05, growth + 0.10]
    pe_levels = [max(8, term_pe - 8), max(8, term_pe - 4), term_pe,
                  term_pe + 4, term_pe + 8]
    st.plotly_chart(
        chart_sensitivity_table(
            current_eps=current_eps, current_price=extras.stock_price,
            growth_levels=growth_levels, pe_levels=pe_levels, wacc=wacc_input,
        ),
        use_container_width=True,
    )

    st.markdown("---")


# ----- 4) Time-horizon thesis -----
short_term = extras.short_term_catalysts or []
medium_term = extras.medium_term_thesis or extras.thesis_points or []
long_term = extras.long_term_thesis or []
exit_triggers = extras.exit_triggers or []

if any([short_term, medium_term, long_term, exit_triggers]):
    st.markdown("#### Time-horizon thesis")
    st.caption(
        "Bullets ranked by time horizon — short-term catalysts (next 1-2 quarters) "
        "through long-term moat trajectory (3-5 years), plus exit triggers."
    )
    h_cols = st.columns(4)
    with h_cols[0]:
        st.markdown("**Short-term catalysts** (1-2 quarters)")
        if short_term:
            for s in short_term:
                st.markdown(f"- {s}")
        else:
            st.caption("_n/a_")
    with h_cols[1]:
        st.markdown("**Base case** (12-24 months)")
        if medium_term:
            for s in medium_term:
                st.markdown(f"- {s}")
        else:
            st.caption("_n/a_")
    with h_cols[2]:
        st.markdown("**Long-term moat** (3-5 years)")
        if long_term:
            for s in long_term:
                st.markdown(f"- {s}")
        else:
            st.caption("_n/a_")
    with h_cols[3]:
        st.markdown("**Exit triggers**")
        if exit_triggers:
            for s in exit_triggers:
                st.markdown(f"- {s}")
        else:
            st.caption("_n/a_")

    st.markdown("---")

# ---------------- ANALYST CONSENSUS + PRICE TARGETS ----------------
left, right = st.columns([1, 2])
with left:
    st.markdown("### Street consensus")
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
    st.markdown("### Our price-target range (12m)")
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

st.markdown("### Council of Legendary Investors")
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
    # Per-persona accent and initials for the avatar circle
    PERSONA_ACCENT = {
        "buffett": "#22d3ee", "munger": "#a3e635", "lynch": "#fbbf24",
        "graham": "#94a3b8", "druck": "#10b981", "wood": "#f472b6",
        "marks": "#fb923c", "burry": "#f43f5e", "dalio": "#60a5fa",
    }

    def _initials(name: str) -> str:
        parts = [w for w in name.split() if w and w[0].isalpha()]
        if not parts: return "?"
        if len(parts) == 1: return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    for vd in verdicts:
        persona = INVESTOR_BY_KEY.get(vd["investor_key"])
        accent = PERSONA_ACCENT.get(vd["investor_key"], "#22d3ee")
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([3, 1, 6])
            with col_a:
                style_str = persona.style if persona else ""
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:10px;'>"
                    f"<div style='width:30px;height:30px;border-radius:50%;"
                    f"background:{accent}15;border:1px solid {accent};"
                    f"display:flex;align-items:center;justify-content:center;"
                    f"color:{accent};font-weight:600;font-size:11px;flex-shrink:0;'>"
                    f"{_initials(vd['investor_name'])}</div>"
                    f"<div><div style='font-weight:600;color:#f1f5f9;font-size:14px;'>"
                    f"{vd['investor_name']}</div>"
                    f"<div style='color:#64748b;font-size:10px;letter-spacing:0.06em;"
                    f"text-transform:uppercase;margin-top:1px;'>{style_str}</div></div></div>",
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
                        f"&nbsp;&nbsp;{pos}"
                        + (f" &nbsp;|&nbsp; {concern}" if concern else "")
                    )
else:
    st.caption("Council has not reviewed this run.")

st.markdown("---")

# ---------------- THESIS / RISKS / CATALYSTS ----------------
t1, t2, t3 = st.columns(3)
with t1:
    st.markdown("### Why we like it")
    if extras.thesis_points:
        for p in extras.thesis_points:
            st.markdown(f"- {p}")
    else:
        st.caption("No thesis bullets available.")
with t2:
    st.markdown("### Key risks")
    if extras.risks:
        for r in extras.risks:
            st.markdown(f"- {r}")
    else:
        st.caption("No risk bullets available.")
with t3:
    st.markdown("### Catalysts")
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
