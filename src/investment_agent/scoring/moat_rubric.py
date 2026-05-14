"""Composite moat-strength scoring (pure python, no LLM).

Composite is 0–100. Hard rule: `single_source=True` is only honored if at
least 2 independent citations support it; otherwise the sole-source points
collapse to zero.
"""
from __future__ import annotations

from dataclasses import dataclass

RUBRIC_VERSION = "moat-v1"

SHARE_BUCKET_POINTS: dict[str, float] = {
    "<10": 0,
    "10-25": 5,
    "25-50": 12,
    "50-75": 20,
    ">75": 25,
    "sole": 25,
}

# Known moat-type points (each non-trivial type contributes; soft cap applied below).
IP_MOAT_TYPES = {"ip", "tech", "patent", "process", "scale"}
REG_MOAT_TYPES = {"regulatory", "export_control", "license", "compliance"}


@dataclass
class MoatScore:
    sole_source_pts: float
    share_pts: float
    ip_pts: float
    regulatory_pts: float
    switching_pts: float
    demand_pts: float
    composite: float
    rationale: str

    def to_dict(self) -> dict[str, float | str]:
        return {
            "sole_source_pts": self.sole_source_pts,
            "share_pts": self.share_pts,
            "ip_pts": self.ip_pts,
            "regulatory_pts": self.regulatory_pts,
            "switching_pts": self.switching_pts,
            "demand_pts": self.demand_pts,
            "composite": self.composite,
            "rationale": self.rationale,
        }


def _switching_pts(text: str | None) -> float:
    if not text:
        return 0
    t = text.lower()
    if any(w in t for w in ("very high", "extreme", "lock-in", "locked in")):
        return 10
    if "high" in t:
        return 7
    if "medium" in t or "moderate" in t:
        return 4
    return 1


def _demand_pts(text: str | None) -> float:
    if not text:
        return 0
    t = text.lower()
    if any(w in t for w in ("accelerating", "exponential", "+100%", "shortage", "backlog")):
        return 10
    if any(w in t for w in ("strong", "growing", "+", "yoy")):
        return 7
    if "stable" in t or "steady" in t:
        return 4
    return 1


def score_company(
    *,
    single_source: bool | None,
    independent_citations_for_sole_source: int = 0,
    market_share_bucket: str | None,
    moat_types: list[str] | None,
    switching_costs: str | None,
    demand_signal: str | None,
) -> MoatScore:
    # Sole-source: requires >=2 independent citations.
    if single_source and independent_citations_for_sole_source >= 2:
        sole_pts = 30
        sole_note = "sole-source confirmed by >=2 independent citations"
    elif single_source:
        sole_pts = 0
        sole_note = "single_source claimed but insufficient independent citations; not credited"
    else:
        sole_pts = 0
        sole_note = "not sole-source"

    share_pts = SHARE_BUCKET_POINTS.get(market_share_bucket or "", 0)

    moat_types_set = {(m or "").lower() for m in (moat_types or [])}
    ip_pts = 15 if moat_types_set & IP_MOAT_TYPES else 0
    reg_pts = 10 if moat_types_set & REG_MOAT_TYPES else 0

    switching_pts = _switching_pts(switching_costs)
    demand_pts = _demand_pts(demand_signal)

    composite = (
        sole_pts + share_pts + ip_pts + reg_pts + switching_pts + demand_pts
    )

    rationale = (
        f"{sole_note}. share_bucket={market_share_bucket} (+{share_pts}). "
        f"ip/tech moat=+{ip_pts}; regulatory moat=+{reg_pts}. "
        f"switching=+{switching_pts}; demand=+{demand_pts}. "
        f"composite={composite}/100."
    )

    return MoatScore(
        sole_source_pts=sole_pts,
        share_pts=share_pts,
        ip_pts=ip_pts,
        regulatory_pts=reg_pts,
        switching_pts=switching_pts,
        demand_pts=demand_pts,
        composite=composite,
        rationale=rationale,
    )
