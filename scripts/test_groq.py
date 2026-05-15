"""Verify your free Groq API key works end-to-end.

Usage:
  export GROQ_API_KEY="..."          # from https://console.groq.com/keys
  PYTHONPATH=src python scripts/test_groq.py
  # or with a custom model:
  PYTHONPATH=src python scripts/test_groq.py llama-3.1-8b-instant
"""
from __future__ import annotations

import os
import sys


def main() -> int:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        print("ERROR: GROQ_API_KEY is not set.")
        print("Get a free key at: https://console.groq.com/keys")
        print('Then run: export GROQ_API_KEY="..."')
        return 1

    model = sys.argv[1] if len(sys.argv) > 1 else "llama-3.3-70b-versatile"

    from investment_agent.llm import LLMMessage, get_provider

    print(f"Provider: groq  Model: {model}")
    print(f"Key:      {key[:6]}...{key[-4:]} ({len(key)} chars)")

    provider = get_provider("groq", model=model)
    resp = provider.complete(
        messages=[
            LLMMessage(role="system", content="You are a terse assistant. Reply with strict JSON only."),
            LLMMessage(
                role="user",
                content=(
                    'Return JSON: {"ok": true, "ai_infra_bottleneck": "<one company name>", '
                    '"why": "<one sentence>"}'
                ),
            ),
        ],
        response_format="json",
        max_tokens=200,
    )

    print("\n--- Response ---")
    print(resp.content)
    print("\n--- Usage ---")
    print(
        f"input_tokens={resp.usage.input_tokens} "
        f"output_tokens={resp.usage.output_tokens} "
        f"cost_usd~${resp.usage.cost_usd:.6f}"
    )
    if resp.content.strip():
        print("\nOK — Groq is wired. You can now run:")
        print(f"  python -m investment_agent.cli run --provider groq --model {model} --max-components 3")
        return 0
    print("\nGot an empty response — likely a model name issue or rate limit.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
