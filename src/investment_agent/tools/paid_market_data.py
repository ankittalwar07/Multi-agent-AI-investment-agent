"""Paid market data tool with vendor sub-stubs.

When the corresponding `*_API_KEY` env var is unset, each sub-op returns a
structured `ok=False` ToolResult so agents can call the interface the same way
and we can swap in real implementations later as a no-op.
"""
from __future__ import annotations

import os
from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from .base import Citation, Tool, ToolResult

Vendor = Literal["bloomberg", "pitchbook", "crunchbase", "similarweb"]
Op = Literal["company", "market_share", "funding", "traffic"]


class PaidMarketDataArgs(BaseModel):
    vendor: Vendor = Field(..., description="Which paid data vendor to query.")
    op: Op = Field(..., description="Which sub-operation to run.")
    query: str = Field(..., description="Company name, ticker, or domain.")
    extra: dict | None = Field(default=None, description="Optional extra args per vendor.")


VENDOR_ENV: dict[Vendor, str] = {
    "bloomberg": "BLOOMBERG_API_KEY",
    "pitchbook": "PITCHBOOK_API_KEY",
    "crunchbase": "CRUNCHBASE_API_KEY",
    "similarweb": "SIMILARWEB_API_KEY",
}


class PaidMarketDataTool(Tool):
    name: ClassVar[str] = "paid_market_data"
    description: ClassVar[str] = (
        "Query paid market data vendors (Bloomberg, PitchBook, Crunchbase, SimilarWeb). "
        "Supports ops: company (profile), market_share, funding (rounds, valuation), "
        "traffic (SimilarWeb). Returns structured JSON. If the vendor API key is not "
        "configured, returns ok=False with a 'stub: <ENV> not set' error — call with a "
        "different vendor or fall back to web_search."
    )
    args_schema: ClassVar[type[BaseModel]] = PaidMarketDataArgs

    def run(self, args: PaidMarketDataArgs) -> ToolResult:
        env_var = VENDOR_ENV[args.vendor]
        if not os.environ.get(env_var):
            return ToolResult(ok=False, error=f"stub: {env_var} not set")

        # When the key IS set, route to the real implementation. These are intentionally
        # left as NotImplementedError so the contract is clear when wiring real vendors.
        raise NotImplementedError(
            f"Live integration for {args.vendor}.{args.op} not yet implemented; "
            "unset the API key to use the stub interface."
        )

    @staticmethod
    def stub_response_examples() -> dict:
        """Documented response shapes — useful when wiring real vendors."""
        return {
            "company": {
                "name": "ASML Holding NV",
                "ticker": "ASML",
                "industry": "Semiconductor Equipment",
                "country": "Netherlands",
                "market_cap_usd": 350_000_000_000,
            },
            "market_share": {
                "market": "EUV lithography systems",
                "as_of": "2025-Q4",
                "shares": [{"company": "ASML", "pct": 100.0}],
            },
            "funding": {
                "company": "CoreWeave",
                "last_round": {"stage": "Series E", "amount_usd": 1_100_000_000},
                "post_money_usd": 19_000_000_000,
            },
            "traffic": {
                "domain": "openai.com",
                "monthly_visits": 2_300_000_000,
                "yoy_growth": 0.45,
            },
        }


def make_stub_citation(vendor: str, query: str) -> Citation:
    return Citation(
        source_url=None,
        source_name=vendor,
        snippet=f"paid:{vendor} lookup for {query}",
        tool_name="paid_market_data",
    )
