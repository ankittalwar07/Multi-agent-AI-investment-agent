from __future__ import annotations

from .base import LLMProvider
from .mock_provider import MockProvider


def get_provider(
    name: str,
    model: str | None = None,
    *,
    mock: bool = False,
    **kwargs,
) -> LLMProvider:
    """Return an LLMProvider for the given name.

    `mock=True` returns the deterministic MockProvider regardless of `name`.
    Concrete provider SDKs are imported lazily so the mock path has no extra deps.
    """
    if mock or name == "mock":
        return MockProvider(model=model)

    name = name.lower()
    if name == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(model=model, **kwargs)
    if name == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(model=model, **kwargs)
    if name == "gemini":
        from .gemini_provider import GeminiProvider

        return GeminiProvider(model=model, **kwargs)
    if name == "groq":
        from .groq_provider import GroqProvider

        return GroqProvider(model=model, **kwargs)
    if name == "ollama":
        from .ollama_provider import OllamaProvider

        return OllamaProvider(model=model, **kwargs)

    raise ValueError(f"Unknown LLM provider: {name!r}")
