"""Ollama provider wiring — does not call the network."""
from __future__ import annotations

from investment_agent.llm import get_provider


def test_ollama_factory_with_default_url(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    p = get_provider("ollama")
    assert p.name == "ollama"
    assert p.model == "qwen2.5:7b"  # default model


def test_ollama_factory_with_custom_model():
    p = get_provider("ollama", model="llama3.1:8b")
    assert p.name == "ollama"
    assert p.model == "llama3.1:8b"


def test_ollama_factory_with_custom_url(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://192.168.1.42:11434/v1")
    p = get_provider("ollama")
    # No actual network call yet — just verify construction succeeded
    assert p.name == "ollama"


def test_ollama_in_factory_mock_path():
    """Verify mock=True still works for ollama."""
    p = get_provider("ollama", mock=True)
    assert p.name == "mock"
