import os

from investment_agent.tools.paid_market_data import PaidMarketDataArgs, PaidMarketDataTool


def test_stub_when_key_missing(monkeypatch):
    monkeypatch.delenv("BLOOMBERG_API_KEY", raising=False)
    tool = PaidMarketDataTool()
    args = PaidMarketDataArgs(vendor="bloomberg", op="company", query="ASML")
    result = tool.run(args)
    assert not result.ok
    assert "BLOOMBERG_API_KEY" in (result.error or "")


def test_stub_response_examples_shape():
    examples = PaidMarketDataTool.stub_response_examples()
    assert {"company", "market_share", "funding", "traffic"}.issubset(examples.keys())
