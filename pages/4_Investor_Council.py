"""Investor Council — cross-portfolio voting matrix and per-investor BUY lists.

Each persona reviews every company in the universe through their lens. This
page surfaces:
- Consensus distribution across the universe
- A voting matrix of the most-loved names
- Each investor's BUY list (so you can pivot to "what would Buffett buy?")
- Divergent picks (alpha-rich names where the council disagrees)
"""
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
    CONSENSUS_COLORS, CONSENSUS_LABELS,
    chart_council_score_distribution, chart_council_voting_matrix,
    consensus_badge, rec_badge, view_to_dataframe,
)
from investment_agent.council.personas import COUNCIL  # noqa: E402
from investment_agent.storage.repository import RunRepository  # noqa: E402

st.title("Investor Council")
st.caption(
    "Six legendary investors review every name in the universe through their lens. "
    "Names with unanimous BUY are the highest-confidence ideas; divided council = "
    "the most alpha-rich (and most controversial)."
)

cfg = st.session_state.get("cfg")
if cfg is None or not cfg.get("chosen_run"):
    st.warning("Pick a run on the home page first.")
    st.stop()

repo = RunRepository(Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.db")
view = repo.get_view(cfg["chosen_run"])
df = view_to_dataframe(view)

if df.empty or df["council_consensus"].isna().all():
    st.warning("This run was generated before the council was added. Regenerate the run from the home page to populate council verdicts.")
    st.stop()

# ============== Council bios ==============
st.markdown("### The council")


def _initials(name: str) -> str:
    parts = [w for w in name.split() if w and w[0].isalpha()]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


PERSONA_ACCENT = {
    "buffett": "#22d3ee", "munger": "#a3e635", "lynch": "#fbbf24",
    "graham": "#94a3b8", "druck": "#10b981", "wood": "#f472b6",
    "marks": "#fb923c", "burry": "#f43f5e", "dalio": "#60a5fa",
}

cols = st.columns(min(len(COUNCIL), 3))
for i, p in enumerate(COUNCIL):
    with cols[i % len(cols)]:
        buy_count = 0
        for c in view.companies:
            for vd in c.extras.council_verdicts:
                if vd.get("investor_key") == p.key and vd.get("verdict") in ("STRONG_BUY", "BUY"):
                    buy_count += 1
                    break
        accent = PERSONA_ACCENT.get(p.key, "#22d3ee")
        with st.container(border=True):
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:10px;'>"
                f"<div style='width:38px;height:38px;border-radius:50%;"
                f"background:{accent}15;border:1px solid {accent};"
                f"display:flex;align-items:center;justify-content:center;"
                f"color:{accent};font-weight:600;font-size:13px;flex-shrink:0;'>"
                f"{_initials(p.name)}</div>"
                f"<div>"
                f"<div style='font-weight:600;color:#f1f5f9;font-size:15px;'>{p.name}</div>"
                f"<div style='color:#64748b;font-size:11px;letter-spacing:0.04em;"
                f"text-transform:uppercase;margin-top:1px;'>"
                f"{p.firm} &nbsp;·&nbsp; {p.style}</div></div></div>"
                f"<div style='color:#cbd5e1;font-size:12px;line-height:1.55;"
                f"font-style:italic;border-left:2px solid {accent}40;padding-left:10px;"
                f"margin-bottom:10px;'>"
                f"\"{p.famous_quote}\"</div>"
                f"<div style='color:#94a3b8;font-size:12px;'>"
                f"<span style='color:{accent};font-weight:600;font-size:14px;'>{buy_count}</span>"
                f" &nbsp;BUY{'s' if buy_count != 1 else ''} in this run</div>",
                unsafe_allow_html=True,
            )

st.markdown("---")

# ============== Consensus distribution ==============
left, right = st.columns([2, 1])
with left:
    st.markdown("### Consensus across the universe")
    cons_counts = df["council_consensus"].value_counts()
    # Build a colored bar
    import plotly.graph_objects as go
    ordered = ["UNANIMOUS_STRONG_BUY", "UNANIMOUS_BUY", "MAJORITY_BUY", "DIVIDED", "MAJORITY_AVOID"]
    counts_ord = [int(cons_counts.get(k, 0)) for k in ordered]
    fig = go.Figure(go.Bar(
        x=[CONSENSUS_LABELS[k] for k in ordered],
        y=counts_ord,
        marker=dict(color=[CONSENSUS_COLORS[k] for k in ordered]),
        text=counts_ord, textposition="outside",
    ))
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300,
                       xaxis_title="", yaxis_title="# companies")
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.markdown("### Council score distribution")
    st.plotly_chart(chart_council_score_distribution(df), use_container_width=True)

st.markdown("---")

# ============== Voting matrix ==============
st.markdown("### Voting matrix — top 25 by council score")
st.caption(
    "Cell legend: **SB** = Strong Buy, **B** = Buy, **H** = Hold, **P** = Pass, **A** = Avoid. "
    "Hover any cell to see that investor's specific reasoning."
)
st.plotly_chart(chart_council_voting_matrix(df, view, top_n=25), use_container_width=True)

st.markdown("---")

# ============== Per-investor BUY list ==============
st.markdown("### Per-investor BUY list")
st.caption("What would each member of the council buy in this universe?")

investor_tabs = st.tabs([p.name for p in COUNCIL])
for tab, persona in zip(investor_tabs, COUNCIL):
    with tab:
        st.markdown(f"**Lens:** {persona.philosophy}")
        st.markdown("**Favors:**")
        for f in persona.favors[:4]:
            st.markdown(f"- {f}")
        st.markdown("**Avoids:**")
        for d in persona.dislikes[:3]:
            st.markdown(f"- {d}")

        # Collect this persona's verdicts
        rows = []
        for c in view.companies:
            for vd in c.extras.council_verdicts:
                if vd.get("investor_key") == persona.key:
                    rows.append({
                        "Company": c.name,
                        "Ticker": c.ticker or "—",
                        "Component": next((cp.name for cp in view.components if cp.id == c.component_id), "?"),
                        "Verdict": vd.get("verdict"),
                        "Conviction": vd.get("conviction"),
                        "Reasoning": (vd.get("reasoning") or [""])[0],
                    })
                    break

        rdf = pd.DataFrame(rows)
        if rdf.empty:
            st.caption("No verdicts found.")
            continue
        order = {"STRONG_BUY": 0, "BUY": 1, "HOLD": 2, "PASS": 3, "AVOID": 4}
        rdf["_o"] = rdf["Verdict"].map(order).fillna(5)
        rdf = rdf.sort_values(["_o", "Company"]).drop(columns=["_o"])

        # Show BUYs as highlighted cards, then the rest as a table
        buys = rdf[rdf["Verdict"].isin(["STRONG_BUY", "BUY"])]
        if not buys.empty:
            st.markdown(f"#### {persona.name}'s BUYs ({len(buys)})")
            for _, row in buys.head(15).iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1, 5])
                    c1.markdown(f"**{row['Company']}** ({row['Ticker']})")
                    c1.caption(row["Component"])
                    c2.markdown(rec_badge(row["Verdict"]) + f"<br><small>{row['Conviction']}</small>",
                                unsafe_allow_html=True)
                    c3.write(row["Reasoning"])

        with st.expander(f"Full ranking ({len(rdf)} names)"):
            st.dataframe(rdf, use_container_width=True, hide_index=True)

st.markdown("---")

# ============== Divergence — alpha-rich picks ==============
st.markdown("### Divergent picks (alpha-rich, controversial)")
st.caption(
    "Names where the council is split — usually the most interesting setups. "
    "If you can resolve the disagreement, that's where the edge is."
)
divided = df[df["council_consensus"] == "DIVIDED"].copy()
divided = divided.sort_values("expected_return_12m", ascending=False).head(10)

if divided.empty:
    st.caption("No divided names in this run — the council was uncommonly unified.")
else:
    show = divided[["name", "ticker", "component", "recommendation",
                    "expected_return_12m", "council_buy_count",
                    "council_score_pct"]].copy()
    show["BUY votes"] = show["council_buy_count"].fillna(0).astype(int).astype(str) + f"/{len(COUNCIL)}"
    show["Council %"] = show["council_score_pct"].fillna(0).round(0).astype(int).astype(str) + "%"
    show["Exp 12m"] = (show["expected_return_12m"].fillna(0) * 100).round(0).astype(int).astype(str) + "%"
    st.dataframe(
        show[["name", "ticker", "component", "recommendation", "Exp 12m", "BUY votes", "Council %"]].rename(
            columns={"name": "Company", "ticker": "Ticker",
                     "component": "Component", "recommendation": "Our rec"}
        ),
        use_container_width=True, hide_index=True,
    )
