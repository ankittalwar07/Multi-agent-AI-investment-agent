"""Build docs/data/*.json for the GitHub Pages dashboard from a research file.

Usage:
    python scripts/build_site_data.py --research work/research.json
    python scripts/build_site_data.py --research work/research.json --sample

No LLM calls. Scoring and the investor council are pure Python from this repo.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from investment_agent.site import build_site_payload, write_site_data  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--research", required=True, type=Path, help="research JSON file")
    ap.add_argument("--out", default=ROOT / "docs" / "data", type=Path)
    ap.add_argument("--sample", action="store_true", help="mark the output as sample data")
    ap.add_argument("--generated-by", default="claude-routine")
    args = ap.parse_args(argv)

    research = json.loads(args.research.read_text(encoding="utf-8"))
    payload = build_site_payload(research, sample=args.sample, generated_by=args.generated_by)
    for p in write_site_data(payload, args.out):
        print(f"wrote {p.relative_to(ROOT) if p.is_relative_to(ROOT) else p}")
    s = payload["stats"]
    print(f"{s['companies']} companies across {s['components']} components, "
          f"{s['cited_sources']} cited sources, {s['sole_source_credited']} sole-source credited")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
