"""Per-persona rubrics — deterministic scoring functions.

Each function takes a `CompanyView` (dict of all the company's fields:
financials + extras + moat composite + structure + supply status) and
returns an InvestorVerdict in that investor's voice.

These rubrics are intentionally explainable: every verdict points to the
concrete fields that drove it. That's the analytical value-add — you can
audit why each council member voted the way they did.
"""
from __future__ import annotations

from typing import Any

from .verdicts import VERDICT_SCORE, Conviction, InvestorVerdict, Verdict

# Type alias for clarity. In practice this is a dict built from CompanyRow +
# CompanyExtras with all the fields the rubrics inspect.
CompanyView = dict[str, Any]


# ---------------- helpers ----------------

def _v(verdict: str, conviction: str, reasoning: list[str],
       pos: str | None, concern: str | None) -> dict:
    return dict(
        verdict=verdict, conviction=conviction,
        reasoning=reasoning, top_positive=pos, top_concern=concern,
    )


def _moat(c: CompanyView) -> float:
    return float(c.get("composite") or 0)


def _pe_t(c): return c.get("pe_trailing")
def _pe_f(c): return c.get("pe_forward")
def _peg(c): return c.get("peg")
def _rev_fwd(c): return c.get("revenue_growth_fwd")
def _rev_ttm(c): return c.get("revenue_growth_ttm")
def _op_mgn(c): return c.get("operating_margin")
def _fcf(c): return c.get("fcf_yield")
def _ev_ebitda(c): return c.get("ev_ebitda")
def _div(c): return c.get("dividend_yield")
def _is_public(c): return bool(c.get("is_public"))
def _ticker(c): return c.get("ticker")
def _bucket(c): return c.get("market_share_bucket")
def _sole(c): return bool(c.get("single_source"))
def _structure(c): return (c.get("structure") or "").lower()
def _supply(c): return (c.get("supply_status") or "").lower()
def _demand(c): return (c.get("demand_signal") or "").lower()
def _exp_ret(c): return c.get("expected_return_12m") or 0


# ---------------- Warren Buffett ----------------

def buffett(c: CompanyView) -> dict:
    """Wonderful business + fair price + understandable."""
    reasoning: list[str] = []
    moat = _moat(c)
    pe_f = _pe_f(c)
    op = _op_mgn(c)

    # Hard pass: not understandable / no earnings (private without comps)
    if not _is_public(c) and not _ticker(c):
        return _v("PASS", "MEDIUM",
                  ["Private and unlisted — outside my circle of competence for direct investment."],
                  None,
                  "No public access; cannot underwrite.")

    # Negative earnings: skip
    if pe_f is None or pe_f <= 0:
        return _v("AVOID", "HIGH",
                  ["No clear path to positive forward earnings — not investable for me."],
                  None, "Negative/missing forward earnings.")

    # Score the quality + price
    quality_score = 0
    if moat >= 70: quality_score += 2; reasoning.append(f"Outstanding moat (composite {moat:.0f}/100) — wide and durable.")
    elif moat >= 50: quality_score += 1; reasoning.append(f"Solid moat (composite {moat:.0f}/100).")
    else: reasoning.append(f"Moat is thin (composite {moat:.0f}/100) — I'd want more.")

    if op is not None and op >= 0.25: quality_score += 1; reasoning.append(f"Excellent operating margin ({op*100:.0f}%) — pricing power.")
    elif op is not None and op >= 0.15: reasoning.append(f"Adequate margin ({op*100:.0f}%).")

    price_score = 0
    if pe_f <= 18: price_score += 2; reasoning.append(f"Reasonable forward P/E of {pe_f:.1f}x.")
    elif pe_f <= 25: price_score += 1; reasoning.append(f"P/E forward {pe_f:.1f}x — fair, not cheap.")
    else: reasoning.append(f"Forward P/E {pe_f:.1f}x is rich for my taste.")

    total = quality_score + price_score
    if quality_score >= 3 and price_score >= 1:
        verdict, conv = "STRONG_BUY", "HIGH"
    elif total >= 3:
        verdict, conv = "BUY", "HIGH"
    elif total >= 2:
        verdict, conv = "BUY", "MEDIUM"
    elif total >= 1:
        verdict, conv = "HOLD", "MEDIUM"
    else:
        verdict, conv = "PASS", "MEDIUM"

    return _v(verdict, conv, reasoning,
              pos=f"Moat composite {moat:.0f}/100",
              concern="Valuation rich" if pe_f and pe_f > 25 else "Watch capital allocation")


# ---------------- Charlie Munger ----------------

def munger(c: CompanyView) -> dict:
    """Pristine quality — would rather pay up for a great business than discount a mediocre one."""
    reasoning: list[str] = []
    moat = _moat(c)
    op = _op_mgn(c)
    pe_f = _pe_f(c)

    if moat < 50:
        return _v("AVOID", "HIGH",
                  [f"Moat composite {moat:.0f}/100 is mediocre — life is too short for cigar butts."],
                  None,
                  "Quality too low; I avoid the swamp.")

    if op is None or op < 0.15:
        return _v("HOLD", "MEDIUM",
                  [f"Margins ({(op or 0)*100:.0f}%) don't reflect a true competitive advantage."],
                  None, "Margins suggest commodity-like economics.")

    score = 0
    if moat >= 75: score += 2; reasoning.append("Truly excellent business — durable, capital-light advantages.")
    elif moat >= 60: score += 1; reasoning.append(f"Strong business (moat {moat:.0f}).")
    if op >= 0.30: score += 1; reasoning.append(f"Outstanding margins ({op*100:.0f}%) — clear pricing power.")
    if pe_f and pe_f <= 30: score += 1; reasoning.append("Valuation is reasonable for the quality.")

    # Munger pays up for quality but won't pay anything
    if pe_f and pe_f > 45:
        return _v("HOLD", "MEDIUM",
                  reasoning + [f"At {pe_f:.0f}x forward earnings even great businesses become poor investments."],
                  pos="Quality is real",
                  concern=f"Forward P/E {pe_f:.0f}x leaves no margin for error.")

    if score >= 3:
        verdict, conv = "STRONG_BUY", "HIGH"
    elif score >= 2:
        verdict, conv = "BUY", "HIGH"
    elif score >= 1:
        verdict, conv = "BUY", "MEDIUM"
    else:
        verdict, conv = "HOLD", "LOW"

    return _v(verdict, conv, reasoning,
              pos=f"Quality compounds ({moat:.0f}/100)",
              concern="Inverted thinking: what could break this moat?")


# ---------------- Peter Lynch ----------------

def lynch(c: CompanyView) -> dict:
    """GARP. PEG < 1.5 is the key gate."""
    reasoning: list[str] = []
    peg = _peg(c)
    rev_fwd = _rev_fwd(c)
    pe_f = _pe_f(c)

    if pe_f is None or pe_f <= 0:
        return _v("PASS", "MEDIUM",
                  ["No forward earnings — I prefer stories I can underwrite."],
                  None, "No earnings to anchor PEG.")

    if rev_fwd is None or rev_fwd < 0.05:
        return _v("HOLD", "MEDIUM",
                  ["Forward growth is weak — this isn't the runway I look for."],
                  None, "Insufficient growth for GARP.")

    score = 0
    if peg is not None and peg <= 1.0:
        score += 3; reasoning.append(f"Excellent PEG ({peg:.2f}) — growth not yet priced in.")
    elif peg is not None and peg <= 1.5:
        score += 2; reasoning.append(f"Solid PEG ({peg:.2f}).")
    elif peg is not None and peg <= 2.5:
        reasoning.append(f"PEG ({peg:.2f}) is rich but tolerable for the growth.")
    else:
        if peg is not None:
            reasoning.append(f"PEG ({peg:.2f}) is too high — growth is fully priced.")

    if rev_fwd >= 0.30: score += 2; reasoning.append(f"Strong growth runway ({rev_fwd*100:.0f}% forward).")
    elif rev_fwd >= 0.15: score += 1; reasoning.append(f"Decent growth ({rev_fwd*100:.0f}% forward).")

    if _exp_ret(c) >= 0.20: score += 1; reasoning.append("Asymmetric upside — potential multi-bagger.")

    if score >= 4:
        verdict, conv = "STRONG_BUY", "HIGH"
    elif score >= 3:
        verdict, conv = "BUY", "HIGH"
    elif score >= 2:
        verdict, conv = "BUY", "MEDIUM"
    elif score >= 1:
        verdict, conv = "HOLD", "MEDIUM"
    else:
        verdict, conv = "PASS", "MEDIUM"

    return _v(verdict, conv, reasoning,
              pos=f"Growth {rev_fwd*100:.0f}% fwd; PEG {peg or 'n/a'}",
              concern="Story rich vs PEG" if peg and peg > 2 else "Watch the growth runway")


# ---------------- Benjamin Graham ----------------

def graham(c: CompanyView) -> dict:
    """Deep value with margin of safety."""
    reasoning: list[str] = []
    pe_t = _pe_t(c)
    pe_f = _pe_f(c)
    ev_ebitda = _ev_ebitda(c)
    div = _div(c)

    if not _is_public(c):
        return _v("PASS", "HIGH",
                  ["No market price, no margin of safety — I require listed securities."],
                  None, "Unlisted; I cannot value it.")

    if pe_t is None or pe_t <= 0:
        return _v("AVOID", "HIGH",
                  [f"Trailing P/E unavailable or negative — speculation, not investment."],
                  None, "Negative trailing earnings.")

    score = 0
    if pe_t <= 12: score += 3; reasoning.append(f"Deeply discounted at {pe_t:.1f}x trailing earnings — true margin of safety.")
    elif pe_t <= 18: score += 2; reasoning.append(f"Modest valuation at {pe_t:.1f}x trailing.")
    elif pe_t <= 25: reasoning.append(f"Trailing P/E {pe_t:.1f}x — borderline.")
    else: reasoning.append(f"Trailing P/E {pe_t:.1f}x is too rich for a defensive position.")

    if pe_f and pe_f <= 12: score += 1; reasoning.append(f"Forward P/E ({pe_f:.1f}x) confirms the value setup.")

    if ev_ebitda is not None and ev_ebitda <= 10:
        score += 1; reasoning.append(f"EV/EBITDA ({ev_ebitda:.1f}x) is reasonable.")
    elif ev_ebitda is not None and ev_ebitda > 18:
        reasoning.append(f"EV/EBITDA ({ev_ebitda:.1f}x) is uncomfortably high.")

    if div and div >= 0.02:
        score += 1; reasoning.append(f"Dividend yield ({div*100:.1f}%) provides a defensive cushion.")

    if score >= 4:
        verdict, conv = "STRONG_BUY", "HIGH"
    elif score >= 3:
        verdict, conv = "BUY", "HIGH"
    elif score >= 2:
        verdict, conv = "BUY", "MEDIUM"
    elif score >= 1:
        verdict, conv = "HOLD", "LOW"
    else:
        verdict, conv = "AVOID", "MEDIUM"

    return _v(verdict, conv, reasoning,
              pos=f"P/E TTM {pe_t:.1f}x" if pe_t else "Defensive setup",
              concern="No margin of safety" if pe_t and pe_t > 25 else "Watch leverage")


# ---------------- Stanley Druckenmiller ----------------

def druck(c: CompanyView) -> dict:
    """Concentrated bets where macro + supply/demand setup align."""
    reasoning: list[str] = []
    supply = _supply(c)
    demand = _demand(c)
    sole = _sole(c)
    bucket = _bucket(c) or ""
    rev_fwd = _rev_fwd(c) or 0

    # Druck wants a clear setup
    setup_strength = 0
    if supply == "constrained":
        setup_strength += 2; reasoning.append("Supply-constrained — pricing power, capacity backlog, the holy grail.")
    if sole or bucket in ("sole", ">75"):
        setup_strength += 2; reasoning.append("Sole or dominant supplier — owns the bottleneck.")
    if any(w in demand for w in ("shortage", "backlog", "accelerating", "exponential", "sold out")):
        setup_strength += 1; reasoning.append("Demand acceleration confirms the macro thesis.")
    if rev_fwd >= 0.25:
        setup_strength += 1; reasoning.append(f"Forward revenue ({rev_fwd*100:.0f}%) backs the secular call.")

    # Druck won't bet on weak setups
    if setup_strength == 0:
        return _v("PASS", "MEDIUM",
                  ["No clear macro/capacity edge — not the kind of asymmetric setup I bet large on."],
                  None, "No edge in this setup.")

    # Concentrated bet sizing
    if setup_strength >= 4:
        verdict, conv = "STRONG_BUY", "HIGH"
        reasoning.append("This is the kind of trade you 'go for the jugular' on.")
    elif setup_strength >= 3:
        verdict, conv = "BUY", "HIGH"
    elif setup_strength >= 2:
        verdict, conv = "BUY", "MEDIUM"
    else:
        verdict, conv = "HOLD", "MEDIUM"

    return _v(verdict, conv, reasoning,
              pos="Supply > demand setup" if supply == "constrained" else "Secular tailwind",
              concern="Crowded trade risk" if bucket in ("sole", ">75") else "Watch macro rollover")


# ---------------- Cathie Wood ----------------

def wood(c: CompanyView) -> dict:
    """Disruptive innovation, S-curve early innings."""
    reasoning: list[str] = []
    rev_fwd = _rev_fwd(c) or 0
    moat = _moat(c)
    structure = _structure(c)

    INNOVATION_COMPONENTS = {
        "AI Accelerator Silicon", "Foundation Model Labs", "GPU Neoclouds",
        "Inference Hardware Startups", "Edge / On-Device Inference",
        "Vector Databases", "Agent Frameworks", "Synthetic Data",
        "Data Labeling / RLHF", "LLM Observability",
    }
    component = c.get("component", "")
    is_innovation = component in INNOVATION_COMPONENTS

    # Mature, low-growth = pass
    if rev_fwd < 0.10 and not is_innovation:
        return _v("PASS", "MEDIUM",
                  [f"Growth too low ({rev_fwd*100:.0f}%) — not on an innovation S-curve."],
                  None, "Mature business, will likely be disrupted.")

    score = 0
    if rev_fwd >= 0.40: score += 3; reasoning.append(f"Exponential growth ({rev_fwd*100:.0f}% fwd) — clear S-curve.")
    elif rev_fwd >= 0.25: score += 2; reasoning.append(f"Strong growth ({rev_fwd*100:.0f}% fwd) — riding the S-curve.")
    elif rev_fwd >= 0.15: score += 1; reasoning.append(f"Moderate growth ({rev_fwd*100:.0f}% fwd).")

    if is_innovation: score += 2; reasoning.append(f"Operating in a frontier AI layer ({component}) — platform shift.")
    if moat >= 60: score += 1; reasoning.append(f"Strong moat ({moat:.0f}/100) anchors the bet.")

    # Cathie embraces private high-growth
    if not _is_public(c) and rev_fwd >= 0.30:
        reasoning.append("Private but clearly riding a platform shift — would seek access via secondaries.")
        score += 1

    if score >= 5:
        verdict, conv = "STRONG_BUY", "HIGH"
    elif score >= 3:
        verdict, conv = "BUY", "HIGH"
    elif score >= 2:
        verdict, conv = "BUY", "MEDIUM"
    elif score >= 1:
        verdict, conv = "HOLD", "MEDIUM"
    else:
        verdict, conv = "PASS", "MEDIUM"

    return _v(verdict, conv, reasoning,
              pos=f"Rev growth {rev_fwd*100:.0f}% fwd",
              concern="Cyclical disruption risk" if not is_innovation else "Capital intensity")


# ---------------- registry ----------------

RUBRICS: dict[str, callable] = {
    "buffett": buffett,
    "munger": munger,
    "lynch": lynch,
    "graham": graham,
    "druck": druck,
    "wood": wood,
}


def apply_rubric(persona_key: str, company: CompanyView) -> InvestorVerdict:
    fn = RUBRICS[persona_key]
    raw = fn(company)
    return InvestorVerdict(
        investor_key=persona_key,
        investor_name="",  # filled by engine
        verdict=raw["verdict"],
        conviction=raw["conviction"],
        reasoning=raw["reasoning"],
        top_positive=raw["top_positive"],
        top_concern=raw["top_concern"],
        score=VERDICT_SCORE[raw["verdict"]],
    )
