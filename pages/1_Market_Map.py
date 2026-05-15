"""Market Map — value-chain visualization with per-layer structure & demand/supply."""
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
from design import render_queue_sidebar, render_deep_dive_status  # noqa: E402

from dashboard_utils import (  # noqa: E402
    fmt_pct, rec_badge, structure_badge, view_to_dataframe,
)
from investment_agent.storage.repository import RunRepository  # noqa: E402

st.title("Market Map — AI infrastructure value chain")
st.caption(
    "Bottom-up walk from raw materials &rarr; fabrication &rarr; silicon &rarr; "
    "datacenter &rarr; cloud &rarr; models &rarr; tooling. Each tier shows market "
    "structure, supply status, top pick, and expected return."
)

cfg = st.session_state.get("cfg")
if cfg is None or not cfg.get("chosen_run"):
    st.warning("Pick a run on the home page first.")
    st.stop()

render_queue_sidebar(cfg.get("chosen_run"))
render_deep_dive_status()

repo = RunRepository(Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.db")
view = repo.get_view(cfg["chosen_run"])
df = view_to_dataframe(view)

# Group components by category (we sort the tiers in display order)
TIER_ORDER = {
    "raw_materials": ("Tier 0", "Raw materials & utilities"),
    "semiconductor_capex": ("Tier 1", "Semiconductor capex"),
    "semiconductor_manufacturing": ("Tier 1", "Semiconductor manufacturing"),
    "compute_silicon": ("Tier 2", "Compute silicon"),
    "memory": ("Tier 2", "Memory"),
    "networking": ("Tier 2", "Networking"),
    "facilities": ("Tier 3", "Datacenter facilities"),
    "compute_platform": ("Tier 4", "Compute platforms"),
    "model_layer": ("Tier 5", "Foundation models"),
    "data_layer": ("Tier 6", "Data layer"),
    "tooling": ("Tier 6", "Tooling"),
    "uncategorized": ("Tier ?", "Uncategorized"),
}

comp_by_id = {c.id: c for c in view.components}

# Map each component -> aggregate stats from companies
def component_stats(comp_id: str) -> dict:
    cos = df[df["component"] == comp_by_id[comp_id].name]
    if cos.empty:
        return {}
    # Structure inferred from the most common value across companies (most are the same)
    struct_modes = cos["structure"].dropna().mode()
    supply_modes = cos["supply_status"].dropna().mode()
    actionable = cos[cos["recommendation"].isin(["STRONG_BUY", "BUY"])].sort_values(
        "expected_return_12m", ascending=False
    )
    top = actionable.iloc[0] if not actionable.empty else cos.iloc[0]
    return {
        "n": len(cos),
        "structure": struct_modes.iloc[0] if not struct_modes.empty else None,
        "supply": supply_modes.iloc[0] if not supply_modes.empty else None,
        "top_name": top["name"],
        "top_ticker": top.get("ticker"),
        "top_rec": top.get("recommendation"),
        "top_ret": top.get("expected_return_12m"),
        "sole_source": bool(cos["single_source"].any()),
    }


# Render by tier
tiers: dict[tuple, list] = {}
for c in view.components:
    tier_key, tier_label = TIER_ORDER.get(c.category or "uncategorized", ("Tier ?", c.category or "Other"))
    tiers.setdefault((tier_key, tier_label), []).append(c)

for (tier_key, tier_label), comps in sorted(tiers.items()):
    st.markdown(f"### {tier_key} — {tier_label}")
    cols = st.columns(min(len(comps), 3) or 1)
    for i, comp in enumerate(comps):
        stats = component_stats(comp.id)
        with cols[i % len(cols)]:
            with st.container(border=True):
                badges = []
                if stats.get("structure"):
                    badges.append(structure_badge(stats["structure"]))
                if stats.get("supply") == "constrained":
                    badges.append(
                        '<span style="background:#dc2626;color:white;padding:3px 8px;'
                        'border-radius:12px;font-size:11px;font-weight:600;">SUPPLY CONSTRAINED</span>'
                    )
                if stats.get("sole_source"):
                    badges.append(
                        '<span style="background:#7c3aed;color:white;padding:3px 8px;'
                        'border-radius:12px;font-size:11px;font-weight:600;">SOLE-SOURCE</span>'
                    )
                st.markdown(
                    f"**{comp.name}**<br/>" + " ".join(badges),
                    unsafe_allow_html=True,
                )
                if stats:
                    st.caption(f"{stats['n']} companies covered")
                    if stats.get("top_name"):
                        ticker_str = f" ({stats['top_ticker']})" if stats.get("top_ticker") else ""
                        ret_str = (
                            f" · +{stats['top_ret'] * 100:.0f}% exp"
                            if stats.get("top_ret") is not None else ""
                        )
                        st.markdown(
                            f"**Top pick:** {stats['top_name']}{ticker_str}{ret_str}<br/>"
                            f"{rec_badge(stats.get('top_rec'))}",
                            unsafe_allow_html=True,
                        )
                if comp.description:
                    st.caption(comp.description)
    st.write("")
