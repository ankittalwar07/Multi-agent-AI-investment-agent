# Multi-Agent AI Infrastructure Investment Agent

A multi-agent system that walks the entire AI infrastructure lifecycle, decomposes it into ~15–20 components (EUV lithography → foundry → HBM → accelerators → networking → power → clouds → foundation models → inference HW → tooling), and spawns a research sub-agent per component to surface companies that are **sole-source or majority suppliers** with strong / growing demand.

The output is a ranked list of investable companies with moat-strength scores, evidence-linked citations, and per-component drill-down — viewable in a Streamlit dashboard.

## Architecture

```
                       ┌────────────────┐
                       │  Decomposer    │  reads seed YAML, expands to ~15–20 components
                       └───────┬────────┘
                               │ fan-out (LangGraph Send)
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ Component    │  ...  │ Component    │  ...  │ Component    │  ReAct loop
│ Researcher 1 │       │ Researcher k │       │ Researcher n │  web search/fetch
└──────┬───────┘       └──────┬───────┘       └──────┬───────┘  + paid stubs + seed
       └──────────────────────┼──────────────────────┘
                              ▼
                  ┌─────────────────────┐
                  │ Concentration       │  rubric scoring
                  │ Analyzer            │  (sole-source, share, IP, ...)
                  └──────────┬──────────┘
                             ▼
                  ┌─────────────────────┐
                  │ Synthesizer         │  ranked report + JSON + Markdown
                  └──────────┬──────────┘
                             ▼
                       SQLite + Streamlit
```

## LLM providers

Pick at run time — the system has a thin `LLMProvider` adapter so the same agents work across:

- `anthropic` (Claude)
- `openai` (GPT)
- `gemini` (Google)
- `mock` (deterministic fixtures, no API calls — used for tests and `make smoke`)

## Quickstart

```bash
make install-dev
cp .env.example .env   # fill in keys for whichever provider(s) you want

# Smoke test end-to-end with the mock provider (no API spend):
make smoke

# Real run with Gemini against the full seed:
python -m investment_agent.cli run --provider gemini --model gemini-1.5-pro

# Streamlit UI:
make ui
```

## Repository layout

See `/root/.claude/plans/i-want-to-create-squishy-hammock.md` for the full plan and `pyproject.toml` for dependencies.

```
src/investment_agent/   # python package (llm, tools, agents, graph, storage, scoring)
app/                    # Streamlit multipage app
data/seeds/             # ai_infra_components.yaml — the taxonomy seed
data/runs/              # per-run SQLite + JSON output
tests/                  # unit + recorded-fixture tests + mock-mode smoke
```

## Data sources

- **Web search** — DuckDuckGo (free, rate-limited).
- **Web fetch** — `httpx` + `trafilatura` for readability; respects `robots.txt`; rejects non-http(s) / private-IP / >5MB; untrusted page content is sentinel-wrapped so the LLM treats it as data.
- **Paid market data** — Bloomberg / PitchBook / Crunchbase / SimilarWeb stubs. When the corresponding `*_API_KEY` env var is unset the tool returns a structured `ok=False` ToolResult; agents still call the interface the same way.
- **Local seed file** — `data/seeds/ai_infra_components.yaml` — a curated taxonomy of AI-infra components and known incumbents, used as a prior so the decomposer doesn't reinvent the wheel each run.

## Moat rubric

Each company is scored 0–100 on:

| Dimension                | Max pts | Notes                                          |
|--------------------------|---------|------------------------------------------------|
| Sole-source              | 30      | Requires ≥2 independent citations              |
| Market-share bucket      | 25      | `<10` / `10-25` / `25-50` / `50-75` / `>75`    |
| IP / tech moat           | 15      |                                                |
| Regulatory moat          | 10      |                                                |
| Switching costs          | 10      |                                                |
| Demand signal            | 10      | Growth / order-book / capex commitments        |

## Verification

- `make test` — unit tests (pure-python: scoring, repository, citation, seed loader).
- `make smoke` — runs `--mock` end-to-end against a 3-component seed subset; asserts SQLite + report.md are produced; $0 cost.
- `make ui` — manual click-through of the four Streamlit pages.

## Risks & caveats

- **Free web search is best-effort** — DuckDuckGo throttles aggressively; budget for retries.
- **Prompt-injection from fetched pages** is mitigated by sentinel-wrapping but not eliminated; never trust extracted page content as agent instructions.
- **Citations are mandatory** — the synthesizer drops any claim that lacks a linked evidence row.
- **Costs** are capped per-run via `MAX_COST_USD` and per-component soft cap; researchers also cap themselves at 8 searches / 15 fetches.
- **No financial advice.** This produces research outputs to inform your own due diligence.
