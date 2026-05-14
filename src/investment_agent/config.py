from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM — default to Gemini Flash (free tier on Google AI Studio).
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    llm_model: str | None = Field(default=None, alias="LLM_MODEL")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")

    # Paid market data (stubs when unset)
    bloomberg_api_key: str | None = Field(default=None, alias="BLOOMBERG_API_KEY")
    pitchbook_api_key: str | None = Field(default=None, alias="PITCHBOOK_API_KEY")
    crunchbase_api_key: str | None = Field(default=None, alias="CRUNCHBASE_API_KEY")
    similarweb_api_key: str | None = Field(default=None, alias="SIMILARWEB_API_KEY")

    # Runtime
    max_cost_usd: float = Field(default=5.0, alias="MAX_COST_USD")
    max_parallel_researchers: int = Field(default=4, alias="MAX_PARALLEL_RESEARCHERS")
    run_output_dir: Path = Field(default=Path("data/runs"), alias="RUN_OUTPUT_DIR")
    seed_file: Path = Field(
        default=Path("data/seeds/ai_infra_components.yaml"), alias="SEED_FILE"
    )

    # Per-researcher caps
    max_searches_per_researcher: int = 8
    max_fetches_per_researcher: int = 15
    per_component_cost_cap_usd: float = 0.5


def get_settings() -> Settings:
    return Settings()
