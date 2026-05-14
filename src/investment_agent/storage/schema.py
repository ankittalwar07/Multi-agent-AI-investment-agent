SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS run (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    provider TEXT NOT NULL,
    model TEXT,
    mock INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL,
    error TEXT
);

CREATE TABLE IF NOT EXISTS component (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES run(id),
    name TEXT NOT NULL,
    category TEXT,
    description TEXT,
    source TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_component_run ON component(run_id);

CREATE TABLE IF NOT EXISTS company (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES run(id),
    component_id TEXT NOT NULL REFERENCES component(id),
    name TEXT NOT NULL,
    is_public INTEGER,
    ticker TEXT,
    hq_country TEXT,
    market_share_pct REAL,
    market_share_bucket TEXT,
    single_source INTEGER,
    moat_types TEXT,
    switching_costs TEXT,
    customer_concentration TEXT,
    demand_signal TEXT,
    valuation_usd REAL,
    notes TEXT
);
CREATE INDEX IF NOT EXISTS ix_company_run ON company(run_id);
CREATE INDEX IF NOT EXISTS ix_company_component ON company(component_id);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL REFERENCES company(id),
    claim TEXT,
    source_url TEXT,
    source_name TEXT,
    retrieved_at TEXT,
    snippet TEXT,
    snippet_hash TEXT,
    tool_name TEXT
);
CREATE INDEX IF NOT EXISTS ix_evidence_company ON evidence(company_id);

CREATE TABLE IF NOT EXISTS score (
    company_id TEXT PRIMARY KEY REFERENCES company(id),
    sole_source_pts REAL DEFAULT 0,
    share_pts REAL DEFAULT 0,
    ip_pts REAL DEFAULT 0,
    regulatory_pts REAL DEFAULT 0,
    switching_pts REAL DEFAULT 0,
    demand_pts REAL DEFAULT 0,
    composite REAL,
    rubric_version TEXT,
    rationale TEXT
);

CREATE TABLE IF NOT EXISTS run_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES run(id),
    ts TEXT NOT NULL,
    level TEXT NOT NULL,
    node TEXT,
    message TEXT
);
CREATE INDEX IF NOT EXISTS ix_event_run ON run_event(run_id, id);
"""
