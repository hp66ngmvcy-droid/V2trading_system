"""Indexed local job queue for the research controller.

DuckDB is the operational queue. JSONL is kept as a lightweight mirror for
manual inspection and backward compatibility with earlier TAR V2 builds.
"""

from __future__ import annotations

import json
import time
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
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
    "no_live",
    "no_mt5_promotion",
    "require_walk_forward",
    "require_min_trades",
    "min_trades",
]
ACTIVE_STATUSES = {"QUEUED", "RUNNING"}
ActiveJobKey = tuple[str, str, str, str, str, str, str, str]
QUEUE_COLUMN_SET = set(QUEUE_COLUMNS)
QUEUE_COLUMN_TYPES = {
    "from_date": "VARCHAR",
    "to_date": "VARCHAR",
    "forward_from_date": "VARCHAR",
    "skip_walk_forward": "BOOLEAN",
    "skip_forward_test": "BOOLEAN",
    "max_walk_forward_splits": "INTEGER",
    "research_stage": "VARCHAR",
    "no_live": "BOOLEAN",
    "no_mt5_promotion": "BOOLEAN",
    "require_walk_forward": "BOOLEAN",
    "require_min_trades": "BOOLEAN",
    "min_trades": "INTEGER",
}
QUEUE_INSERT_SQL = """
INSERT INTO research_jobs (
    job_id, type, strategy, symbol, timeframe, file, broker, status, priority,
    data_hash, params_hash, created_at, started_at, completed_at, result_path,
    recommendation, cost_sensitive, swap_drag, session_filter_used, from_date,
    to_date, forward_from_date, skip_walk_forward, skip_forward_test,
    max_walk_forward_splits, research_stage, no_live, no_mt5_promotion,
    require_walk_forward, require_min_trades, min_trades
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
QUEUE_INSERT_OR_REPLACE_SQL = """
INSERT OR REPLACE INTO research_jobs (
    job_id, type, strategy, symbol, timeframe, file, broker, status, priority,
    data_hash, params_hash, created_at, started_at, completed_at, result_path,
    recommendation, cost_sensitive, swap_drag, session_filter_used, from_date,
    to_date, forward_from_date, skip_walk_forward, skip_forward_test,
    max_walk_forward_splits, research_stage, no_live, no_mt5_promotion,
    require_walk_forward, require_min_trades, min_trades
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
QUEUE_UPDATE_SQL = {
    "type": "UPDATE research_jobs SET type = ? WHERE job_id = ?",
    "strategy": "UPDATE research_jobs SET strategy = ? WHERE job_id = ?",
    "symbol": "UPDATE research_jobs SET symbol = ? WHERE job_id = ?",
    "timeframe": "UPDATE research_jobs SET timeframe = ? WHERE job_id = ?",
    "file": "UPDATE research_jobs SET file = ? WHERE job_id = ?",
    "broker": "UPDATE research_jobs SET broker = ? WHERE job_id = ?",
    "status": "UPDATE research_jobs SET status = ? WHERE job_id = ?",
    "priority": "UPDATE research_jobs SET priority = ? WHERE job_id = ?",
    "data_hash": "UPDATE research_jobs SET data_hash = ? WHERE job_id = ?",
    "params_hash": "UPDATE research_jobs SET params_hash = ? WHERE job_id = ?",
    "created_at": "UPDATE research_jobs SET created_at = ? WHERE job_id = ?",
    "started_at": "UPDATE research_jobs SET started_at = ? WHERE job_id = ?",
    "completed_at": "UPDATE research_jobs SET completed_at = ? WHERE job_id = ?",
    "result_path": "UPDATE research_jobs SET result_path = ? WHERE job_id = ?",
    "recommendation": "UPDATE research_jobs SET recommendation = ? WHERE job_id = ?",
    "cost_sensitive": "UPDATE research_jobs SET cost_sensitive = ? WHERE job_id = ?",
    "swap_drag": "UPDATE research_jobs SET swap_drag = ? WHERE job_id = ?",
    "session_filter_used": "UPDATE research_jobs SET session_filter_used = ? WHERE job_id = ?",
    "from_date": "UPDATE research_jobs SET from_date = ? WHERE job_id = ?",
    "to_date": "UPDATE research_jobs SET to_date = ? WHERE job_id = ?",
    "forward_from_date": "UPDATE research_jobs SET forward_from_date = ? WHERE job_id = ?",
    "skip_walk_forward": "UPDATE research_jobs SET skip_walk_forward = ? WHERE job_id = ?",
    "skip_forward_test": "UPDATE research_jobs SET skip_forward_test = ? WHERE job_id = ?",
    "max_walk_forward_splits": "UPDATE research_jobs SET max_walk_forward_splits = ? WHERE job_id = ?",
    "research_stage": "UPDATE research_jobs SET research_stage = ? WHERE job_id = ?",
    "no_live": "UPDATE research_jobs SET no_live = ? WHERE job_id = ?",
    "no_mt5_promotion": "UPDATE research_jobs SET no_mt5_promotion = ? WHERE job_id = ?",
    "require_walk_forward": "UPDATE research_jobs SET require_walk_forward = ? WHERE job_id = ?",
    "require_min_trades": "UPDATE research_jobs SET require_min_trades = ? WHERE job_id = ?",
    "min_trades": "UPDATE research_jobs SET min_trades = ? WHERE job_id = ?",
}
QUEUE_ALTER_SQL = {
    "from_date": "ALTER TABLE research_jobs ADD COLUMN from_date VARCHAR",
    "to_date": "ALTER TABLE research_jobs ADD COLUMN to_date VARCHAR",
    "forward_from_date": "ALTER TABLE research_jobs ADD COLUMN forward_from_date VARCHAR",
    "skip_walk_forward": "ALTER TABLE research_jobs ADD COLUMN skip_walk_forward BOOLEAN",
    "skip_forward_test": "ALTER TABLE research_jobs ADD COLUMN skip_forward_test BOOLEAN",
    "max_walk_forward_splits": "ALTER TABLE research_jobs ADD COLUMN max_walk_forward_splits INTEGER",
    "research_stage": "ALTER TABLE research_jobs ADD COLUMN research_stage VARCHAR",
    "no_live": "ALTER TABLE research_jobs ADD COLUMN no_live BOOLEAN",
    "no_mt5_promotion": "ALTER TABLE research_jobs ADD COLUMN no_mt5_promotion BOOLEAN",
    "require_walk_forward": "ALTER TABLE research_jobs ADD COLUMN require_walk_forward BOOLEAN",
    "require_min_trades": "ALTER TABLE research_jobs ADD COLUMN require_min_trades BOOLEAN",
    "min_trades": "ALTER TABLE research_jobs ADD COLUMN min_trades INTEGER",
}


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
    no_live: bool = True,
    no_mt5_promotion: bool = True,
    require_walk_forward: bool = True,
    require_min_trades: bool = False,
    min_trades: int = 30,
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
        "no_live": no_live,
        "no_mt5_promotion": no_mt5_promotion,
        "require_walk_forward": require_walk_forward,
        "require_min_trades": require_min_trades,
        "min_trades": min_trades,
    }
    inserted = _insert_duckdb_unless_active_duplicate(job)
    _mirror_jsonl()
    return inserted


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
    with _connect() as connection:
        connection.execute("BEGIN TRANSACTION")
        try:
            for key, value in allowed.items():
                connection.execute(QUEUE_UPDATE_SQL[_queue_column(key)], [value, job_id])
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
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


def count_active_jobs() -> int:
    _ensure_queue_table()
    with _connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM research_jobs WHERE status IN ('QUEUED', 'RUNNING')"
        ).fetchone()
    return int(row[0]) if row else 0


def count_running_jobs() -> int:
    _ensure_queue_table()
    with _connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM research_jobs WHERE status = 'RUNNING'"
        ).fetchone()
    return int(row[0]) if row else 0


def diagnose_failures(stale_running_minutes: int = 120) -> dict[str, Any]:
    """Return structured failure breakdown from the job queue."""
    _ensure_queue_table()
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=stale_running_minutes)).isoformat()
    with _connect() as connection:
        failed_rows = connection.execute(
            "SELECT research_stage, strategy, symbol, timeframe FROM research_jobs WHERE status = 'FAILED'"
        ).fetchall()
        skipped_count = connection.execute(
            "SELECT COUNT(*) FROM research_jobs WHERE status = 'SKIPPED'"
        ).fetchone()
        stale_rows = connection.execute(
            "SELECT * FROM research_jobs WHERE status = 'RUNNING' AND started_at IS NOT NULL AND started_at < ?",
            [cutoff],
        ).fetchall()
        stale_cols = [item[0] for item in connection.description] if connection.description else []

    by_stage: Counter[str] = Counter(row[0] or "unknown" for row in failed_rows)
    by_target: Counter[str] = Counter(
        f"{row[1]} {row[2]} {row[3]}" for row in failed_rows
    )
    return {
        "total_failed": len(failed_rows),
        "total_skipped": int(skipped_count[0]) if skipped_count else 0,
        "by_stage": by_stage.most_common(),
        "by_target": by_target.most_common(10),
        "stale_running": [_row_to_job(stale_cols, row) for row in stale_rows],
    }


def classify_failed_job(job: dict[str, Any]) -> str:
    """Classify a failed job without mutating the queue."""
    result_path = job.get("result_path")
    if result_path and Path(str(result_path)).exists():
        return "failed_with_result_path_exists"
    if result_path:
        return "failed_with_missing_result_path"
    if job.get("skip_walk_forward") is True or job.get("skip_forward_test") is True:
        return "failed_dashboard_or_fast_batch_no_result"
    if job.get("completed_at") is None:
        return "failed_no_completion_timestamp"
    if job.get("started_at") is None:
        return "failed_never_started"
    return "failed_no_result_path"


def queue_health(limit: int = 10) -> dict[str, Any]:
    """Return a compact, non-mutating health summary for the research queue."""
    jobs = read_jobs()
    failed = [job for job in jobs if job.get("status") == "FAILED"]
    active = [job for job in jobs if job.get("status") in ACTIVE_STATUSES]
    failed_buckets: Counter[str] = Counter(classify_failed_job(job) for job in failed)
    failed_by_stage: Counter[str] = Counter(str(job.get("research_stage") or "none") for job in failed)
    failed_by_strategy: Counter[str] = Counter(str(job.get("strategy") or "unknown") for job in failed)
    failed_by_symbol: Counter[str] = Counter(str(job.get("symbol") or "unknown") for job in failed)
    failed_by_timeframe: Counter[str] = Counter(str(job.get("timeframe") or "unknown") for job in failed)
    recent_failed = sorted(failed, key=lambda job: str(job.get("created_at") or ""), reverse=True)[:limit]
    return {
        "queue_stats": queue_stats(),
        "total_jobs": len(jobs),
        "active_jobs": len(active),
        "failed_jobs": len(failed),
        "failed_buckets": dict(failed_buckets),
        "failed_by_stage": failed_by_stage.most_common(limit),
        "failed_by_strategy": failed_by_strategy.most_common(limit),
        "failed_by_symbol": failed_by_symbol.most_common(limit),
        "failed_by_timeframe": failed_by_timeframe.most_common(limit),
        "recent_failed_preview": [
            {
                "job_id": job.get("job_id"),
                "strategy": job.get("strategy"),
                "symbol": job.get("symbol"),
                "timeframe": job.get("timeframe"),
                "research_stage": job.get("research_stage"),
                "created_at": job.get("created_at"),
                "classification": classify_failed_job(job),
            }
            for job in recent_failed
        ],
    }


def reset_stale_running(max_minutes: int = 120) -> int:
    """Mark RUNNING jobs older than max_minutes as FAILED. Returns count reset."""
    _ensure_queue_table()
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=max_minutes)).isoformat()
    now = _now()
    with _connect() as connection:
        result = connection.execute(
            """
            UPDATE research_jobs
            SET status = 'FAILED', completed_at = ?
            WHERE status = 'RUNNING' AND started_at IS NOT NULL AND started_at < ?
            RETURNING job_id
            """,
            [now, cutoff],
        ).fetchall()
    if result:
        _mirror_jsonl()
    return len(result)


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
            QUEUE_INSERT_OR_REPLACE_SQL,
            [payload[column] for column in QUEUE_COLUMNS],
        )
    if mirror:
        _mirror_jsonl()


def _insert_duckdb_unless_active_duplicate(job: dict[str, Any]) -> dict[str, Any]:
    """Atomically insert a job unless an equivalent active job already exists.

    Callers should not have to remember to call ``has_active_job`` before
    queueing. DuckDB permits one writer at a time, so keeping the active check
    and insert in one transaction closes the common check-then-insert race.
    """

    _ensure_queue_table()
    payload = {column: job.get(column) for column in QUEUE_COLUMNS}
    dedupe_token = str(job.get("data_hash") or job.get("file") or "")
    with _connect() as connection:
        connection.execute("BEGIN TRANSACTION")
        try:
            duplicate = connection.execute(
                """
                SELECT * FROM research_jobs
                WHERE status IN ('QUEUED', 'RUNNING')
                  AND strategy = ?
                  AND symbol = ?
                  AND timeframe = ?
                  AND type = ?
                  AND COALESCE(data_hash, file, '') = ?
                  AND COALESCE(from_date, '') = ?
                  AND COALESCE(to_date, '') = ?
                  AND COALESCE(research_stage, 'full') = ?
                ORDER BY created_at ASC
                LIMIT 1
                """,
                [
                    job.get("strategy"),
                    job.get("symbol"),
                    job.get("timeframe"),
                    job.get("type"),
                    dedupe_token,
                    str(job.get("from_date") or ""),
                    str(job.get("to_date") or ""),
                    str(job.get("research_stage") or "full"),
                ],
            ).fetchone()
            columns = [item[0] for item in connection.description] if connection.description else []
            if duplicate:
                connection.execute("COMMIT")
                return _row_to_job(columns, duplicate)
            connection.execute(
                QUEUE_INSERT_SQL,
                [payload[column] for column in QUEUE_COLUMNS],
            )
            connection.execute("COMMIT")
            return job
        except Exception:
            connection.execute("ROLLBACK")
            raise


def _ensure_queue_columns(connection: duckdb.DuckDBPyConnection) -> None:
    existing = {row[1] for row in connection.execute("PRAGMA table_info('research_jobs')").fetchall()}
    for column in QUEUE_COLUMN_TYPES:
        if column not in existing:
            connection.execute(QUEUE_ALTER_SQL[_queue_column(column)])


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


def _queue_column(column: str) -> str:
    if column not in QUEUE_COLUMN_SET:
        raise ValueError(f"Unknown queue column: {column}")
    return column
