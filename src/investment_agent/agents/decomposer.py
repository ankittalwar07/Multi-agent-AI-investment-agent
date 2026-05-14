from __future__ import annotations

import json
from dataclasses import dataclass

from ..llm.base import LLMMessage, LLMProvider
from ..tools.seed_loader import SeedComponent, SeedLoaderTool
from .prompts import DECOMPOSER


@dataclass
class DecomposedComponent:
    name: str
    category: str
    description: str
    source: str  # "seed" | "llm_expanded"


class Decomposer:
    def __init__(self, llm: LLMProvider, seed_tool: SeedLoaderTool, max_components: int | None = None):
        self.llm = llm
        self.seed_tool = seed_tool
        self.max_components = max_components

    def run(self) -> tuple[list[DecomposedComponent], float]:
        seed: list[SeedComponent] = self.seed_tool.all_components()
        seed_json = json.dumps([c.model_dump() for c in seed], indent=2)

        user = (
            "Here is the seeded taxonomy of AI-infrastructure components:\n\n"
            f"{seed_json}\n\n"
            "Preserve all seeded components verbatim (set source='seed'). Then, "
            "if you can identify additional components that materially matter, "
            "add them in 'added' with justification. Return JSON only."
        )
        messages = [
            LLMMessage(role="system", content=DECOMPOSER),
            LLMMessage(role="user", content=user),
        ]
        resp = self.llm.complete(messages=messages, response_format="json", max_tokens=2048)

        # All seed components are always present, regardless of what the LLM returned.
        components: list[DecomposedComponent] = [
            DecomposedComponent(
                name=c.name, category=c.category, description=c.description, source="seed"
            )
            for c in seed
        ]

        # Try to parse additions; failures are non-fatal.
        try:
            payload = json.loads(resp.content) if resp.content else {}
            for a in payload.get("added", []) or []:
                if not a.get("name"):
                    continue
                # Avoid dupes against seeded names (case-insensitive).
                if any(c.name.lower() == a["name"].lower() for c in components):
                    continue
                components.append(
                    DecomposedComponent(
                        name=a["name"],
                        category=a.get("category", "uncategorized"),
                        description=a.get("description", ""),
                        source="llm_expanded",
                    )
                )
        except json.JSONDecodeError:
            pass

        if self.max_components is not None:
            components = components[: self.max_components]

        return components, resp.usage.cost_usd
