from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from investment_agent.storage.repository import RunRepository  # noqa: E402

st.title("Components")

cfg = st.session_state.get("cfg")
if cfg is None or not cfg.get("chosen_run"):
    st.warning("Pick a run from the sidebar on the home page.")
    st.stop()

repo = RunRepository(Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.db")
view = repo.get_view(cfg["chosen_run"])

by_component: dict[str, list] = {}
for co in view.companies:
    by_component.setdefault(co.component_id, []).append(co)

st.write(f"**Run:** {cfg['chosen_run']}  •  **Provider:** {view.run.provider}")

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
        with st.expander("Companies"):
            st.dataframe(
                [
                    {
                        "name": c.name,
                        "ticker": c.ticker,
                        "share": c.market_share_bucket,
                        "sole?": c.single_source,
                        "score": (c.score.composite if c.score else None),
                    }
                    for c in cos_sorted
                ],
                use_container_width=True,
            )
