"""Local DuckDB store for positioning context."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from tar_system.settings import DATA_DIR


DB_PATH = Path(DATA_DIR) / "tar_system.duckdb"


@dataclass
class PositioningRecord:
    source: str
    symbol: str
    date: str
    positioning_score: float
    bias: str
    confidence: float
    notes: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    source_file: str = ""
    file_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def save_positioning_record(record: PositioningRecord) -> PositioningRecord:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    normalised_date = normalise_positioning_date(record.date)
    with duckdb.connect(str(DB_PATH)) as con:
        _ensure_table(con)
        con.execute(
            """
            INSERT INTO positioning_records (
                source, symbol, date, positioning_score, bias, confidence,
                notes, metrics_json, source_file, file_hash, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                record.source,
                record.symbol.upper(),
                normalised_date,
                float(record.positioning_score),
                record.bias,
                float(record.confidence),
                record.notes,
                json.dumps(record.metrics, default=str),
                record.source_file,
                record.file_hash,
                record.created_at,
            ],
        )
    return record


def normalise_positioning_date(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "nat", "none"}:
        return ""
    parsed = pd.to_datetime(text, errors="coerce", utc=False)
    if pd.isna(parsed):
        return text
    return parsed.date().isoformat()


def load_positioning_records(symbol: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(DB_PATH)) as con:
        _ensure_table(con)
        if symbol:
            rows = con.execute(
                """
                SELECT source, symbol, date, positioning_score, bias, confidence,
                       notes, metrics_json, source_file, file_hash, created_at
                FROM positioning_records
                WHERE symbol = ?
                ORDER BY date DESC, created_at DESC
                LIMIT ?
                """,
                [symbol.upper(), limit],
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT source, symbol, date, positioning_score, bias, confidence,
                       notes, metrics_json, source_file, file_hash, created_at
                FROM positioning_records
                ORDER BY date DESC, created_at DESC
                LIMIT ?
                """,
                [limit],
            ).fetchall()
    return [_row_to_dict(row) for row in rows]


def latest_positioning_score(symbol: str) -> dict[str, Any]:
    records = load_positioning_records(symbol, limit=30)
    if not records:
        return {
            "symbol": symbol.upper(),
            "positioning_score": 0.0,
            "bias": "NEUTRAL",
            "confidence": 0.0,
            "sources": [],
            "context_only": True,
        }
    by_source: dict[str, dict[str, Any]] = {}
    for record in records:
        by_source.setdefault(str(record["source"]), record)
    selected = list(by_source.values())
    weighted = sum(float(row["positioning_score"]) * float(row["confidence"]) for row in selected)
    confidence = sum(float(row["confidence"]) for row in selected)
    score = weighted / confidence if confidence else 0.0
    bias = _bias_from_score(score)
    return {
        "symbol": symbol.upper(),
        "positioning_score": round(score, 2),
        "bias": bias,
        "confidence": round(min(1.0, confidence / max(1, len(selected))), 2),
        "sources": selected,
        "context_only": True,
    }


def _ensure_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS positioning_records (
            source TEXT,
            symbol TEXT,
            date TEXT,
            positioning_score DOUBLE,
            bias TEXT,
            confidence DOUBLE,
            notes TEXT,
            metrics_json TEXT,
            source_file TEXT,
            file_hash TEXT,
            created_at TEXT
        )
        """
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_positioning_symbol_date ON positioning_records(symbol, date)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_positioning_source_hash ON positioning_records(source, file_hash)")


def _row_to_dict(row: tuple[Any, ...]) -> dict[str, Any]:
    metrics_raw = row[7] or "{}"
    try:
        metrics = json.loads(metrics_raw)
    except json.JSONDecodeError:
        metrics = {}
    return {
        "source": row[0],
        "symbol": row[1],
        "date": row[2],
        "positioning_score": row[3],
        "bias": row[4],
        "confidence": row[5],
        "notes": row[6],
        "metrics": metrics,
        "source_file": row[8],
        "file_hash": row[9],
        "created_at": row[10],
    }


def _bias_from_score(score: float) -> str:
    if score >= 25:
        return "BULLISH"
    if score <= -25:
        return "BEARISH"
    return "NEUTRAL"
