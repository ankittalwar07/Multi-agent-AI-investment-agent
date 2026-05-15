# Cost Optimization — Why this runs free

> _Last updated: May 2026 · five optimizations (Ollama local fallback added)_

Walks through the five design decisions that bring the cost of a full
analytical run from "blows past every free LLM quota" down to "fits
comfortably in two free cloud tiers combined PLUS an unlimited local
fallback." Written so you can explain it to a non-technical stakeholder
in 5 minutes.

---

## The basic problem

**LLMs charge by the token.** A "token" is roughly ¾ of an English word.
A long prompt + long answer = lots of tokens = expensive.

An AI dashboard that researches 60+ companies the naive way uses **500,000
tokens per run** — about $5 on Claude, or 50% of a free Gemini daily quota.
Refresh a few times and you're out of free tokens and into paid territory.

We want to do the same work in **< 300,000 tokens** and have it fit
**entirely inside free tiers**. Here's how.

---

## Quota cheat sheet (free tiers, May 2026)

| Provider | Model | Tokens / day | Cost | Location |
|---|---|---|---|---|
| Google Gemini | gemini-2.0-flash | ~1,000,000 | $0 | Cloud |
| Groq | llama-3.1-8b-instant | 500,000 | $0 | Cloud |
| Groq | llama-3.3-70b-versatile | 100,000 | $0 | Cloud |
| **Ollama (local)** | **qwen2.5:7b** | **UNLIMITED** | **$0** | **Your machine** |
| Anthropic Claude | (no free tier) | n/a | ~$3-15 per 1M tokens | Cloud |
| OpenAI GPT-4o | (no free tier) | n/a | ~$2.5-10 per 1M tokens | Cloud |

The dashboard's default setup uses **Gemini + Groq + Ollama in rotation**:
~1.5M cloud tokens/day at $0, **plus unlimited local inference** as the
fallback. The optimizations below ensure we use < 300k tokens for a full
run — leaving 5x headroom on the cloud budget, and if you ever blow
through it, the local model picks up seamlessly.

---

## Optimization 1 — Two-tier analysis

### The naive approach (rejected)

For every company in every layer of the AI stack:
- Do a multi-step ReAct loop with web searches
- Pull P/E, ROIC, capex, customer concentration, insider activity, etc.
- Write a full thesis

For ~60 companies × ~5 LLM calls each = **300 LLM calls, ~500k tokens**.

### The two-tier approach (chosen)

**Tier 1 — Triage** (cheap):
- One LLM call per **layer** (not per company)
- Ask: "Give me 3-5 incumbents with sparse data: name, ticker, share
  bucket, sole-source flag, one-line thesis"
- ~25 layers × 1 call = **25 LLM calls, ~75k tokens**

**Tier 2 — Deep Dive** (expensive, on user-pick):
- Full ReAct research with web search
- Only runs on companies the **user explicitly picks** from triage
- Typical: 5-10 companies, ~5 calls each = **50 LLM calls, ~200k tokens**

**Total: ~75 calls / ~275k tokens** instead of ~300 calls / ~500k tokens.

### Why this works

Most companies aren't worth deep analysis. You don't need a 12-page report
on a company you'd never buy. Triage tells you what's interesting; you
deep-dive only the names that look real.

### What you get on a Triage-only run

Already populated:
- ✅ Recommendation badges (STRONG BUY / BUY / HOLD)
- ✅ Council of 9 verdicts (rubrics work on sparse data)
- ✅ Moat scores (composite 0-100)
- ✅ Market structure (mono / duo / oligo / fragmented)
- ✅ Sole-source flags
- ✅ Top-picks card on the home page

Not yet (requires deep dive):
- ❌ Stock price, P/E, ROIC, capex intensity, etc.
- ❌ Bull/base/bear price targets + scenario sliders
- ❌ Cited evidence URLs from real research
- ❌ Full multi-bullet thesis with time-horizon mapping

---

## Optimization 2 — Multi-provider rotation

### The problem

Even with triage, a single Tier 1 + Tier 2 session uses ~275k tokens.
Groq 8B Instant has 500k/day. Two sessions in a day = quota gone.

### The solution

The `MultiProviderLLM` wrapper holds a list of providers (e.g., Gemini
first, then Groq) and rotates on rate-limit errors.

```
LLM call →
   ├─ try Gemini
   │    └─ HTTP 429 "try again in 60s" → record cooldown
   ├─ rotate to Groq
   │    └─ success → return result
   └─ both throttled → sleep until earliest cooldown expires
```

It even parses the API's "try again in Xs" hint to know exactly how long
to wait.

### Effect

- Gemini daily: ~1M tokens
- Groq 8B daily: ~500k tokens
- **Combined: ~1.5M tokens/day** at $0

That's **5+ full triage + deep-dive sessions per day** before any throttling.

---

## Optimization 3 — Resumable pipeline

### The problem

A long deep-dive on 10 companies can take 5+ minutes. If something fails
halfway (rate limit, network hiccup, browser tab closed), you don't want
to redo the work.

### The solution

Every component's status is persisted to SQLite as soon as the researcher
finishes it:

```
component status: pending → researching → done
                                       ↓
                                       error / rate_limited
```

When you re-run with `--resume <run_id>`, the pipeline:
1. Skips the Decomposer (components already exist)
2. Filters to only `pending` / `error` / `rate_limited` components
3. Re-researches only those — never duplicates work
4. Re-runs scoring + council + synthesis on the full (old + new) set

### Effect

- **Network failure mid-run?** Re-run with `--resume`, picks up where it
  stopped, no tokens wasted
- **Hit rate limit on component 12 of 25?** Components 1-11 are already
  saved. Resume picks up at component 12
- **Overnight run interrupted?** Same — resume in the morning, lose nothing

This means you can run the CLI script overnight and not worry about
interruptions:

```bash
PYTHONPATH=src python scripts/overnight_run.py
# Ctrl-C anytime; resume with:
PYTHONPATH=src python scripts/overnight_run.py --resume <run_id>
```

---

## Optimization 4 — Deterministic rubrics for scoring

### The problem

A naive system would ask the LLM for every scoring decision:

```
"On a scale of 1-10, how strong is NVIDIA's moat?"
"Should Warren Buffett buy NVIDIA?"
"What's the bull case probability?"
```

Each of these is a separate LLM call. Expensive, slow, inconsistent
(the LLM might say "8/10" today and "7/10" tomorrow), and non-explainable.

### The solution

Move all the **scoring logic** into pure Python rules. The LLM only
*gathers the data*; the *scoring* is deterministic.

Examples:

**Moat composite** (0-100):
```python
score = (
    30 if (single_source and ≥2 citations) else 0
  + 25 if share == ">75%" else 20 if "50-75%" else ...
  + 15 if "ip" or "tech" or "scale" in moat_types else 0
  + 10 if "regulatory" in moat_types else 0
  + (10 if "very high lock-in" in switching else 7 if "high" else ...)
  + (10 if "accelerating" in demand else 7 if "growing" else ...)
)
```

**Warren Buffett's verdict**:
```python
if private and no ticker: return PASS  # outside circle of competence
if pe_fwd > 0:
    score = points_for_moat + points_for_op_margin + points_for_pe
    if balance sheet is fortress (net cash > $5B): score += 1
    if leverage too high (debt/EBITDA > 3.5): score -= 1
    if score ≥ 5: return STRONG_BUY HIGH
    elif score ≥ 3: return BUY HIGH
    ...
```

### Effect on cost

The Concentration Analyzer + nine Council members + Intelligence Agent
= **0 LLM tokens**. All Python.

This is roughly 30% of the system's "intelligence" — moved out of
the LLM into deterministic code. That's a third of the token cost
eliminated entirely while gaining:
- **Explainability** — every verdict cites which rules fired
- **Reproducibility** — same data → same verdict
- **Speed** — these run in milliseconds, not seconds

---

## Optimization 5 — Local fallback via Ollama (the safety net)

### The problem

Even with the four optimizations above, you can imagine days where:

- You run triage several times to refresh data
- Then deep-dive 15+ companies for a portfolio review
- Total: 600k+ tokens in one day

Cloud free quotas (1M Gemini + 500k Groq = 1.5M combined) still cover
this — but barely. And if you're doing overnight analyses, you don't
want to wake up to a half-finished run because both clouds throttled
at 2am.

### The solution — Ollama as the third fallback

[Ollama](https://ollama.com) runs open-source LLMs (Qwen 2.5, Llama 3.1/3.3,
Mistral Nemo) **on your local machine**. One-click install, OpenAI-compatible
API at `http://localhost:11434/v1`. Default model `qwen2.5:7b` is ~4 GB.

The `MultiProviderLLM` rotation chain now has three rungs:

```
Try Gemini   → 429 → Try Groq → 429 → Try Ollama (local, never 429s)
```

When both cloud providers exhaust their daily quotas, the system silently
falls back to local inference. No interruption, no wake-up-at-2am alarm.

### Trade-off — speed

Local inference is **20-100x slower** than cloud:

| Hardware (running qwen2.5:7b) | Throughput |
|---|---|
| Apple M3 Max | ~80-150 tok/sec |
| Apple M2 Pro | ~50-100 tok/sec |
| RTX 4090 | ~200+ tok/sec |
| RTX 4060 | ~80-120 tok/sec |
| CPU only (modern Intel/AMD) | ~10-25 tok/sec |
| **Cloud Gemini (for reference)** | **~200 tok/sec + ~0ms network** |

A full pipeline that takes 2-3 min on Gemini might take 15-30 min on
Ollama. But it **never throttles** — exactly what you want for
overnight runs.

### Why this matters for the cost story

Before Ollama: "We've cut tokens by 50% so it fits in free cloud quotas."

After Ollama: **"There is no hard upper limit on daily work."** You can
explore the universe of AI infrastructure companies as much as you want,
forever, at $0. The cloud quotas are just there to speed things up when
you're in interactive mode.

### Privacy bonus

Local inference means **no data leaves your machine**. For analyses
where you don't want OpenAI/Google/Anthropic seeing your investment
research workflow, run `--providers ollama` and the cloud providers
never see a single token.

---

## Putting it all together

| Run scenario | LLM calls | Tokens | Fits in free Gemini? | Fits in free Groq 8B? | Fits in local Ollama? |
|---|---|---|---|---|---|
| Naive: deep on all 60 companies | ~300 | ~500k | No | No (5x over) | **Yes** (unlimited) |
| Triage only | ~27 | ~80k | Yes (8% of daily) | Yes (16%) | **Yes** |
| Triage + deep on 10 picks | ~77 | ~275k | Yes (28%) | Yes (55%) | **Yes** |
| Triage + deep + multi-provider rotation + local fallback | same | distributed | **Yes** | **Yes** | **Yes (infinite)** |

### Real-world workflow (interactive — daytime use)

1. **Morning**: Run **Quick triage** in the dashboard (~80k tokens, 30
   seconds on Gemini) → fills the dashboard with sparse data on all ~60
   companies
2. **Browse**: Open the Investor Council page, see what's interesting
3. **Mark**: Click `+ Deep dive` on 8-10 companies anywhere in the dashboard
4. **Run dive**: Sidebar button → background thread does the full
   research (~200k tokens, 2 minutes)
5. **Read**: Each deepened company has a full Investment Thesis page with
   ROIC, P/E, customer concentration, council verdicts, scenario sliders,
   intelligence signals, cited evidence

Total daily cloud cost: **$0**. Total daily LLM tokens: **~280k of available
~1.5M** — plenty of headroom for re-runs and exploration.

### Overnight workflow (unlimited — leave running)

1. **Before bed**: Open terminal, run:
   ```bash
   PYTHONPATH=src python scripts/overnight_run.py \
       --providers gemini,groq,ollama
   ```
2. Pipeline tries Gemini first. When daily quota exhausts (~8pm), rotates
   to Groq. When that exhausts, falls back to **local Ollama**.
3. Local Ollama keeps researching every component all night, slowly but
   steadily. No throttling, no 2am wake-up.
4. **Morning**: Full deep-dive report waiting in `data/runs/<id>.json`
   and the Streamlit dashboard.

Total cost: **$0**. Hard upper limit on work: **none**.

---

## What you'd pay for this on Claude API

Just for reference — to underscore the cost savings:

| Provider | 1M tokens (input/output blended) |
|---|---|
| Claude Sonnet 4.6 | ~$9 |
| GPT-4o | ~$7 |
| Gemini 2.0 Flash (paid) | ~$0.25 |
| Groq Llama 3.1 8B (paid) | ~$0.06 |
| **Ollama qwen2.5:7b (local)** | **$0 (your electricity)** |

A single full run (~275k tokens) costs:

| Provider | Cost |
|---|---|
| Claude Sonnet 4.6 API | **~$2.50** |
| GPT-4o API | **~$1.90** |
| Gemini paid | **~$0.07** |
| Groq paid | **~$0.02** |
| **Free Gemini / Groq / Ollama** | **$0.00** |

The optimizations don't just save money — they make this dashboard
**runnable by anyone with a free Google account or a laptop**.

A user with **no internet** and **no cloud accounts** can still run
the entire framework with `--providers ollama` after a 5-minute local
install. The whole pipeline, the 9-investor council, the intelligence
signal aggregation, the scenario math — all of it works offline.
