"""Verify your free Gemini API key works end-to-end.

Usage:
  export GOOGLE_API_KEY="..."          # from https://aistudio.google.com/apikey
  PYTHONPATH=src python scripts/test_gemini.py
  # or with a custom model:
  PYTHONPATH=src python scripts/test_gemini.py gemini-1.5-flash
"""
from __future__ import annotations

import os
import sys


def main() -> int:
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not key:
        print("ERROR: GOOGLE_API_KEY is not set.")
        print("Get a free key at: https://aistudio.google.com/apikey")
        print('Then run: export GOOGLE_API_KEY="..."')
        return 1

    model = sys.argv[1] if len(sys.argv) > 1 else "gemini-2.0-flash"

    from investment_agent.llm import LLMMessage, get_provider

    print(f"Provider: gemini  Model: {model}")
    print(f"Key:      {key[:6]}...{key[-4:]} ({len(key)} chars)")

    provider = get_provider("gemini", model=model)
    resp = provider.complete(
        messages=[
            LLMMessage(
                role="system",
                content="You are a terse assistant. Reply with strict JSON only.",
            ),
            LLMMessage(
                role="user",
                content=(
                    'Return JSON: {"ok": true, "ai_infra_winner": "<one company name>", '
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
        f"cost_usd≈${resp.usage.cost_usd:.6f}"
    )
    if resp.content.strip():
        print("\nOK — your key works. You can now run:")
        print("  python -m investment_agent.cli run --provider gemini --max-components 3")
        return 0
    print("\nGot an empty response — likely a quota / safety / model-name issue.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
