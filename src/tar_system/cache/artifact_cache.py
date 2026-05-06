"""Indexed artifact cache for compute-once local research steps."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from tar_system.settings import DATA_DIR

DB_PATH = Path(DATA_DIR) / "tar_system.duckdb"


def make_artifact_key(
    artifact_type: str,
    strategy: str,
    symbol: str,
    timeframe: str,
    data_hash: str | None,
    params_hash: str | None = None,
    broker_hash: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    feature_version: str = "v1",
    cost_model_version: str = "v1",
) -> str:
    payload = {
        "artifact_type": artifact_type,
        "strategy": strategy,
        "symbol": symbol,
        "timeframe": timeframe,
        "data_hash": data_hash,
        "params_hash": params_hash,
        "broker_hash": broker_hash,
        "date_from": date_from,
        "date_to": date_to,
        "feature_version": feature_version,
        "cost_model_version": cost_model_version,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def record_artifact(
    cache_key: str,
    artifact_type: str,
    path: str | Path,
    strategy: str = "",
    symbol: str = "",
    timeframe: str = "",
    data_hash: str | None = None,
    params_hash: str | None = None,
    broker_hash: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ensure_table()
    payload = {
        "cache_key": cache_key,
        "artifact_type": artifact_type,
        "strategy": strategy,
        "symbol": symbol,
        "timeframe": timeframe,
        "data_hash": data_hash,
        "params_hash": params_hash,
        "broker_hash": broker_hash,
        "date_from": date_from,
        "date_to": date_to,
        "path": str(path),
        "metadata_json": json.dumps(metadata or {}),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _connect() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO artifact_cache (
                cache_key, artifact_type, strategy, symbol, timeframe, data_hash,
                params_hash, broker_hash, date_from, date_to, path, metadata_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            list(payload.values()),
        )
    return payload


def get_artifact(cache_key: str) -> dict[str, Any] | None:
    _ensure_table()
    with _connect() as connection:
        row = connection.execute("SELECT * FROM artifact_cache WHERE cache_key = ?", [cache_key]).fetchone()
        columns = [item[0] for item in connection.description] if connection.description else []
    if not row:
        return None
    payload = dict(zip(columns, row))
    if payload.get("created_at") and hasattr(payload["created_at"], "isoformat"):
        payload["created_at"] = payload["created_at"].isoformat()
    return payload


def has_valid_artifact(cache_key: str) -> bool:
    artifact = get_artifact(cache_key)
    return bool(artifact and Path(str(artifact.get("path", ""))).exists())


def save_json_artifact(cache_key: str, artifact_type: str, path: str | Path, payload: dict[str, Any], **metadata: Any) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    record_artifact(cache_key, artifact_type, output, metadata=metadata)
    return output


def artifact_stats() -> dict[str, int]:
    _ensure_table()
    with _connect() as connection:
        rows = connection.execute("SELECT artifact_type, COUNT(*) FROM artifact_cache GROUP BY artifact_type").fetchall()
    return {str(name): int(count) for name, count in rows}


def _ensure_table() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS artifact_cache (
                cache_key VARCHAR PRIMARY KEY,
                artifact_type VARCHAR,
                strategy VARCHAR,
                symbol VARCHAR,
                timeframe VARCHAR,
                data_hash VARCHAR,
                params_hash VARCHAR,
                broker_hash VARCHAR,
                date_from VARCHAR,
                date_to VARCHAR,
                path VARCHAR,
                metadata_json JSON,
                created_at TIMESTAMP
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_artifact_target ON artifact_cache(artifact_type, strategy, symbol, timeframe)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_artifact_hash ON artifact_cache(data_hash, params_hash, broker_hash)")


def _connect(retries: int = 20, delay: float = 0.2) -> duckdb.DuckDBPyConnection:
    for attempt in range(retries):
        try:
            return duckdb.connect(str(DB_PATH))
        except duckdb.IOException:
            if attempt == retries - 1:
                raise
            time.sleep(delay * (attempt + 1))
    return duckdb.connect(str(DB_PATH))
