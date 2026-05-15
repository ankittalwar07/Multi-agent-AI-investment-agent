# AI Infrastructure — Investment Brief

A multi-agent AI dashboard that walks the entire AI-infrastructure value chain
(from copper and rare earths up through ASML's EUV scanners, NVIDIA GPUs,
hyperscaler clouds, and Anthropic's Claude) and surfaces the companies most
worth buying — with a debate-driven analysis from a council of nine legendary
investors and signals from government policy and political trading.

> **Built for the savvy investor hunting** sole-source bottlenecks,
> capacity-constrained incumbents, and mispriced private positions across
> the AI stack — not generic "what's hot" suggestions.

---

## The problem this solves

Every news cycle has a different AI hype darling. But the real money in any
buildout cycle is made by **owning the bottleneck** — the supplier nobody can
replace. In the railroad era it was steel. In the internet era it was fiber.
In the AI era, what is it? GPUs? Power? Cooling? Rare earths? Photoresist?
You need to walk the whole stack systematically.

A single Google search won't tell you. Asking ChatGPT once gives you one
shallow opinion. What you want is:

1. **Comprehensive coverage** — every layer of the AI value chain, including
   the upstream stuff (copper, gases, substrates) that's underrated
2. **Differentiated opinions** — bull voices AND bear voices, debating each name
3. **Real data** — not hype; actual P/E ratios, ROIC, capex intensity, customer
   concentration
4. **Non-financial signals** — CHIPS Act awards, congressional trading,
   foreign government activity, policy headwinds
5. **Cost control** — running this kind of analysis on every company in the
   universe is expensive in LLM tokens. We need to be smart about it.

This dashboard delivers all five.

---

## What you see when you use it

After running once (~30 seconds for free triage; ~2 minutes for deep dives on
your top picks):

- **Executive Summary** — top 5 high-conviction picks with recommendation
  badges (STRONG BUY / BUY / HOLD), expected 12-month return, and the
  council's consensus rating
- **Datacenter Anatomy** — visual stack diagram from raw materials at the
  bottom to applications at the top, with supply-constraint and sole-source
  flags on each tier
- **Market Map** — value chain organized by tier with structure badges
  (monopoly / duopoly / oligopoly / fragmented) on every component
- **Investment Thesis** (per company) — full analyst report with:
  - Stock & valuation (price, P/E TTM + forward, PEG, EV/EBITDA, market cap)
  - Earnings power & balance sheet (ROIC vs WACC, net cash/debt, capex
    intensity, FCF after capex, R&D intensity)
  - Risk & sentiment (customer concentration, hyperscaler capex beta,
    China revenue %, insider activity, short interest, EPS revisions)
  - Intelligence signals (CHIPS Act funding, federal contracts,
    congressional trades, foreign sovereign activity, policy headwinds)
  - Scenario math (probability-weighted bull/base/bear returns, editable
    5-year DCF, sensitivity grid)
  - **Council of nine investors** with each one's verdict + reasoning
  - Time-horizon thesis (short / base / long / exit triggers)
- **Investor Council** — voting matrix across all companies, per-investor
  BUY lists, "divergent picks" view where bulls and bears disagree
- **Portfolio** — conviction-weighted aggregation of all BUY-rated names

---

## How it works — the multi-agent architecture

The dashboard is powered by **eight cooperating AI agents** plus deterministic
analysis layers. Each agent has a narrow specialty and feeds the next:

```
                ┌──────────────┐
                │  Decomposer  │  Breaks the AI stack into
                └──────┬───────┘  ~25 components from a seed taxonomy
                       │
                       ▼ fan-out (one per component)
┌──────────────────────────────────────────────────────┐
│  Triage Researcher  (one LLM call per component)     │  ← TIER 1 (cheap)
│  Outputs: 3-5 incumbents with sparse moat data       │
└──────────────────────────────────────────────────────┘
                       │
                       ▼  USER picks high-conviction names from triage
┌──────────────────────────────────────────────────────┐
│  Deep-Dive Researcher  (full ReAct + web search)     │  ← TIER 2 (expensive)
│  Outputs: full earnings power, risk, scenario data   │
└──────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  Concentration Analyzer  (deterministic rubric)      │
│  Scores moat strength 0-100 across 6 dimensions      │
└──────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  Intelligence Agent  (government + political flows)  │
│  Pulls CHIPS Act / DoD / Senate EFD / SEC EDGAR      │
└──────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  Council of Investors  (9 personas)                  │
│  Each persona votes with their distinct lens         │
└──────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  Synthesizer  (ranks all and writes a brief)         │
└──────────────────────────────────────────────────────┘
                       │
                       ▼
              SQLite + Streamlit dashboard
```

### What each agent does, in plain English

| Agent | Job | Why it exists |
|---|---|---|
| **Decomposer** | Lists the ~25 layers of the AI stack | One LLM is bad at researching everything at once. Split the work first. |
| **Triage Researcher** | One quick LLM call per layer; returns "the 3-5 incumbents that matter, with a one-line thesis" | Most companies don't deserve deep analysis. Find what's interesting first. |
| **Deep-Dive Researcher** | Full ReAct loop with web search on user-selected companies | The expensive analysis — only spent on names you actually care about. |
| **Concentration Analyzer** | Scores each company's moat 0-100 (sole-source, share, IP, regulatory, switching costs, demand) | Standardized scorecard so different companies are comparable. Pure Python — no LLM tokens. |
| **Intelligence Agent** | Pulls non-financial signals: CHIPS Act funding, congressional trading, foreign government activity, policy headwinds | These signals are public but invisible to standard financial APIs. Often predictive. |
| **Council of Legendary Investors** | Nine famous investors each vote on every company through their distinct lens | A single AI gives one opinion. A council surfaces debate and **alpha-rich divergence**. |
| **Synthesizer** | Ranks everyone, writes the final investment brief | Turns 60+ company records into a digestible top-N list with cross-stack themes. |

---

## The Council of Legendary Investors

Each company is reviewed through nine distinct lenses. This is the most
important design decision in the dashboard: **a single AI hallucinating one
"recommendation" is dangerous — a debate of nine differentiated opinions
surfaces both confidence and controversy.**

### The bulls (mainline analysis)

| Investor | Lens | What they reward |
|---|---|---|
| **Warren Buffett** | Wonderful businesses at fair prices | High ROIC, predictable cash flows, P/E < 25, op margin > 20%, fortress balance sheet |
| **Charlie Munger** | Quality + mental models | ROIC > 20%, ROIC-WACC spread > 5pp, durable competitive advantage, capital allocators |
| **Peter Lynch** | Growth at a Reasonable Price (GARP) | PEG < 1.5, forward growth > 15%, understandable products |
| **Stanley Druckenmiller** | Macro + concentration + capacity | Sole-source positioning, hyperscaler capex beta > 1.0, EPS revisions trending up |
| **Cathie Wood** | Disruptive innovation | Forward revenue growth > 30%, platform shifts (AI accelerators, foundation models), industrial-policy backing |

### The bears (cycle awareness — added explicitly to avoid AI confirmation bias)

| Investor | Lens | What they push back on |
|---|---|---|
| **Benjamin Graham** | Deep value + margin of safety | Anything with P/E > 25; speculation without earnings |
| **Howard Marks** | Cycle awareness + crowding | "Multiple euphoria signals stacked" — high P/E + parabolic growth + consensus love + low short interest = AVOID |
| **Michael Burry** | Bubble caller | P/E > 40, PEG > 2.5, FCF burn, AI-hype layers at > 30x forward — "this is 1999" |
| **Ray Dalio** | Macro / debt cycle / geopolitics | China revenue > 25%, single-customer > 40%, parabolic growth with no dividend cushion |

### What the dashboard does with this

Every company gets nine verdicts. The system computes a **consensus label**:

- **Unanimous STRONG BUY** — 6+ STRONG BUYs (highest confidence — e.g., ASML)
- **Unanimous BUY** — 8/9 BUY or STRONG BUY (strong consensus)
- **Majority BUY** — 5/9 BUY (the typical case for a strong pick)
- **DIVIDED** — bulls and bears squarely opposed (often the most alpha-rich
  setups — e.g., MP Materials, where Druckenmiller buys the rare-earth
  supply story while Munger avoids the thin moat)
- **Majority PASS/AVOID** — the bears have won

The **Investor Council page** also shows a per-company × per-investor voting
matrix so you can see at a glance who agrees and who pushes back.

---

## The cost optimization design — why this is cheap to run

LLM tokens are the main cost. A naive implementation would do a multi-step
ReAct loop with web search for every company in every layer — easily 150+
LLM calls and 400-500k tokens per full run. That blows past free-tier
quotas in one shot.

We made four design decisions to bring this down by 70%+ while preserving
analytical quality:

### 1. Two-tier analysis: Triage → Deep Dive

The old approach: do exhaustive ReAct research on every company in every
layer. ~5 LLM calls × ~60 companies = ~300 calls.

The new approach:
- **Tier 1 (Triage)** — one LLM call per layer (~25 calls total) returns
  3-5 incumbents per layer with sparse data: name, ticker, market share
  bucket, structure, sole-source flag, demand signal, one-line thesis.
  That's enough to populate the moat rubric and run the council.
- **Tier 2 (Deep Dive)** — the expensive multi-step research only runs on
  companies the **user explicitly picks** from the triage view. Typically
  5-10 names.

Total: ~27 (triage) + ~50 (deep on 10 picks) = **~75 LLM calls instead of
~300**. And **100% of the tokens are spent on companies you care about** —
not wasted on every component in the seed file.

### 2. Multi-provider rotation (free quotas combined)

Free LLM tiers have small daily caps (Gemini ~1M tokens/day, Groq 8B
~500k/day). One provider runs out before a full deep dive is done.

The `MultiProviderLLM` wrapper tries Gemini first; when 429-rate-limited,
rotates to Groq; when both are throttled, sleeps until the earliest reset.
Parses the API's "try again in Xs" hint to know how long to wait.

Effect: **combined daily quota is ~1.5M tokens** — enough for a full triage
run + multiple deep-dive sessions per day, all at $0 cost.

### 3. Resumable pipeline (hit run once, walk away)

Long-running deep-dive sessions can hit rate limits mid-run. Rather than
fail, the pipeline:

- Persists each component's status (`pending` / `researching` / `done` /
  `rate_limited` / `error`) to SQLite as it goes
- On rate limit: marks the component, sleeps, and either rotates providers
  or waits for quota reset
- `run_until_done()` keeps looping until every component is `done`
- `Pipeline.run(resume_run_id=...)` picks up where it left off — only
  re-researches non-done components, no duplicate work
- A CLI script (`scripts/overnight_run.py`) wraps this for laptop-overnight
  use; the Streamlit "Run until done" button does the same in-browser

### 4. Deterministic rubrics over LLM scoring

The Concentration Analyzer scores each company's moat 0-100 across six
dimensions. The Council's nine personas each apply a rubric (e.g., "Munger
AVOIDs anything with ROIC < WACC", "Burry stacks bubble flags").

These are **pure Python functions** — no LLM tokens spent. The math is
explainable and consistent. The LLM is only used to *gather the data*; the
*scoring* is rule-based.

This trades some nuance for: explainability (every verdict cites which rule
fired), reproducibility (same data → same verdict), and dramatic cost
reduction (zero token cost for ~30% of the pipeline's "intelligence").

### Token economics summary

| Scenario | LLM calls | Tokens (approx) | Fits in free Gemini? | Fits in free Groq 8B? |
|---|---|---|---|---|
| Old: deep research on all 60 companies | ~300 | ~500,000 | No (uses 50% of daily quota in one run) | **No** (5x over daily cap) |
| New: triage only (~25 components) | ~27 | ~75,000 | **Yes** (7.5% of quota) | **Yes** (15% of quota) |
| New: triage + deep dive on 10 picks | ~77 | ~275,000 | **Yes** (27% of quota) | **Yes** (55% of quota) |

---

## Intelligence signals — what's different from a standard analyst report

Most financial APIs (Bloomberg, FactSet) cover P/E and ROIC well. They
don't cover the public-but-buried signals that often move stocks:

- **CHIPS Act funding** — Intel got $8.5B, TSMC $6.6B, Samsung $4.7B,
  Micron $6.1B. These are huge announcements made via DoC press releases.
- **Defense Production Act stakes** — MP Materials got $400M from DoD for
  rare-earth processing. Critical for the rare-earth thesis.
- **Congressional STOCK Act disclosures** — Senate and House members are
  required to disclose stock trades within 45 days. Famously, Nancy Pelosi's
  NVDA call option purchase made the news. Aggregated, these tell you what
  political insiders are positioning around.
- **Foreign government activity** — China Big Fund Phase III is investing
  $47B in domestic semis. Saudi PIF / UAE Mubadala are funding G42's
  Microsoft partnership. METI is subsidizing Japanese substrate makers.
- **Policy headwinds** — BIS Entity List additions, CFIUS reviews, DOJ
  antitrust cases. These cut revenue or kill deals.
- **SEC Form 4 cluster buys** — when multiple insiders buy in the same week
  it's historically predictive.

The **Intelligence Agent** aggregates these into a composite "intelligence
score" per company (−100 to +100), with positive scores meaning policy
tailwinds + insider/political buying, and negative scores meaning Entity
List / antitrust / sovereign headwinds.

Council members consume this signal:
- **Druckenmiller** rewards strong government investment ("policy is the
  macro tailwind")
- **Cathie Wood** treats it as platform validation
- **Howard Marks** flags politically-crowded names ("this trade is in the
  public consciousness now")
- **Ray Dalio** uses China revenue % and customer concentration to score
  geopolitical chokepoint risk

Data sources documented below — most are free APIs.

---

## How to read a recommendation

When you open the **Investment Thesis** page for, say, ASML, here's how to
read it from top to bottom:

1. **Header** — company name, ticker, recommendation badge (e.g.,
   STRONG BUY in dark emerald), conviction (HIGH / MEDIUM / LOW)
2. **Headline thesis** — one-sentence summary of why the system likes
   (or dislikes) this name
3. **Stock & valuation** — current price, market cap, 52-week range, P/E
   TTM + forward, PEG, EV/EBITDA, EV/Sales
4. **Earnings power & balance sheet** — ROIC vs WACC (the real moat in
   basis points), net cash/debt, capex intensity, FCF after capex.
   **Auto-generated flag bullets** highlight things like "Exceptional ROIC
   (82%) — every reinvested dollar earns extraordinary returns" or "Negative
   FCF after capex — funded by debt"
5. **Risk & sentiment** — top customer %, China revenue %, hyperscaler
   capex beta, insider 6m net buying, short interest, EPS revisions.
   Flag bullets call out concentration risks and crowding signals
6. **Intelligence signals** — CHIPS Act / federal contracts / congressional
   trades / policy headwinds with $ amounts and source links
7. **Scenario math** — slider-driven probability weights (bull / base / bear)
   showing the probability-weighted expected return + an editable DCF
   model with sensitivity grid
8. **Council of nine investors** — each one's verdict, conviction, and
   reasoning in their voice
9. **Time-horizon thesis** — short-term catalysts (1-2 quarters), base case
   (12-24m), long-term moat (3-5 years), exit triggers
10. **Market position** — share bucket, sole-source flag, structure, moat
    types, switching costs, customer concentration

The point is: every claim is anchored to a number, and the bull case is
always paired with a bear case.

---

## Quickstart — running it yourself

### Option A: Free path with Gemini + Groq (recommended)

You can run the full pipeline at $0 cost using two free LLM providers in
rotation. No credit card required.

```bash
# 1. Get the free keys (30 seconds each):
#    Gemini: https://aistudio.google.com/apikey
#    Groq:   https://console.groq.com/keys

export GOOGLE_API_KEY="AIza..."
export GROQ_API_KEY="gsk_..."

# 2. Verify they work
PYTHONPATH=src python scripts/test_gemini.py
PYTHONPATH=src python scripts/test_groq.py

# 3. Launch the dashboard
streamlit run streamlit_app.py
```

Then in the sidebar pick **Provider: `multi`** (rotates Gemini and Groq) and
run a **Quick triage**. Mark the names you care about with the **+ Deep dive**
button and click **Run dive** in the sidebar.

### Option B: Demo mode (no API keys at all)

```bash
streamlit run streamlit_app.py
```

Toggle **Demo mode** ON in the sidebar. The pipeline runs against
hand-crafted illustrative data — 62 companies across 25 components — so
you can evaluate the framework and UI without spending any tokens.

### Option C: Overnight CLI runner

For really long runs where you want to hit "go" once and walk away:

```bash
PYTHONPATH=src python scripts/overnight_run.py
```

Persists progress continuously, sleeps when both providers are throttled,
resumes from where it left off if killed:

```bash
PYTHONPATH=src python scripts/overnight_run.py --resume <run_id>
```

### Deploy to Streamlit Cloud

The repo is set up for one-click deploy on
[share.streamlit.io](https://share.streamlit.io):

1. **New app** → select this repo, branch `main`, main file `streamlit_app.py`
2. **App settings → Secrets** → paste in TOML:
   ```toml
   GOOGLE_API_KEY = "AIza..."
   GROQ_API_KEY = "gsk_..."
   ```
3. Deploy. You'll get a public URL like
   `https://multi-agent-ai-investment-agent.streamlit.app`

---

## Repository layout

```
streamlit_app.py             # Home page (Executive Summary)
dashboard_utils.py           # Shared chart builders + recommendation logic
design.py                    # Design system: typography, colors, queue helpers
pages/                       # Streamlit auto-discovered pages
  0_Datacenter_Anatomy.py    #   Visual stack diagram of the AI value chain
  1_Market_Map.py            #   Components organized by tier
  2_Components.py            #   Per-component drill-in
  3_Investment_Thesis.py     #   Per-company full report
  4_Investor_Council.py      #   Voting matrix + per-investor BUY lists
  5_Portfolio.py             #   Conviction-weighted aggregation
  6_Run.py                   #   Trigger a triage or deep-dive run
src/investment_agent/
  agents/                    # Each cooperating agent
    decomposer.py            #   Splits AI stack into ~25 components
    triage_researcher.py     #   Tier 1: one cheap LLM call/component
    component_researcher.py  #   Tier 2: ReAct deep-dive
    concentration_analyzer.py# Moat scoring (pure Python rubric)
    synthesizer.py           #   Final investment brief writer
  council/                   # Nine investor personas + rubrics
    personas.py              #   Bios, philosophies, famous quotes
    rubrics.py               #   Per-persona scoring functions
    engine.py                #   Apply all personas to one company
  intelligence/              # Government + political flow signals
    sources.py               #   Catalog of 12 data sources (free + paid)
    agent.py                 #   Aggregate signals → composite score
    signals.py               #   IntelligenceSignal Pydantic types
  llm/                       # Provider-agnostic LLM layer
    base.py                  #   LLMProvider protocol, types
    factory.py               #   get_provider("gemini" | "groq" | ...)
    multi.py                 #   MultiProviderLLM: rotates on 429s
    gemini_provider.py       #   Google Gemini wrapper
    groq_provider.py         #   Groq (Llama / Mixtral / Gemma) wrapper
    anthropic_provider.py    #   Anthropic Claude wrapper
    openai_provider.py       #   OpenAI GPT wrapper
    mock_provider.py         #   Deterministic fixture-based for Demo mode
    mock_data.py             #   Hand-crafted realistic data per company
  tools/                     # Tools the researcher agents can call
    web_search.py            #   DuckDuckGo search
    web_fetch.py             #   httpx + trafilatura with robots.txt
    seed_loader.py           #   Loads ai_infra_components.yaml taxonomy
    paid_market_data.py      #   Bloomberg/PitchBook/Crunchbase stubs
  graph/                     # Pipeline orchestration
    build.py                 #   Pipeline.run() + run_until_done() + deep_dive_companies()
    state.py                 #   Per-run state object
  storage/                   # SQLite persistence (one DB per run)
    schema.py                #   Tables: run, component, company, evidence, score, run_event
    repository.py            #   RunRepository CRUD
    models.py                #   Pydantic view models
  scoring/
    moat_rubric.py           #   Pure-Python composite moat score (0-100)
  cli.py                     #   `python -m investment_agent.cli ...`
data/
  seeds/ai_infra_components.yaml  # 25-layer AI-infra taxonomy + known incumbents
  runs/                      # Per-run SQLite databases + JSON + Markdown reports
scripts/
  overnight_run.py           # Hit-run-once-walk-away CLI runner with multi-provider + resume
  test_gemini.py             # One-call sanity check
  test_groq.py               # One-call sanity check
tests/                       # 15 tests covering scoring, storage, council, pipeline e2e
```

---

## Data sources for the Intelligence Agent

The Intelligence Agent aggregates non-financial signals. In Demo mode these
come from a hand-crafted patch dict; in live runs the LLM provider populates
them via the documented public sources.

### Free (no API key)

| Source | URL | What it provides |
|---|---|---|
| **USAspending.gov** | <https://api.usaspending.gov> | All US federal contracts + grants since 2008 |
| **DoD Daily Contracts** | <https://www.defense.gov/News/Contracts/> | Defense contracts >$7.5M posted daily |
| **Senate EFD** | <https://efdsearch.senate.gov/search/> | Senate Periodic Transaction Reports |
| **House Clerk Disclosures** | <https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure> | House financial disclosures |
| **SEC EDGAR Form 4** | <https://www.sec.gov/cgi-bin/browse-edgar> | Corporate insider transactions |
| **OpenInsider** | <http://openinsider.com/screener> | Form 4 aggregator with cluster-buy flags |
| **BIS Entity List** | <https://www.bis.doc.gov/.../entity-list> | Export-control restrictions |
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
| **FactSet Government Edge** | Structured, back-tested gov contract + lobbying + congressional trade data |

---

## Design principles summary

1. **Agent specialization over single-prompt mega-queries.** Each agent has a
   narrow job. A Decomposer just lists components. A Researcher just gathers
   data. A Scorer just applies rules. A Council just debates. Specialization
   produces better output than one big "please analyze AI infrastructure"
   prompt.

2. **Debate over single recommendations.** Nine investors with explicit
   bull and bear lenses. Unanimous BUY is genuine confidence; divided
   council is alpha-rich controversy.

3. **Cost is a first-class design constraint.** Two-tier triage / deep dive,
   multi-provider rotation, resumable pipeline, deterministic rubrics over
   LLM scoring. The whole point is that an end user can run this for free
   on Gemini + Groq, not burn $50 of Claude API per run.

4. **Explainable, auditable, reproducible.** Every council verdict shows
   which rubric rules fired. Every claim in the deep-dive output has a
   cited evidence row. The moat composite is decomposable into its six
   components. No mystery scores.

5. **User-in-the-loop.** The system doesn't decide what's worth investigating;
   the user does, via the deep-dive queue. Triage shows you what's there;
   you pick what to research deeper.

6. **Free + reproducible by default.** No paid APIs are required. Demo mode
   lets you evaluate the framework without any keys. Live mode uses free
   tiers from Google and Groq.

---

## Further reading

- [**docs/architecture.md**](docs/architecture.md) — deep dive into why the
  system is built the way it is. Walks through each of the 10 major
  design decisions with rationale. Read this if you want to explain the
  framework to a non-technical stakeholder.
- [**docs/cost-optimization.md**](docs/cost-optimization.md) — focused
  one-pager on the four cost optimizations: two-tier triage, multi-provider
  rotation, resumable pipeline, deterministic rubrics. Token math
  worked out. Read this if your question is "why does this run free?"

## Status & contributing

This is a personal-research-grade prototype. The framework is mature; the
LLM live-run path may need tuning depending on which providers and models
you use (Gemini, Groq, Claude, GPT-4o all have different JSON-output quirks).

15 tests cover the scoring rubric, storage layer, council logic, multi-provider
factory, and end-to-end mock pipeline. Run them with:

```bash
PYTHONPATH=src:. python -m pytest tests/ -q
```

**Not investment advice.** This produces research output to inform your own
due diligence.
