"""Streamlit dashboard entry point.

Run with: streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT / "app") not in sys.path:
    sys.path.insert(0, str(ROOT / "app"))

from investment_agent.config import get_settings  # noqa: E402
from investment_agent.storage.repository import RunRepository, list_run_ids  # noqa: E402

st.set_page_config(
    page_title="AI Infra Arbitrage",
    page_icon=":dart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


PROVIDERS = ["anthropic", "openai", "gemini", "mock"]
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "gemini": "gemini-1.5-pro",
    "mock": "mock-v1",
}


def sidebar() -> dict:
    settings = get_settings()
    with st.sidebar:
        st.markdown("### :gear: LLM")
        # Default to Anthropic Claude.
        prov_default = settings.llm_provider if settings.llm_provider in PROVIDERS else "anthropic"
        provider = st.selectbox(
            "Provider",
            PROVIDERS,
            index=PROVIDERS.index(prov_default) if prov_default in PROVIDERS else 0,
        )
        model = st.text_input("Model", value=settings.llm_model or DEFAULT_MODELS[provider])
        mock = st.toggle(
            "Demo mode (no API spend)",
            value=(provider == "mock"),
            help="When on, uses hand-crafted realistic mock data so you can play with the dashboard without API keys.",
        )

        st.markdown("---")
        st.markdown("### :money_with_wings: Run controls")
        max_cost = st.slider("Max cost (USD)", min_value=0.5, max_value=50.0, value=float(settings.max_cost_usd), step=0.5)
        max_components = st.number_input(
            "Limit components (0 = all)",
            min_value=0, max_value=40, value=0, step=1,
            help="Useful for quick demos; e.g. 5 components.",
        )

        st.markdown("---")
        st.markdown("### :file_folder: Run picker")
        runs = list_run_ids(settings.run_output_dir)
        chosen_run = st.selectbox("Existing runs", runs) if runs else None
        if not runs:
            st.caption("No runs yet — go to the **Run** page to generate one.")

    return {
        "provider": provider,
        "model": model,
        "mock": mock,
        "max_cost": max_cost,
        "max_components": int(max_components) or None,
        "chosen_run": chosen_run,
        "output_dir": settings.run_output_dir,
    }


cfg = sidebar()
st.session_state["cfg"] = cfg

# Hero
st.markdown("# :dart: AI Infrastructure Arbitrage Dashboard")
st.markdown(
    "_For investors hunting **sole-source bottlenecks**, **capacity-constrained incumbents**, "
    "and **mispriced private positions** across the AI stack._"
)

if not cfg["chosen_run"]:
    st.info(
        ":sparkles: **First time here?** Generate a demo run right now — the dashboard "
        "uses hand-crafted realistic mock data for every layer of the AI stack so you can "
        "explore the visuals without configuring any API keys."
    )
    col_a, col_b = st.columns([1, 3])
    if col_a.button(":rocket: Generate demo run", type="primary", use_container_width=True):
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
                RunOptions(
                    provider="mock", model="mock-v1", mock=True,
                    max_components=None, output_dir=cfg["output_dir"],
                )
            )
        st.success(f"Demo run complete: `{result.run_id}` ({len(result.state.scored)} companies). Reload the page or pick it from the sidebar.")
        st.rerun()
    col_b.markdown(
        "_or_ head to the **Run** page in the sidebar and click _Start new run_."
    )
    st.stop()

# Selected run summary
try:
    repo = RunRepository(Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.db")
    view = repo.get_view(cfg["chosen_run"])
except Exception as e:
    st.error(f"Could not load run: {e}")
    st.stop()

from dashboard_utils import (  # noqa: E402
    chart_top_arbitrage,
    chart_demand_vs_share,
    chart_moat_heatmap,
    chart_score_distribution,
    view_to_dataframe,
)

df = view_to_dataframe(view)

# Top-line metrics
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Components", len(view.components))
c2.metric("Companies", len(view.companies))
sole = int(df["single_source"].sum()) if not df.empty else 0
c3.metric("Sole-source", sole)
priv = int((df["is_public"] == False).sum()) if not df.empty else 0  # noqa: E712
c4.metric("Private", priv)
c5.metric("Cost (USD)", f"${view.run.cost_usd:.2f}")

st.caption(
    f"Run **{view.run.id}** · provider **{view.run.provider}** · model **{view.run.model or '-'}** "
    f"· started **{view.run.started_at}** · status **{view.run.status}**"
)

st.markdown("---")

# Featured chart: top arbitrage opportunities
st.subheader(":fire: Top Arbitrage Opportunities")
st.caption(
    "Composite moat score boosted by an _arbitrage tilt_ — private status, "
    "capacity shortage, customer concentration, sole-source position."
)
st.plotly_chart(chart_top_arbitrage(df, top_n=12), use_container_width=True)

st.markdown("---")

cols = st.columns([1, 1])
with cols[0]:
    st.subheader(":bar_chart: Moat × Share Heatmap")
    st.caption("Where the moat clusters by share bucket across the stack.")
    st.plotly_chart(chart_moat_heatmap(df), use_container_width=True)
with cols[1]:
    st.subheader(":crystal_ball: Demand vs Share")
    st.caption("Bubble size = valuation (USD). Top-right = high share + high moat.")
    st.plotly_chart(chart_demand_vs_share(df), use_container_width=True)

st.markdown("---")
st.subheader(":chart_with_upwards_trend: Composite Score Distribution")
st.plotly_chart(chart_score_distribution(df), use_container_width=True)

st.markdown("---")
st.markdown(
    "**Next:** explore the sidebar pages →\n"
    "- :rocket: **Run** — kick off a fresh research run\n"
    "- :package: **Components** — drill into each layer of the AI stack\n"
    "- :office: **Companies** — filter + evidence drill-down\n"
    "- :brain: **Synthesis** — written investment thesis with downloadable report"
)
