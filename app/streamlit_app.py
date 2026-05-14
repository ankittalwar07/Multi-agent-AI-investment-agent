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

from investment_agent.config import get_settings  # noqa: E402
from investment_agent.storage.repository import RunRepository, list_run_ids  # noqa: E402

st.set_page_config(
    page_title="AI Infra Investment Agent",
    page_icon=":dart:",
    layout="wide",
)

st.title("Multi-Agent AI Infrastructure Investment Agent")
st.write(
    "Decompose the AI-infrastructure stack, research each layer with sub-agents, "
    "and surface sole-source / majority-supplier opportunities."
)


def sidebar() -> dict:
    settings = get_settings()
    with st.sidebar:
        st.header("Configuration")
        provider = st.selectbox(
            "LLM provider",
            ["mock", "anthropic", "openai", "gemini"],
            index=["mock", "anthropic", "openai", "gemini"].index(settings.llm_provider)
            if settings.llm_provider in ("mock", "anthropic", "openai", "gemini")
            else 0,
        )
        default_models = {
            "mock": "mock-v1",
            "anthropic": "claude-sonnet-4-6",
            "openai": "gpt-4o",
            "gemini": "gemini-1.5-pro",
        }
        model = st.text_input("Model", value=settings.llm_model or default_models[provider])
        mock = st.toggle("Mock mode", value=(provider == "mock"))
        max_cost = st.slider("Max cost (USD)", min_value=0.5, max_value=50.0, value=float(settings.max_cost_usd), step=0.5)
        max_components = st.number_input(
            "Limit components (0 = all)", min_value=0, max_value=40, value=0, step=1
        )

        st.divider()
        st.header("Run picker")
        runs = list_run_ids(settings.run_output_dir)
        chosen_run = None
        if runs:
            chosen_run = st.selectbox("Existing runs", runs)
        else:
            st.caption("No runs yet.")

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

st.subheader("Selected run")
if cfg["chosen_run"]:
    try:
        repo = RunRepository(Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.db")
        view = repo.get_view(cfg["chosen_run"])
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Components", len(view.components))
        col2.metric("Companies", len(view.companies))
        col3.metric("Cost (USD)", f"${view.run.cost_usd:.4f}")
        col4.metric("Status", view.run.status)
        st.caption(f"Provider: {view.run.provider} | Model: {view.run.model or '-'} | Started: {view.run.started_at}")
    except Exception as e:
        st.error(f"Could not load run: {e}")
else:
    st.info("No run selected. Use the **Run** page to launch a new pipeline (or pick an existing run from the sidebar).")

st.divider()
st.markdown(
    "**Navigate** using the sidebar pages:\n"
    "- :rocket: **Run** — launch a new research pipeline\n"
    "- :package: **Components** — per-component summary\n"
    "- :office: **Companies** — drill into companies + evidence\n"
    "- :brain: **Synthesis** — top-N investable opportunities"
)
