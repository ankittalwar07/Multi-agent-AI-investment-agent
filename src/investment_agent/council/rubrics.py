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


# ---------------- Howard Marks ----------------

def marks(c: CompanyView) -> dict:
    """Cycle awareness + second-level thinking. The crowd matters as much as the company."""
    reasoning: list[str] = []
    pe_f = _pe_f(c)
    pe_t = _pe_t(c)
    moat = _moat(c)
    rev_fwd = _rev_fwd(c) or 0
    bucket = _bucket(c) or ""
    structure = _structure(c)

    # Marks cares about euphoria signals as much as fundamentals
    euphoria_score = 0
    if pe_t and pe_t > 35: euphoria_score += 2
    if pe_f and pe_f > 30: euphoria_score += 2
    if rev_fwd > 0.50: euphoria_score += 1  # very high growth often = priced perfection
    if bucket == ">75" and structure in ("monopoly", "oligopoly"): euphoria_score += 1  # crowded long
    if (c.get("analyst_buy") or 0) >= 30 and (c.get("analyst_sell") or 0) <= 1: euphoria_score += 1  # consensus love

    # Quality consideration
    quality_ok = moat >= 60

    if euphoria_score >= 4:
        return _v("AVOID", "HIGH",
                  [
                      f"Multiple euphoria signals stacked (P/E {pe_f or pe_t}, growth {rev_fwd*100:.0f}%, consensus love).",
                      "Second-level question: when this many things are going right, what does the next surprise look like?",
                      "Risk-adjusted, this is asymmetric to the downside.",
                  ],
                  pos="Cyclical setup is real",
                  concern="Priced for perfection — late-cycle warning")
    if euphoria_score >= 3:
        return _v("HOLD", "MEDIUM",
                  [
                      "Quality is here, but the entry price reflects too much optimism.",
                      "I'd rather wait for a 20% pullback than chase the consensus long.",
                  ],
                  pos="Underlying business is sound",
                  concern="Crowd is fully positioned — what's the next marginal buyer?")

    # Look for contrarian setups
    if pe_t and pe_t < 15 and quality_ok:
        return _v("STRONG_BUY", "HIGH",
                  [
                      f"Trading at {pe_t:.0f}x trailing — clearly out of favor despite real quality.",
                      "Second-level: while everyone chases obvious AI winners, this gets ignored.",
                      "Margin of safety relative to where the cycle stands.",
                  ],
                  pos="Contrarian value setup",
                  concern="Could stay out-of-favor longer than expected")

    if pe_f and pe_f < 20 and quality_ok:
        score = 0
        score += 2 if rev_fwd >= 0.10 else 0
        score += 1 if moat >= 70 else 0
        if score >= 2:
            return _v("BUY", "HIGH",
                      [
                          f"Reasonable P/E ({pe_f:.0f}x fwd) for the quality on offer.",
                          "Cycle has not yet over-priced this name.",
                      ],
                      pos="Risk-adjusted setup",
                      concern="Watch for cycle rollover")

    if pe_f and pe_f >= 25:
        return _v("HOLD", "MEDIUM",
                  [
                      f"P/E forward {pe_f:.0f}x leaves little room for cycle disappointment.",
                      "I'd want a more attractive entry before committing capital.",
                  ],
                  pos="Quality acknowledged",
                  concern="Late-cycle valuation")

    return _v("HOLD", "LOW",
              ["Neutral — neither cheap nor euphoric. Waiting for a clearer setup."],
              pos=None, concern="No edge here")


# ---------------- Michael Burry ----------------

def burry(c: CompanyView) -> dict:
    """Bubble caller. Math over narrative. Short the consensus when the numbers don't work."""
    reasoning: list[str] = []
    pe_f = _pe_f(c)
    pe_t = _pe_t(c)
    peg = _peg(c)
    rev_fwd = _rev_fwd(c) or 0
    op = _op_mgn(c)
    fcf = _fcf(c)
    bucket = _bucket(c) or ""
    component = c.get("component", "")

    if not _is_public(c):
        return _v("PASS", "MEDIUM",
                  ["Private — I can't short it, can't size it, can't trust the markup."],
                  None, "No real price discovery on private marks.")

    # Hard AVOID signals (bubble territory)
    bubble_flags = []
    if pe_t is not None and pe_t > 40: bubble_flags.append(f"P/E TTM {pe_t:.0f}x")
    if pe_f is not None and pe_f > 35: bubble_flags.append(f"P/E fwd {pe_f:.0f}x")
    if peg is not None and peg > 2.5: bubble_flags.append(f"PEG {peg:.1f}")
    if op is not None and op < 0: bubble_flags.append(f"negative op margin ({op*100:.0f}%)")
    if fcf is not None and fcf < -0.05: bubble_flags.append(f"burning cash (FCF yield {fcf*100:.1f}%)")

    # Capex-heavy AI hype names
    AI_HYPE_LAYERS = {"AI Accelerator Silicon", "Foundation Model Labs", "GPU Neoclouds",
                       "Inference Hardware Startups"}

    if len(bubble_flags) >= 3:
        return _v("AVOID", "HIGH",
                  [
                      f"Multiple bubble signals stacked: {', '.join(bubble_flags)}.",
                      f"This is what 1999 looked like in {component}.",
                      "I would short into rallies. The math doesn't work.",
                  ],
                  pos="Narrative is strong (which is the problem)",
                  concern="Re-rating risk on first earnings disappointment is brutal")

    if len(bubble_flags) >= 2:
        return _v("AVOID", "MEDIUM",
                  [
                      f"Two bubble signals: {', '.join(bubble_flags)}.",
                      "I'd avoid here — the asymmetry is wrong.",
                  ],
                  pos="Real business under the hype",
                  concern="Consensus too crowded")

    if pe_f is not None and pe_f > 30 and component in AI_HYPE_LAYERS:
        return _v("PASS", "MEDIUM",
                  [
                      f"AI hype layer at {pe_f:.0f}x forward — this is the trade everyone is in.",
                      "I look for what nobody wants, not what everyone owns.",
                  ],
                  pos="Real growth", concern="Priced for ten-year perfection")

    # Burry will buy crashed quality
    score = 0
    if pe_t is not None and pe_t < 12: score += 3; reasoning.append(f"P/E TTM {pe_t:.0f}x — clearly distressed.")
    if pe_f is not None and pe_f < 15: score += 2; reasoning.append(f"Forward P/E {pe_f:.0f}x is value-investor territory.")
    if peg is not None and peg < 1.0: score += 1; reasoning.append(f"PEG {peg:.2f} — growth essentially free.")
    if fcf is not None and fcf > 0.05: score += 1; reasoning.append(f"FCF yield {fcf*100:.1f}% is real cash.")

    if score >= 4:
        verdict, conv = "STRONG_BUY", "HIGH"
        reasoning.append("This is the kind of crashed-quality setup I size into.")
    elif score >= 2:
        verdict, conv = "BUY", "MEDIUM"
    elif score >= 1:
        verdict, conv = "HOLD", "LOW"
    else:
        verdict, conv = "PASS", "MEDIUM"
        if not reasoning:
            reasoning.append("Nothing to do — neither cheap enough to buy nor extreme enough to short.")

    return _v(verdict, conv, reasoning,
              pos=f"Distressed multiples ({pe_t:.0f}x TTM)" if pe_t and pe_t < 15 else "Real cash flow",
              concern="Watch for accounting / capex surprises")


# ---------------- Ray Dalio ----------------

def dalio(c: CompanyView) -> dict:
    """Macro + debt cycle + geopolitics. Diversify, avoid concentrated geopolitical chokepoints."""
    reasoning: list[str] = []
    hq = (c.get("hq_country") or "").lower()
    customer = (c.get("customer_concentration") or "").lower()
    rev_fwd = _rev_fwd(c) or 0
    op = _op_mgn(c)
    div = _div(c) or 0
    pe_f = _pe_f(c)
    sole = _sole(c)

    # Geopolitical risk overlay
    geopolitical_risk = 0
    if any(w in hq for w in ("taiwan", "china", "korea")):
        geopolitical_risk += 2
        reasoning.append(f"Headquartered in {c.get('hq_country')} — meaningful geopolitical concentration risk.")
    if "china" in customer or "taiwan" in customer:
        geopolitical_risk += 1
        reasoning.append("Customer base has Taiwan/China concentration — export-control exposure.")

    # All-weather scoring
    aw_score = 0
    if op is not None and op >= 0.20: aw_score += 1; reasoning.append(f"Strong margins ({op*100:.0f}%) — survives drawdowns.")
    if div >= 0.015: aw_score += 1; reasoning.append(f"Dividend ({div*100:.1f}%) cushions through regime changes.")
    if pe_f is not None and pe_f <= 22: aw_score += 1; reasoning.append(f"Reasonable valuation ({pe_f:.0f}x fwd).")
    if rev_fwd >= 0.10 and rev_fwd <= 0.30: aw_score += 1; reasoning.append("Sustainable growth (not parabolic).")

    # Sole-source / single-region = concentration risk in Dalio's framework
    if sole and geopolitical_risk >= 1:
        return _v("HOLD", "MEDIUM",
                  ["Sole-source + geopolitical concentration is exactly the chokepoint I diversify away from."]
                  + reasoning,
                  pos="Underlying productivity gain is real",
                  concern="Single point of failure in a fracturing world")

    # High-flyer with no geographic balance = pass
    if rev_fwd > 0.50 and div < 0.005:
        return _v("PASS", "MEDIUM",
                  [
                      "Parabolic growth without dividend cushion fails in a tightening regime.",
                      "I'd want diversification or a hedge.",
                  ] + reasoning,
                  pos="Productivity gain", concern="No defense in a regime change")

    if geopolitical_risk >= 2:
        return _v("HOLD" if aw_score >= 2 else "PASS", "MEDIUM",
                  ["Geopolitical chokepoint risk dominates the underwriting."] + reasoning,
                  pos="Quality acknowledged",
                  concern="Diversification mandate would cap position size")

    if aw_score >= 3 and geopolitical_risk == 0:
        return _v("BUY", "HIGH",
                  reasoning + [
                      "Diversified, profitable, reasonably valued — this works in multiple regimes.",
                  ],
                  pos="All-weather characteristics",
                  concern="Watch debt-cycle sensitivity")

    if aw_score >= 2:
        return _v("BUY", "MEDIUM",
                  reasoning + ["Holds together in most regimes."],
                  pos="Defensive characteristics",
                  concern="Geographic concentration to monitor")

    if aw_score >= 1:
        return _v("HOLD", "LOW", reasoning, None, "Position-size carefully")

    return _v("PASS", "MEDIUM",
              ["Neither defensive nor diversified enough for an all-weather portfolio."],
              None, "Doesn't fit my framework")


# ---------------- registry ----------------

RUBRICS: dict[str, callable] = {
    "buffett": buffett,
    "munger": munger,
    "lynch": lynch,
    "graham": graham,
    "druck": druck,
    "wood": wood,
    "marks": marks,
    "burry": burry,
    "dalio": dalio,
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
