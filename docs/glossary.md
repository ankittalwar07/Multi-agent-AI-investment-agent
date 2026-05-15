# Glossary — terms used in this dashboard

> _A non-technical reference for the jargon in the README and architecture
> docs. Read this if a term in the dashboard or code isn't familiar._

## A

**AI accelerator** — A specialized chip optimized for AI workloads. NVIDIA's
GPUs are the dominant example; AMD's MI series, Google's TPUs, and
Microsoft's Maia are alternatives. Different from "CPU" because they have
thousands of cores designed for parallel matrix math.

**Agent** — In this dashboard, a software component with one specific job
(e.g., the Decomposer agent lists the layers of the AI stack; the
Triage Researcher agent does a quick scan of incumbents per layer).
Each agent has its own prompt and either calls an LLM or applies a
deterministic rule.

**Analyst consensus** — The aggregated buy / hold / sell recommendations of
Wall Street analysts covering a stock. We surface counts (e.g., "32 BUY,
4 HOLD, 1 SELL") and a price-target range.

## B

**Backlog** — Orders the company has received but not yet shipped/billed.
A growing backlog means future revenue is locked in.

**Beta** — A stock's volatility relative to the market. Beta = 1.0 means
moves with the market; > 1.0 means amplified; < 1.0 means dampened.

**Bull/Base/Bear case** — Three scenarios for a stock's future price:
optimistic, central, pessimistic. We assign a probability to each and
compute a probability-weighted expected return.

## C

**Capex** — Capital expenditure. Money spent on long-lived assets (buildings,
machinery, chip fabs). High capex = lots of cash going into the business
each year before any returns; matters for AI infra because hyperscaler
capex ($100B+/year combined) is what drives demand for chips.

**Capex / Sales ratio** — Capex as a % of revenue. NVIDIA is ~3%
(capital-light). TSMC is ~41% (capital-heavy). Tells you how much of
each dollar of revenue gets reinvested before any profit shows up.

**CHIPS Act** — The 2022 US law that allocates $52B in subsidies to
semiconductor manufacturers building fabs in the US. Major recipients:
Intel ($8.5B), TSMC ($6.6B), Samsung ($4.7B), Micron ($6.1B). Tracked
by our Intelligence Agent as a `us_gov_investment` signal.

**Composite moat score** — A 0-100 score we compute for each company by
adding points across six dimensions: sole-source, market share, IP/tech
moat, regulatory moat, switching costs, demand signal. Pure Python rule,
no LLM tokens.

**Conviction** (HIGH / MEDIUM / LOW) — How confident the recommendation
is. Drives position sizing in the portfolio view.

**Consensus label** — How unified the 9-investor council is on a name:
`UNANIMOUS_STRONG_BUY` / `UNANIMOUS_BUY` / `MAJORITY_BUY` / `DIVIDED` /
`MAJORITY_AVOID`. Divided is often the most alpha-rich.

**CoWoS** — Chip-on-Wafer-on-Substrate. TSMC's advanced packaging
technology that bonds AI accelerators (NVIDIA GPUs) to HBM memory stacks.
The single biggest physical bottleneck on AI shipments — capacity
expansion takes years.

**Customer concentration** — % of revenue coming from the top customer(s).
A company where one customer = 60% of revenue (CoreWeave / Microsoft) has
huge concentration risk. We track top-1, top-3, top-10 percentages.

## D

**DCF** — Discounted Cash Flow. A valuation method that projects future
cash flows and discounts them back to today's value. Our dashboard has a
simplified 5-year EPS-based DCF with sliders for growth, terminal P/E,
margin uplift, and WACC.

**Deep dive** (in this dashboard) — Full multi-step research on a single
company using the ReAct loop with web search. Expensive in LLM tokens.
Only runs on companies the user explicitly picks.

**Demo mode** — Toggle in the sidebar that makes the LLM return
hand-crafted illustrative data instead of hitting any API. Lets you
explore the framework without any API keys or token costs.

## E

**Earnings power** — How much profit the business can generate. We track
ROIC, op margin, FCF after capex, R&D intensity, balance sheet strength.
Section title on the Investment Thesis page.

**Entity List** — A US Commerce Department list of foreign companies
restricted from buying US technology without a license. Adding a company
to it can crush their revenue overnight (e.g., Huawei, SMIC).

**EUV** — Extreme Ultraviolet lithography. The technology used to make
the smallest chip features (5nm, 3nm, 2nm). ASML is the sole supplier
of EUV scanners worldwide — the cleanest monopoly in tech.

**EV / EBITDA** — Enterprise Value / Earnings Before Interest, Taxes,
Depreciation, Amortization. A valuation ratio that accounts for debt
(unlike P/E). Lower = cheaper.

## F

**FCF** — Free Cash Flow. Cash the business generates after paying for
capex. "FCF after capex" is what's actually left for shareholders.
Negative FCF means the business is funded by debt or equity issuance,
not internal cash.

**FCF yield** — FCF / market cap. How much free cash you get for each
dollar of stock. High FCF yield = cheap stock with real cash returns.

**Form 4** — SEC filing required when corporate insiders (officers,
directors) buy or sell their company's stock. We aggregate these into
the `form4_insider` signal category. A "cluster buy" (multiple insiders
buying in the same week) is historically predictive.

## G

**GARP** — Growth at a Reasonable Price. Peter Lynch's investment style —
buy growing companies before the PEG ratio gets crowded.

**Gemini** — Google's family of LLM models. We use Gemini 2.0 Flash on
the free tier (~1M tokens/day, no credit card).

**Groq** — A company that runs open-source models (Llama, Mistral, Gemma)
on custom hardware called LPUs. Very fast inference. Has a free tier
with ~500k tokens/day on Llama 3.1 8B Instant.

## H

**HBM** — High-Bandwidth Memory. Stacked DRAM chips bonded to AI
accelerators. Three suppliers: SK Hynix (leader), Samsung, Micron.
Three-supplier oligopoly with sustained pricing power.

**Hyperscaler** — Massive cloud providers running tens of millions of
servers. The "big 4": Microsoft (Azure), Google (GCP), Amazon (AWS),
Meta. Their combined capex (~$200B/year) is the single biggest driver
of demand for AI infrastructure.

**Hyperscaler capex beta** — How much a company's revenue changes when
hyperscaler capex changes. NVIDIA ≈ 2.0x (huge leverage). Apple ≈ −0.1x
(slightly negative, consumer-driven). Vertiv ≈ 1.5x (pure datacenter
power play).

## I

**Intelligence signal** — A non-financial data point that may move a stock:
CHIPS Act award, federal contract, congressional STOCK Act trade,
foreign government investment, BIS Entity List addition, etc. Aggregated
by our Intelligence Agent into a composite score (-100 to +100).

## L

**LLM** — Large Language Model. The AI models that power the research
agents (Gemini, Claude, GPT-4, Llama, Qwen). We rotate between multiple
providers to manage rate limits.

## M

**Market share bucket** — Where a company sits in its market:
`<10%` / `10-25%` / `25-50%` / `50-75%` / `>75%` / `sole`. Sole-source
is the most defensible position; we require ≥2 independent citations
to credit it.

**Mock provider** — A deterministic stand-in for an LLM. Returns the
same hand-crafted JSON every time, used in Demo mode and unit tests.

**Moat** — Warren Buffett's term for a sustainable competitive advantage
that protects a business from competition. Types we track: IP / tech,
scale, regulatory, switching costs, process, brand, network effects.

## O

**Ollama** — Open-source software for running LLMs locally on your own
machine. Free, no rate limits, full privacy. Default model: Qwen 2.5 7B.
The dashboard auto-detects Ollama running at localhost:11434 and adds
it to the rotation chain.

**Oligopoly** — A market dominated by a small number of suppliers (3-5).
HBM is an oligopoly: SK Hynix, Samsung, Micron. Stable pricing because
no one wants a price war.

## P

**P/E ratio** (TTM / forward) — Price-to-Earnings. Stock price divided
by earnings per share. TTM = trailing twelve months (already happened).
Forward = next twelve months (estimate). Lower = cheaper relative to
earnings. NVIDIA at 50x TTM is expensive; HBM names at 10x are cheap.

**PEG ratio** — P/E divided by earnings growth rate. PEG < 1.0 means
"growth is essentially free" (Lynch's golden zone). PEG > 2.5 means
growth is already priced in (Burry's bubble signal).

**Probability-weighted return** — Expected return weighted by scenario
probabilities. If bull = +50% at 30% prob, base = +20% at 50% prob,
bear = −20% at 20% prob, the probability-weighted return is
0.3 × 50 + 0.5 × 20 + 0.2 × (−20) = 21%.

## R

**ReAct loop** — A pattern where the LLM alternates between "reasoning"
(thinking about what to do) and "acting" (calling a tool like web_search
or web_fetch). Used in our Deep-Dive Researcher. Multiple rounds per
company, which is why it's expensive.

**Recommendation badges** — `STRONG_BUY` / `BUY` / `HOLD` / `SELL` /
`STRONG_SELL` / `PASS` / `AVOID`. Color-coded throughout the dashboard.
Pass and Avoid are different: Pass = "not for me," Avoid = "actively
short-able / dangerous."

**ROIC** — Return on Invested Capital. After-tax operating profit divided
by capital deployed. The most important Buffett/Munger metric — measures
how good the business is at generating returns on each dollar of capital.
NVIDIA ≈ 82% (exceptional). Most industrials ≈ 10-15%.

**Run** (in this dashboard) — One execution of the pipeline. Each run gets
a unique ID (e.g., `20260515T034512Z-abc123`) and its own SQLite database
at `data/runs/<run_id>.db`.

## S

**Scoring rubric** — A Python function that maps a company's data to a
verdict. Each of the 9 council members has their own rubric (Buffett's
rewards ROIC > 20%; Burry's rewards distressed multiples). Deterministic
and explainable — every verdict cites which rule fired.

**Short interest** — % of a stock's tradeable shares that have been sold
short (bet against). > 10% = controversy. < 1% = no skeptics left.
Both extremes are signals.

**Sole-source** — A single supplier with no commercial alternative.
ASML in EUV lithography is the cleanest example. Sole-source positions
have extraordinary pricing power.

**SQLite** — A simple file-based database. We use one DB per run, stored
at `data/runs/<run_id>.db`. No server needed — just a file you can
back up, ship, or inspect with any SQLite tool.

**STOCK Act** — The 2012 US law requiring members of Congress to
disclose stock trades within 45 days. We surface aggregated congressional
trading activity per company (e.g., "Nancy Pelosi disclosed NVDA call
options purchase") as an Intelligence signal.

**Streamlit** — The Python framework we use for the dashboard UI. Lets
us build pages with plain Python — no JavaScript needed.

**Switching costs** — How hard / expensive it is for a customer to switch
to a competitor's product. NVIDIA's CUDA software ecosystem is the
canonical example — software written for CUDA doesn't trivially run on
AMD or Intel chips, so customers are locked in.

## T

**Tier 1 / Tier 2 (in this dashboard)** — Our two-tier analysis pattern.
Tier 1 (Triage) is one cheap LLM call per market layer. Tier 2 (Deep
Dive) is the expensive full-research pass, run only on user-picked
companies.

**TPD / TPM** — Tokens Per Day / Tokens Per Minute. LLM provider quota
units. Groq's free Llama 3.3 70B has 12,000 TPM and 100,000 TPD — we
hit both limits in early testing.

**Triage** (in this dashboard) — The Tier 1 quick scan. One LLM call per
market layer returns 3-5 incumbents with sparse data (name, ticker,
share bucket, sole-source flag, one-line thesis). ~75k tokens total.

## V

**Value chain** — The sequence of companies that contribute to a final
product. The AI value chain runs from copper mines and rare-earth
processing → photoresist + photolithography → wafer fabrication →
chip packaging → memory + accelerators → servers → datacenters →
cloud platforms → foundation models → applications.

## W

**WACC** — Weighted Average Cost of Capital. The rate a company has to
beat to create value. ROIC > WACC = creating value. ROIC < WACC =
destroying value (Munger's hard-pass criterion).

## Y

**YoY** — Year-over-Year. Comparing this quarter / year to the same
period one year ago. "Revenue +50% YoY" means revenue is 50% higher
than the same quarter last year.

---

If a term is missing from this glossary, open an issue and I'll add it.
