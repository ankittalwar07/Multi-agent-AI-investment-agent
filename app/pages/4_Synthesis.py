from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

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


st.title("Synthesis")

cfg = st.session_state.get("cfg")
if cfg is None or not cfg.get("chosen_run"):
    st.warning("Pick a run from the sidebar on the home page.")
    st.stop()

run_dir = Path(cfg["output_dir"])
run_id = cfg["chosen_run"]
repo = RunRepository(run_dir / f"{run_id}.db")
view = repo.get_view(run_id)

# Load JSON + markdown report if present
json_path = run_dir / f"{run_id}.json"
md_path = run_dir / f"{run_id}.md"

report = None
if json_path.exists():
    try:
        report = json.loads(json_path.read_text())
    except json.JSONDecodeError:
        report = None

if report and report.get("report"):
    st.subheader("Summary")
    st.write(report["report"].get("summary", "_no summary_"))

    st.subheader("Top Companies")
    top_companies = report["report"].get("top_companies", []) or []
    st.dataframe(top_companies, use_container_width=True)

    st.subheader("Themes")
    for t in report["report"].get("themes", []) or []:
        st.markdown(f"- {t}")
else:
    st.info("No synthesis report found for this run yet.")

st.divider()
st.subheader("Top 20 by composite score")
ranked = sorted(
    view.companies,
    key=lambda c: (c.score.composite if c.score and c.score.composite is not None else -1),
    reverse=True,
)
comp_by_id = {c.id: c.name for c in view.components}
rows = [
    {
        "rank": i + 1,
        "name": c.name,
        "ticker": c.ticker,
        "component": comp_by_id.get(c.component_id, "?"),
        "share": c.market_share_bucket,
        "sole?": c.single_source,
        "moats": ", ".join(c.moat_types),
        "score": c.score.composite if c.score else None,
    }
    for i, c in enumerate(ranked[:20])
]
st.dataframe(rows, use_container_width=True)

st.divider()
cols = st.columns(3)
if md_path.exists():
    cols[0].download_button(
        "Download Markdown report", data=md_path.read_text(), file_name=md_path.name
    )
if json_path.exists():
    cols[1].download_button(
        "Download JSON report", data=json_path.read_text(), file_name=json_path.name
    )
cols[2].download_button(
    "Download companies CSV",
    data=_to_csv(rows),
    file_name=f"{run_id}-top.csv",
)
