"""Personas for the investor council.

Each persona has a documented philosophy, signature criteria, and a famous
quote. The rubric module turns these into deterministic scoring functions.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InvestorPersona:
    key: str                # short id used in code/UI
    name: str               # display name
    firm: str
    era: str
    style: str              # one-tag style (Value, GARP, Quality, ...)
    philosophy: str         # one-line philosophy
    favors: list[str]       # what they like
    dislikes: list[str]     # what they avoid
    famous_quote: str
    avatar: str             # emoji shortcode for the UI


COUNCIL: list[InvestorPersona] = [
    InvestorPersona(
        key="buffett",
        name="Warren Buffett",
        firm="Berkshire Hathaway",
        era="Living legend",
        style="Quality + Value",
        philosophy="Wonderful businesses at fair prices, held forever.",
        favors=[
            "Durable economic moat (sole-source, switching costs, brand)",
            "Predictable, understandable business",
            "Reasonable P/E (typically <25 for great quality)",
            "High operating margins and ROIC",
            "Owner-friendly capital allocation",
        ],
        dislikes=[
            "Speculative growth with no earnings",
            "Complexity / financial engineering",
            "Crowded / pricey 'story' stocks",
        ],
        famous_quote=(
            "It is far better to buy a wonderful company at a fair price than "
            "a fair company at a wonderful price."
        ),
        avatar=":man_in_business_suit_levitating:",
    ),
    InvestorPersona(
        key="munger",
        name="Charlie Munger",
        firm="Berkshire Hathaway",
        era="1924–2023",
        style="Quality",
        philosophy="Avoid stupidity rather than seek brilliance. Quality compounds.",
        favors=[
            "Truly excellent business with durable competitive advantage",
            "Reasonable price for a great company",
            "Strong incentives and culture (capital allocators)",
            "Lollapalooza effects (multiple advantages stacking)",
        ],
        dislikes=[
            "Mediocre business at any price ('cigar butts')",
            "Hidden risk / regulatory bombs",
            "Twitter-finance fads",
        ],
        famous_quote="It's not supposed to be easy. Anyone who finds it easy is stupid.",
        avatar=":older_man:",
    ),
    InvestorPersona(
        key="lynch",
        name="Peter Lynch",
        firm="Fidelity Magellan",
        era="Living legend",
        style="GARP",
        philosophy="Growth at a reasonable price. Look for 10-baggers in plain sight.",
        favors=[
            "PEG ratio < 1.5 (growth not yet priced in)",
            "Forward revenue growth > 15%",
            "Understandable business — you'd shop there",
            "Insider ownership / management buying",
        ],
        dislikes=[
            "High PEG with no clear earnings runway",
            "Diversifications away from core business",
            "Hot stocks in hot industries (already crowded)",
        ],
        famous_quote=(
            "Know what you own, and know why you own it."
        ),
        avatar=":man_office_worker:",
    ),
    InvestorPersona(
        key="graham",
        name="Benjamin Graham",
        firm="Graham-Newman",
        era="1894–1976 · Father of Value Investing",
        style="Deep Value",
        philosophy="Margin of safety. Buy a dollar for fifty cents.",
        favors=[
            "P/E < 15, ideally trailing AND forward",
            "Strong balance sheet — low debt, current assets cover liabilities",
            "Dividend record — earnings stability over a decade",
            "EV/EBITDA < 10",
        ],
        dislikes=[
            "Glamour stocks with sky-high P/E",
            "Negative earnings",
            "Speculative or unprofitable companies",
        ],
        famous_quote=(
            "The intelligent investor is a realist who sells to optimists "
            "and buys from pessimists."
        ),
        avatar=":books:",
    ),
    InvestorPersona(
        key="druck",
        name="Stanley Druckenmiller",
        firm="Duquesne Family Office",
        era="Living legend",
        style="Macro + Concentration",
        philosophy="Big positions in the best ideas where the macro and capacity setup align.",
        favors=[
            "Capacity-constrained suppliers in growing markets",
            "Sole-source or oligopoly positioning",
            "Secular tailwinds (AI buildout, energy transition, reshoring)",
            "Concentrated bet quality > diversification",
        ],
        dislikes=[
            "Crowded longs with no marginal buyer",
            "Weak macro setup (rate cycle, regulatory, geopolitics)",
            "Story without a real near-term catalyst",
        ],
        famous_quote=(
            "The way to build long-term returns is through preservation of "
            "capital and home runs. When you have tremendous conviction, you "
            "have to go for the jugular."
        ),
        avatar=":chart_with_upwards_trend:",
    ),
    InvestorPersona(
        key="wood",
        name="Cathie Wood",
        firm="ARK Invest",
        era="Living",
        style="Disruptive Innovation",
        philosophy="Buy the platforms behind the next exponential S-curve.",
        favors=[
            "Forward revenue growth > 30%",
            "Platform shift / S-curve early-innings",
            "AI-native, frontier-model, accelerator businesses",
            "Private high-growth names are OK if access exists",
        ],
        dislikes=[
            "Mature, low-growth businesses",
            "Cyclical incumbents likely to be disrupted",
            "Heavy fixed costs without operating leverage",
        ],
        famous_quote=(
            "Innovation solves problems and gains traction during turbulent "
            "times — that's when investors should be increasing exposure."
        ),
        avatar=":rocket:",
    ),

    # --------- BEAR / SKEPTIC VOICES ---------

    InvestorPersona(
        key="marks",
        name="Howard Marks",
        firm="Oaktree Capital",
        era="Living legend",
        style="Cycle-aware Contrarian",
        philosophy="Second-level thinking. Where are we in the cycle? What's already priced in?",
        favors=[
            "Margin of safety relative to where the cycle stands",
            "Contrarian setups — buying when others are selling",
            "Risk-adjusted returns over absolute returns",
            "Distressed or out-of-favor quality businesses",
        ],
        dislikes=[
            "Crowded longs at peak euphoria",
            "Stocks priced for perfection (no room for error)",
            "'This time it's different' narratives",
            "Late-cycle capex booms that look like 1999",
        ],
        famous_quote=(
            "The most dangerous words in investing are 'this time it's different.'"
        ),
        avatar=":hourglass:",
    ),
    InvestorPersona(
        key="burry",
        name="Michael Burry",
        firm="Scion Asset Management",
        era="Living",
        style="Bubble Caller / Contrarian",
        philosophy="Identify mispricing through original research; short the consensus when the math doesn't work.",
        favors=[
            "Crashed names with hidden value (post-bubble pickup)",
            "Real cash flow — not narrative growth",
            "P/E and EV/EBITDA at clearly distressed levels",
            "Inflection situations where consensus is wrong",
        ],
        dislikes=[
            "Extreme valuations (P/E > 35, PEG > 2) regardless of growth",
            "Capex-heavy unprofitable businesses funded by hype",
            "AI/semis trading at peak-cycle multiples — 'this is 1999'",
            "Crowded passive flows propping up index favorites",
        ],
        famous_quote=(
            "What is most amazing is not just the boom, but the broad complacency about it."
        ),
        avatar=":no_entry:",
    ),
    InvestorPersona(
        key="dalio",
        name="Ray Dalio",
        firm="Bridgewater Associates",
        era="Living legend",
        style="Macro / Debt-Cycle / Geopolitics",
        philosophy="Diversify intelligently. Understand the long-term debt and geopolitical cycles.",
        favors=[
            "Diversified geographic and end-market exposure",
            "All-weather businesses that work in multiple regimes",
            "Strong balance sheets to weather drawdowns",
            "Secular productivity gains that survive policy shocks",
        ],
        dislikes=[
            "Heavy China-export concentration (export-control risk)",
            "Single-region geopolitical chokepoints (Taiwan, Korea)",
            "Highly levered capex cyclicals at peak demand",
            "Concentration when diversification is cheap",
        ],
        famous_quote=(
            "He who lives by the crystal ball will eat shattered glass."
        ),
        avatar=":globe_with_meridians:",
    ),
]


# Lookup helpers
BY_KEY: dict[str, InvestorPersona] = {p.key: p for p in COUNCIL}
