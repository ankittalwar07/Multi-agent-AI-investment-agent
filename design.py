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


# ============== Deep-dive queue (session-state, cross-page) ==============
#
# A user-curated list of company names to pull from triage-tier sparse data
# into full deep-dive analysis. Buttons live on the Home top-5 cards,
# Investment Thesis header, Investor Council BUY lists, and Component picks.
# A single "Run deep dive on queue" button in the sidebar fires them all.

_QUEUE_KEY = "deep_dive_queue"


def _queue() -> set:
    if _QUEUE_KEY not in st.session_state:
        st.session_state[_QUEUE_KEY] = set()
    return st.session_state[_QUEUE_KEY]


def queue_contents() -> list[str]:
    return sorted(_queue())


def queue_size() -> int:
    return len(_queue())


def queue_has(name: str) -> bool:
    return name in _queue()


def add_to_queue(name: str) -> None:
    _queue().add(name)


def remove_from_queue(name: str) -> None:
    _queue().discard(name)


def clear_queue() -> None:
    _queue().clear()


def deep_dive_button(
    company_name: str,
    analysis_depth: str | None,
    *,
    key_prefix: str,
    label_add: str = "+ Deep dive",
    label_remove: str = "✗ Queued",
    label_done: str = "✓ Deep",
) -> None:
    """Render an inline button to add/remove a company from the deep-dive queue.

    Skipped when the company is already at 'deep' depth.
    Use a unique `key_prefix` per location so Streamlit doesn't collide.
    """
    if (analysis_depth or "triage") == "deep":
        st.markdown(
            f"<span style='display:inline-block;background:rgba(16,185,129,0.10);"
            f"border:1px solid #10b981;color:#10b981;padding:2px 8px;"
            f"border-radius:3px;font-size:10px;font-weight:600;letter-spacing:0.06em;"
            f"text-transform:uppercase;'>{label_done}</span>",
            unsafe_allow_html=True,
        )
        return
    queued = queue_has(company_name)
    safe = company_name.replace(" ", "_").replace("'", "").replace("/", "_")[:40]
    key = f"q_{key_prefix}_{safe}"
    if queued:
        if st.button(label_remove, key=key, help="Remove from deep-dive queue"):
            remove_from_queue(company_name)
            st.rerun()
    else:
        if st.button(label_add, key=key, help="Queue for deep-dive analysis"):
            add_to_queue(company_name)
            st.rerun()


def _default_deep_dive_runner(names: list[str]) -> None:
    """Built-in callback that fires Pipeline.deep_dive_companies on a thread.

    Reads the active run + provider config from st.session_state['cfg'].
    Posts results into st.session_state['deep_dive_result'].
    """
    import os
    import threading

    cfg = st.session_state.get("cfg") or {}
    run_id = cfg.get("chosen_run")
    if not run_id:
        st.toast("Pick a run first.", icon="ℹ")
        return

    def _build_llm():
        from investment_agent.llm import MultiProviderLLM, get_provider
        if cfg.get("mock"):
            return get_provider("mock")
        prov = cfg.get("provider", "gemini")
        if prov != "multi":
            return get_provider(prov, model=cfg.get("model"), mock=False)
        chain = []
        for name, model in [("gemini", "gemini-2.0-flash"),
                              ("groq", "llama-3.1-8b-instant")]:
            env = "GOOGLE_API_KEY" if name == "gemini" else "GROQ_API_KEY"
            if os.environ.get(env):
                try:
                    chain.append(get_provider(name, model=model))
                except Exception:
                    pass
        # Ollama (local) as a no-rate-limit fallback if reachable
        try:
            import urllib.request
            base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            urllib.request.urlopen(
                base.rstrip("/v1").rstrip("/") + "/api/tags", timeout=1.5,
            )
            chain.append(get_provider("ollama", model="qwen2.5:7b"))
        except Exception:
            pass
        if not chain:
            return get_provider("mock")
        return MultiProviderLLM.from_providers(chain)

    from investment_agent.config import Settings as _Settings
    from investment_agent.graph.build import Pipeline
    pipeline = Pipeline(settings=_Settings(), llm_factory=_build_llm)

    st.session_state["deep_dive_in_progress"] = True
    st.session_state["deep_dive_result"] = None

    def _target():
        try:
            res = pipeline.deep_dive_companies(
                run_id, names, output_dir=cfg.get("output_dir"),
            )
            st.session_state["deep_dive_result"] = res
            clear_queue()
        except Exception as e:
            st.session_state["deep_dive_result"] = {"error": str(e)}
        finally:
            st.session_state["deep_dive_in_progress"] = False

    threading.Thread(target=_target, daemon=True).start()
    st.toast(f"Deep dive started on {len(names)} companies", icon=":dart:")


def render_queue_sidebar(run_id: str | None, on_run_callback=None) -> None:
    """Render the queue panel in the sidebar. Call once per page (after apply_design).

    If no on_run_callback is supplied, uses the built-in deep-dive runner
    that reads cfg from session_state.
    """
    on_run = on_run_callback or _default_deep_dive_runner
    contents = queue_contents()
    with st.sidebar:
        st.markdown("---")
        st.markdown("### Deep-dive queue")
        if not contents:
            st.caption(
                "Mark interesting companies with **+ Deep dive** from anywhere "
                "in the dashboard. Run them all at once from here."
            )
            return
        st.caption(f"**{len(contents)}** companies queued")
        for name in contents[:10]:
            cols = st.columns([5, 1])
            cols[0].markdown(
                f"<div style='color:#cbd5e1;font-size:12px;padding:2px 0;'>"
                f"• {name}</div>",
                unsafe_allow_html=True,
            )
            if cols[1].button("✗", key=f"qx_{name[:30]}",
                                help=f"Remove {name}"):
                remove_from_queue(name)
                st.rerun()
        if len(contents) > 10:
            st.caption(f"… and {len(contents) - 10} more")

        c1, c2 = st.columns(2)
        run_disabled = run_id is None
        in_progress = st.session_state.get("deep_dive_in_progress", False)
        if c1.button("Run dive", type="primary",
                       disabled=run_disabled or in_progress,
                       key="run_queue_btn",
                       help="Run full ReAct loop on every queued company"):
            on_run(list(contents))
        if c2.button("Clear", key="clear_queue_btn"):
            clear_queue()
            st.rerun()


def render_deep_dive_status() -> None:
    """Show the running / completed status banner. Call once per page below the title."""
    if st.session_state.get("deep_dive_in_progress"):
        st.info(
            ":hourglass_flowing_sand: Deep dive running in background. "
            "Reload this page after a minute to see updated data."
        )
    res = st.session_state.get("deep_dive_result")
    if res:
        if res.get("error"):
            st.error(f"Deep dive failed: {res['error']}")
        else:
            st.success(
                f"Deep dive complete: **{len(res.get('deepened', []))}** companies deepened "
                f"(${res.get('cost_usd', 0):.4f}). Their Investment Thesis pages now have "
                "full earnings power + risk + scenario data."
            )
        st.session_state["deep_dive_result"] = None
