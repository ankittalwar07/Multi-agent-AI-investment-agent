from __future__ import annotations

import json
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
    chart_score_distribution,
    chart_top_arbitrage,
    view_to_dataframe,
)
from investment_agent.storage.repository import RunRepository  # noqa: E402


def _to_csv(rows: list[dict]) -> str:
    import csv
    import io
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


st.title(":brain: Synthesis")
st.caption("Cross-stack investment thesis, themes, and downloadable report.")

cfg = st.session_state.get("cfg")
if cfg is None or not cfg.get("chosen_run"):
    st.warning("Pick a run from the sidebar on the home page.")
    st.stop()

run_dir = Path(cfg["output_dir"])
run_id = cfg["chosen_run"]
repo = RunRepository(run_dir / f"{run_id}.db")
view = repo.get_view(run_id)
df = view_to_dataframe(view)

json_path = run_dir / f"{run_id}.json"
md_path = run_dir / f"{run_id}.md"

report = None
if json_path.exists():
    try:
        report = json.loads(json_path.read_text())
    except json.JSONDecodeError:
        report = None

# Thesis summary card
if report and report.get("report") and report["report"].get("summary"):
    with st.container(border=True):
        st.markdown("### :pencil: Investment Thesis")
        st.write(report["report"]["summary"])

# Themes
themes = (report or {}).get("report", {}).get("themes", []) or []
if themes:
    st.markdown("### :bulb: Key Themes")
    cols = st.columns(min(len(themes), 3) or 1)
    for i, t in enumerate(themes):
        with cols[i % len(cols)]:
            with st.container(border=True):
                st.markdown(f"**Theme {i + 1}**")
                st.write(t)

st.markdown("---")
st.subheader(":trophy: Top by Arbitrage Score")
st.plotly_chart(chart_top_arbitrage(df, top_n=15), use_container_width=True)

st.markdown("---")
st.subheader(":chart_with_upwards_trend: Score Distribution")
st.plotly_chart(chart_score_distribution(df), use_container_width=True)

st.markdown("---")
st.subheader("Top 20 by composite score")
ranked = df.sort_values("arb_score", ascending=False).head(20).copy()
ranked.insert(0, "rank", range(1, len(ranked) + 1))
st.dataframe(
    ranked[
        ["rank", "name", "ticker", "component", "market_share_bucket", "single_source", "moat_types", "composite", "arb_tilt", "arb_score"]
    ],
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
cols = st.columns(3)
if md_path.exists():
    cols[0].download_button(
        ":page_facing_up: Download Markdown report",
        data=md_path.read_text(),
        file_name=md_path.name,
        use_container_width=True,
    )
if json_path.exists():
    cols[1].download_button(
        ":notebook_with_decorative_cover: Download JSON",
        data=json_path.read_text(),
        file_name=json_path.name,
        use_container_width=True,
    )
cols[2].download_button(
    ":bar_chart: Download CSV",
    data=_to_csv(ranked.to_dict(orient="records")),
    file_name=f"{run_id}-top.csv",
    use_container_width=True,
)
