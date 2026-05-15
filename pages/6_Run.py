from __future__ import annotations

import os
import sys
import threading
import time
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
from investment_agent.llm import MultiProviderLLM, get_provider  # noqa: E402
from investment_agent.storage.repository import RunRepository, list_run_ids  # noqa: E402

st.title("Run")

cfg = st.session_state.get("cfg")
if cfg is None:
    st.warning("Open the home page first to configure provider/model.")
    st.stop()


def _build_llm():
    """Return a single-provider or MultiProviderLLM depending on UI selection."""
    if cfg["mock"]:
        return get_provider("mock")
    if cfg["provider"] != "multi":
        return get_provider(cfg["provider"], model=cfg["model"], mock=False)
    # Multi: try gemini then groq, whichever is configured
    chain = []
    for name, model in [
        ("gemini", "gemini-2.0-flash"),
        ("groq", "llama-3.1-8b-instant"),
    ]:
        env = "GOOGLE_API_KEY" if name == "gemini" else "GROQ_API_KEY"
        if os.environ.get(env):
            try:
                chain.append(get_provider(name, model=model))
            except Exception:
                pass
    if not chain:
        st.error("No providers configured. Set GOOGLE_API_KEY and/or GROQ_API_KEY in Streamlit secrets.")
        st.stop()
    return MultiProviderLLM.from_providers(chain)


def _launch(opts: RunOptions, until_done: bool = False) -> str:
    settings = get_settings()
    pipeline = Pipeline(settings=settings, llm_factory=_build_llm)
    if until_done:
        result = pipeline.run_until_done(opts, max_iterations=30, sleep_between_s=15)
    else:
        result = pipeline.run(opts)
    return result.run_id


# ============== Two-tier flow ==============
st.markdown("### Step 1 — Quick triage")
st.caption(
    "One LLM call per component (~25 calls total) gets a sparse company list "
    "with moat / share / sole-source / one-line thesis. Cheap (~5x less tokens "
    "than deep dive). Use this to find what's interesting, then deep-dive on "
    "the names you actually care about."
)

colA, colB, colC = st.columns([1, 1, 2])

with colA:
    if st.button("Quick triage", type="primary"):
        opts = RunOptions(
            provider=cfg["provider"], model=cfg["model"], mock=cfg["mock"],
            max_components=cfg["max_components"],
            mode="triage",
        )
        st.session_state["run_in_progress"] = True
        st.session_state["run_thread_result"] = {"run_id": None}

        def _target():
            try:
                rid = _launch(opts, until_done=True)  # auto-resume on rate limits
                st.session_state["run_thread_result"]["run_id"] = rid
            except Exception as e:
                st.session_state["run_thread_result"]["error"] = str(e)
            finally:
                st.session_state["run_in_progress"] = False

        threading.Thread(target=_target, daemon=True).start()
        st.rerun()

with colB:
    if st.button("Full deep dive (slow)", type="secondary",
                  help="Runs the full ReAct loop on every company. Use only when you have token budget."):
        opts = RunOptions(
            provider=cfg["provider"], model=cfg["model"], mock=cfg["mock"],
            max_components=cfg["max_components"],
            mode="deep",
        )
        st.session_state["run_in_progress"] = True
        st.session_state["run_thread_result"] = {"run_id": None}

        def _target():
            try:
                rid = _launch(opts, until_done=True)
                st.session_state["run_thread_result"]["run_id"] = rid
            except Exception as e:
                st.session_state["run_thread_result"]["error"] = str(e)
            finally:
                st.session_state["run_in_progress"] = False

        threading.Thread(target=_target, daemon=True).start()
        st.rerun()

with colC:
    if cfg["mock"]:
        st.caption("_Demo mode on — runs are instant on hand-crafted data._")
    elif cfg["provider"] != "multi":
        st.caption(
            "_Tip: switch Provider to **multi** in the home sidebar — "
            "rotates Gemini ↔ Groq when one throttles._"
        )

# ============== Step 2 — Deep dive on selected ==============
runs_for_dive = list_run_ids(cfg["output_dir"])
if runs_for_dive:
    latest_for_dive = runs_for_dive[0]
    try:
        latest_repo = RunRepository(Path(cfg["output_dir"]) / f"{latest_for_dive}.db")
        latest_view = latest_repo.get_view(latest_for_dive)
        triage_companies = [
            c for c in latest_view.companies
            if c.extras.analysis_depth == "triage"
        ]
        if triage_companies:
            st.markdown("### Step 2 — Deep dive on selected companies")
            st.caption(
                f"You have {len(triage_companies)} triage-level companies in run "
                f"`{latest_for_dive}`. Pick the ones worth a full ReAct-loop "
                "analysis (P/E, ROIC, cited sources, scenario math, full thesis)."
            )
            options = [
                f"{c.name} ({c.ticker or '—'})  ·  comp: {next((cp.name for cp in latest_view.components if cp.id == c.component_id), '?')}  ·  score: {(c.score.composite if c.score else 0):.0f}"
                for c in sorted(
                    triage_companies,
                    key=lambda c: (c.score.composite if c.score else 0),
                    reverse=True,
                )
            ]
            picked = st.multiselect(
                "Companies to deepen",
                options,
                max_selections=15,
                placeholder="Pick 5-10 high-conviction names",
            )
            if st.button("Run deep dive on selected", type="primary",
                          disabled=len(picked) == 0):
                # Map back to company names
                picked_names = [opt.split(" (")[0] for opt in picked]
                st.session_state["run_in_progress"] = True
                st.session_state["run_thread_result"] = {"run_id": None}

                def _deepen():
                    settings = get_settings()
                    pipeline = Pipeline(settings=settings, llm_factory=_build_llm)
                    try:
                        result = pipeline.deep_dive_companies(
                            latest_for_dive, picked_names,
                            output_dir=cfg["output_dir"],
                        )
                        st.session_state["run_thread_result"]["run_id"] = latest_for_dive
                        st.session_state["run_thread_result"]["deep_summary"] = result
                    except Exception as e:
                        st.session_state["run_thread_result"]["error"] = str(e)
                    finally:
                        st.session_state["run_in_progress"] = False

                threading.Thread(target=_deepen, daemon=True).start()
                st.rerun()

        deep_summary = st.session_state.get("run_thread_result", {}).get("deep_summary")
        if deep_summary:
            st.success(
                f"Deep dive complete: {len(deep_summary.get('deepened', []))} companies deepened "
                f"(${deep_summary.get('cost_usd', 0):.4f} cost). "
                + (f"Errors: {deep_summary.get('errors', [])[:2]}"
                   if deep_summary.get('errors') else "")
            )
    except Exception:
        pass

# ============== Resume an existing partial run ==============
runs = list_run_ids(cfg["output_dir"])
partial_runs = []
for r in runs[:20]:  # check the most recent 20
    try:
        rep = RunRepository(Path(cfg["output_dir"]) / f"{r}.db")
        v = rep.get_view(r)
        if v.run.status in ("partial", "error", "running"):
            partial_runs.append((r, v.run.status, len(v.components), v.run.cost_usd))
    except Exception:
        pass

if partial_runs:
    st.markdown("### Resume an unfinished run")
    st.caption("Picks up exactly where the run left off — only re-researches non-done components.")
    options = [f"{r}  ·  {st_}  ·  {n} components  ·  ${c:.3f}"
               for r, st_, n, c in partial_runs]
    chosen = st.selectbox("Pick a run to resume", options, label_visibility="collapsed")
    chosen_rid = partial_runs[options.index(chosen)][0]
    if st.button("Resume this run", type="primary"):
        opts = RunOptions(
            provider="multi" if not cfg["mock"] else cfg["provider"],
            model=None, mock=cfg["mock"],
            max_components=cfg["max_components"],
            resume_run_id=chosen_rid,
        )
        st.session_state["run_in_progress"] = True
        st.session_state["run_thread_result"] = {"run_id": None}

        def _target():
            try:
                rid = _launch(opts, until_done=True)
                st.session_state["run_thread_result"]["run_id"] = rid
            except Exception as e:
                st.session_state["run_thread_result"]["error"] = str(e)
            finally:
                st.session_state["run_in_progress"] = False

        threading.Thread(target=_target, daemon=True).start()
        st.rerun()

# ============== Live status ==============
if st.session_state.get("run_in_progress"):
    st.info(
        ":hourglass_flowing_sand: Run in progress. Page auto-refreshes every 15s to show progress."
    )
    time.sleep(15)
    st.rerun()

# Show per-component status + event tail for the latest/chosen run.
latest = (
    st.session_state.get("run_thread_result", {}).get("run_id")
    or (runs[0] if runs else None)
)

if latest:
    st.markdown("---")
    st.subheader(f"Latest: {latest}")
    repo = RunRepository(Path(cfg["output_dir"]) / f"{latest}.db")
    view = repo.get_view(latest)
    cols = st.columns(5)
    cols[0].metric("Components", len(view.components))
    done_n = sum(1 for c in view.components if c.status == "done")
    cols[1].metric("Done", f"{done_n}/{len(view.components)}")
    cols[2].metric("Companies", len(view.companies))
    cols[3].metric("Cost (USD)", f"${view.run.cost_usd:.4f}")
    cols[4].metric("Status", view.run.status)

    st.subheader("Components")
    st.dataframe(
        [
            {"name": c.name, "category": c.category, "source": c.source, "status": c.status}
            for c in view.components
        ],
        use_container_width=True, hide_index=True,
    )

    st.subheader("Event log (latest 200)")
    st.dataframe(
        [
            {"ts": e.ts, "level": e.level, "node": e.node, "message": e.message}
            for e in view.events
        ],
        use_container_width=True, hide_index=True,
    )
else:
    st.caption("No runs yet. Click **Start new run** or **Run until done** to launch one.")
