# Architecture & Design Decisions

This document explains **why** the system is built the way it is. The
[README](../README.md) explains **what** it does. Read this if you want to
understand the trade-offs and walk a non-technical stakeholder through the
choices.

## The original problem

Building an AI investment dashboard naively goes like this:

```python
# Naive approach
for company in all_ai_companies:
    response = llm.chat(f"Should I buy {company}? Give me everything.")
    show(response)
```

Three things go wrong:

1. **One AI gives one shallow opinion.** No bear case. No debate. You don't
   know if you're hearing genuine analysis or AI confirmation bias on whatever
   was hot in the training data.
2. **Cost explodes.** A serious "everything" prompt for 60 companies is
   ~500k tokens. That's 50%+ of a free Gemini daily quota or ~$5 of paid
   Claude API — every time you refresh.
3. **No structure.** "Should I buy ASML" is a question with many sub-questions
   (moat? valuation? balance sheet? risk? policy?) — the model conflates them.

The architecture below addresses all three.

---

## Decision 1 — Multi-agent, not single-prompt

Instead of one big prompt, the system has **eight cooperating agents** each
with a narrow job:

| Agent | Single responsibility |
|---|---|
| Decomposer | List the ~25 layers of the AI value chain |
| Triage Researcher | For one layer, list 3-5 incumbents with sparse data |
| Deep-Dive Researcher | For one company, do full ReAct research with web search |
| Concentration Analyzer | Score moat 0-100 across 6 dimensions (no LLM) |
| Intelligence Agent | Aggregate gov/political signals (no LLM in current impl) |
| Council Member × 9 | Each persona votes through their lens |
| Synthesizer | Rank everyone, write the final brief |

### Why this is better than one mega-prompt

1. **Each agent has a focused prompt.** Specialized prompts produce
   higher-quality structured output than generic "analyze X" prompts.
2. **Parallelism.** Researcher fan-out can run multiple components in
   parallel. A monolithic prompt can't.
3. **Failure isolation.** If the Triage Researcher 429-rate-limits on one
   component, the others continue. With one mega-prompt, one error fails
   the whole run.
4. **Mix LLM and pure code.** The Concentration Analyzer and Council
   rubrics are deterministic Python — no token cost. The LLM is reserved
   for the parts that genuinely need natural-language understanding.
5. **Testability.** Each agent has small inputs/outputs you can unit-test.
   A mega-prompt is impossible to test.

---

## Decision 2 — A council of nine investors, not one recommendation

The most important analytical decision. A single LLM produces one
recommendation per company. Useful, but limited:

- It might be hallucinating
- It can't articulate the bear case while also bullish
- It collapses different investor philosophies into one "balanced" view
- It hides confidence — is "BUY" a strong BUY or a weak BUY?

So we built a **council of nine distinct personas**, each with:
- A documented philosophy
- A favors / dislikes list
- **A pure-Python rubric** that maps the company's data → verdict + reasoning
- Iconic personality (Buffett's CUDA moat talk, Munger's cigar butt
  metaphor, Marks's second-level thinking)

### Bull voices (5)

- **Warren Buffett** — wonderful businesses at fair prices
- **Charlie Munger** — quality + mental models
- **Peter Lynch** — GARP / PEG
- **Stanley Druckenmiller** — macro + capacity + concentration
- **Cathie Wood** — disruptive innovation

### Bear voices (4) — deliberately added

The original council had 6 voices, mostly bull-leaning. For the AI supercycle,
that's dangerous — every name would be "BUY" because the AI narrative is
strong. We added three explicit bears:

- **Benjamin Graham** — deep value, margin of safety, hates anything > 25x P/E
- **Howard Marks** — cycle awareness, "this time it's different" is the most
  dangerous phrase, flags crowded longs
- **Michael Burry** — bubble caller, "this is 1999"
- **Ray Dalio** — macro / debt cycle / geopolitical chokepoints

### Consensus mechanic

Each company gets 9 verdicts. The system computes a **consensus label**:

```
UNANIMOUS_STRONG_BUY   ≥ 6 STRONG BUYs (highest confidence)
UNANIMOUS_BUY          ≥ 8/9 BUY-or-better
MAJORITY_BUY           ≥ 5/9 BUY
DIVIDED                bulls and bears squarely opposed
MAJORITY_AVOID         majority PASS/AVOID
```

### Why this matters

When the council is **unanimous**, you have unusually high confidence —
multiple lenses agree.

When the council is **DIVIDED**, you've found alpha-rich territory. Example
from the demo data:

- **MP Materials** (rare-earth mining)
  - Druckenmiller: **BUY** ("supply-constrained — the holy grail")
  - Cathie Wood: **BUY** ("exponential growth — 65% fwd")
  - Munger: **AVOID** ("moat composite 37/100 is mediocre")
  - Burry: **HOLD** ("insiders bought $18M — they see something")
  - Graham: **AVOID** ("trailing P/E negative — speculation")
  - Dalio: **PASS** ("parabolic growth no dividend cushion")

This is the most interesting kind of setup. If you can resolve the
disagreement — say, you believe the China-export-restriction tailwind is
real — that's edge. A single AI recommendation would have given you one
of those verdicts and hidden the others.

---

## Decision 3 — Two-tier analysis (Triage → Deep Dive)

A full ReAct-loop research pass on a company takes ~5 LLM calls. With ~60
companies, that's 300+ calls per run.

Most of those companies aren't worth the depth. The investor cares about
maybe 10. So we split:

### Tier 1 — Triage (cheap)

One LLM call per **component** (~25 calls total). Returns 3-5 incumbents
with just enough sparse data to populate the moat rubric and council:

- Name, ticker, public/private
- Market share bucket (one of `<10` / `10-25` / `25-50` / `50-75` / `>75` / `sole`)
- Single-source flag
- Structure (mono / duo / oligo / fragmented)
- Demand signal (1 sentence)
- Moat types (e.g., `["ip", "scale", "regulatory"]`)
- One-line thesis

No web search, no ReAct loop. Just structured market knowledge from the LLM.

### Tier 2 — Deep Dive (expensive, on-demand)

The full ReAct researcher with web_search + web_fetch tools. Pulls:

- Real-time stock price, P/E TTM + forward, EV/EBITDA, PEG
- ROIC, capex intensity, FCF after capex, R&D / sales
- Customer concentration (top 1 / top 3), China revenue %
- Hyperscaler capex beta
- Insider activity (Form 4), short interest, EPS revisions
- Bull/base/bear price targets + DCF assumptions
- Full multi-bullet thesis with time-horizon mapping

But **only runs on companies the user explicitly picks** via the deep-dive
queue (anywhere in the dashboard — Home top picks, Council BUY list,
Investment Thesis page, etc.).

### Token economics

| Phase | LLM calls | Tokens |
|---|---|---|
| Decomposer | 1 | ~3k |
| Triage × 25 components | 25 | ~75k |
| Council rubrics + Intel + Score | 0 | 0 (pure Python) |
| Synthesizer | 1 | ~5k |
| **Triage total** | **27** | **~80k** |
| Deep dive × 10 user-picked | 50 | ~200k |
| **Full triage + 10 deep dives** | **77** | **~280k** |

Compared to the old "deep on everyone" approach (~300 calls, ~500k tokens),
this is **~50% fewer tokens** while preserving 100% of the depth on the names
that matter.

### Why the user picks, not the system

It would be easy to auto-rank the triage results and deep-dive the top 10
automatically. We deliberately don't:

- The dashboard's job is to **surface** opportunities, not decide for you
- A user's existing portfolio matters: maybe you already own NVIDIA and
  want to dive on its supply-chain dependencies instead
- A user has time-horizon context the system doesn't (e.g., "I want
  short-term catalysts" vs "I want 5-year compounders")

So the queue is user-curated. Pick from Home / Council / Components, click
**Run dive**, walk away.

---

## Decision 4 — Multi-provider LLM rotation

Free LLM tiers have small daily caps:

- **Gemini 2.0 Flash**: ~1M tokens/day
- **Groq Llama 3.1 8B**: 500k tokens/day
- **Groq Llama 3.3 70B**: 100k tokens/day (got us in trouble)

A single full triage uses ~80k tokens — fine for any of these. But a
deep-dive session of 10 companies adds 200k. And if you want to re-run
through the day, you'll exhaust one provider quickly.

The `MultiProviderLLM` wrapper:

1. Tries Provider A (Gemini)
2. On 429 (rate limit), records cooldown time parsed from the API's
   "try again in Xs" hint
3. Rotates to Provider B (Groq)
4. If B also throttles, sleeps until the earliest cooldown expires
5. Daily-quota errors (TPD) get a 1-hour cooldown (since they won't recover
   until UTC midnight, but we re-check periodically)

Effective daily quota with Gemini + Groq combined: **~1.5M tokens** — enough
for a triage + multiple deep-dive sessions per day, all $0.

---

## Decision 5 — Resumable pipeline

A long deep-dive run can hit rate limits mid-stream. With a naive
implementation, that fails the entire run and you start over.

Instead, the pipeline persists each component's status to SQLite:

```
pending → researching → done       (happy path)
                     → error        (non-recoverable failure)
                     → rate_limited (will retry)
```

Three resume mechanics:

1. **`Pipeline.run(resume_run_id=...)`** — picks up an existing run, skips
   the decomposer (components already exist), only re-researches non-done
   components, never duplicates work
2. **`Pipeline.run_until_done(opts)`** — outer loop that keeps calling
   `run()` with resume, sleeps between passes, exits when every component
   is `done`
3. **`scripts/overnight_run.py`** — CLI wrapper for "hit run once and walk
   away overnight". Prints live progress to stdout. Survives Ctrl-C —
   the next invocation with `--resume <run_id>` continues exactly where
   it stopped

The Streamlit "Run until done" button in the UI does the same thing
in-browser (kicks off a background thread).

---

## Decision 6 — Deterministic rubrics for scoring (no LLM)

A lot of the system's "intelligence" doesn't actually need an LLM:

- "ROIC > 20% AND ROIC > WACC AND fwd P/E < 25" → Buffett STRONG BUY
- "ROIC < WACC" → Munger AVOID
- "PEG < 1.0" → Lynch STRONG BUY
- "P/E TTM > 40 AND insiders sold > $50M AND PEG > 2.5" → Burry AVOID HIGH

These are **rules**, not opinions. Each council member's rubric is a Python
function: takes the company's data dict, returns a verdict + reasoning
bullets that explicitly cite which rules fired.

Benefits:

1. **Zero token cost** for the ~30% of the pipeline that does scoring
2. **Reproducible** — same company data always produces the same verdicts
3. **Explainable** — every verdict says exactly which rule(s) drove it
4. **Auditable** — you can read `rubrics.py` and understand the entire
   council in 200 lines of Python

The Concentration Analyzer's moat composite (0-100) is also a pure-Python
function over six dimensions:

- Sole-source: 0 or 30 (requires ≥2 independent citations to credit)
- Market share bucket: 0-25 (based on bucket)
- IP / tech moat: 0 or 15
- Regulatory moat: 0 or 10
- Switching costs: 0-10 (parsed from free-text description)
- Demand signal: 0-10 (parsed from free-text description)

So the LLM's job is *gathering the data*. The *scoring* is rule-based.
This is the key trade-off: less nuance, but explainable + reproducible +
much cheaper.

---

## Decision 7 — Intelligence Agent for non-financial signals

Most of what investors care about isn't in Bloomberg:

- **CHIPS Act award** — Intel got $8.5B. Massive policy signal.
- **DoD price-floor contract** — MP Materials got a $400M NdPr offtake.
  De-risks the rare-earth thesis.
- **Pelosi NVDA call** — congressional STOCK Act disclosures move retail.
- **China Big Fund Phase III** — $47B going to SMIC, YMTC, AMEC, NAURA.
- **BIS Entity List addition** — kills a company's China revenue overnight.

The **Intelligence Agent** aggregates these into per-company signals:

```
IntelligenceSignal(
  category='us_gov_investment',
  headline='CHIPS Act direct funding — Arizona Fabs 1+2',
  counterparty='US Department of Commerce',
  amount_usd=6_600_000_000,
  direction='bullish',
  weight=5,
  source_name='DoC press release',
  source_url='https://commerce.gov/...',
)
```

And rolls them up into a composite **intelligence_score (−100 to +100)**.

In Demo mode the signals come from a hand-crafted patch dict for the top
~20 names. In live mode, the LLM provider populates them via web_search +
web_fetch on documented public sources (USAspending.gov, Senate EFD,
House Clerk disclosures, SEC EDGAR Form 4, DoC press releases).

This signal feeds the council:
- **Druckenmiller** rewards strong government investment as macro tailwind
- **Cathie Wood** treats it as industrial-policy validation
- **Howard Marks** flags politically-crowded names ("this trade is in the
  public consciousness")
- **Ray Dalio** uses China revenue % and customer concentration to score
  geopolitical chokepoint risk

---

## Decision 8 — Demo mode with hand-crafted data

The dashboard ships with a 62-company / 25-component hand-crafted dataset
(`src/investment_agent/llm/mock_data.py`). When Demo mode is on, the LLM
calls return data from this dict instead of hitting any API.

Why this exists:

1. **Evaluate the framework with no API keys** — anyone can clone, run, and
   see the dashboard work in 5 seconds
2. **Deterministic tests** — 15 unit + integration tests run against the
   mock provider and finish in 2 seconds
3. **UI development** — design changes are testable on real-looking data
   without burning tokens
4. **Demos & screenshots** — the data is curated to highlight the most
   interesting setups (sole-source ASML, divided MP Materials council, etc.)

The mock data has full earnings power + risk + scenario + intelligence
fields for the headline names (NVIDIA, ASML, TSMC, SK Hynix, MP Materials,
CoreWeave, Vertiv, Coherent, etc.) so all dashboard sections render with
meaningful content.

---

## Decision 9 — SQLite, one DB per run

Each pipeline run gets its own SQLite database at `data/runs/{run_id}.db`.

Why one DB per run:

1. **No migration headaches** — schema changes don't break old runs
2. **Easy parallelism** — multiple users can have independent runs without
   contention
3. **Trivial to back up / share** — `data/runs/<id>.db` is one self-contained file
4. **No infrastructure** — no Postgres / Mongo / cloud DB needed
5. **Resume is local** — `Pipeline.run(resume_run_id=<id>)` just opens
   the existing DB

Tables: `run`, `component`, `company`, `evidence`, `score`, `run_event`,
plus a `extras_json` BLOB on `company` that stores the rich
CompanyExtras (financials, risk, scenarios, intelligence, council verdicts).

The repository is read by the Streamlit pages via a single
`get_view(run_id) -> RunView` call that returns Pydantic objects.

---

## Decision 10 — Streamlit (not React / Next.js)

Streamlit was chosen for:

1. **Pure Python** — the same Python that runs the agents renders the UI
2. **Zero auth / hosting overhead** — Streamlit Cloud deploys from a
   GitHub push in seconds
3. **Built-in widgets** — sliders, multiselects, dataframes, plotly charts,
   no JavaScript needed
4. **Fast iteration** — change a Python file, save, refresh browser

Trade-offs accepted:
- Less granular UI control (vs custom React)
- Page reruns from top on every interaction (state lives in session_state)
- Background threads are session-scoped (which is why the overnight CLI
  exists for true multi-hour runs)

For a personal-research-grade prototype, the productivity wins crush the
limitations.

---

## What this is NOT

- **Not investment advice.** Research output to inform your own due diligence.
- **Not real-time.** Triage runs in seconds; deep dives in minutes; data is
  whatever the LLM provider's training data + web search knows at that
  moment.
- **Not a backtest engine.** It scores companies on current data; doesn't
  simulate historical performance.
- **Not a portfolio manager.** It surfaces opportunities; doesn't track
  positions or execute trades.
- **Not a Bloomberg replacement.** Bloomberg has decades of structured data
  and millisecond-fresh prices; this has free LLM-pulled snapshots.

What it IS: a thinking tool for a savvy investor who wants to do bottom-up
research on the AI infrastructure stack in a structured, debate-driven,
cost-controlled way.
