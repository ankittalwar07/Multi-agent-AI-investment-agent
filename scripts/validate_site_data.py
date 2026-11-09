"""Validate docs/data before it is committed (no LLM, standard library only).

Usage:
    python scripts/validate_site_data.py            # checks docs/data
    python scripts/validate_site_data.py --research work/research.json

Exits non-zero with a list of problems. The weekly Claude routine must get a clean
pass before it pushes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = re.compile(r"[\u2012\u2013\u2014\u2015]")
SECRET = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{10,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}"
    r"|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{30,}|xox[abpr]-[A-Za-z0-9-]{10,}|gsk_[A-Za-z0-9]{20,})"
)
PLACEHOLDER_HOSTS = ("example.com", "example.org", "localhost", "127.0.0.1")
SHARE_BUCKETS = {"<10", "10-25", "25-50", "50-75", ">75", "sole", None}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_BYTES = 2_000_000


def _check_text(label: str, text: str, problems: list[str]) -> None:
    if DASH.search(text):
        problems.append(f"{label}: contains an em or en dash")
    if SECRET.search(text):
        problems.append(f"{label}: contains something that looks like a key or token")


def _check_url(label: str, url: str | None, problems: list[str]) -> None:
    if url is None:
        return
    if not isinstance(url, str) or not url.startswith("https://"):
        problems.append(f"{label}: source_url must be https or null, got {url!r}")
    elif any(h in url for h in PLACEHOLDER_HOSTS):
        problems.append(f"{label}: placeholder URL {url}")


def validate_payload(d: dict, label: str) -> list[str]:
    p: list[str] = []
    for key in ("schema_version", "sample", "run_date", "summary", "stats",
                "components", "companies"):
        if key not in d:
            p.append(f"{label}: missing key {key}")
    if p:
        return p
    if d["schema_version"] != 1:
        p.append(f"{label}: schema_version must be 1")
    if not DATE.match(str(d["run_date"])):
        p.append(f"{label}: run_date must be YYYY-MM-DD")
    comp_ids = {c.get("id") for c in d["components"]}
    if len(comp_ids) != len(d["components"]):
        p.append(f"{label}: duplicate component ids")
    if not d["companies"]:
        p.append(f"{label}: no companies")
    for c in d["companies"]:
        cl = f"{label}: {c.get('name')}"
        if c.get("component_id") not in comp_ids:
            p.append(f"{cl}: unknown component_id {c.get('component_id')}")
        if c.get("market_share_bucket") not in SHARE_BUCKETS:
            p.append(f"{cl}: bad market_share_bucket {c.get('market_share_bucket')}")
        s = c.get("score") or {}
        comp = s.get("composite")
        if not isinstance(comp, (int, float)) or not 0 <= comp <= 100:
            p.append(f"{cl}: composite must be 0 to 100")
        elif abs(sum((s.get("breakdown") or {}).values()) - comp) > 0.01:
            p.append(f"{cl}: score breakdown does not add up to composite")
        if len((c.get("council") or {}).get("verdicts") or []) != 9:
            p.append(f"{cl}: council must have 9 verdicts")
        for e in c.get("evidence") or []:
            _check_url(cl, e.get("source_url"), p)
        for s2 in c.get("signals") or []:
            _check_url(cl, s2.get("source_url"), p)
        if not d["sample"] and not any((e.get("source_url") or "").startswith("https://")
                                       for e in c.get("evidence") or []):
            p.append(f"{cl}: real runs need at least one cited https source per company")
    if not d["sample"] and not d["summary"].strip():
        p.append(f"{label}: summary is empty")
    return p


def validate_research(path: Path) -> list[str]:
    p: list[str] = []
    text = path.read_text(encoding="utf-8")
    _check_text(str(path), text, p)
    d = json.loads(text)
    comp_ids = {c.get("id") for c in d.get("components", [])}
    if not comp_ids:
        p.append(f"{path}: no components")
    for c in d.get("companies", []):
        cl = f"{path}: {c.get('name')}"
        if c.get("component_id") not in comp_ids:
            p.append(f"{cl}: unknown component_id {c.get('component_id')}")
        urls = [e.get("source_url") for e in c.get("evidence") or []]
        if not any(isinstance(u, str) and u.startswith("https://") for u in urls):
            p.append(f"{cl}: needs at least one evidence entry with an https source_url")
        for u in urls:
            _check_url(cl, u, p)
    return p


def validate_dir(data_dir: Path) -> list[str]:
    p: list[str] = []
    latest = data_dir / "latest.json"
    if not latest.exists():
        return [f"{latest} is missing"]
    for f in sorted(data_dir.rglob("*.json")):
        text = f.read_text(encoding="utf-8")
        rel = f.relative_to(data_dir)
        if len(text.encode("utf-8")) > MAX_BYTES:
            p.append(f"{rel}: larger than {MAX_BYTES} bytes")
        _check_text(str(rel), text, p)
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            p.append(f"{rel}: invalid JSON ({exc})")
    d = json.loads(latest.read_text(encoding="utf-8"))
    p += validate_payload(d, "latest.json")
    dated = data_dir / "history" / f"{d.get('run_date')}.json"
    if not dated.exists():
        p.append(f"history/{d.get('run_date')}.json is missing")
    elif json.loads(dated.read_text(encoding="utf-8")) != d:
        p.append(f"history/{dated.name} does not match latest.json")
    index = data_dir / "history" / "index.json"
    if index.exists():
        runs = json.loads(index.read_text(encoding="utf-8")).get("runs", [])
        if not runs or runs[0].get("run_date") != d.get("run_date"):
            p.append("history/index.json does not list the latest run first")
    else:
        p.append("history/index.json is missing")
    return p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=ROOT / "docs" / "data", type=Path)
    ap.add_argument("--research", type=Path, help="also check a research file")
    args = ap.parse_args(argv)
    problems = validate_dir(args.data)
    if args.research:
        problems += validate_research(args.research)
    if problems:
        print(f"FAIL: {len(problems)} problem(s)")
        for line in problems:
            print(f"  - {line}")
        return 1
    print("OK: site data is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
