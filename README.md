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

## Quickstart (local) — free LLM options

The dashboard ships with two free LLM options (no credit card). Pick either or
both — they have independent rate limits, so when one throttles you switch:

| Provider | Model | Get key | Free tier | Best for |
|---|---|---|---|---|
| **Gemini** | `gemini-2.0-flash` | <https://aistudio.google.com/apikey> | ~15 req/min, ~1M tokens/day | Default. Best general quality. |
| **Groq** | `llama-3.3-70b-versatile` | <https://console.groq.com/keys> | ~30 req/min, ~14k req/day | Fastest (~200 tok/sec). Open-source Llama. Independent quota when Gemini throttles. |

```bash
pip install -r requirements.txt

# Pick one (or both)
export GOOGLE_API_KEY="paste-gemini-key-here"
export GROQ_API_KEY="paste-groq-key-here"

# Verify either provider works end-to-end (one call, prints the response)
PYTHONPATH=src python scripts/test_gemini.py
PYTHONPATH=src python scripts/test_groq.py

# Generate a run — swap --provider gemini | groq | anthropic | openai
PYTHONPATH=src python -m investment_agent.cli run \
    --provider groq --model llama-3.3-70b-versatile --max-components 5

# Launch the dashboard
streamlit run streamlit_app.py
```

Claude / GPT-4o are also wired in (paid). All providers selectable via the
sidebar dropdown in the dashboard.

The dashboard ships with **Demo mode** on by default — it uses hand-crafted
realistic mock data (real incumbents, plausible shares, demand signals) so you
can explore the visuals without any API keys.

## Deploy to Streamlit Community Cloud (free public link)

1. Push this repo to GitHub (already the case for `ankittalwar07/Multi-agent-AI-investment-agent`).
2. Go to <https://share.streamlit.io> → **New app**.
3. Select the repo, branch `claude/multi-agent-market-analysis-NKfET` (or `main`), main file: `streamlit_app.py`.
4. Click **Deploy**. You'll get a public URL like `https://<your-app>.streamlit.app`.
5. (Optional) Add `ANTHROPIC_API_KEY` etc. in **App settings → Secrets** if you want live runs against Claude/Gemini/OpenAI. Without keys the app still works in Demo mode.

The repo includes:
- `streamlit_app.py` at the root (Streamlit Cloud's expected entry point)
- `pages/` directory at the root (auto-discovered multipage layout)
- `requirements.txt` with all deps
- `.streamlit/config.toml` with a dark investor theme

## Repository layout

See `/root/.claude/plans/i-want-to-create-squishy-hammock.md` for the full plan and `pyproject.toml` for dependencies.

```
src/investment_agent/   # python package (llm, tools, agents, graph, storage, scoring)
app/                    # Streamlit multipage app
data/seeds/             # ai_infra_components.yaml — the taxonomy seed
data/runs/              # per-run SQLite + JSON output
tests/                  # unit + recorded-fixture tests + mock-mode smoke
```

## Intelligence Agent — data sources

The Intelligence Agent aggregates non-financial signals that the market often
misprices: US government investments, federal contracts, congressional STOCK Act
trades, foreign sovereign activity, policy headwinds, and SEC Form 4 cluster
buys. In Demo mode signals come from a hand-crafted patch dict; in live runs
the LLM provider populates them via the documented public sources.

### Free (no API key)

| Source | URL | What it provides |
|---|---|---|
| **USAspending.gov** | <https://api.usaspending.gov/api/v2/search/spending_by_award/> | All US federal contract awards + grants since 2008 |
| **DoD Daily Contracts** | <https://www.defense.gov/News/Contracts/> | Defense contracts >$7.5M posted daily |
| **Senate EFD** | <https://efdsearch.senate.gov/search/> | Senate Periodic Transaction Reports (STOCK Act) |
| **House Clerk Disclosures** | <https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure> | House financial disclosures |
| **SEC EDGAR Form 4** | <https://www.sec.gov/cgi-bin/browse-edgar> | Corporate insider transactions |
| **OpenInsider** | <http://openinsider.com/screener> | Form 4 aggregator with cluster-buy flags |
| **BIS Entity List** | <https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern/entity-list> | Export-control restrictions |
| **DoC press releases** | <https://www.commerce.gov/news/press-releases> | CHIPS Act preliminary memoranda + definitive awards |
| **Capitol Trades** | <https://www.capitoltrades.com/> | Front-end for STOCK Act disclosures |

### Free with API key

| Source | URL | Env var |
|---|---|---|
| **Quiver Quantitative** | <https://api.quiverquant.com/> | `QUIVER_API_KEY` (free tier: 10 req/day) |

### Paid

| Source | Why |
|---|---|
| **Bloomberg Terminal** | Best coverage of sovereign flows + China Big Fund |
| **FactSet Government Edge** | Structured, back-tested gov contract + lobbying + congressional trade |

### Live-run integration

In Demo mode the agent reads from `INTELLIGENCE` in `src/investment_agent/llm/mock_data.py`.
For live runs against Claude/Gemini, the LLM provider can call the existing
`web_search` and `web_fetch` tools to populate the same `IntelligenceSignal`
shape (defined in `src/investment_agent/intelligence/signals.py`). Quiver and
SEC EDGAR responses parse directly into that shape.

The status of each source (connected vs gated) is also viewable from
`investment_agent.intelligence.sources.source_status()`.

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
