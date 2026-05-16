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
        "GOOGLE_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
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
    page_title="AI Infra — Investment Brief",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

from design import (  # noqa: E402
    apply_design, deep_dive_button, render_queue_sidebar,
)
apply_design()


PROVIDERS = ["multi", "gemini", "groq", "ollama", "anthropic", "openai", "mock"]
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "gemini": "gemini-2.0-flash",
    "groq": "llama-3.1-8b-instant",
    "ollama": "qwen2.5:7b",
    "multi": "(rotating: gemini → groq)",
    "mock": "mock-v1",
}
PROVIDER_HINTS = {
    "multi": "Rotates Gemini → Groq on rate limits. Best for long runs. Needs both keys set.",
    "gemini": "Free tier — get key at aistudio.google.com/apikey",
    "groq": "Free tier — Llama 3.1 8B Instant has 500k tokens/day (5x the 70B). Get key at console.groq.com/keys",
    "ollama": "Local open-source — install from ollama.com, `ollama pull qwen2.5:7b`. NOTE: Streamlit Cloud can't reach your laptop's localhost — run Streamlit locally, OR tunnel Ollama via cloudflared and set OLLAMA_BASE_URL secret.",
    "anthropic": "Paid — claude-sonnet-4-6",
    "openai": "Paid — gpt-4o",
    "mock": "No API call — hand-crafted demo data",
}


def sidebar() -> dict:
    settings = get_settings()
    with st.sidebar:
        st.markdown("### Provider")
        prov_default = settings.llm_provider if settings.llm_provider in PROVIDERS else "gemini"
        provider = st.selectbox(
            "LLM provider", PROVIDERS,
            index=PROVIDERS.index(prov_default) if prov_default in PROVIDERS else 0,
            label_visibility="collapsed",
        )
        st.caption(PROVIDER_HINTS.get(provider, ""))
        model = st.text_input("Model", value=settings.llm_model or DEFAULT_MODELS[provider])
        mock = st.toggle(
            "Demo mode",
            value=(provider == "mock"),
            help="Hand-crafted illustrative data — no API spend.",
        )

        st.markdown("### Run")
        runs = list_run_ids(settings.run_output_dir)
        chosen_run = st.selectbox("Existing runs", runs, label_visibility="collapsed") if runs else None
        if not runs:
            st.caption("No runs yet.")

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

from design import render_deep_dive_status  # noqa: E402
render_queue_sidebar(cfg.get("chosen_run"))
render_deep_dive_status()

st.markdown(
    "<h1 style='margin-bottom:0;'>AI Infrastructure — Investment Brief</h1>"
    "<p style='color:#94a3b8;margin-top:6px;font-size:15px;line-height:1.5;max-width:780px;'>"
    "Bottom-up coverage of the AI value chain — sole-source moats, "
    "capacity-constrained incumbents, and mispriced positions across the stack "
    "from raw materials to foundation models."
    "</p>",
    unsafe_allow_html=True,
)


if not cfg["chosen_run"]:
    st.info(
        "First time here? Generate a demo run — the dashboard ships with hand-crafted "
        "illustrative data so you can evaluate the framework without API keys."
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
    chart_hyperscaler_capex_sensitivity,
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
st.markdown("## Top high-conviction picks")
st.caption("Filtered to STRONG BUY / BUY with high conviction. Drill into any name on the Investment Thesis page.")

# Re-rank to give a boost to council-backed names
df_sorted = df.copy()
df_sorted["_council_boost"] = df_sorted["council_score_pct"].fillna(0) / 100
top5 = get_top_picks(df_sorted, n=5)
def _depth_for(name: str) -> str:
    for c in view.companies:
        if c.name == name:
            return c.extras.analysis_depth or "triage"
    return "triage"


for _, row in top5.iterrows():
    rec = row["recommendation"]
    exp_ret_pct = (row["expected_return_12m"] or 0) * 100
    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 3, 1.1])
        with c1:
            ticker_html = (
                f"<span style='color:#64748b;font-size:14px;font-weight:500;"
                f"letter-spacing:0.04em;'>{row['ticker']}</span>"
                if row['ticker'] else ""
            )
            st.markdown(
                f"<div style='font-size:18px;font-weight:600;color:#f1f5f9;"
                f"margin-bottom:4px;letter-spacing:-0.01em;'>"
                f"{row['name']} &nbsp; {ticker_html}</div>"
                f"<div style='margin-bottom:8px;'>{rec_badge(rec)} &nbsp; "
                f"{consensus_badge(row.get('council_consensus'))}</div>"
                f"<div style='color:#94a3b8;font-size:12px;'>"
                f"{row['component']} &nbsp;·&nbsp; {row['conviction'] or '—'} conviction</div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.metric("Price", fmt_price(row["stock_price"]))
            st.caption(f"Mkt cap {fmt_money(row['market_cap_usd'])}")
        with c3:
            st.metric("12m expected", f"+{exp_ret_pct:.0f}%")
            cb = int(row.get('council_buy_count') or 0)
            st.caption(f"Council {cb}/9 BUY")
        with c4:
            if row.get("thesis_summary"):
                st.markdown(
                    f"<div style='color:#cbd5e1;font-size:13px;line-height:1.5;'>"
                    f"{row['thesis_summary']}</div>",
                    unsafe_allow_html=True,
                )
        with c5:
            deep_dive_button(
                row["name"], _depth_for(row["name"]), key_prefix="home_top5",
            )

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


# ---------------- HYPERSCALER CAPEX SENSITIVITY ----------------
st.markdown("## Hyperscaler capex exposure")
st.caption(
    "Revenue beta to combined Microsoft + Google + Amazon + Meta capex. "
    "Vertical dashed line at 1.0x is parity — anything above is real leverage to the AI capex cycle."
)
st.plotly_chart(chart_hyperscaler_capex_sensitivity(df, top_n=18), use_container_width=True)

st.markdown("---")


# ---------------- WHERE TO GO NEXT ----------------
st.markdown(
    """
### Explore the brief
- **Datacenter Anatomy** — visual walk through the stack from raw materials to applications
- **Market Map** — value-chain visualization with structure badges and demand/supply call-outs per layer
- **Components** — drill into any layer (Copper, HBM, Foundation Models, etc.)
- **Investment Thesis** — per-company write-up with earnings power, risk & sentiment, intelligence signals, scenario math, and the 9-investor council
- **Investor Council** — cross-portfolio voting matrix
- **Portfolio** — conviction-weighted basket with expected portfolio return
"""
)

st.caption(
    "_This dashboard is research output, not investment advice. Demo-mode data is illustrative; "
    "switch to a live LLM provider for cited, real-time research._"
)
