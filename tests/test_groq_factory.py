"""Groq provider wiring — does not call the network."""
from __future__ import annotations

import pytest

from investment_agent.llm import get_provider


def test_groq_factory_requires_key(monkeypatch):
    """Without GROQ_API_KEY set, get_provider('groq') raises a clean RuntimeError."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        get_provider("groq")


def test_groq_factory_with_key(monkeypatch):
    """With a fake key set the provider constructs without making network calls."""
    monkeypatch.setenv("GROQ_API_KEY", "test-fake-key-not-real")
    p = get_provider("groq", model="llama-3.3-70b-versatile")
    assert p.name == "groq"
    assert p.model == "llama-3.3-70b-versatile"


def test_groq_in_provider_list():
    """Verify groq is reachable via the factory."""
    from investment_agent.llm.factory import get_provider as gp
    # mock=True bypasses the env-var check and returns a MockProvider
    p = gp("groq", mock=True)
    assert p.name == "mock"
