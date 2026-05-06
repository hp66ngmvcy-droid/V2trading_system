"""Indexed local job queue for the research controller.

DuckDB is the operational queue. JSONL is kept as a lightweight mirror for
manual inspection and backward compatibility with earlier TAR V2 builds.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from tar_system.settings import DATA_DIR

QUEUE_PATH = Path("runtime/job_queue.jsonl")
DB_PATH = Path(DATA_DIR) / "tar_system.duckdb"
STATUSES = {"QUEUED", "RUNNING", "COMPLETED", "FAILED", "SKIPPED"}
QUEUE_COLUMNS = [
    "job_id",
    "type",
    "strategy",
    "symbol",
    "timeframe",
    "file",
    "broker",
    "status",
    "priority",
    "data_hash",
    "params_hash",
    "created_at",
    "started_at",
    "completed_at",
    "result_path",
    "recommendation",
    "cost_sensitive",
    "swap_drag",
    "session_filter_used",
    "from_date",
    "to_date",
    "forward_from_date",
    "skip_walk_forward",
    "skip_forward_test",
    "max_walk_forward_splits",
    "research_stage",
]
ACTIVE_STATUSES = {"QUEUED", "RUNNING"}
ActiveJobKey = tuple[str, str, str, str, str, str, str, str]


def add_job(
    strategy: str,
    symbol: str,
    timeframe: str,
    file: str,
    broker: str = "current_broker_demo",
    job_type: str = "full_pipeline",
    priority: int = 100,
    data_hash: str | None = None,
    params_hash: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    forward_from_date: str | None = None,
    skip_walk_forward: bool = False,
    skip_forward_test: bool = False,
    max_walk_forward_splits: int = 100,
    research_stage: str = "full",
) -> dict[str, Any]:
    job = {
        "job_id": uuid.uuid4().hex,
        "type": job_type,
        "strategy": strategy,
        "symbol": symbol,
        "timeframe": timeframe,
        "file": file,
        "broker": broker,
        "status": "QUEUED",
        "priority": priority,
        "data_hash": data_hash,
        "params_hash": params_hash,
        "created_at": _now(),
        "started_at": None,
        "completed_at": None,
        "result_path": None,
        "recommendation": None,
        "cost_sensitive": None,
        "swap_drag": None,
        "session_filter_used": None,
        "from_date": from_date,
        "to_date": to_date,
        "forward_from_date": forward_from_date,
        "skip_walk_forward": skip_walk_forward,
        "skip_forward_test": skip_forward_test,
        "max_walk_forward_splits": max_walk_forward_splits,
        "research_stage": research_stage,
    }
    _insert_duckdb(job)
    _mirror_jsonl()
    return job


def has_active_job(
    strategy: str,
    symbol: str,
    timeframe: str,
    file: str,
    job_type: str = "full_pipeline",
    data_hash: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    research_stage: str = "full",
) -> bool:
    return make_active_job_key(strategy, symbol, timeframe, file, job_type, data_hash, from_date, to_date, research_stage) in active_job_keys()


def make_active_job_key(
    strategy: str,
    symbol: str,
    timeframe: str,
    file: str,
    job_type: str = "full_pipeline",
    data_hash: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    research_stage: str = "full",
) -> ActiveJobKey:
    dedupe_token = str(data_hash or file)
    return (strategy, symbol, timeframe, job_type, dedupe_token, str(from_date or ""), str(to_date or ""), research_stage)


def active_job_keys() -> set[ActiveJobKey]:
    keys: set[ActiveJobKey] = set()
    for job in read_jobs():
        if job.get("status") not in ACTIVE_STATUSES:
            continue
        keys.add(
            make_active_job_key(
                str(job.get("strategy") or ""),
                str(job.get("symbol") or ""),
                str(job.get("timeframe") or ""),
                str(job.get("file") or ""),
                str(job.get("type") or "full_pipeline"),
                str(job.get("data_hash")) if job.get("data_hash") else None,
                str(job.get("from_date")) if job.get("from_date") else None,
                str(job.get("to_date")) if job.get("to_date") else None,
                str(job.get("research_stage") or "full"),
            )
        )
    return keys


def read_jobs() -> list[dict[str, Any]]:
    jobs = _read_duckdb_jobs()
    if jobs:
        return jobs
    if not QUEUE_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in QUEUE_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def next_queued_job() -> dict[str, Any] | None:
    _ensure_queue_table()
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT * FROM research_jobs
            WHERE status = 'QUEUED'
            ORDER BY priority ASC, created_at ASC
            LIMIT 1
            """
        ).fetchone()
        columns = [item[0] for item in connection.description] if connection.description else []
    return _row_to_job(columns, row) if row else None


def claim_next_job() -> dict[str, Any] | None:
    """Atomically move the next queued job to RUNNING and return it."""
    _ensure_queue_table()
    with _connect() as connection:
        row = connection.execute(
            """
            UPDATE research_jobs
            SET status = 'RUNNING', started_at = ?
            WHERE job_id = (
                SELECT job_id FROM research_jobs
                WHERE status = 'QUEUED'
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
            )
            AND status = 'QUEUED'
            RETURNING *
            """,
            [_now()],
        ).fetchone()
        columns = [item[0] for item in connection.description] if connection.description else []
    if not row:
        return None
    _mirror_jsonl()
    return _row_to_job(columns, row)


def update_job(job_id: str, **updates: Any) -> dict[str, Any]:
    status = updates.get("status")
    if status and status not in STATUSES:
        raise ValueError(f"Unknown job status: {status}")
    allowed = {key: value for key, value in updates.items() if key in QUEUE_COLUMNS and key != "job_id"}
    if not allowed:
        job = _get_job(job_id)
        if job is None:
            raise KeyError(f"Unknown job_id: {job_id}")
        return job
    _ensure_queue_table()
    assignments = ", ".join(f"{key} = ?" for key in allowed)
    values = list(allowed.values()) + [job_id]
    with _connect() as connection:
        connection.execute(f"UPDATE research_jobs SET {assignments} WHERE job_id = ?", values)
    updated = _get_job(job_id)
    if updated is None:
        raise KeyError(f"Unknown job_id: {job_id}")
    _mirror_jsonl()
    return updated


def clear_completed() -> Path:
    _ensure_queue_table()
    with _connect() as connection:
        connection.execute("DELETE FROM research_jobs WHERE status IN ('COMPLETED', 'FAILED', 'SKIPPED')")
    return _mirror_jsonl()


def delete_jobs_by_data_hash_prefix(prefix: str) -> Path:
    _ensure_queue_table()
    with _connect() as connection:
        connection.execute("DELETE FROM research_jobs WHERE data_hash LIKE ?", [f"{prefix}%"])
    return _mirror_jsonl()


def queue_stats() -> dict[str, int]:
    stats = {status: 0 for status in sorted(STATUSES)}
    for job in read_jobs():
        status = str(job.get("status", ""))
        if status in stats:
            stats[status] += 1
    return stats


def _ensure_queue_table() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS research_jobs (
                job_id VARCHAR PRIMARY KEY,
                type VARCHAR,
                strategy VARCHAR,
                symbol VARCHAR,
                timeframe VARCHAR,
                file VARCHAR,
                broker VARCHAR,
                status VARCHAR,
                priority INTEGER,
                data_hash VARCHAR,
                params_hash VARCHAR,
                created_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                result_path VARCHAR,
                recommendation VARCHAR,
                cost_sensitive BOOLEAN,
                swap_drag DOUBLE,
                session_filter_used BOOLEAN
            )
            """
        )
        _ensure_queue_columns(connection)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_research_jobs_status_priority ON research_jobs(status, priority, created_at)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_research_jobs_target ON research_jobs(strategy, symbol, timeframe)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_research_jobs_hash ON research_jobs(data_hash, strategy, symbol, timeframe)")
        count = connection.execute("SELECT COUNT(*) FROM research_jobs").fetchone()[0]
    if count == 0 and QUEUE_PATH.exists():
        for job in _read_jsonl_jobs():
            _insert_duckdb(job, mirror=False, ensure=False)


def _insert_duckdb(job: dict[str, Any], mirror: bool = True, ensure: bool = True) -> None:
    if ensure:
        _ensure_queue_table()
    payload = {column: job.get(column) for column in QUEUE_COLUMNS}
    with _connect() as connection:
        connection.execute(
            f"INSERT OR REPLACE INTO research_jobs ({', '.join(QUEUE_COLUMNS)}) VALUES ({', '.join(['?'] * len(QUEUE_COLUMNS))})",
            [payload[column] for column in QUEUE_COLUMNS],
        )
    if mirror:
        _mirror_jsonl()


def _ensure_queue_columns(connection: duckdb.DuckDBPyConnection) -> None:
    existing = {row[1] for row in connection.execute("PRAGMA table_info('research_jobs')").fetchall()}
    additions = {
        "from_date": "VARCHAR",
        "to_date": "VARCHAR",
        "forward_from_date": "VARCHAR",
        "skip_walk_forward": "BOOLEAN",
        "skip_forward_test": "BOOLEAN",
        "max_walk_forward_splits": "INTEGER",
        "research_stage": "VARCHAR",
    }
    for column, column_type in additions.items():
        if column not in existing:
            connection.execute(f"ALTER TABLE research_jobs ADD COLUMN {column} {column_type}")


def _read_duckdb_jobs() -> list[dict[str, Any]]:
    _ensure_queue_table()
    with _connect() as connection:
        rows = connection.execute("SELECT * FROM research_jobs ORDER BY created_at ASC").fetchall()
        columns = [item[0] for item in connection.description] if connection.description else []
    return [_row_to_job(columns, row) for row in rows]


def _get_job(job_id: str) -> dict[str, Any] | None:
    _ensure_queue_table()
    with duckdb.connect(str(DB_PATH)) as connection:
        row = connection.execute("SELECT * FROM research_jobs WHERE job_id = ?", [job_id]).fetchone()
        columns = [item[0] for item in connection.description] if connection.description else []
    return _row_to_job(columns, row) if row else None


def _read_jsonl_jobs() -> list[dict[str, Any]]:
    if not QUEUE_PATH.exists():
        return []
    return [json.loads(line) for line in QUEUE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def _row_to_job(columns: list[str], row: Any) -> dict[str, Any]:
    payload = dict(zip(columns, row))
    return {key: (value.isoformat() if hasattr(value, "isoformat") else value) for key, value in payload.items()}


def _mirror_jsonl() -> Path:
    jobs = _read_duckdb_jobs()
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text("\n".join(json.dumps(job, default=str) for job in jobs) + ("\n" if jobs else ""), encoding="utf-8")
    return QUEUE_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(retries: int = 20, delay: float = 0.2) -> duckdb.DuckDBPyConnection:
    for attempt in range(retries):
        try:
            return duckdb.connect(str(DB_PATH))
        except duckdb.IOException:
            if attempt == retries - 1:
                raise
            time.sleep(delay * (attempt + 1))
    return duckdb.connect(str(DB_PATH))
