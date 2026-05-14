"""Hand-crafted realistic-ish mock findings per component.

Used by the MockProvider so the dashboard is meaningful out-of-the-box without
burning API credits. Numbers are PLAUSIBLE but illustrative — not investment
advice. The visual prototype's job is to demonstrate the system; live runs
against Claude/Gemini/OpenAI will produce real, cited findings.
"""
from __future__ import annotations

MOCK_FINDINGS: dict[str, list[dict]] = {
    "EUV Lithography": [
        {
            "name": "ASML Holding", "is_public": True, "ticker": "ASML",
            "hq_country": "Netherlands",
            "market_share_pct": 100.0, "market_share_bucket": "sole", "single_source": True,
            "moat_types": ["ip", "regulatory", "scale", "process"],
            "switching_costs": "very high lock-in (decade-long install + training)",
            "customer_concentration": "TSMC, Samsung, Intel = >85% of revenue",
            "demand_signal": "exponential growth, multi-year backlog into 2028+",
            "valuation_usd": 320_000_000_000,
            "notes": "Sole producer of EUV scanners. High-NA EUV monopoly extends to 2030+.",
        },
        {
            "name": "Carl Zeiss SMT", "is_public": False,
            "hq_country": "Germany",
            "market_share_pct": 100.0, "market_share_bucket": "sole", "single_source": True,
            "moat_types": ["ip", "process", "scale"],
            "switching_costs": "lock-in", "demand_signal": "tied to ASML capacity expansion",
            "valuation_usd": None, "notes": "Sole supplier of EUV optics to ASML; private subsidiary.",
        },
    ],
    "Leading-edge Foundry": [
        {
            "name": "TSMC", "is_public": True, "ticker": "TSM",
            "hq_country": "Taiwan",
            "market_share_pct": 92.0, "market_share_bucket": ">75", "single_source": False,
            "moat_types": ["scale", "process", "ip"],
            "switching_costs": "high - process libraries are not portable",
            "customer_concentration": "Apple ~25%, NVIDIA ~10%, AMD ~7%",
            "demand_signal": "shortage of CoWoS capacity; pricing power",
            "valuation_usd": 850_000_000_000,
            "notes": ">90% share at <=3nm logic. Geopolitical concentration risk.",
        },
        {
            "name": "Samsung Foundry", "is_public": True, "ticker": "005930.KS",
            "hq_country": "South Korea",
            "market_share_pct": 7.0, "market_share_bucket": "<10",
            "single_source": False, "moat_types": ["scale"],
            "switching_costs": "medium",
            "demand_signal": "stable but losing share at leading edge",
            "valuation_usd": None, "notes": "Distant #2; yield issues at 3nm.",
        },
    ],
    "AI Accelerator Silicon": [
        {
            "name": "NVIDIA", "is_public": True, "ticker": "NVDA",
            "hq_country": "United States",
            "market_share_pct": 86.0, "market_share_bucket": ">75",
            "single_source": False, "moat_types": ["ip", "scale", "tech"],
            "switching_costs": "very high - CUDA ecosystem lock-in",
            "customer_concentration": "hyperscalers + neoclouds dominate orders",
            "demand_signal": "accelerating, backlog into 2026",
            "valuation_usd": 3_200_000_000_000,
            "notes": "Dominant in training; CUDA moat is the real differentiator.",
        },
        {
            "name": "AMD", "is_public": True, "ticker": "AMD",
            "hq_country": "United States",
            "market_share_pct": 9.0, "market_share_bucket": "<10",
            "single_source": False, "moat_types": ["tech"],
            "switching_costs": "medium - ROCm narrowing the gap",
            "demand_signal": "growing customer pipeline (Meta, MS)",
            "valuation_usd": 220_000_000_000,
        },
        {
            "name": "Google TPU", "is_public": True, "ticker": "GOOGL",
            "hq_country": "United States",
            "market_share_pct": 4.0, "market_share_bucket": "<10",
            "single_source": False, "moat_types": ["ip", "tech"],
            "switching_costs": "captive (internal use + GCP customers)",
            "demand_signal": "strong internal demand", "valuation_usd": None,
        },
    ],
    "High-Bandwidth Memory (HBM)": [
        {
            "name": "SK Hynix", "is_public": True, "ticker": "000660.KS",
            "hq_country": "South Korea",
            "market_share_pct": 53.0, "market_share_bucket": "50-75",
            "single_source": False, "moat_types": ["process", "scale", "ip"],
            "switching_costs": "high - qualified by NVIDIA on HBM3E",
            "customer_concentration": "NVIDIA is >40% of HBM bookings",
            "demand_signal": "shortage through 2026, all capacity sold out",
            "valuation_usd": 115_000_000_000,
            "notes": "HBM3E leader; first-to-market premium.",
        },
        {
            "name": "Samsung Memory", "is_public": True, "ticker": "005930.KS",
            "hq_country": "South Korea",
            "market_share_pct": 38.0, "market_share_bucket": "25-50",
            "single_source": False, "moat_types": ["scale", "process"],
            "switching_costs": "high", "demand_signal": "strong; behind on HBM3E qual",
            "valuation_usd": None,
        },
        {
            "name": "Micron", "is_public": True, "ticker": "MU",
            "hq_country": "United States",
            "market_share_pct": 9.0, "market_share_bucket": "<10",
            "single_source": False, "moat_types": ["process"],
            "switching_costs": "medium", "demand_signal": "ramping; 2026 capacity full",
            "valuation_usd": 145_000_000_000,
        },
    ],
    "Advanced Packaging (CoWoS / SoIC)": [
        {
            "name": "TSMC (CoWoS)", "is_public": True, "ticker": "TSM",
            "hq_country": "Taiwan",
            "market_share_pct": 88.0, "market_share_bucket": ">75",
            "single_source": False, "moat_types": ["process", "scale", "ip"],
            "switching_costs": "very high - the binding constraint on AI buildout",
            "customer_concentration": "NVIDIA absorbs majority of capacity",
            "demand_signal": "shortage; capacity 2x'ing but still oversold",
            "valuation_usd": None,
            "notes": "Capacity-constrained — TSMC is doubling CoWoS but still oversold.",
        },
        {
            "name": "Amkor Technology", "is_public": True, "ticker": "AMKR",
            "hq_country": "United States",
            "market_share_pct": 6.0, "market_share_bucket": "<10",
            "single_source": False, "moat_types": ["scale"],
            "switching_costs": "medium", "demand_signal": "growing as 2nd source",
            "valuation_usd": 7_500_000_000,
        },
    ],
    "Datacenter Networking Silicon": [
        {
            "name": "Broadcom", "is_public": True, "ticker": "AVGO",
            "hq_country": "United States",
            "market_share_pct": 62.0, "market_share_bucket": "50-75",
            "single_source": False, "moat_types": ["ip", "scale", "tech"],
            "switching_costs": "high - custom ASIC partnerships with hyperscalers",
            "customer_concentration": "Google, Meta, Apple AI silicon partners",
            "demand_signal": "+50% YoY AI networking revenue",
            "valuation_usd": 850_000_000_000,
        },
        {
            "name": "NVIDIA Networking (Mellanox)", "is_public": True, "ticker": "NVDA",
            "hq_country": "United States",
            "market_share_pct": 22.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["ip", "tech"],
            "switching_costs": "very high (NVLink lock-in within NVIDIA stacks)",
            "demand_signal": "strong, tied to GPU shipments",
            "valuation_usd": None,
        },
        {
            "name": "Marvell", "is_public": True, "ticker": "MRVL",
            "hq_country": "United States",
            "market_share_pct": 9.0, "market_share_bucket": "<10",
            "single_source": False, "moat_types": ["tech"],
            "demand_signal": "Amazon custom silicon partnership ramping",
            "valuation_usd": 65_000_000_000,
        },
    ],
    "Optical Interconnect / Transceivers": [
        {
            "name": "Coherent", "is_public": True, "ticker": "COHR",
            "hq_country": "United States",
            "market_share_pct": 28.0, "market_share_bucket": "25-50",
            "single_source": False, "moat_types": ["ip", "scale"],
            "switching_costs": "medium", "demand_signal": "800G ramp accelerating",
            "valuation_usd": 14_000_000_000,
        },
        {
            "name": "Lumentum", "is_public": True, "ticker": "LITE",
            "hq_country": "United States",
            "market_share_pct": 18.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["tech"],
            "demand_signal": "growing", "valuation_usd": 4_500_000_000,
        },
        {
            "name": "Innolight", "is_public": False,
            "hq_country": "China",
            "market_share_pct": 28.0, "market_share_bucket": "25-50",
            "single_source": False, "moat_types": ["scale"],
            "demand_signal": "fast growth in China hyperscalers",
            "valuation_usd": None,
        },
    ],
    "Datacenter Power & Cooling": [
        {
            "name": "Vertiv Holdings", "is_public": True, "ticker": "VRT",
            "hq_country": "United States",
            "market_share_pct": 24.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["scale", "tech"],
            "switching_costs": "high - integrated into rack/PUE design",
            "demand_signal": "accelerating - liquid cooling backlog",
            "valuation_usd": 45_000_000_000,
        },
        {
            "name": "Schneider Electric", "is_public": True, "ticker": "SU.PA",
            "hq_country": "France",
            "market_share_pct": 19.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["scale"],
            "demand_signal": "strong - power infrastructure shortage",
            "valuation_usd": 145_000_000_000,
        },
        {
            "name": "Eaton", "is_public": True, "ticker": "ETN",
            "hq_country": "Ireland",
            "market_share_pct": 14.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["scale"],
            "demand_signal": "strong + UPS shortage", "valuation_usd": 130_000_000_000,
        },
    ],
    "Hyperscale Cloud": [
        {
            "name": "AWS", "is_public": True, "ticker": "AMZN",
            "hq_country": "United States",
            "market_share_pct": 32.0, "market_share_bucket": "25-50",
            "single_source": False, "moat_types": ["scale", "tech"],
            "switching_costs": "very high", "demand_signal": "strong, AI workloads growing",
            "valuation_usd": None,
        },
        {
            "name": "Microsoft Azure", "is_public": True, "ticker": "MSFT",
            "hq_country": "United States",
            "market_share_pct": 25.0, "market_share_bucket": "25-50",
            "single_source": False, "moat_types": ["scale", "tech"],
            "switching_costs": "very high",
            "demand_signal": "accelerating - OpenAI partnership",
            "valuation_usd": None,
        },
        {
            "name": "Google Cloud", "is_public": True, "ticker": "GOOGL",
            "hq_country": "United States",
            "market_share_pct": 11.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["tech"],
            "demand_signal": "growing - Gemini + TPU pull",
            "valuation_usd": None,
        },
    ],
    "GPU Neoclouds": [
        {
            "name": "CoreWeave", "is_public": True, "ticker": "CRWV",
            "hq_country": "United States",
            "market_share_pct": 40.0, "market_share_bucket": "25-50",
            "single_source": False, "moat_types": ["scale"],
            "customer_concentration": "Microsoft is >60% of revenue",
            "demand_signal": "+200% YoY contracted backlog",
            "valuation_usd": 35_000_000_000,
            "notes": "NVIDIA-preferred. Customer concentration is the key risk.",
        },
        {
            "name": "Lambda", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 15.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["tech"],
            "demand_signal": "growing - researcher + startup demand",
            "valuation_usd": 5_000_000_000,
        },
        {
            "name": "Crusoe", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 10.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["scale"],
            "demand_signal": "strong - stranded power moat",
            "valuation_usd": 2_800_000_000,
        },
    ],
    "Foundation Model Labs": [
        {
            "name": "OpenAI", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 55.0, "market_share_bucket": "50-75",
            "single_source": False, "moat_types": ["ip", "scale", "tech"],
            "switching_costs": "medium - API portable but apps lock in",
            "demand_signal": "exponential, $10B+ run-rate",
            "valuation_usd": 300_000_000_000,
        },
        {
            "name": "Anthropic", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 22.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["ip", "tech"],
            "switching_costs": "medium",
            "demand_signal": "+300% YoY API revenue",
            "valuation_usd": 60_000_000_000,
        },
        {
            "name": "Google DeepMind", "is_public": True, "ticker": "GOOGL",
            "hq_country": "United Kingdom",
            "market_share_pct": 14.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["ip", "tech"],
            "demand_signal": "Gemini gaining share", "valuation_usd": None,
        },
        {
            "name": "xAI", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 5.0, "market_share_bucket": "<10",
            "single_source": False, "moat_types": ["scale"],
            "demand_signal": "rapid customer ramp", "valuation_usd": 50_000_000_000,
        },
    ],
    "Inference Hardware Startups": [
        {
            "name": "Groq", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 4.0, "market_share_bucket": "<10",
            "single_source": False, "moat_types": ["ip", "tech"],
            "switching_costs": "medium", "demand_signal": "growing inference customers",
            "valuation_usd": 2_800_000_000,
        },
        {
            "name": "Cerebras", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 3.0, "market_share_bucket": "<10",
            "single_source": False, "moat_types": ["ip", "tech"],
            "demand_signal": "wafer-scale niche workloads",
            "valuation_usd": 4_300_000_000,
        },
        {
            "name": "SambaNova", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 2.0, "market_share_bucket": "<10",
            "single_source": False, "moat_types": ["tech"],
            "valuation_usd": 5_000_000_000,
        },
    ],
    "Vector Databases": [
        {
            "name": "Pinecone", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 35.0, "market_share_bucket": "25-50",
            "single_source": False, "moat_types": ["tech", "scale"],
            "switching_costs": "medium", "demand_signal": "RAG-driven growth",
            "valuation_usd": 750_000_000,
        },
        {
            "name": "Weaviate", "is_public": False,
            "hq_country": "Netherlands",
            "market_share_pct": 14.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["tech"],
            "demand_signal": "OSS-led adoption", "valuation_usd": 200_000_000,
        },
        {
            "name": "Qdrant", "is_public": False,
            "hq_country": "Germany",
            "market_share_pct": 10.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["tech"],
            "demand_signal": "fast OSS growth", "valuation_usd": 150_000_000,
        },
    ],
    "LLM Observability": [
        {
            "name": "LangSmith (LangChain)", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 30.0, "market_share_bucket": "25-50",
            "single_source": False, "moat_types": ["scale"],
            "switching_costs": "low - tracing is portable",
            "demand_signal": "strong - LangChain pull",
            "valuation_usd": 1_100_000_000,
        },
        {
            "name": "Arize AI", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 14.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["tech"],
            "demand_signal": "growing enterprise pipeline",
            "valuation_usd": 700_000_000,
        },
    ],
    "Data Labeling / RLHF": [
        {
            "name": "Scale AI", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 42.0, "market_share_bucket": "25-50",
            "single_source": False, "moat_types": ["scale", "tech"],
            "switching_costs": "high - workflow integration",
            "customer_concentration": "frontier labs + DoD heavy",
            "demand_signal": "strong - frontier RLHF demand",
            "valuation_usd": 14_000_000_000,
        },
        {
            "name": "Surge AI", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 20.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["scale"],
            "demand_signal": "preferred by some frontier labs",
            "valuation_usd": 1_000_000_000,
        },
    ],
    "Agent Frameworks": [
        {
            "name": "LangChain", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 45.0, "market_share_bucket": "25-50",
            "single_source": False, "moat_types": ["scale"],
            "switching_costs": "low - OSS, easy to swap",
            "demand_signal": "developer mindshare leader",
            "valuation_usd": 1_100_000_000,
        },
        {
            "name": "LlamaIndex", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 18.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["tech"],
            "demand_signal": "RAG-focused growth",
            "valuation_usd": 220_000_000,
        },
    ],
    "Synthetic Data": [
        {
            "name": "Gretel.ai", "is_public": False,
            "hq_country": "United States",
            "market_share_pct": 25.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["tech"],
            "demand_signal": "growing - data scarcity tailwind",
            "valuation_usd": 320_000_000,
        },
        {
            "name": "Mostly AI", "is_public": False,
            "hq_country": "Austria",
            "market_share_pct": 15.0, "market_share_bucket": "10-25",
            "single_source": False, "moat_types": ["tech"],
            "demand_signal": "EU privacy tailwind",
            "valuation_usd": 200_000_000,
        },
    ],
    "Edge / On-Device Inference": [
        {
            "name": "Qualcomm", "is_public": True, "ticker": "QCOM",
            "hq_country": "United States",
            "market_share_pct": 38.0, "market_share_bucket": "25-50",
            "single_source": False, "moat_types": ["ip", "scale"],
            "switching_costs": "high - modem+NPU bundle",
            "demand_signal": "AI PC + AI phone tailwind",
            "valuation_usd": 200_000_000_000,
        },
        {
            "name": "Apple Neural Engine", "is_public": True, "ticker": "AAPL",
            "hq_country": "United States",
            "market_share_pct": 28.0, "market_share_bucket": "25-50",
            "single_source": False, "moat_types": ["ip", "scale", "tech"],
            "demand_signal": "captive - all Apple devices",
            "valuation_usd": None,
        },
        {
            "name": "Hailo", "is_public": False,
            "hq_country": "Israel",
            "market_share_pct": 5.0, "market_share_bucket": "<10",
            "single_source": False, "moat_types": ["ip", "tech"],
            "demand_signal": "automotive + industrial growth",
            "valuation_usd": 1_200_000_000,
        },
    ],
}


def evidence_for(company_name: str, component: str) -> list[dict]:
    """Generate plausible-looking evidence rows for a mock company."""
    return [
        {
            "claim": f"{company_name} holds the position described in {component}.",
            "source_url": f"https://example.com/research/{component.lower().replace(' ', '-')}",
            "source_name": "web",
            "tool_name": "web_search",
            "snippet": f"Industry analysts cite {company_name} as a key player in {component}.",
        },
        {
            "claim": f"Recent filings support market position for {company_name}.",
            "source_url": f"https://example.com/filings/{(company_name.split()[0] if company_name else 'co').lower()}-10k",
            "source_name": "web",
            "tool_name": "web_fetch",
            "snippet": "10-K disclosure cited.",
        },
    ]


def findings_for_component(component_name: str) -> list[dict]:
    base = MOCK_FINDINGS.get(component_name)
    if not base:
        # Generic fallback for any LLM-added component
        return [
            {
                "name": f"Leader (mock) for {component_name}",
                "is_public": True, "ticker": "TBD",
                "market_share_pct": 45.0, "market_share_bucket": "25-50",
                "single_source": False, "moat_types": ["scale"],
                "switching_costs": "medium", "demand_signal": "growing",
                "valuation_usd": None, "notes": "Generic mock placeholder.",
            }
        ]
    # Attach evidence to each
    enriched = []
    for c in base:
        c2 = dict(c)
        c2.setdefault("evidence", evidence_for(c["name"], component_name))
        enriched.append(c2)
    return enriched
