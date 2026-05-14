"""AI Datacenter Anatomy — visual entry point into the analysis.

Walks the entire stack from raw materials at the bottom (copper, rare earths,
industrial gases, ABF substrates, water) up through fabrication, silicon,
networking, power, cloud, models, and applications at the top. Each layer is
clickable: pick one, hand off to the Components page for the deep-dive.

Three views:
  1. The Stack — hero HTML/CSS layered diagram
  2. The Material Flow — plotly Sankey (raw inputs -> compute outputs)
  3. The Hierarchy — plotly sunburst, sized by # companies covered
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard_utils import (  # noqa: E402
    fmt_money, fmt_pct, rec_badge, structure_badge, view_to_dataframe,
)
from investment_agent.storage.repository import RunRepository  # noqa: E402

st.set_page_config(layout="wide")
st.title("AI Datacenter Anatomy")
st.caption(
    "What actually goes into an AI datacenter — bottom-up. From copper in the "
    "wires and ASML's EUV scanners, to NVIDIA accelerators on TSMC CoWoS, to "
    "Anthropic's Claude on Microsoft Azure. Each layer is a market with its "
    "own bottlenecks and incumbents — click any layer to drill into the analysis."
)

cfg = st.session_state.get("cfg")
if cfg is None or not cfg.get("chosen_run"):
    st.warning("Pick a run on the home page first.")
    st.stop()

repo = RunRepository(Path(cfg["output_dir"]) / f"{cfg['chosen_run']}.db")
view = repo.get_view(cfg["chosen_run"])
df = view_to_dataframe(view)


# ============================================================================
# Layer model — the canonical anatomy of an AI datacenter
# ============================================================================

LAYERS = [
    {
        "tier": "T+1",
        "name": "Applications",
        "color": "#0ea5e9",
        "icon": ":sparkles:",
        "blurb": "End-user products: ChatGPT, Claude, Gemini, Copilot, agent frameworks",
        "examples": ["ChatGPT", "Claude", "Gemini", "Perplexity", "Copilot"],
        "components": ["Agent Frameworks"],
    },
    {
        "tier": "T 5",
        "name": "Foundation Models",
        "color": "#a855f7",
        "icon": ":brain:",
        "blurb": "The model labs training frontier general-purpose intelligence",
        "examples": ["OpenAI", "Anthropic", "Google DeepMind", "Meta", "xAI"],
        "components": ["Foundation Model Labs"],
    },
    {
        "tier": "T 4",
        "name": "Cloud & Compute Platforms",
        "color": "#8b5cf6",
        "icon": ":cloud:",
        "blurb": "Where models train and serve — hyperscalers + GPU neoclouds",
        "examples": ["AWS", "Azure", "GCP", "CoreWeave", "Lambda"],
        "components": ["Hyperscale Cloud", "GPU Neoclouds"],
    },
    {
        "tier": "T 3",
        "name": "Datacenter Infrastructure",
        "color": "#6366f1",
        "icon": ":factory:",
        "blurb": "Power, cooling, water — the binding constraint of the AI buildout",
        "examples": ["Vertiv", "Schneider", "Eaton", "Xylem"],
        "components": ["Datacenter Power & Cooling", "Datacenter Water Infrastructure"],
    },
    {
        "tier": "T 2b",
        "name": "Networking & Interconnect",
        "color": "#3b82f6",
        "icon": ":satellite_antenna:",
        "blurb": "Switches, optical transceivers, NVLink — moves data inside the cluster",
        "examples": ["Broadcom", "Marvell", "Coherent", "Lumentum", "NVIDIA Mellanox"],
        "components": ["Datacenter Networking Silicon", "Optical Interconnect / Transceivers"],
    },
    {
        "tier": "T 2a",
        "name": "Compute Silicon + Memory",
        "color": "#06b6d4",
        "icon": ":computer:",
        "blurb": "AI accelerators (GPU/TPU) bonded to HBM stacks — the compute engine",
        "examples": ["NVIDIA", "AMD", "Google TPU", "SK Hynix", "Samsung", "Micron"],
        "components": [
            "AI Accelerator Silicon", "High-Bandwidth Memory (HBM)",
            "Inference Hardware Startups", "Edge / On-Device Inference",
        ],
    },
    {
        "tier": "T 1",
        "name": "Fabrication & Packaging",
        "color": "#14b8a6",
        "icon": ":wrench:",
        "blurb": "Where silicon is made: EUV lithography, leading-edge foundry, advanced packaging",
        "examples": ["ASML", "Carl Zeiss SMT", "TSMC", "Samsung Foundry", "Amkor"],
        "components": [
            "EUV Lithography", "Leading-edge Foundry",
            "Advanced Packaging (CoWoS / SoIC)",
        ],
    },
    {
        "tier": "T 0",
        "name": "Raw Materials & Utilities",
        "color": "#f59e0b",
        "icon": ":pick:",
        "blurb": "Copper, rare earths, industrial gases, photoresist, ABF substrates, water — the physical foundation",
        "examples": [
            "Freeport-McMoRan", "MP Materials", "Linde",
            "Shin-Etsu", "Ibiden", "Xylem",
        ],
        "components": [
            "Copper", "Rare Earths & Specialty Metals", "Industrial Gases",
            "Specialty Semiconductor Chemicals", "Chip Substrates (ABF)",
        ],
    },
]


def _layer_stats(layer: dict) -> dict:
    """Aggregate # companies, # BUYs, top pick across all components in this layer."""
    cos = df[df["component"].isin(layer["components"])]
    if cos.empty:
        return {"n_companies": 0, "n_buys": 0, "top_pick": None}
    buys = cos[cos["recommendation"].isin(["STRONG_BUY", "BUY"])]
    top = (
        buys.sort_values("expected_return_12m", ascending=False).iloc[0]
        if not buys.empty else cos.iloc[0]
    )
    return {
        "n_companies": len(cos),
        "n_buys": len(buys),
        "top_pick": top["name"],
        "top_ticker": top.get("ticker"),
        "top_rec": top.get("recommendation"),
        "top_ret": top.get("expected_return_12m"),
        "constrained": (cos["supply_status"].fillna("") == "constrained").any(),
        "sole_source": bool(cos["single_source"].any()),
    }


# ============================================================================
# 1. THE STACK — hero HTML/CSS layered diagram
# ============================================================================

st.markdown("## The Stack")
st.caption("Top-down: from end-user apps down to the copper in the wires.")

for layer in LAYERS:
    stats = _layer_stats(layer)
    constraint_chip = ""
    if stats.get("constrained"):
        constraint_chip = (
            '<span style="background:#dc2626;color:white;padding:2px 8px;'
            'border-radius:10px;font-size:11px;font-weight:600;margin-left:6px;">'
            'SUPPLY CONSTRAINED</span>'
        )
    sole_chip = ""
    if stats.get("sole_source"):
        sole_chip = (
            '<span style="background:#7c3aed;color:white;padding:2px 8px;'
            'border-radius:10px;font-size:11px;font-weight:600;margin-left:6px;">'
            'SOLE-SOURCE</span>'
        )

    examples_html = "".join(
        f'<span style="background:rgba(255,255,255,0.10);color:#e5e7eb;'
        f'padding:3px 10px;border-radius:10px;font-size:12px;margin:2px 4px 2px 0;'
        f'display:inline-block;">{e}</span>'
        for e in layer["examples"]
    )

    top_str = ""
    if stats.get("top_pick"):
        ret = stats.get("top_ret")
        ret_str = f" · +{ret*100:.0f}% exp" if ret is not None else ""
        ticker_str = f" ({stats['top_ticker']})" if stats.get("top_ticker") else ""
        top_str = (
            f'<div style="margin-top:6px;font-size:13px;color:#cbd5e1;">'
            f'<strong>Top pick:</strong> {stats["top_pick"]}{ticker_str}{ret_str}'
            f'</div>'
        )

    html = f"""
    <div style="
        border-left: 6px solid {layer['color']};
        background: linear-gradient(90deg, {layer['color']}15 0%, transparent 100%);
        padding: 14px 20px;
        margin-bottom: 8px;
        border-radius: 6px;
    ">
        <div style="display:flex;align-items:center;justify-content:space-between;">
            <div>
                <span style="color:{layer['color']};font-weight:700;font-size:11px;
                       letter-spacing:1.5px;text-transform:uppercase;">
                    {layer['tier']}
                </span>
                <span style="font-size:18px;font-weight:700;color:#f1f5f9;margin-left:10px;">
                    {layer['name']}
                </span>
                {constraint_chip}{sole_chip}
            </div>
            <div style="color:#94a3b8;font-size:13px;">
                {stats['n_companies']} companies · {stats['n_buys']} BUYs
            </div>
        </div>
        <div style="color:#94a3b8;font-size:13px;margin-top:4px;">{layer['blurb']}</div>
        <div style="margin-top:8px;">{examples_html}</div>
        {top_str}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

st.write("")

# Layer-to-component drill-down — feeds the Components page via session state.
all_layer_components = []
for layer in LAYERS:
    for c in layer["components"]:
        all_layer_components.append((layer["name"], c))

st.markdown("### Drill into a layer")
col_l, col_c, col_btn = st.columns([2, 3, 1])
chosen_layer = col_l.selectbox("Layer", [l["name"] for l in LAYERS], index=6)  # default to Compute Silicon
chosen_layer_obj = next(l for l in LAYERS if l["name"] == chosen_layer)
chosen_component = col_c.selectbox(
    "Component", chosen_layer_obj["components"],
    index=0,
)
if col_btn.button("Open in Components →", type="primary"):
    st.session_state["jump_to_component"] = chosen_component
    st.switch_page("pages/2_Components.py")


st.markdown("---")


# ============================================================================
# 2. THE MATERIAL FLOW — Sankey
# ============================================================================

st.markdown("## The Material Flow")
st.caption(
    "How raw materials flow through fabrication into AI compute. Width of each "
    "ribbon ≈ how critical the input is to the final product."
)

# Define nodes in a sensible order: materials -> fab -> silicon -> system -> compute -> apps
nodes = [
    # Tier 0 - Raw materials (0-5)
    "Copper", "Rare Earths", "Industrial Gases", "Photoresist & Chemicals",
    "ABF Substrates", "Water",
    # Tier 1 - Fabrication (6-8)
    "EUV Lithography (ASML)", "Leading-edge Foundry (TSMC)", "CoWoS Packaging (TSMC)",
    # Tier 2 - Silicon (9-11)
    "AI Accelerator (NVIDIA / AMD / TPU)", "HBM Memory (SK Hynix / Samsung)",
    "Networking Silicon (Broadcom)",
    # Tier 3 - System (12-14)
    "AI Server / Rack", "Datacenter Power & Cooling", "Optical Interconnect",
    # Tier 4 - Cluster/Cloud (15-17)
    "AI Cluster / Pod", "Hyperscale Cloud", "GPU Neoclouds",
    # Tier 5 - Models (18)
    "Foundation Models",
    # Tier 6 - Apps (19)
    "AI Applications",
]

NODE_COLORS = (
    ["#f59e0b"] * 6        # raw
    + ["#14b8a6"] * 3      # fab
    + ["#06b6d4"] * 3      # silicon
    + ["#3b82f6"] * 3      # system
    + ["#6366f1", "#8b5cf6", "#8b5cf6"]  # cluster, cloud, neocloud
    + ["#a855f7"]          # models
    + ["#0ea5e9"]          # apps
)

# Edges: (source, target, value)
links = [
    # Materials → Fab
    (0, 12, 8), (0, 13, 5),  # Copper into AI Server, into Power/Cooling
    (1, 9, 2),              # Rare Earths into Accelerator
    (2, 6, 6), (2, 7, 6),   # Industrial Gases into EUV + Foundry
    (3, 6, 7), (3, 7, 8),   # Photoresist + chemicals into EUV + Foundry
    (4, 9, 7),              # ABF Substrate into Accelerator
    (5, 13, 6),             # Water into power/cooling

    # Fab → Silicon
    (6, 7, 12),             # EUV → Foundry
    (7, 9, 12), (7, 10, 8), (7, 11, 4),  # Foundry → Accelerator/HBM/Networking
    (8, 9, 10), (8, 10, 4),  # CoWoS → Accelerator + HBM bonded

    # Silicon → System
    (9, 12, 14),            # Accelerator → Server
    (10, 12, 8),            # HBM → Server
    (11, 12, 5),            # Networking → Server
    (13, 12, 4),            # Power/Cooling → Server
    (14, 12, 4),            # Optical → Server

    # System → Cluster
    (12, 15, 18),

    # Cluster → Cloud
    (15, 16, 14), (15, 17, 6),

    # Cloud → Models
    (16, 18, 14), (17, 18, 4),

    # Models → Apps
    (18, 19, 18),
]

sources, targets, values = zip(*links)

sankey = go.Figure(go.Sankey(
    arrangement="snap",
    node=dict(
        pad=18, thickness=18, line=dict(color="rgba(255,255,255,0.2)", width=0.5),
        label=nodes, color=NODE_COLORS,
    ),
    link=dict(
        source=list(sources), target=list(targets), value=list(values),
        color=["rgba(148, 163, 184, 0.18)"] * len(sources),
        hovertemplate="<b>%{source.label}</b> → <b>%{target.label}</b><br>relative criticality: %{value}<extra></extra>",
    ),
))
sankey.update_layout(
    margin=dict(l=0, r=0, t=10, b=0), height=540,
    font=dict(size=12, color="#e5e7eb"),
    paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(sankey, use_container_width=True)

st.caption(
    "_Width is illustrative of how dependent the downstream layer is on the "
    "upstream input — not a literal volume measure._"
)

st.markdown("---")


# ============================================================================
# 3. THE HIERARCHY — Sunburst (clickable filtering)
# ============================================================================

st.markdown("## The Hierarchy")
st.caption(
    "Hierarchical breakdown of the universe, sized by number of companies covered. "
    "Click any wedge to zoom; click center to reset."
)

# Build sunburst data: AI Datacenter -> Tier -> Component -> Companies
TIER_GROUPING = {
    "raw_materials": "Tier 0 · Materials & Utilities",
    "semiconductor_capex": "Tier 1 · Fabrication",
    "semiconductor_manufacturing": "Tier 1 · Fabrication",
    "compute_silicon": "Tier 2 · Compute & Memory",
    "memory": "Tier 2 · Compute & Memory",
    "networking": "Tier 2 · Networking",
    "facilities": "Tier 3 · Datacenter Infra",
    "compute_platform": "Tier 4 · Cloud Platforms",
    "model_layer": "Tier 5 · Foundation Models",
    "data_layer": "Tier 6 · Data & Tooling",
    "tooling": "Tier 6 · Data & Tooling",
}
TIER_COLORS = {
    "Tier 0 · Materials & Utilities": "#f59e0b",
    "Tier 1 · Fabrication": "#14b8a6",
    "Tier 2 · Compute & Memory": "#06b6d4",
    "Tier 2 · Networking": "#3b82f6",
    "Tier 3 · Datacenter Infra": "#6366f1",
    "Tier 4 · Cloud Platforms": "#8b5cf6",
    "Tier 5 · Foundation Models": "#a855f7",
    "Tier 6 · Data & Tooling": "#0ea5e9",
}

ids: list[str] = []
labels: list[str] = []
parents: list[str] = []
values: list[float] = []
colors: list[str] = []

ROOT_ID = "AI Datacenter"
ids.append(ROOT_ID); labels.append("AI Datacenter"); parents.append(""); values.append(0); colors.append("#0f172a")

# Tier ring
tier_added: dict[str, str] = {}
for c in view.components:
    tier_label = TIER_GROUPING.get(c.category or "", "Tier ? · Other")
    if tier_label not in tier_added:
        tier_added[tier_label] = tier_label
        ids.append(tier_label); labels.append(tier_label); parents.append(ROOT_ID); values.append(0)
        colors.append(TIER_COLORS.get(tier_label, "#475569"))

# Component ring
for c in view.components:
    tier_label = TIER_GROUPING.get(c.category or "", "Tier ? · Other")
    n = int((df["component"] == c.name).sum())
    if n == 0: continue
    ids.append(c.name); labels.append(c.name); parents.append(tier_label); values.append(n)
    colors.append(TIER_COLORS.get(tier_label, "#475569"))

sunburst = go.Figure(go.Sunburst(
    ids=ids, labels=labels, parents=parents, values=values,
    branchvalues="total",
    marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0.4)", width=1)),
    hovertemplate="<b>%{label}</b><br>%{value} companies<extra></extra>",
    insidetextorientation="radial",
))
sunburst.update_layout(
    margin=dict(l=0, r=0, t=10, b=0), height=560,
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e5e7eb"),
)
st.plotly_chart(sunburst, use_container_width=True)

# ============================================================================
# Footer / summary
# ============================================================================

st.markdown("---")
st.markdown("### Where to next?")
nav_cols = st.columns(4)
with nav_cols[0]:
    st.page_link("pages/2_Components.py", label="Components", icon=":package:")
with nav_cols[1]:
    st.page_link("pages/3_Investment_Thesis.py", label="Investment Thesis", icon=":bar_chart:")
with nav_cols[2]:
    st.page_link("pages/4_Investor_Council.py", label="Investor Council", icon=":classical_building:")
with nav_cols[3]:
    st.page_link("pages/5_Portfolio.py", label="Portfolio", icon=":bookmark_tabs:")
