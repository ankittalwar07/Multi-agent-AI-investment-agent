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
]


# Lookup helpers
BY_KEY: dict[str, InvestorPersona] = {p.key: p for p in COUNCIL}
