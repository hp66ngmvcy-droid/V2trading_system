"""DuckDB-backed local strategy memory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from tar_system.settings import DATA_DIR


MEMORY_COLUMNS: dict[str, str] = {
    "strategy": "VARCHAR",
    "version": "VARCHAR",
    "base_strategy": "VARCHAR",
    "variant_name": "VARCHAR",
    "symbol": "VARCHAR",
    "timeframe": "VARCHAR",
    "broker": "VARCHAR",
    "asset_profile_json": "JSON",
    "broker_profile_json": "JSON",
    "parameters": "JSON",
    "parameters_json": "JSON",
    "metrics": "JSON",
    "backtest_metrics_json": "JSON",
    "walk_forward_metrics_json": "JSON",
    "forward_test_metrics_json": "JSON",
    "score": "DOUBLE",
    "verdict": "VARCHAR",
    "reason_codes": "JSON",
    "promoted": "BOOLEAN",
    "notes": "VARCHAR",
    "created_at": "TIMESTAMP",
}
MEMORY_COLUMN_SET = set(MEMORY_COLUMNS)
MEMORY_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS strategy_memory (
    strategy VARCHAR,
    version VARCHAR,
    base_strategy VARCHAR,
    variant_name VARCHAR,
    symbol VARCHAR,
    timeframe VARCHAR,
    broker VARCHAR,
    asset_profile_json JSON,
    broker_profile_json JSON,
    parameters JSON,
    parameters_json JSON,
    metrics JSON,
    backtest_metrics_json JSON,
    walk_forward_metrics_json JSON,
    forward_test_metrics_json JSON,
    score DOUBLE,
    verdict VARCHAR,
    reason_codes JSON,
    promoted BOOLEAN,
    notes VARCHAR,
    created_at TIMESTAMP
)
"""
MEMORY_ALTER_SQL = {
    "strategy": "ALTER TABLE strategy_memory ADD COLUMN strategy VARCHAR",
    "version": "ALTER TABLE strategy_memory ADD COLUMN version VARCHAR",
    "base_strategy": "ALTER TABLE strategy_memory ADD COLUMN base_strategy VARCHAR",
    "variant_name": "ALTER TABLE strategy_memory ADD COLUMN variant_name VARCHAR",
    "symbol": "ALTER TABLE strategy_memory ADD COLUMN symbol VARCHAR",
    "timeframe": "ALTER TABLE strategy_memory ADD COLUMN timeframe VARCHAR",
    "broker": "ALTER TABLE strategy_memory ADD COLUMN broker VARCHAR",
    "asset_profile_json": "ALTER TABLE strategy_memory ADD COLUMN asset_profile_json JSON",
    "broker_profile_json": "ALTER TABLE strategy_memory ADD COLUMN broker_profile_json JSON",
    "parameters": "ALTER TABLE strategy_memory ADD COLUMN parameters JSON",
    "parameters_json": "ALTER TABLE strategy_memory ADD COLUMN parameters_json JSON",
    "metrics": "ALTER TABLE strategy_memory ADD COLUMN metrics JSON",
    "backtest_metrics_json": "ALTER TABLE strategy_memory ADD COLUMN backtest_metrics_json JSON",
    "walk_forward_metrics_json": "ALTER TABLE strategy_memory ADD COLUMN walk_forward_metrics_json JSON",
    "forward_test_metrics_json": "ALTER TABLE strategy_memory ADD COLUMN forward_test_metrics_json JSON",
    "score": "ALTER TABLE strategy_memory ADD COLUMN score DOUBLE",
    "verdict": "ALTER TABLE strategy_memory ADD COLUMN verdict VARCHAR",
    "reason_codes": "ALTER TABLE strategy_memory ADD COLUMN reason_codes JSON",
    "promoted": "ALTER TABLE strategy_memory ADD COLUMN promoted BOOLEAN",
    "notes": "ALTER TABLE strategy_memory ADD COLUMN notes VARCHAR",
    "created_at": "ALTER TABLE strategy_memory ADD COLUMN created_at TIMESTAMP",
}


def record_strategy_result(
    strategy: str,
    version: str,
    symbol: str,
    timeframe: str,
    parameters: dict[str, object],
    metrics: dict[str, float],
    score: float,
    verdict: str,
    reason_codes: list[str],
    walk_forward_metrics: dict[str, Any] | None = None,
) -> None:
    record_strategy_memory(
        base_strategy=strategy,
        variant_name=strategy,
        version=version,
        symbol=symbol,
        timeframe=timeframe,
        broker="current_broker_demo",
        asset_profile={},
        broker_profile={},
        parameters=parameters,
        backtest_metrics=metrics,
        walk_forward_metrics=walk_forward_metrics or {},
        forward_test_metrics={},
        score=score,
        verdict=verdict,
        reason_codes=reason_codes,
        promoted=False,
        notes="legacy record_strategy_result",
    )


def record_strategy_memory(
    base_strategy: str,
    variant_name: str,
    version: str,
    symbol: str,
    timeframe: str,
    broker: str,
    asset_profile: dict[str, Any],
    broker_profile: dict[str, Any],
    parameters: dict[str, Any],
    backtest_metrics: dict[str, Any],
    walk_forward_metrics: dict[str, Any] | None,
    forward_test_metrics: dict[str, Any] | None,
    score: float,
    verdict: str,
    reason_codes: list[str],
    promoted: bool = False,
    notes: str = "",
) -> None:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(Path(DATA_DIR) / "tar_system.duckdb")) as connection:
        _ensure_memory_table(connection)
        now = datetime.now(timezone.utc)
        params_json = json.dumps(parameters)
        backtest_json = json.dumps(backtest_metrics)
        connection.execute(
            """
            INSERT INTO strategy_memory (
                strategy, version, base_strategy, variant_name, symbol, timeframe, broker,
                asset_profile_json, broker_profile_json, parameters, parameters_json,
                metrics, backtest_metrics_json, walk_forward_metrics_json, forward_test_metrics_json,
                score, verdict, reason_codes, promoted, notes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                base_strategy,
                version,
                base_strategy,
                variant_name,
                symbol,
                timeframe,
                broker,
                json.dumps(asset_profile),
                json.dumps(broker_profile),
                params_json,
                params_json,
                backtest_json,
                backtest_json,
                json.dumps(walk_forward_metrics or {}),
                json.dumps(forward_test_metrics or {}),
                score,
                verdict,
                json.dumps(reason_codes),
                promoted,
                notes,
                now,
            ],
        )


def _ensure_memory_table(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(MEMORY_CREATE_TABLE_SQL)
    existing = {row[1] for row in connection.execute("PRAGMA table_info('strategy_memory')").fetchall()}
    for name in MEMORY_COLUMNS:
        if name not in existing:
            connection.execute(MEMORY_ALTER_SQL[_memory_column(name)])


def update_latest_verdict(strategy: str, symbol: str, timeframe: str, verdict: str, notes: str = "") -> bool:
    path = Path(DATA_DIR) / "tar_system.duckdb"
    if not path.exists():
        return False
    with duckdb.connect(str(path)) as connection:
        _ensure_memory_table(connection)
        row = connection.execute(
            """
            SELECT created_at FROM strategy_memory
            WHERE strategy = ? AND symbol = ? AND timeframe = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [strategy, symbol, timeframe],
        ).fetchone()
        if not row:
            return False
        connection.execute(
            """
            UPDATE strategy_memory
            SET verdict = ?, notes = ?
            WHERE strategy = ? AND symbol = ? AND timeframe = ? AND created_at = ?
            """,
            [verdict, notes, strategy, symbol, timeframe, row[0]],
        )
        return True


def latest_memory_record(strategy: str, symbol: str, timeframe: str) -> dict[str, Any] | None:
    path = Path(DATA_DIR) / "tar_system.duckdb"
    if not path.exists():
        return None
    with duckdb.connect(str(path)) as connection:
        _ensure_memory_table(connection)
        row = connection.execute(
            """
            SELECT strategy, symbol, timeframe, score, verdict, promoted, notes, created_at
            FROM strategy_memory
            WHERE strategy = ? AND symbol = ? AND timeframe = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [strategy, symbol, timeframe],
        ).fetchone()
        if not row:
            return None
        return {
            "strategy": row[0],
            "symbol": row[1],
            "timeframe": row[2],
            "score": row[3],
            "verdict": row[4],
            "promoted": row[5],
            "notes": row[6],
            "created_at": row[7],
        }


def _memory_column(column: str) -> str:
    if column not in MEMORY_COLUMN_SET:
        raise ValueError(f"Unknown memory column: {column}")
    return column

