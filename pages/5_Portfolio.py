"""Portfolio — weighted aggregation of BUY-rated names with expected return."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from design import apply_design  # noqa: E402
apply_design()

from dashboard_utils import (  # noqa: E402
    chart_treemap_by_recommendation, fmt_money, fmt_pct, fmt_price,
    rec_badge, view_to_dataframe,
)
from investment_agent.storage.repository import RunRepository  # noqa: E402

st.title("Portfolio Brief")
st.caption("Aggregated view of all BUY-rated names. Default weights are equal-conviction-weighted.")

cfg = st.session_state.get("cfg")
if cfg is None or not cfg.get("chosen_run"):
    st.warning("Pick a run on the home page first.")
    st.stop()

repo = RunRepository(Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.db")
view = repo.get_view(cfg["chosen_run"])
df = view_to_dataframe(view)

# Filter actionable
actionable = df[df["recommendation"].isin(["STRONG_BUY", "BUY"])].copy()
if actionable.empty:
    st.info("No actionable BUY recommendations in this run.")
    st.stop()

# Assign weights based on conviction
conv_w = {"HIGH": 3.0, "MEDIUM": 2.0, "LOW": 1.0}
rec_w = {"STRONG_BUY": 2.0, "BUY": 1.0}
actionable["weight_raw"] = (
    actionable["conviction"].map(conv_w).fillna(1.0)
    * actionable["recommendation"].map(rec_w).fillna(1.0)
)
actionable["weight"] = actionable["weight_raw"] / actionable["weight_raw"].sum()
actionable["contribution"] = actionable["weight"] * actionable["expected_return_12m"].fillna(0)
portfolio_return = actionable["contribution"].sum()

# Top KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("Positions", len(actionable))
k2.metric("Public", int((actionable["is_public"] == True).sum()))  # noqa: E712
k3.metric("Private", int((actionable["is_public"] == False).sum()))  # noqa: E712
k4.metric("Expected portfolio return (12m)", f"+{portfolio_return * 100:.1f}%")

st.markdown("---")

# Treemap
st.markdown("### Recommendation map — area = market cap, color = expected return")
st.plotly_chart(chart_treemap_by_recommendation(df), use_container_width=True)

st.markdown("---")

# Sector exposure
st.markdown("### Sector exposure (by weight)")
sector = actionable.groupby("component", as_index=False).agg(
    weight=("weight", "sum"),
    n=("name", "count"),
    avg_return=("expected_return_12m", "mean"),
)
sector = sector.sort_values("weight", ascending=False)
sector["weight_pct"] = (sector["weight"] * 100).round(1)
sector["avg_return_pct"] = (sector["avg_return"] * 100).round(1)
st.dataframe(
    sector[["component", "n", "weight_pct", "avg_return_pct"]].rename(
        columns={"component": "Component", "n": "# names", "weight_pct": "Weight %", "avg_return_pct": "Avg return %"}
    ),
    use_container_width=True, hide_index=True,
)

st.markdown("---")

# Position table
st.markdown("### Position list (ranked by weight × expected return)")
positions = actionable.sort_values("contribution", ascending=False).copy()
positions["Weight"] = (positions["weight"] * 100).round(1).astype(str) + "%"
positions["Expected 12m"] = (positions["expected_return_12m"].fillna(0) * 100).round(0).astype(int).astype(str) + "%"
positions["Contribution"] = (positions["contribution"] * 100).round(2).astype(str) + "%"

display = positions[[
    "name", "ticker", "component", "recommendation", "conviction",
    "stock_price", "pe_forward", "Weight", "Expected 12m", "Contribution",
]].rename(columns={
    "name": "Company", "ticker": "Ticker", "component": "Component",
    "recommendation": "Rec", "conviction": "Conv",
    "stock_price": "Price", "pe_forward": "P/E fwd",
})
st.dataframe(display, use_container_width=True, hide_index=True)

st.markdown("---")

# Themes from synthesizer
import json
json_path = Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.json"
if json_path.exists():
    try:
        data = json.loads(json_path.read_text())
        themes = (data.get("report") or {}).get("themes") or []
        summary = (data.get("report") or {}).get("summary")
    except Exception:
        themes = []
        summary = None
    if summary:
        st.markdown("### Cross-stack thesis")
        st.write(summary)
    if themes:
        st.markdown("### Key themes")
        for t in themes:
            st.markdown(f"- {t}")

# Downloads
st.markdown("---")
cols = st.columns(3)
md_path = Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.md"
if md_path.exists():
    cols[0].download_button("Download Markdown report", data=md_path.read_text(), file_name=md_path.name)
if json_path.exists():
    cols[1].download_button("Download JSON", data=json_path.read_text(), file_name=json_path.name)
cols[2].download_button(
    "Download positions CSV",
    data=positions.to_csv(index=False),
    file_name=f"{cfg['chosen_run']}-positions.csv",
)
