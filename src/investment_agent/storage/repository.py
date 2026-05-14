from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .models import (
    CompanyExtras,
    CompanyRow,
    ComponentRow,
    EvidenceRow,
    RunEvent,
    RunRow,
    RunView,
    ScoreRow,
)
from .schema import SCHEMA_SQL


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bool(v: Any) -> int | None:
    if v is None:
        return None
    return 1 if v else 0


def _from_bool(v: Any) -> bool | None:
    if v is None:
        return None
    return bool(v)


class RunRepository:
    """SQLite-backed repository — one DB per run at `data/runs/{run_id}.db`."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(SCHEMA_SQL)

    @classmethod
    def for_run(cls, output_dir: Path, run_id: str) -> "RunRepository":
        return cls(Path(output_dir) / f"{run_id}.db")

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ---------- writes ----------

    def create_run(
        self, *, provider: str, model: str | None, mock: bool, run_id: str | None = None
    ) -> str:
        rid = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO run(id, started_at, provider, model, mock, status) VALUES(?,?,?,?,?,?)",
                (rid, _now(), provider, model, _bool(mock), "running"),
            )
        return rid

    def finish_run(self, run_id: str, *, status: str, error: str | None = None, cost_usd: float = 0.0) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE run SET finished_at=?, status=?, error=?, cost_usd=? WHERE id=?",
                (_now(), status, error, cost_usd, run_id),
            )

    def add_cost(self, run_id: str, delta_usd: float) -> None:
        with self._conn() as conn:
            conn.execute("UPDATE run SET cost_usd = cost_usd + ? WHERE id=?", (delta_usd, run_id))

    def upsert_component(
        self,
        *,
        run_id: str,
        name: str,
        category: str | None,
        description: str | None,
        source: str,
        status: str = "pending",
        component_id: str | None = None,
    ) -> str:
        cid = component_id or f"comp_{uuid.uuid4().hex[:10]}"
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO component(id, run_id, name, category, description, source, status)
                   VALUES(?,?,?,?,?,?,?)""",
                (cid, run_id, name, category, description, source, status),
            )
        return cid

    def set_component_status(self, component_id: str, status: str) -> None:
        with self._conn() as conn:
            conn.execute("UPDATE component SET status=? WHERE id=?", (status, component_id))

    def add_company(
        self,
        *,
        run_id: str,
        component_id: str,
        name: str,
        is_public: bool | None = None,
        ticker: str | None = None,
        hq_country: str | None = None,
        market_share_pct: float | None = None,
        market_share_bucket: str | None = None,
        single_source: bool | None = None,
        moat_types: list[str] | None = None,
        switching_costs: str | None = None,
        customer_concentration: str | None = None,
        demand_signal: str | None = None,
        valuation_usd: float | None = None,
        notes: str | None = None,
        extras: dict | None = None,
    ) -> str:
        cid = f"co_{uuid.uuid4().hex[:10]}"
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO company(id, run_id, component_id, name, is_public, ticker,
                   hq_country, market_share_pct, market_share_bucket, single_source,
                   moat_types, switching_costs, customer_concentration, demand_signal,
                   valuation_usd, notes, extras_json)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    cid,
                    run_id,
                    component_id,
                    name,
                    _bool(is_public),
                    ticker,
                    hq_country,
                    market_share_pct,
                    market_share_bucket,
                    _bool(single_source),
                    json.dumps(moat_types or []),
                    switching_costs,
                    customer_concentration,
                    demand_signal,
                    valuation_usd,
                    notes,
                    json.dumps(extras) if extras else None,
                ),
            )
        return cid

    def add_evidence(
        self,
        *,
        company_id: str,
        claim: str | None,
        source_url: str | None,
        source_name: str | None,
        retrieved_at: datetime | None = None,
        snippet: str | None = None,
        snippet_hash: str | None = None,
        tool_name: str | None = None,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO evidence(company_id, claim, source_url, source_name,
                   retrieved_at, snippet, snippet_hash, tool_name)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (
                    company_id,
                    claim,
                    source_url,
                    source_name,
                    (retrieved_at or datetime.now(timezone.utc)).isoformat(),
                    snippet,
                    snippet_hash,
                    tool_name,
                ),
            )

    def set_score(
        self,
        *,
        company_id: str,
        sole_source_pts: float,
        share_pts: float,
        ip_pts: float,
        regulatory_pts: float,
        switching_pts: float,
        demand_pts: float,
        composite: float,
        rubric_version: str,
        rationale: str | None = None,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO score(company_id, sole_source_pts, share_pts,
                   ip_pts, regulatory_pts, switching_pts, demand_pts, composite,
                   rubric_version, rationale)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    company_id,
                    sole_source_pts,
                    share_pts,
                    ip_pts,
                    regulatory_pts,
                    switching_pts,
                    demand_pts,
                    composite,
                    rubric_version,
                    rationale,
                ),
            )

    def log_event(self, *, run_id: str, level: str, node: str | None, message: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO run_event(run_id, ts, level, node, message) VALUES(?,?,?,?,?)",
                (run_id, _now(), level, node, message),
            )

    # ---------- reads ----------

    def get_run(self, run_id: str) -> RunRow | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM run WHERE id=?", (run_id,)).fetchone()
        return _row_to_run(row) if row else None

    def list_runs(self) -> list[RunRow]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM run ORDER BY started_at DESC").fetchall()
        return [_row_to_run(r) for r in rows]

    def get_view(self, run_id: str) -> RunView:
        with self._conn() as conn:
            run_row = conn.execute("SELECT * FROM run WHERE id=?", (run_id,)).fetchone()
            comp_rows = conn.execute(
                "SELECT * FROM component WHERE run_id=? ORDER BY name", (run_id,)
            ).fetchall()
            co_rows = conn.execute(
                "SELECT * FROM company WHERE run_id=? ORDER BY name", (run_id,)
            ).fetchall()
            company_ids = [r["id"] for r in co_rows]
            ev_rows = []
            score_rows = []
            if company_ids:
                placeholders = ",".join("?" * len(company_ids))
                ev_rows = conn.execute(
                    f"SELECT * FROM evidence WHERE company_id IN ({placeholders}) ORDER BY id",
                    company_ids,
                ).fetchall()
                score_rows = conn.execute(
                    f"SELECT * FROM score WHERE company_id IN ({placeholders})",
                    company_ids,
                ).fetchall()
            event_rows = conn.execute(
                "SELECT * FROM run_event WHERE run_id=? ORDER BY id DESC LIMIT 200",
                (run_id,),
            ).fetchall()

        if not run_row:
            raise KeyError(f"run not found: {run_id}")

        ev_by_co: dict[str, list[EvidenceRow]] = {}
        for r in ev_rows:
            ev_by_co.setdefault(r["company_id"], []).append(_row_to_evidence(r))

        scores_by_co: dict[str, ScoreRow] = {r["company_id"]: _row_to_score(r) for r in score_rows}

        companies = [
            _row_to_company(
                r,
                evidence=ev_by_co.get(r["id"], []),
                score=scores_by_co.get(r["id"]),
            )
            for r in co_rows
        ]

        return RunView(
            run=_row_to_run(run_row),
            components=[_row_to_component(r) for r in comp_rows],
            companies=companies,
            events=[_row_to_event(r) for r in event_rows],
        )


# ---------- row mappers ----------


def _row_to_run(r: sqlite3.Row) -> RunRow:
    return RunRow(
        id=r["id"],
        started_at=r["started_at"],
        finished_at=r["finished_at"],
        provider=r["provider"],
        model=r["model"],
        mock=bool(r["mock"]),
        cost_usd=r["cost_usd"] or 0.0,
        status=r["status"],
        error=r["error"],
    )


def _row_to_component(r: sqlite3.Row) -> ComponentRow:
    return ComponentRow(
        id=r["id"],
        run_id=r["run_id"],
        name=r["name"],
        category=r["category"],
        description=r["description"],
        source=r["source"],
        status=r["status"],
    )


def _row_to_evidence(r: sqlite3.Row) -> EvidenceRow:
    return EvidenceRow(
        id=r["id"],
        company_id=r["company_id"],
        claim=r["claim"],
        source_url=r["source_url"],
        source_name=r["source_name"],
        retrieved_at=r["retrieved_at"],
        snippet=r["snippet"],
        snippet_hash=r["snippet_hash"],
        tool_name=r["tool_name"],
    )


def _row_to_score(r: sqlite3.Row) -> ScoreRow:
    return ScoreRow(
        company_id=r["company_id"],
        sole_source_pts=r["sole_source_pts"] or 0,
        share_pts=r["share_pts"] or 0,
        ip_pts=r["ip_pts"] or 0,
        regulatory_pts=r["regulatory_pts"] or 0,
        switching_pts=r["switching_pts"] or 0,
        demand_pts=r["demand_pts"] or 0,
        composite=r["composite"],
        rubric_version=r["rubric_version"],
        rationale=r["rationale"],
    )


def _row_to_company(
    r: sqlite3.Row,
    *,
    evidence: Iterable[EvidenceRow],
    score: ScoreRow | None,
) -> CompanyRow:
    moat_types: list[str] = []
    if r["moat_types"]:
        try:
            moat_types = json.loads(r["moat_types"])
        except json.JSONDecodeError:
            moat_types = []
    extras = CompanyExtras()
    try:
        extras_raw = r["extras_json"]
    except (IndexError, KeyError):
        extras_raw = None
    if extras_raw:
        try:
            extras = CompanyExtras.model_validate(json.loads(extras_raw))
        except (json.JSONDecodeError, Exception):
            extras = CompanyExtras()
    return CompanyRow(
        id=r["id"],
        run_id=r["run_id"],
        component_id=r["component_id"],
        name=r["name"],
        is_public=_from_bool(r["is_public"]),
        ticker=r["ticker"],
        hq_country=r["hq_country"],
        market_share_pct=r["market_share_pct"],
        market_share_bucket=r["market_share_bucket"],
        single_source=_from_bool(r["single_source"]),
        moat_types=moat_types,
        switching_costs=r["switching_costs"],
        customer_concentration=r["customer_concentration"],
        demand_signal=r["demand_signal"],
        valuation_usd=r["valuation_usd"],
        notes=r["notes"],
        extras=extras,
        evidence=list(evidence),
        score=score,
    )


def _row_to_event(r: sqlite3.Row) -> RunEvent:
    return RunEvent(
        id=r["id"],
        run_id=r["run_id"],
        ts=r["ts"],
        level=r["level"],
        node=r["node"],
        message=r["message"],
    )


def list_run_ids(output_dir: Path) -> list[str]:
    output_dir = Path(output_dir)
    if not output_dir.exists():
        return []
    return sorted(
        (p.stem for p in output_dir.glob("*.db")),
        reverse=True,
    )
