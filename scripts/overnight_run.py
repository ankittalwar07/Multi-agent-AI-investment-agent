"""Overnight pipeline runner — hit once, walk away.

Runs the full multi-agent pipeline with multi-provider fallback (Gemini +
Groq). When a provider hits its rate limit, the wrapper rotates to the
other; when both are throttled, it sleeps until the earliest reset.
Components that succeed are persisted continuously, so if the script is
killed and restarted with --resume <run_id>, it picks up exactly where
it left off — never re-doing completed work.

Designed for "leave laptop on overnight" use cases.

Usage:
  # Fresh run, both providers (recommended)
  GOOGLE_API_KEY=... GROQ_API_KEY=... \\
    python scripts/overnight_run.py

  # Resume an existing partial run by id
  python scripts/overnight_run.py --resume 20260515T040121Z-7a05eb

  # Single provider only
  python scripts/overnight_run.py --providers gemini

  # Quick test on a 3-component subset
  python scripts/overnight_run.py --max-components 3

The script prints live progress to stdout. Press Ctrl-C to stop —
progress is already persisted, so resume any time.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--providers",
        default="gemini,groq",
        help="Comma-separated provider chain. Default: gemini,groq",
    )
    parser.add_argument(
        "--gemini-model", default="gemini-2.0-flash",
        help="Gemini model (default: gemini-2.0-flash)",
    )
    parser.add_argument(
        "--groq-model", default="llama-3.1-8b-instant",
        help="Groq model (default: llama-3.1-8b-instant — 5x daily quota of 70B)",
    )
    parser.add_argument("--resume", default=None, help="Resume the given run_id")
    parser.add_argument("--max-components", type=int, default=None, help="Limit components for testing")
    parser.add_argument("--max-iterations", type=int, default=20,
                         help="Outer-loop max retries (default 20)")
    parser.add_argument("--sleep", type=float, default=10.0,
                         help="Outer-loop sleep between retry passes (seconds)")
    args = parser.parse_args()

    from investment_agent.config import get_settings
    from investment_agent.graph.build import Pipeline, RunOptions
    from investment_agent.llm import MultiProviderLLM, get_provider

    provider_names = [p.strip() for p in args.providers.split(",") if p.strip()]
    if not provider_names:
        print("ERROR: --providers must list at least one")
        return 2

    # Build provider chain
    providers = []
    for name in provider_names:
        try:
            if name == "gemini":
                if not os.environ.get("GOOGLE_API_KEY"):
                    print(f"  skipping gemini — GOOGLE_API_KEY not set")
                    continue
                providers.append(get_provider("gemini", model=args.gemini_model))
            elif name == "groq":
                if not os.environ.get("GROQ_API_KEY"):
                    print(f"  skipping groq — GROQ_API_KEY not set")
                    continue
                providers.append(get_provider("groq", model=args.groq_model))
            elif name == "mock":
                providers.append(get_provider("mock"))
            else:
                providers.append(get_provider(name))
            print(f"  ✓ {name} ready ({providers[-1].model})")
        except Exception as e:
            print(f"  ✗ {name} init failed: {e}")

    if not providers:
        print("ERROR: no providers initialized — set GOOGLE_API_KEY and/or GROQ_API_KEY")
        return 1

    # Progress callbacks for the multi-provider wrapper
    def on_wait(seconds: float, provider_name: str) -> None:
        eta = time.strftime("%H:%M:%S", time.localtime(time.time() + seconds))
        print(
            f"  [wait] all providers throttled — sleeping {seconds:.0f}s "
            f"(woken by {provider_name} at {eta})"
        )

    def on_switch(from_p: str, to_p: str, reason: str) -> None:
        print(f"  [switch] {from_p} → {to_p}: {reason}")

    multi_llm = MultiProviderLLM.from_providers(
        providers, on_wait=on_wait, on_switch=on_switch,
    )

    settings = get_settings()
    pipeline = Pipeline(
        settings=settings,
        llm_factory=lambda: multi_llm,
        progress_cb=lambda node, msg: print(f"  [{node}] {msg}"),
    )

    opts = RunOptions(
        provider="multi",
        model="+".join(p.name for p in providers),
        mock=False,
        max_components=args.max_components,
        resume_run_id=args.resume,
    )

    def on_iter(i: int, done: int, total: int, pending: int, run_id: str) -> None:
        print(f"\n=== Iteration {i} complete · {done}/{total} done · "
               f"{pending} still need research · run {run_id} ===")
        st = multi_llm.status()
        for s in st:
            cd = s["cooldown_remaining_s"]
            cd_str = f"{cd:.0f}s cooldown" if cd > 0 else "ready"
            print(f"    {s['provider']}: {s['calls']} calls, "
                   f"{s['tokens']:,} tokens, {cd_str}")

    print(f"\nStarting pipeline at {time.strftime('%H:%M:%S')}")
    print(f"Provider chain: {' → '.join(p.name for p in providers)}")
    if args.resume:
        print(f"Resuming run: {args.resume}")
    print()

    result = pipeline.run_until_done(
        opts, max_iterations=args.max_iterations,
        sleep_between_s=args.sleep, on_progress=on_iter,
    )

    print(f"\n{'=' * 60}")
    print(f"Final run id: {result.run_id}")
    print(f"DB:       {result.db_path}")
    print(f"JSON:     {result.json_path}")
    print(f"Markdown: {result.markdown_path}")
    print(f"Cost:     ${result.state.cost_usd:.4f}")
    print(f"Companies scored: {len(result.state.scored)}")
    statuses = result.state.per_component_status
    done = sum(1 for s in statuses.values() if s == "done")
    print(f"Components: {done}/{len(statuses)} done")
    if done < len(statuses):
        not_done = [n for n, s in statuses.items() if s != "done"]
        print(f"Still pending: {not_done[:6]}{'...' if len(not_done) > 6 else ''}")
        print(f"\nResume any time: python scripts/overnight_run.py --resume {result.run_id}")
        return 1
    print("\n✓ All components complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
