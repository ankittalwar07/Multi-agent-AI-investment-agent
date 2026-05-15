"""MultiProviderLLM — rotates across providers with quota-aware backoff.

Use case: free-tier Gemini (~1M tokens/day) + Groq 8B (500k tokens/day) +
mock as a deterministic last-resort. When provider A throttles (TPM or TPD),
the wrapper records its cooldown time, switches to provider B, etc. When
all providers are cooled down, it sleeps until the earliest reset.

Designed for "hit run once and walk away" overnight runs.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Callable, Literal

from .base import LLMMessage, LLMProvider, LLMResponse, ToolSpec, Usage

# Match formats from Gemini, Groq, OpenAI, Anthropic — most include "try again"
_RETRY_AFTER_PATTERNS = [
    re.compile(r"try again in ([\d.]+)\s*s", re.I),
    re.compile(r"try again in (\d+)\s*m\s*([\d.]+)\s*s", re.I),
    re.compile(r"retry after\s*[:=]?\s*([\d.]+)", re.I),
    re.compile(r"in\s+(\d+)m([\d.]+)s", re.I),
]


def _parse_retry_after(exc: Exception) -> float:
    """Extract suggested wait in seconds from the API's error message."""
    msg = str(exc)
    # Look for "Xm Y.Zs" first (more specific)
    for pat in _RETRY_AFTER_PATTERNS:
        m = pat.search(msg)
        if not m:
            continue
        groups = m.groups()
        try:
            if len(groups) == 2:
                return float(groups[0]) * 60 + float(groups[1]) + 0.5
            return float(groups[0]) + 0.5
        except (ValueError, TypeError):
            continue
    return 30.0  # default cooldown when API doesn't tell us


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "429" in msg
        or "rate limit" in msg
        or "rate_limit" in msg
        or "quota" in msg
        or "resource exhausted" in msg
    )


def _is_daily_quota(exc: Exception) -> bool:
    """Daily quota errors won't recover until UTC midnight (or many minutes)."""
    msg = str(exc).lower()
    return (
        "tokens per day" in msg
        or "(tpd)" in msg
        or "daily" in msg and "quota" in msg
        or "requests per day" in msg
        or "(rpd)" in msg
    )


@dataclass
class ProviderState:
    provider: LLMProvider
    cooldown_until: float = 0.0          # unix timestamp
    consecutive_failures: int = 0
    total_calls: int = 0
    total_tokens: int = 0


@dataclass
class MultiProviderLLM(LLMProvider):
    """Rotates across providers with cooldown tracking.

    states: ordered list — first non-cooled provider gets each call
    on_wait: callback(seconds, provider_name) for UI progress
    on_switch: callback(from_name, to_name, reason) for UI progress
    max_total_wait_s: hard ceiling for ANY single .complete() call (default 8h
        — long enough for Groq daily quota to reset at UTC midnight)
    """
    states: list[ProviderState] = field(default_factory=list)
    on_wait: Callable[[float, str], None] | None = None
    on_switch: Callable[[str, str, str], None] | None = None
    max_total_wait_s: float = 8 * 3600

    name: str = "multi"
    model: str = "rotating"

    def __post_init__(self):
        if not self.states:
            raise ValueError("MultiProviderLLM needs at least one ProviderState")
        # Inherit display model from primary
        self.model = "+".join(s.provider.name for s in self.states)

    @classmethod
    def from_providers(
        cls,
        providers: list[LLMProvider],
        on_wait: Callable[[float, str], None] | None = None,
        on_switch: Callable[[str, str, str], None] | None = None,
    ) -> "MultiProviderLLM":
        return cls(
            states=[ProviderState(provider=p) for p in providers],
            on_wait=on_wait,
            on_switch=on_switch,
        )

    def _next_available(self, now: float) -> ProviderState | None:
        for s in self.states:
            if s.cooldown_until <= now:
                return s
        return None

    def _earliest_resume(self, now: float) -> float:
        return min((s.cooldown_until for s in self.states), default=now)

    def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolSpec] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        response_format: Literal["text", "json"] = "text",
    ) -> LLMResponse:
        deadline = time.time() + self.max_total_wait_s
        last_provider_name: str | None = None

        while time.time() < deadline:
            now = time.time()
            state = self._next_available(now)
            if state is None:
                # All cooled down — sleep until earliest resumes
                wait = max(2.0, self._earliest_resume(now) - now)
                if self.on_wait:
                    waiting_for = sorted(self.states, key=lambda s: s.cooldown_until)[0]
                    self.on_wait(wait, waiting_for.provider.name)
                time.sleep(min(wait, 60))  # wake every minute to re-check
                continue

            if last_provider_name and last_provider_name != state.provider.name and self.on_switch:
                self.on_switch(last_provider_name, state.provider.name, "previous throttled")
            last_provider_name = state.provider.name

            try:
                resp = state.provider.complete(
                    messages=messages, tools=tools,
                    temperature=temperature, max_tokens=max_tokens,
                    response_format=response_format,
                )
                state.consecutive_failures = 0
                state.total_calls += 1
                state.total_tokens += resp.usage.input_tokens + resp.usage.output_tokens
                return resp

            except Exception as e:
                if not _is_rate_limit_error(e):
                    # Non-rate-limit error — propagate
                    raise

                # Rate limit. Decide cooldown.
                if _is_daily_quota(e):
                    # Conservative: 1 hour. Actual TPD reset is UTC midnight,
                    # but we re-check every wakeup anyway.
                    cooldown = 3600.0
                else:
                    # TPM — short backoff with the API-suggested wait
                    cooldown = max(_parse_retry_after(e), 5.0)

                state.cooldown_until = time.time() + cooldown
                state.consecutive_failures += 1
                if self.on_switch:
                    self.on_switch(
                        state.provider.name, "(any-other)",
                        f"429: cooling for {cooldown:.0f}s",
                    )
                # Loop back — try next available provider

        raise RuntimeError(
            f"MultiProviderLLM exhausted {self.max_total_wait_s/3600:.1f}h budget "
            "without successful completion across providers."
        )

    # Convenience for diagnostics
    def status(self) -> list[dict]:
        now = time.time()
        return [
            {
                "provider": s.provider.name,
                "cooldown_remaining_s": max(0, s.cooldown_until - now),
                "calls": s.total_calls,
                "tokens": s.total_tokens,
                "consecutive_failures": s.consecutive_failures,
            }
            for s in self.states
        ]
