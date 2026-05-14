"""Verdict types for the investor council."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Verdict = Literal["STRONG_BUY", "BUY", "HOLD", "PASS", "AVOID"]
Conviction = Literal["HIGH", "MEDIUM", "LOW"]

VERDICT_SCORE: dict[str, int] = {
    "STRONG_BUY": 2,
    "BUY": 1,
    "HOLD": 0,
    "PASS": -1,
    "AVOID": -2,
}


class InvestorVerdict(BaseModel):
    investor_key: str           # e.g. "buffett"
    investor_name: str          # e.g. "Warren Buffett"
    verdict: Verdict
    conviction: Conviction
    reasoning: list[str] = Field(default_factory=list)
    top_positive: str | None = None
    top_concern: str | None = None
    score: int = 0              # numeric score from VERDICT_SCORE
