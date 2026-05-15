"""Verify your local Ollama setup works end-to-end.

Usage:
  # First install Ollama from https://ollama.com/download
  # Then pull a model:
  ollama pull qwen2.5:7b
  # Then run this:
  PYTHONPATH=src python scripts/test_ollama.py
  # Or with a different model:
  PYTHONPATH=src python scripts/test_ollama.py llama3.1:8b
"""
from __future__ import annotations

import os
import sys
import time


def main() -> int:
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:7b"
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    from investment_agent.llm import LLMMessage, get_provider

    print(f"Provider: ollama  Model: {model}  Base URL: {base_url}")

    provider = get_provider("ollama", model=model)
    t0 = time.time()
    try:
        resp = provider.complete(
            messages=[
                LLMMessage(role="system",
                            content="You are a terse assistant. Reply with strict JSON only."),
                LLMMessage(role="user", content=(
                    'Return JSON: {"ok": true, "ai_infra_bottleneck": "<one company>", '
                    '"why": "<one sentence>"}')),
            ],
            response_format="json",
            max_tokens=200,
        )
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1

    elapsed = time.time() - t0
    print(f"\n--- Response (took {elapsed:.1f}s) ---")
    print(resp.content)
    print(f"\n--- Usage ---")
    print(f"input_tokens={resp.usage.input_tokens}  "
          f"output_tokens={resp.usage.output_tokens}  cost=$0.00 (local)")
    tok_per_sec = (resp.usage.output_tokens / elapsed) if elapsed > 0 else 0
    print(f"Throughput: {tok_per_sec:.0f} tok/sec")

    if resp.content.strip():
        print("\nOK — Ollama is wired. You can now run:")
        print(f"  PYTHONPATH=src python -m investment_agent.cli run "
               f"--provider ollama --model {model} --max-components 3")
        return 0
    print("\nGot an empty response — try a different model or check logs.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
