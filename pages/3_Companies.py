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

from dashboard_utils import arbitrage_tilt, composite_with_tilt  # noqa: E402
from investment_agent.storage.repository import RunRepository  # noqa: E402

st.title(":office: Companies")

cfg = st.session_state.get("cfg")
if cfg is None or not cfg.get("chosen_run"):
    st.warning("Pick a run from the sidebar on the home page.")
    st.stop()

repo = RunRepository(Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.db")
view = repo.get_view(cfg["chosen_run"])
comp_by_id = {c.id: c.name for c in view.components}

with st.expander("Filters", expanded=True):
    public_filter = st.radio("Public/Private", ["all", "public", "private"], horizontal=True)
    sole_only = st.toggle("Sole-source only", value=False)
    min_score = st.slider("Min composite score", 0, 100, 0)
    moat_filter = st.text_input("Moat type contains (comma-sep)", value="")

def _passes(c) -> bool:
    if public_filter == "public" and not c.is_public:
        return False
    if public_filter == "private" and c.is_public:
        return False
    if sole_only and not c.single_source:
        return False
    composite = c.score.composite if (c.score and c.score.composite is not None) else 0
    if composite < min_score:
        return False
    if moat_filter.strip():
        needles = [m.strip().lower() for m in moat_filter.split(",") if m.strip()]
        haystack = " ".join(c.moat_types).lower()
        if not any(n in haystack for n in needles):
            return False
    return True


filtered = [c for c in view.companies if _passes(c)]
filtered.sort(
    key=lambda c: (c.score.composite if c.score and c.score.composite is not None else -1),
    reverse=True,
)

st.caption(f"{len(filtered)} of {len(view.companies)} companies matching filters")

rows = [
    {
        "name": c.name,
        "component": comp_by_id.get(c.component_id, "?"),
        "public": c.is_public,
        "ticker": c.ticker,
        "share": c.market_share_bucket,
        "share_pct": c.market_share_pct,
        "sole?": c.single_source,
        "moats": ", ".join(c.moat_types),
        "score": c.score.composite if c.score else None,
        "arb_tilt": arbitrage_tilt(c),
        "arb_score": composite_with_tilt(c),
    }
    for c in filtered
]
st.dataframe(rows, use_container_width=True)

st.divider()
st.subheader("Evidence drill-down")
names = [c.name for c in filtered]
chosen = st.selectbox("Company", names) if names else None
if chosen:
    c = next(x for x in filtered if x.name == chosen)
    cols = st.columns(3)
    cols[0].metric("Score", f"{c.score.composite:.0f}" if c.score and c.score.composite is not None else "-")
    cols[1].metric("Share", c.market_share_bucket or "-")
    cols[2].metric("Sole?", "yes" if c.single_source else "no")
    if c.score and c.score.rationale:
        st.markdown(f"**Rationale:** {c.score.rationale}")
    st.markdown(f"**Demand signal:** {c.demand_signal or '_n/a_'}")
    st.markdown(f"**Switching costs:** {c.switching_costs or '_n/a_'}")
    st.markdown("**Evidence**")
    if not c.evidence:
        st.caption("No evidence rows.")
    for ev in c.evidence:
        with st.container(border=True):
            st.markdown(f"**Claim:** {ev.claim or '_(unspecified)_'}")
            meta = f"_{ev.source_name or 'web'}_ via `{ev.tool_name or '-'}` · {ev.retrieved_at or ''}"
            st.caption(meta)
            if ev.source_url:
                st.markdown(f"[source]({ev.source_url})")
            if ev.snippet:
                st.write(ev.snippet)
