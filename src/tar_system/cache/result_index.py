"""Ranked result index — one scored row per (strategy, symbol, timeframe, stage).

Replaces glob-based discovery for ranked queries. Written on job completion,
read by dashboard, research loop, and diagnosis tools.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from tar_system.settings import DATA_DIR

DB_PATH = Path(DATA_DIR) / "tar_system.duckdb"


def upsert_result(
    strategy: str,
    symbol: str,
    timeframe: str,
    stage: str,
    score: float,
    verdict: str,
    total_trades: int,
    profit_factor: float,
    max_drawdown: float,
    sharpe_ratio: float = 0.0,
    data_hash: str | None = None,
) -> None:
    _ensure_table()
    with _connect() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO result_index
                (strategy, symbol, timeframe, stage, score, verdict,
                 total_trades, profit_factor, max_drawdown, sharpe_ratio,
                 data_hash, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                strategy, symbol, timeframe, stage,
                float(score), verdict, int(total_trades),
                float(profit_factor), float(max_drawdown), float(sharpe_ratio),
                data_hash, datetime.now(timezone.utc).isoformat(),
            ],
        )


def get_ranked_results(
    min_score: float = 0.0,
    min_trades: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    _ensure_table()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT * FROM result_index
            WHERE score >= ? AND total_trades >= ?
            ORDER BY score DESC
            LIMIT ?
            """,
            [min_score, min_trades, limit],
        ).fetchall()
        columns = [item[0] for item in connection.description] if connection.description else []
    return [dict(zip(columns, row)) for row in rows]


def get_best_by_target() -> list[dict[str, Any]]:
    """One best-scored result per (strategy, symbol, timeframe)."""
    _ensure_table()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT r.* FROM result_index r
            INNER JOIN (
                SELECT strategy, symbol, timeframe, MAX(score) AS max_score
                FROM result_index
                GROUP BY strategy, symbol, timeframe
            ) best
                ON r.strategy = best.strategy
               AND r.symbol   = best.symbol
               AND r.timeframe = best.timeframe
               AND r.score    = best.max_score
            ORDER BY r.score DESC
            """,
        ).fetchall()
        columns = [item[0] for item in connection.description] if connection.description else []
    return [dict(zip(columns, row)) for row in rows]


def result_index_stats() -> dict[str, Any]:
    _ensure_table()
    with _connect() as connection:
        total = connection.execute("SELECT COUNT(*) FROM result_index").fetchone()[0]
        by_verdict = connection.execute(
            "SELECT verdict, COUNT(*) FROM result_index GROUP BY verdict ORDER BY COUNT(*) DESC"
        ).fetchall()
        top5 = connection.execute(
            """
            SELECT strategy, symbol, timeframe, score, verdict, total_trades
            FROM result_index ORDER BY score DESC LIMIT 5
            """
        ).fetchall()
    return {
        "total": int(total),
        "by_verdict": {str(v): int(c) for v, c in by_verdict},
        "top_5": [
            {"strategy": r[0], "symbol": r[1], "timeframe": r[2],
             "score": r[3], "verdict": r[4], "trades": r[5]}
            for r in top5
        ],
    }


def _ensure_table() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS result_index (
                strategy      VARCHAR,
                symbol        VARCHAR,
                timeframe     VARCHAR,
                stage         VARCHAR,
                score         DOUBLE,
                verdict       VARCHAR,
                total_trades  INTEGER,
                profit_factor DOUBLE,
                max_drawdown  DOUBLE,
                sharpe_ratio  DOUBLE,
                data_hash     VARCHAR,
                indexed_at    TIMESTAMP,
                PRIMARY KEY (strategy, symbol, timeframe, stage)
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_result_score ON result_index(score DESC)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_result_verdict ON result_index(verdict, score DESC)"
        )


def _connect(retries: int = 20, delay: float = 0.2) -> duckdb.DuckDBPyConnection:
    for attempt in range(retries):
        try:
            return duckdb.connect(str(DB_PATH))
        except duckdb.IOException:
            if attempt == retries - 1:
                raise
            time.sleep(delay * (attempt + 1))
    return duckdb.connect(str(DB_PATH))
