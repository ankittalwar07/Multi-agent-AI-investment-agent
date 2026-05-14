"""Component Deep Dive — pick a layer, see structure, demand/supply, top picks, risks."""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard_utils import (  # noqa: E402
    chart_demand_supply, chart_share_pie,
    fmt_money, fmt_pct, fmt_price, rec_badge, structure_badge,
    view_to_dataframe,
)
from investment_agent.storage.repository import RunRepository  # noqa: E402

st.title("Component Deep Dive")

cfg = st.session_state.get("cfg")
if cfg is None or not cfg.get("chosen_run"):
    st.warning("Pick a run on the home page first.")
    st.stop()

repo = RunRepository(Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.db")
view = repo.get_view(cfg["chosen_run"])
df = view_to_dataframe(view)

# Component selector at top — honors a hand-off from the Datacenter Anatomy page
comp_names = sorted({c.name for c in view.components})
jump_to = st.session_state.pop("jump_to_component", None)
if jump_to and jump_to in comp_names:
    default_idx = comp_names.index(jump_to)
elif "AI Accelerator Silicon" in comp_names:
    default_idx = comp_names.index("AI Accelerator Silicon")
else:
    default_idx = 0
component = st.selectbox("Component", comp_names, index=default_idx)

comp_obj = next(c for c in view.components if c.name == component)
sub = df[df["component"] == component].copy().sort_values(
    "market_share_pct", ascending=False, na_position="last"
)

# ----- Header strip -----
struct_modes = sub["structure"].dropna().mode()
supply_modes = sub["supply_status"].dropna().mode()
structure = struct_modes.iloc[0] if not struct_modes.empty else None
supply = supply_modes.iloc[0] if not supply_modes.empty else None
sole = bool(sub["single_source"].any())

badges = []
if structure:
    badges.append(structure_badge(structure))
if supply == "constrained":
    badges.append('<span style="background:#dc2626;color:white;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;">DEMAND &gt; SUPPLY</span>')
if sole:
    badges.append('<span style="background:#7c3aed;color:white;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;">SOLE-SOURCE PRESENT</span>')

st.markdown(
    f"### {component}<br/>{' '.join(badges)}",
    unsafe_allow_html=True,
)
if comp_obj.description:
    st.caption(comp_obj.description)
if comp_obj.category:
    st.caption(f"Category: `{comp_obj.category}` · {len(sub)} companies covered")

st.markdown("---")

# ----- Charts row -----
c1, c2 = st.columns([1, 1])
with c1:
    st.plotly_chart(chart_share_pie(sub, component), use_container_width=True)
with c2:
    st.plotly_chart(chart_demand_supply(sub, component), use_container_width=True)

st.markdown("---")

# ----- Companies in this layer -----
st.markdown("### Companies in this layer")
display = sub[[
    "name", "ticker", "is_public", "market_share_pct", "single_source",
    "pe_trailing", "pe_forward", "ev_ebitda", "expected_return_12m",
    "recommendation", "conviction",
]].rename(columns={
    "name": "Company",
    "ticker": "Ticker",
    "is_public": "Public?",
    "market_share_pct": "Share %",
    "single_source": "Sole?",
    "pe_trailing": "P/E (TTM)",
    "pe_forward": "P/E (fwd)",
    "ev_ebitda": "EV/EBITDA",
    "expected_return_12m": "Expected 12m",
    "recommendation": "Rec",
    "conviction": "Conv",
})
st.dataframe(display, use_container_width=True, hide_index=True)

# ----- Top picks for this component -----
actionable = sub[sub["recommendation"].isin(["STRONG_BUY", "BUY"])].copy()
if not actionable.empty:
    st.markdown("### Recommended picks in this layer")
    for _, row in actionable.iterrows():
        rec = row["recommendation"]
        exp_ret_pct = (row["expected_return_12m"] or 0) * 100
        with st.container(border=True):
            top_cols = st.columns([3, 1, 1, 2, 2])
            top_cols[0].markdown(
                f"**{row['name']}** "
                + (f"({row['ticker']})" if row.get("ticker") else "")
                + f"<br/>{rec_badge(rec)}",
                unsafe_allow_html=True,
            )
            top_cols[1].metric("Price", fmt_price(row["stock_price"]))
            top_cols[2].metric("Exp 12m", f"+{exp_ret_pct:.0f}%")
            top_cols[3].metric("P/E fwd", f"{row['pe_forward']:.1f}x" if row.get("pe_forward") else "—")
            top_cols[4].metric("EV/EBITDA", f"{row['ev_ebitda']:.1f}x" if row.get("ev_ebitda") else "—")
            if row.get("thesis_summary"):
                st.write(row["thesis_summary"])

# ----- Risks across this layer -----
risk_strings: list[str] = []
for c in view.companies:
    if c.component_id != comp_obj.id:
        continue
    for r in c.extras.risks:
        risk_strings.append(f"_{c.name}_ — {r}")
if risk_strings:
    st.markdown("### Key risks in this layer")
    for r in risk_strings[:10]:
        st.markdown(f"- {r}")
