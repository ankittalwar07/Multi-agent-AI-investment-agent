"""Intelligence Agent — aggregates non-financial signals that the market often misprices.

5 signal categories:
1. US government investments  (CHIPS Act, DPA, DoE loans, strategic stockpile)
2. Federal contracts          (DoD, DARPA, NSF, NTIA)
3. Politicians trading        (STOCK Act disclosures, Senate EFD, House Clerk)
4. Foreign government activity (China Big Fund, Saudi PIF, EU Chips Act, etc.)
5. Policy / regulatory flags  (Entity List, CFIUS, export controls)
6. Corporate Form 4 cluster buys (SEC EDGAR)

The agent produces a structured set of IntelligenceSignal records per company plus
a composite intelligence_score (-100 to +100).

In Demo mode, signals come from the INTELLIGENCE patch dict in mock_data.py. In
live mode, signals are fetched from the documented public APIs (see sources.py).
"""
from .agent import IntelligenceAgent, run_intelligence
from .signals import IntelligenceSignal, IntelligenceSummary, SignalCategory

__all__ = [
    "IntelligenceAgent",
    "IntelligenceSignal",
    "IntelligenceSummary",
    "SignalCategory",
    "run_intelligence",
]
