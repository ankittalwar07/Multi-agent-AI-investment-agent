import json

from investment_agent.llm import LLMMessage, get_provider
from investment_agent.llm.mock_provider import MockProvider


def test_decomposer_returns_components_json():
    p = get_provider("mock")
    resp = p.complete(
        messages=[
            LLMMessage(role="system", content="<<AGENT:decomposer>>\nrules"),
            LLMMessage(role="user", content="decompose"),
        ],
        response_format="json",
    )
    payload = json.loads(resp.content)
    assert "components" in payload


def test_researcher_first_call_emits_tool_use():
    p = MockProvider()
    from investment_agent.llm.base import ToolSpec

    tools = [ToolSpec(name="web_search", description="", json_schema={"type": "object"})]
    resp = p.complete(
        messages=[
            LLMMessage(role="system", content="<<AGENT:component_researcher>>\nComponent: EUV Lithography"),
            LLMMessage(role="user", content="go"),
        ],
        tools=tools,
    )
    assert resp.tool_calls
    assert resp.tool_calls[0].name == "web_search"


def test_researcher_second_call_emits_final_json():
    p = MockProvider()
    msgs = [
        LLMMessage(role="system", content="<<AGENT:component_researcher>>\nComponent: EUV Lithography"),
        LLMMessage(role="user", content="go"),
    ]
    # First call -> tool use
    p.complete(messages=msgs)
    # Second call -> final answer
    resp = p.complete(messages=msgs)
    payload = json.loads(resp.content)
    assert payload["component"] == "EUV Lithography"
    assert payload["companies"]
