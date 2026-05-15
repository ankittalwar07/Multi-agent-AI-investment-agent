from __future__ import annotations

import sys
import threading
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

from investment_agent.config import get_settings  # noqa: E402
from investment_agent.graph.build import Pipeline, RunOptions  # noqa: E402
from investment_agent.llm import get_provider  # noqa: E402
from investment_agent.storage.repository import RunRepository, list_run_ids  # noqa: E402

st.title("Run")

cfg = st.session_state.get("cfg")
if cfg is None:
    st.warning("Open the home page first to configure provider/model.")
    st.stop()


def _launch(opts: RunOptions) -> str:
    settings = get_settings()

    def _llm_factory():
        return get_provider(cfg["provider"], model=cfg["model"], mock=cfg["mock"])

    pipeline = Pipeline(settings=settings, llm_factory=_llm_factory)
    result = pipeline.run(opts)
    return result.run_id


col_a, col_b = st.columns([1, 3])
with col_a:
    if st.button("Start new run", type="primary"):
        opts = RunOptions(
            provider=cfg["provider"],
            model=cfg["model"],
            mock=cfg["mock"],
            max_components=cfg["max_components"],
        )
        st.session_state["run_in_progress"] = True
        st.session_state["run_thread_result"] = {"run_id": None}

        def _target():
            try:
                rid = _launch(opts)
                st.session_state["run_thread_result"]["run_id"] = rid
            except Exception as e:  # noqa: BLE001
                st.session_state["run_thread_result"]["error"] = str(e)
            finally:
                st.session_state["run_in_progress"] = False

        threading.Thread(target=_target, daemon=True).start()
        st.rerun()

with col_b:
    if st.session_state.get("run_in_progress"):
        st.info("Run in progress... (refresh every few seconds to see updates)")

# Show per-component status + event tail for the chosen run.
runs = list_run_ids(cfg["output_dir"])
latest = st.session_state.get("run_thread_result", {}).get("run_id") or (runs[0] if runs else None)

if latest:
    st.subheader(f"Status: {latest}")
    repo = RunRepository(Path(cfg["output_dir"]) / f"{latest}.db")
    view = repo.get_view(latest)
    cols = st.columns(4)
    cols[0].metric("Components", len(view.components))
    cols[1].metric("Companies", len(view.companies))
    cols[2].metric("Cost (USD)", f"${view.run.cost_usd:.4f}")
    cols[3].metric("Status", view.run.status)

    st.subheader("Components")
    st.dataframe(
        [
            {"name": c.name, "category": c.category, "source": c.source, "status": c.status}
            for c in view.components
        ],
        use_container_width=True,
    )

    st.subheader("Event log (latest 200)")
    st.dataframe(
        [
            {"ts": e.ts, "level": e.level, "node": e.node, "message": e.message}
            for e in view.events
        ],
        use_container_width=True,
    )
else:
    st.caption("No runs yet. Click **Start new run** to launch one.")
