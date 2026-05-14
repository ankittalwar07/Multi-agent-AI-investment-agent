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

from dashboard_utils import (  # noqa: E402
    chart_component_concentration,
    chart_public_vs_private_treemap,
    view_to_dataframe,
)
from investment_agent.storage.repository import RunRepository  # noqa: E402

st.title(":package: Components")
st.caption("Each component is a layer of the AI infrastructure stack. Click into one to see incumbents, share, and the per-layer thesis.")

cfg = st.session_state.get("cfg")
if cfg is None or not cfg.get("chosen_run"):
    st.warning("Pick a run from the sidebar on the home page.")
    st.stop()

repo = RunRepository(Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.db")
view = repo.get_view(cfg["chosen_run"])
df = view_to_dataframe(view)

by_component: dict[str, list] = {}
for co in view.companies:
    by_component.setdefault(co.component_id, []).append(co)

# Top-level concentration view
st.subheader("Market concentration by component")
st.caption("Stacked share — taller stacks = more discovered share; tall single-color bars = high concentration.")
st.plotly_chart(chart_component_concentration(df), use_container_width=True)

st.markdown("---")
st.subheader("Public vs Private map")
st.caption("Treemap: tile area ≈ moat composite. Click into a tile to expand.")
st.plotly_chart(chart_public_vs_private_treemap(df), use_container_width=True)

st.markdown("---")
st.subheader("Per-component drill-down")

for comp in view.components:
    cos = by_component.get(comp.id, [])
    cos_sorted = sorted(
        cos,
        key=lambda c: (c.score.composite if c.score and c.score.composite is not None else -1),
        reverse=True,
    )
    top = cos_sorted[0] if cos_sorted else None
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 3])
        c1.markdown(f"### {comp.name}")
        c1.caption(f"{comp.category or '-'} · source={comp.source} · status={comp.status}")
        c2.metric("Companies", len(cos))
        c3.metric(
            "Top score",
            f"{top.score.composite:.0f}" if top and top.score and top.score.composite is not None else "-",
        )
        c4.write(f"**Top:** {top.name if top else '-'}")
        with st.expander("Incumbents in this layer"):
            st.dataframe(
                [
                    {
                        "name": c.name,
                        "ticker": c.ticker,
                        "public?": c.is_public,
                        "share": c.market_share_bucket,
                        "share %": c.market_share_pct,
                        "sole?": c.single_source,
                        "demand": c.demand_signal,
                        "score": (c.score.composite if c.score else None),
                    }
                    for c in cos_sorted
                ],
                use_container_width=True,
            )
