"""Executive Summary — the front page of the AI Infra Arbitrage Dashboard.

Designed for a savvy investor: glance-able. Top BUY recommendations, expected
portfolio return, recommendation distribution. Drill into the other pages for
the value chain map, per-component deep dive, per-company thesis.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from investment_agent.config import get_settings  # noqa: E402
from investment_agent.storage.repository import RunRepository, list_run_ids  # noqa: E402


def _load_secrets_into_env() -> None:
    """Copy Streamlit Cloud secrets into env vars so providers can pick them up."""
    import os
    for key in (
        "GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
        "BLOOMBERG_API_KEY", "PITCHBOOK_API_KEY", "CRUNCHBASE_API_KEY", "SIMILARWEB_API_KEY",
    ):
        try:
            val = st.secrets.get(key)  # type: ignore[attr-defined]
        except Exception:
            val = None
        if val and not os.environ.get(key):
            os.environ[key] = str(val)


_load_secrets_into_env()

st.set_page_config(
    page_title="AI Infra Arbitrage",
    page_icon=":dart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


PROVIDERS = ["gemini", "anthropic", "openai", "mock"]
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "gemini": "gemini-2.0-flash",
    "mock": "mock-v1",
}


def sidebar() -> dict:
    settings = get_settings()
    with st.sidebar:
        st.markdown("### LLM")
        prov_default = settings.llm_provider if settings.llm_provider in PROVIDERS else "gemini"
        provider = st.selectbox(
            "Provider", PROVIDERS,
            index=PROVIDERS.index(prov_default) if prov_default in PROVIDERS else 0,
        )
        model = st.text_input("Model", value=settings.llm_model or DEFAULT_MODELS[provider])
        mock = st.toggle(
            "Demo mode (no API spend)",
            value=(provider == "mock"),
            help="Uses hand-crafted realistic data so you can explore the dashboard without API keys.",
        )

        st.markdown("---")
        st.markdown("### Run picker")
        runs = list_run_ids(settings.run_output_dir)
        chosen_run = st.selectbox("Existing runs", runs) if runs else None
        if not runs:
            st.caption("No runs yet.")

        st.markdown("---")
        with st.expander("Advanced"):
            max_cost = st.slider("Max cost (USD)", 0.5, 50.0, float(settings.max_cost_usd), 0.5)
            max_components = st.number_input("Limit components (0=all)", 0, 40, 0, 1)

    return {
        "provider": provider, "model": model, "mock": mock,
        "max_cost": max_cost if 'max_cost' in locals() else float(settings.max_cost_usd),
        "max_components": int(max_components) or None if 'max_components' in locals() else None,
        "chosen_run": chosen_run,
        "output_dir": settings.run_output_dir,
    }


cfg = sidebar()
st.session_state["cfg"] = cfg

st.markdown(
    "<h1 style='margin-bottom:0;'>AI Infrastructure — Investment Brief</h1>"
    "<p style='color:#94a3b8;margin-top:4px;'>"
    "Bottom-up coverage of the AI value chain. Sole-source moats, capacity-constrained "
    "incumbents, and mispriced positions across raw materials &rarr; silicon &rarr; cloud &rarr; models."
    "</p>",
    unsafe_allow_html=True,
)


if not cfg["chosen_run"]:
    st.info(
        "**First time here?** Generate a demo run — the dashboard ships with realistic "
        "hand-crafted data so you can evaluate it without configuring any API keys."
    )
    if st.button("Generate demo run", type="primary"):
        from investment_agent.config import Settings as _Settings
        from investment_agent.graph.build import Pipeline, RunOptions
        from investment_agent.llm import get_provider

        with st.spinner("Decomposing AI stack, dispatching researchers, scoring moats..."):
            settings = _Settings(
                SEED_FILE=Path("data/seeds/ai_infra_components.yaml"),
                RUN_OUTPUT_DIR=cfg["output_dir"],
                LLM_PROVIDER="mock",
                MAX_PARALLEL_RESEARCHERS=4,
            )
            pipeline = Pipeline(settings=settings, llm_factory=lambda: get_provider("mock"))
            result = pipeline.run(
                RunOptions(provider="mock", model="mock-v1", mock=True,
                           max_components=None, output_dir=cfg["output_dir"])
            )
        st.success(f"Demo run complete: `{result.run_id}` ({len(result.state.scored)} companies).")
        st.rerun()
    st.stop()


try:
    repo = RunRepository(Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.db")
    view = repo.get_view(cfg["chosen_run"])
except Exception as e:
    st.error(f"Could not load run `{cfg['chosen_run']}`: {e}")
    st.stop()

from dashboard_utils import (  # noqa: E402
    REC_COLORS, REC_LABELS,
    chart_recommendation_distribution, chart_top_picks_bar, chart_market_structure,
    consensus_badge,
    fmt_money, fmt_pct, fmt_price, get_top_picks, rec_badge, structure_badge,
    view_to_dataframe,
)

df = view_to_dataframe(view)

# Show progress UI if a run is in progress or empty
if view.run.status == "running" or df.empty:
    if view.run.status == "running":
        st.warning(
            f":hourglass_flowing_sand: Run **{view.run.id}** is still in progress — "
            f"provider **{view.run.provider}**, model **{view.run.model or '-'}**. "
            "Refresh in ~30s, or switch to a completed run from the sidebar."
        )
    elif view.run.status == "error":
        st.error(
            f"Run **{view.run.id}** failed: {view.run.error or 'unknown error'}. "
            "Pick a different run from the sidebar, or try Demo mode if a live "
            "provider run errored out."
        )
    else:
        st.warning(
            f"Run **{view.run.id}** completed with no companies — the LLM provider "
            "likely returned malformed JSON or hit a rate limit. Try Demo mode "
            "or check the Run page event log."
        )
    # Show events tail so the user can see what's happening
    st.markdown("### Run event log (most recent 30)")
    events_to_show = view.events[:30]
    st.dataframe(
        [
            {"ts": e.ts, "level": e.level, "node": e.node, "message": e.message}
            for e in events_to_show
        ],
        use_container_width=True, hide_index=True,
    )
    st.stop()


# ---------------- KPI ROW ----------------
strong_buy_df = df[df["recommendation"] == "STRONG_BUY"]
buy_df = df[df["recommendation"] == "BUY"]
actionable_df = pd.concat([strong_buy_df, buy_df])
sole_source_df = df[df["single_source"] == True]  # noqa: E712
exp_ret = actionable_df["expected_return_12m"].dropna()
weighted_exp_ret = exp_ret.mean() if not exp_ret.empty else 0

unanimous_count = int(df["council_consensus"].isin(["UNANIMOUS_STRONG_BUY", "UNANIMOUS_BUY"]).sum()) if "council_consensus" in df.columns else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("STRONG BUY", len(strong_buy_df))
c2.metric("BUY", len(buy_df))
c3.metric("Sole-source", len(sole_source_df))
c4.metric("Components covered", len(view.components))
c5.metric("Avg expected return (12m)", f"+{weighted_exp_ret * 100:.1f}%")
c6.metric("Council unanimous", unanimous_count, help="Companies the full council voted BUY or STRONG BUY on")

st.caption(
    f"Coverage as of run **{view.run.id}** &middot; provider **{view.run.provider}** &middot; "
    f"{len(view.companies)} companies &middot; total LLM cost ${view.run.cost_usd:.2f}"
)

st.markdown("---")


# ---------------- TOP 5 PICKS ----------------
st.markdown("## :fire: Top high-conviction picks")
st.caption("Filtered to STRONG BUY / BUY with HIGH conviction. Click any name to drill into the full thesis.")

# Re-rank to give a boost to council-backed names
df_sorted = df.copy()
df_sorted["_council_boost"] = df_sorted["council_score_pct"].fillna(0) / 100
top5 = get_top_picks(df_sorted, n=5)
for _, row in top5.iterrows():
    rec = row["recommendation"]
    exp_ret_pct = (row["expected_return_12m"] or 0) * 100
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([4, 2, 2, 3])
        with c1:
            st.markdown(
                f"### {row['name']} "
                + (f"<span style='color:#94a3b8;font-size:18px;'>· {row['ticker']}</span>" if row['ticker'] else "")
                + f"<br/>{rec_badge(rec)} &nbsp; {consensus_badge(row.get('council_consensus'))}",
                unsafe_allow_html=True,
            )
            st.caption(f"_{row['component']}_  &middot;  {row['conviction'] or '—'} conviction")
        with c2:
            st.metric("Price", fmt_price(row["stock_price"]))
            st.caption(f"Mkt cap {fmt_money(row['market_cap_usd'])}")
        with c3:
            st.metric("12m expected", f"+{exp_ret_pct:.0f}%")
            st.caption(f"Council {int(row.get('council_buy_count') or 0)}/6 BUY")
        with c4:
            if row.get("thesis_summary"):
                st.write(row["thesis_summary"])

st.markdown("---")


# ---------------- RECOMMENDATION DISTRIBUTION + MARKET STRUCTURE ----------------
left, right = st.columns([2, 1])
with left:
    st.markdown("### Recommendation distribution")
    st.caption("How conviction is allocated across the universe.")
    st.plotly_chart(chart_recommendation_distribution(df), use_container_width=True)
with right:
    st.markdown("### Market structure")
    st.caption("Structure of each component (mono/duo/oligo/fragmented).")
    st.plotly_chart(chart_market_structure(df), use_container_width=True)


st.markdown("---")


# ---------------- EXPECTED RETURN — top 10 ----------------
st.markdown("## Expected 12-month return — top 10")
st.plotly_chart(chart_top_picks_bar(df, n=10), use_container_width=True)


st.markdown("---")


# ---------------- WHERE TO GO NEXT ----------------
st.markdown(
    """
### Explore the brief
- **:world_map: Market Map** — value-chain visualization with structure badges and demand/supply call-outs per layer
- **:package: Components** — drill into any layer (e.g. _Copper_, _HBM_, _Foundation Models_) with share splits, top picks, risks
- **:office: Companies** — sortable / filterable table with full financials and analyst consensus
- **:bar_chart: Investment Thesis** — full per-company write-up: price card, P/E ratios, bull/base/bear price targets, thesis bullets, risks, catalysts
- **:bookmark_tabs: Portfolio** — weighted aggregation of all BUY-rated names with expected portfolio return
"""
)

st.caption(
    "_This dashboard is research output, not investment advice. Demo-mode data is illustrative; "
    "switch to a live LLM provider for cited, real-time research._"
)
