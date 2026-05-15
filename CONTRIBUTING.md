# Contributing

Thanks for the interest. This guide covers everything you need to set up a
development environment, find your way around the code, and submit changes.

## Quick start (dev environment)

```bash
# 1. Clone and install
git clone https://github.com/ankittalwar07/Multi-agent-AI-investment-agent.git
cd Multi-agent-AI-investment-agent
pip install -r requirements.txt

# 2. Run the tests (should take ~3 seconds)
PYTHONPATH=src:. python -m pytest tests/ -q

# 3. Run the dashboard in Demo mode (no API keys needed)
streamlit run streamlit_app.py
# Toggle "Demo mode" ON in the sidebar
```

If the tests pass and the dashboard loads with all sidebar pages
(Datacenter Anatomy / Market Map / Components / Investment Thesis /
Investor Council / Portfolio / Run), you're set up.

## Where to find things

```
streamlit_app.py             # Home (Executive Summary)
dashboard_utils.py           # Shared chart builders + recommendation logic
design.py                    # Design system + deep-dive queue helpers
pages/                       # Streamlit auto-discovered pages
src/investment_agent/
  agents/                    # Each cooperating AI agent
  council/                   # 9 investor personas + scoring rubrics
  intelligence/              # Government / political flow signals
  llm/                       # Provider-agnostic LLM layer
    base.py                  #   Protocol + types
    factory.py               #   get_provider("...") dispatcher
    multi.py                 #   MultiProviderLLM (rotation chain)
    {gemini,groq,ollama,anthropic,openai,mock}_provider.py
    mock_data.py             #   Hand-crafted Demo-mode dataset
  tools/                     # Tools the researcher can call
  graph/build.py             # Pipeline orchestration
  storage/                   # SQLite persistence
  scoring/moat_rubric.py     # Pure-Python composite moat score
  cli.py                     # `python -m investment_agent.cli ...`
data/
  seeds/ai_infra_components.yaml   # AI-infra taxonomy
  runs/                      # Per-run SQLite + JSON + Markdown
scripts/                     # CLI runners + test scripts
tests/                       # pytest test suite
docs/                        # Architecture + cost-optimization + glossary
```

## Common contribution recipes

### Adding a new investor to the council

1. Open `src/investment_agent/council/personas.py`. Add a new
   `InvestorPersona` entry to the `COUNCIL` list with: `key`,
   `name`, `firm`, `era`, `style`, `philosophy`, `favors`,
   `dislikes`, `famous_quote`, `avatar`.
2. Open `src/investment_agent/council/rubrics.py`. Write a function
   matching the existing pattern (see `buffett`, `marks`, etc.) — takes
   a `CompanyView` dict, returns `_v(verdict, conviction, reasoning,
   pos, concern)`. Register it in the `RUBRICS` dict at the bottom.
3. Pick an accent color and add it to `PERSONA_ACCENT` in both
   `pages/3_Investment_Thesis.py` and `pages/4_Investor_Council.py`.
4. Run the tests: `PYTHONPATH=src:. python -m pytest tests/ -q`.
5. Run the dashboard in Demo mode and verify the new persona appears
   in the council cards and BUY-list tabs.

### Adding a new market layer (component)

1. Open `data/seeds/ai_infra_components.yaml`. Add a new entry with
   `name`, `category`, `description`, `incumbents`, and (optionally)
   `notes`.
2. If you want rich Demo-mode data for it, add entries in
   `src/investment_agent/llm/mock_data.py` under `MOCK_FINDINGS`.
   Optional patches: `EARNINGS_POWER`, `RISK_SENTIMENT`, `SCENARIOS`,
   `INTELLIGENCE` per company.
3. Open `pages/0_Datacenter_Anatomy.py`. Add the component to the
   appropriate tier in `LAYERS`.

### Adding a new LLM provider

1. Create `src/investment_agent/llm/<name>_provider.py` mirroring
   `groq_provider.py` (which is the simplest example — OpenAI-compatible
   wrapper).
2. Wire into `src/investment_agent/llm/factory.py` with a new `if
   name == "<name>": ...` branch.
3. Add `"<name>"` to `PROVIDERS` and `DEFAULT_MODELS` /
   `PROVIDER_HINTS` in `streamlit_app.py`.
4. Add a test script at `scripts/test_<name>.py` mirroring
   `scripts/test_groq.py`.
5. Add unit tests at `tests/test_<name>_factory.py` mirroring
   `tests/test_groq_factory.py`.
6. Update `.env.example` if a new env var is required.

### Adding an intelligence-signal data source

1. Open `src/investment_agent/intelligence/sources.py`. Add a new
   `DataSource(...)` entry to the `SOURCES` list with: `name`, `url`,
   `category`, `auth`, `description`.
2. If it requires an API key, document the env var name in the `auth`
   field (e.g., `"env:USASPENDING_API_KEY"`).
3. Add real-data fetch code in `src/investment_agent/intelligence/agent.py`
   if the data is structured (most public sources are scrape-only and
   should use the existing `web_fetch` tool path instead).
4. Document the source in the README "Data sources for the Intelligence
   Agent" table.

## Testing

### Running tests

```bash
PYTHONPATH=src:. python -m pytest tests/ -q
```

Should complete in 2-3 seconds. All 19 tests should pass.

### When to add tests

- New scoring logic → add a test in `tests/test_scoring.py`
- New provider → factory test in `tests/test_<name>_factory.py`
- New repository column → round-trip test in `tests/test_repository.py`
- New end-to-end flow → mock-pipeline test in `tests/test_pipeline_smoke.py`

### What NOT to test

- Don't add tests that hit real LLM APIs (paid + flaky)
- Don't snapshot-test plotly figure HTML (changes too often)
- Mock providers in tests — see `tests/test_mock_provider.py` for the pattern

## Code style

- Python 3.11+
- Type hints encouraged (`from __future__ import annotations` at top of every file)
- Pydantic for any data structure that crosses module boundaries
- Black-compatible formatting (we don't enforce in CI but it's the standard)
- Imports: `from __future__`, stdlib, third-party, local — separated by blank lines
- Strings: double quotes preferred; f-strings for interpolation

## Commit style

- One feature / fix per commit
- Commit message: imperative mood ("Add X", "Fix Y") on the subject line
- A short body explaining **why** the change matters (not what changed —
  the diff shows that)
- Reference the docs that need updating in the commit body if applicable

## Submitting changes

1. Fork the repo
2. Create a branch: `git checkout -b feature/short-name`
3. Make changes + add tests
4. Run `PYTHONPATH=src:. python -m pytest tests/ -q` and verify all
   tests pass
5. Run the dashboard locally in Demo mode and click through every page
   to verify nothing broke visually
6. Open a Pull Request against `main` with a brief description

## Things I'm specifically looking for help with

- **Real Intelligence Agent connectors**: USAspending.gov, Senate EFD,
  SEC EDGAR Form 4 actual fetchers (currently the Demo dict)
- **More upstream layers**: water infrastructure, specialty chemicals,
  data labeling, autonomous-vehicle compute
- **Sub-second triage**: prompt engineering to get under 50k tokens
  for a full triage pass
- **Yahoo Finance live price overlay**: when a company has a ticker,
  fetch the current price via yfinance and stamp it on the Investment
  Thesis page (with a disclaimer about delayed data)
- **PDF analyst-memo export**: each Investment Thesis page → printable PDF

## Code of conduct

Be kind. Disagree about ideas, not people. If a discussion gets heated,
take it offline.

## License

MIT (see LICENSE file). All contributions are accepted under the same.

---

Questions? Open an issue, or just send a PR with a clear description.
