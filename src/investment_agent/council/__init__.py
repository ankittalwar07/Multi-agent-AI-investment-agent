"""Council of legendary investors.

Each persona applies their distinct investment philosophy to every company in
the universe and returns a verdict (STRONG BUY / BUY / HOLD / PASS / AVOID),
conviction, and reasoning in their voice.

The council runs deterministically on the company's data — works the same in
Demo mode and live runs.
"""
from .engine import run_council
from .personas import COUNCIL, InvestorPersona
from .verdicts import InvestorVerdict, Verdict

__all__ = ["COUNCIL", "InvestorPersona", "InvestorVerdict", "Verdict", "run_council"]
